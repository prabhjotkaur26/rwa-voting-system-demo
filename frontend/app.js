// RWA Voting System - Frontend JavaScript

class VotingClient {
    constructor() {
        // Configuration - Set API endpoint here
        this.API_ENDPOINT = this.getAPIEndpoint();
        this.authToken = null;
        this.currentElectionId = null;
        this.votes = {}; // Track selected votes
        this.resultRefreshInterval = null;

        this.initializeEventListeners();
    }

    // ============================================================================
    // Configuration Methods
    // ============================================================================

    getAPIEndpoint() {
        // Try to get from localStorage
        const saved = localStorage.getItem('apiEndpoint');
        if (saved) return saved;

        // Default - Change this to your deployed API endpoint
        return "https://vxvqzxd6rb.execute-api.ap-south-1.amazonaws.com/prod";
    }

    setAPIEndpoint(endpoint) {
        this.API_ENDPOINT = endpoint;
        localStorage.setItem('apiEndpoint', endpoint);
    }

    formatISTTime(timestamp) {
        // Convert Unix timestamp to IST time format
        const date = new Date(timestamp * 1000);
        // toLocaleString automatically handles the timezone conversion to Asia/Kolkata (IST)
        return date.toLocaleString('en-IN', { 
            timeZone: 'Asia/Kolkata',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });
    }

    // ============================================================================
    // UI State Management
    // ============================================================================

    showSection(sectionId) {
        console.log('Showing section:', sectionId);
        
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
            section.style.display = 'none';
        });

        // Show target section
        const section = document.getElementById(sectionId);
        if (section) {
            section.classList.add('active');
            section.style.display = 'block';
            console.log('Section displayed:', sectionId);
        } else {
            console.error('Section not found:', sectionId);
            return;
        }

        // Scroll to top
        window.scrollTo(0, 0);
    }

    showMessage(containerId, message, type = 'info') {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Check if container itself is the message element
        if (container.classList.contains('message')) {
            // Container IS the message element
            // Use innerHTML to support HTML formatting like <br> tags
            container.innerHTML = message;
            container.className = `message ${type}`;
            container.style.display = 'block';
        } else {
            // Container has a nested message element
            const messageEl = container.querySelector('.message');
            if (messageEl) {
                messageEl.innerHTML = message;
                messageEl.className = `message ${type}`;
                messageEl.style.display = 'block';
            }
        }
        
        // Scroll the message into view
        setTimeout(() => {
            container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
    }

    showSpinner(show = true) {
        const spinner = document.getElementById('loadingSpinner');
        if (spinner) {
            spinner.style.display = show ? 'flex' : 'none';
        }
    }

    showStatusBar(message, duration = 3000) {
        const statusBar = document.getElementById('statusBar');
        const statusText = document.getElementById('statusText');

        if (statusBar && statusText) {
            statusText.textContent = message;
            statusBar.style.display = 'block';

            setTimeout(() => {
                statusBar.style.display = 'none';
            }, duration);
        }
    }

    // ============================================================================
    // API Methods
    // ============================================================================

    async apiCall(endpoint, method = 'GET', body = null) {
        try {
            const options = {
                method,
                headers: {
                    'Content-Type': 'application/json',
                },
            };

            if (body) {
                options.body = JSON.stringify(body);
            }

            const url = `${this.API_ENDPOINT}${endpoint}`;
            console.log(`[API] ${method} ${endpoint}`, body ? `Body: ${JSON.stringify(body)}` : '');
            
            const response = await fetch(url, options);
            const data = await response.json();

            console.log(`[API] Response status: ${response.status}, ok: ${response.ok}`);
            console.log(`[API] Response data:`, data);

            if (!response.ok && !data.success) {
                const errorMsg = data.message || 'API Error';
                console.log(`[API] Throwing error: ${errorMsg}`);
                throw new Error(errorMsg);
            }

            return data;
        } catch (error) {
            console.error('[API] API Error caught:', error.message);
            throw error;
        }
    }

    async sendOTP(mobileNumber) {
        this.showSpinner(true);
        try {
            const normalizedNumber = this.normalizeMobileNumber(mobileNumber);
            console.log('Sending OTP to:', normalizedNumber);
            
            const result = await this.apiCall('/auth/send-otp', 'POST', {
                mobileNumber: normalizedNumber,
                electionId: this.currentElectionId,
            });

            console.log('OTP sent successfully:', result);
            
            // Check if OTP already exists - if so, show message and proceed to verification
            if (result.data.otpAlreadyExists) {
                this.showMessage('authMessage', result.data.message, 'warning');
            } else {
                this.showMessage('authMessage', result.data.message, 'success');
            }
            
            console.log('About to show OTP section');
            this.showOTPSection(mobileNumber);
            this.startOTPTimer();

            return result;
        } catch (error) {
            console.error('SendOTP Error:', error);
            const errorMessage = error.message || 'Failed to send OTP';
            this.showMessage('authMessage', errorMessage, 'error');
            throw error;
        } finally {
            this.showSpinner(false);
        }
    }

    async verifyOTP(mobileNumber, otp) {
        this.showSpinner(true);
        try {
            const normalizedNumber = this.normalizeMobileNumber(mobileNumber);
            const result = await this.apiCall('/auth/verify-otp', 'POST', {
                mobileNumber: normalizedNumber,
                otp,
            });

            this.authToken = result.data.token;
            this.showMessage('otpMessage', result.data.message, 'success');
            
            // Fetch elections
            await this.loadElections();
            
            return result;
        } catch (error) {
            this.showMessage('otpMessage', error.message, 'error');
            throw error;
        } finally {
            this.showSpinner(false);
        }
    }

    async loadElections() {
        try {
            this.showSection('electionSection');
            this.showSpinner(true);
            
            // Fetch real elections from API
            const response = await this.apiCall('/elections', 'GET');
            
            if (response.success && response.data && Array.isArray(response.data)) {
                this.displayElections(response.data);
            } else if (response.data && Array.isArray(response.data)) {
                this.displayElections(response.data);
            } else {
                this.showMessage('electionMessage', 'No elections available', 'warning');
            }
        } catch (error) {
            console.error('Failed to load elections:', error);
            this.showMessage('electionMessage', 'Failed to load elections. Please try again.', 'error');
        } finally {
            this.showSpinner(false);
        }
    }

    displayElections(elections) {
        const electionList = document.getElementById('electionList');
        
        if (!elections || elections.length === 0) {
            electionList.innerHTML = '<p class="no-elections">No elections available at this time.</p>';
            return;
        }

        electionList.innerHTML = elections
            .map(
                (election) => {
                    const startTimeIST = election.startTime ? this.formatISTTime(election.startTime) : 'N/A';
                    const endTimeIST = election.endTime ? this.formatISTTime(election.endTime) : 'N/A';
                    
                    return `
            <div class="election-card" onclick="votingClient.selectElection('${election.electionId}')"
                 style="cursor: pointer;">
                <h3>${election.electionName || election.electionId}</h3>
                <p>${election.description || 'Vote for your preferred candidates'}</p>
                <div style="font-size: 0.85em; color: #666; margin-top: 8px; padding-top: 8px; border-top: 1px solid #ddd;">
                    <div><strong>Start (IST):</strong> ${startTimeIST}</div>
                    <div><strong>End (IST):</strong> ${endTimeIST}</div>
                </div>
                <span class="election-status ${election.status}">${election.status || 'active'}</span>
            </div>
        `;
                }
            )
            .join('');
    }

    async selectElection(electionId) {
        console.log('═══════════════════════════════════════════════════════');
        console.log('selectElection() called with electionId:', electionId);
        console.log('═══════════════════════════════════════════════════════');
        
        this.currentElectionId = electionId;
        
        // Before showing voting interface, check if user has already voted in this election
        // by calling send-otp with the electionId - this triggers the duplicate vote check
        try {
            const mobileNumber = document.getElementById('mobileNumber').value;
            const normalizedNumber = this.normalizeMobileNumber(mobileNumber);
            
            console.log('Step 1: Got mobile number:', normalizedNumber);
            console.log('Step 2: About to call send-otp with electionId...');
            console.log('Request body:', {
                mobileNumber: normalizedNumber,
                electionId: electionId
            });
            
            // This call will check for duplicate votes if electionId is provided
            const response = await this.apiCall('/auth/send-otp', 'POST', {
                mobileNumber: normalizedNumber,
                electionId: electionId
            });
            
            // If we reach here, voter verified and hasn't already voted - proceed to voting
            console.log('Step 3: send-otp succeeded (no duplicate vote)');
            console.log('Response:', response);
            console.log('✓ User can vote - proceeding to voting interface');
            this.showSection('votingSection');
            this.loadVotingInterface(electionId);
        } catch (error) {
            // Show error message on election selection screen
            const errorMsg = error.message || 'Failed to load election';
            console.error('❌ Step 2b: send-otp failed with error:', errorMsg);
            console.error('Full error:', error);
            
            // Check if this is a duplicate vote error
            console.log('Checking if error includes "already voted"...');
            console.log('Error message:', errorMsg);
            console.log('Includes "already voted"?', errorMsg.includes('already voted'));
            
            if (errorMsg.includes('already voted')) {
                console.log('✓ Recognized as ALREADY_VOTED error');
                const userMessage = `
                    <strong>❌ You have already voted in this election!</strong>
                    <br><br>
                    You cannot vote again. Each voter can only vote once per election.
                `;
                this.showMessage(
                    'electionMessage', 
                    userMessage, 
                    'error'
                );
                console.log('✓ Error message displayed on election selection screen');
                console.log('User friendly message:', userMessage);

            } else {
                console.log('Different error, showing generic message');
                // Show other errors but don't proceed to voting
                this.showMessage('electionMessage', errorMsg, 'error');
            }
            
            console.log('✓ Returning without showing voting section');
            // IMPORTANT: Do NOT proceed to voting section on any error
            // User stays on election selection screen until error is resolved
            return;
        }
    }

    async loadVotingInterface(electionId) {
        this.showSpinner(true);
        try {
            // Fetch real candidates/posts from API
            const response = await this.apiCall(`/elections/${electionId}/posts`, 'GET');
            
            let posts = [];
            if (response.success && response.data) {
                posts = response.data.posts || response.data;
            } else if (response.data) {
                posts = response.data.posts || response.data;
            }
            
            if (posts && Array.isArray(posts)) {
                this.displayVotingInterface(posts);
            } else {
                this.showMessage('votingMessage', 'Failed to load candidates. Please try again.', 'error');
                this.showSection('electionSection');
            }
        } catch (error) {
            console.error('Failed to load voting interface:', error);
            this.showMessage('votingMessage', 'Failed to load voting interface. Please try again.', 'error');
            this.showSection('electionSection');
        } finally {
            this.showSpinner(false);
        }
    }

    displayVotingInterface(posts) {
        const container = document.getElementById('votingContainer');
        const titleEl = document.getElementById('votingTitle');

        titleEl.textContent = `Cast Your Votes`;
        
        // Initialize votes object to track selections
        this.votes = {};
        
        if (!posts || posts.length === 0) {
            container.innerHTML = '<p class="no-posts">No posts available for voting.</p>';
            return;
        }

        container.innerHTML = posts
            .map((post) => this.createPostHTML(post))
            .join('');

        // Add event listeners to radio buttons
        document.querySelectorAll('.candidate-option input[type="radio"]').forEach((radio) => {
            radio.addEventListener('change', (e) => this.handleVoteSelection(e));
        });
    }

    createPostHTML(post) {
        const candidates = post.candidates || [];
        
        if (candidates.length === 0) {
            return `
        <div class="post-section">
            <div class="post-title">${post.postId}. ${post.postName}</div>
            <p>No candidates available for this post.</p>
        </div>
            `;
        }
        
        return `
        <div class="post-section">
            <div class="post-title">${post.postId}. ${post.postName}</div>
            <div class="candidates-grid">
                ${candidates
                    .map(
                        (candidate) => `
                    <label class="candidate-option">
                        <input
                            type="radio"
                            name="post-${post.postId}"
                            value="${candidate.candidateId}"
                            data-post-id="${post.postId}"
                        >
                        ${candidate.imageUrl ? `<div class="candidate-image"><img src="${candidate.imageUrl}" alt="${candidate.name || candidate.candidateName}"></div>` : ''}
                        <div class="candidate-info">
                            <div class="candidate-name">${candidate.name || candidate.candidateName}</div>
                            ${candidate.party ? `<div class="candidate-party">${candidate.party}</div>` : ''}
                        </div>
                        <div class="vote-status"></div>
                    </label>
                `
                    )
                    .join('')}
            </div>
        </div>
        `;
    }

    handleVoteSelection(event) {
        const postId = event.target.dataset.postId;
        const candidateId = event.target.value;

        this.votes[postId] = candidateId;

        // Update UI
        document.querySelectorAll(`input[name="post-${postId}"]`).forEach((radio) => {
            const status = radio.parentElement.querySelector('.vote-status');
            if (radio.value === candidateId) {
                radio.parentElement.classList.add('selected');
                status.textContent = '✓ Selected';
                status.classList.add('selected');
            } else {
                radio.parentElement.classList.remove('selected');
                status.textContent = '';
                status.classList.remove('selected');
            }
        });
    }

    async submitVotes() {
        // Get all posts from DOM to determine total number of posts
        const postElements = document.querySelectorAll('.post-section');
        const totalPosts = postElements.length;
        const postsWithVotes = Object.keys(this.votes).length;
        
        if (totalPosts === 0) {
            this.showMessage(
                'votingMessage',
                'No posts available for voting.',
                'error'
            );
            return;
        }
        
        if (postsWithVotes < totalPosts) {
            this.showMessage(
                'votingMessage',
                `Please vote for all ${totalPosts} posts. You've voted for ${postsWithVotes}/${totalPosts}.`,
                'error'
            );
            return;
        }

        this.showSpinner(true);
        try {
            // Submit votes one by one
            const mobileNumber = this.normalizeMobileNumber(document.getElementById('mobileNumber').value);

            for (const [postId, candidateId] of Object.entries(this.votes)) {
                await this.apiCall('/vote/cast-vote', 'POST', {
                    mobileNumber,
                    electionId: this.currentElectionId,
                    postId,
                    candidateId,
                });
            }

            this.showSection('successSection');
        } catch (error) {
            this.showMessage('votingMessage', `Failed to submit votes: ${error.message}`, 'error');
        } finally {
            this.showSpinner(false);
        }
    }

    async getResults(electionId) {
        this.showSpinner(true);
        try {
            const result = await this.apiCall(`/results/${electionId}`, 'GET');
            this.displayResults(result.data.results);
        } catch (error) {
            this.showMessage('resultsSection', 'Failed to load results', 'error');
        } finally {
            this.showSpinner(false);
        }
    }

    displayResults(results) {
        const container = document.getElementById('resultsContainer');

        container.innerHTML = Object.entries(results)
            .map(([postId, post]) => this.createResultHTML(postId, post))
            .join('');
    }

    createResultHTML(postId, post) {
        const maxVotes = Math.max(...post.candidates.map((c) => c.votes), 1);

        return `
        <div class="result-post">
            <div class="result-post-title">${postId}. ${post.postName}</div>
            <div class="result-post-subtitle">Total votes: ${post.totalVotes}</div>
            <div class="result-candidates">
                ${post.candidates
                    .map((candidate) => {
                        const percentage = maxVotes > 0 ? (candidate.votes / maxVotes) * 100 : 0;
                        return `
                    <div class="result-candidate">
                        <div class="result-candidate-info">
                            <div class="result-candidate-name">${candidate.candidateName}</div>
                            <div class="result-vote-bar">
                                <div class="result-vote-fill" style="width: ${percentage}%"></div>
                            </div>
                        </div>
                        <div class="result-vote-count">${candidate.votes}</div>
                    </div>
                    `;
                    })
                    .join('')}
            </div>
        </div>
        `;
    }

    startAutoRefreshResults(electionId) {
        const checkbox = document.getElementById('autoRefreshCheckbox');

        if (checkbox.checked) {
            this.resultRefreshInterval = setInterval(() => {
                this.getResults(electionId);
            }, 5000);
        } else {
            clearInterval(this.resultRefreshInterval);
        }
    }

    // ============================================================================
    // Utility Methods
    // ============================================================================

    normalizeMobileNumber(mobile) {
        let normalized = mobile.replace(/\D/g, '');
        if (normalized.length === 12) {
            normalized = normalized.slice(2); // Remove 91
        } else if (normalized.length === 11) {
            normalized = normalized.slice(1); // Remove 0
        }
        return normalized;
    }

    startOTPTimer() {
        let seconds = 300; // 5 minutes
        const timerEl = document.getElementById('otpTimer');

        const interval = setInterval(() => {
            seconds--;
            const minutes = Math.floor(seconds / 60);
            const secs = seconds % 60;
            timerEl.textContent = `OTP expires in: ${minutes}:${secs < 10 ? '0' : ''}${secs}`;

            if (seconds <= 0) {
                clearInterval(interval);
                timerEl.textContent = 'OTP Expired';
                timerEl.style.color = 'var(--danger-color)';
            }
        }, 1000);
    }

    showOTPSection(mobileNumber) {
        console.log('showOTPSection called with:', mobileNumber);
        
        const displayMobile = document.getElementById('displayMobile');
        if (!displayMobile) {
            console.error('displayMobile element not found');
            return;
        }
        
        const maskedNumber = this.maskMobileNumber(mobileNumber);
        console.log('Masked number:', maskedNumber);
        displayMobile.textContent = maskedNumber;

        this.showSection('otpSection');
        const otpInput = document.getElementById('otp');
        if (otpInput) {
            otpInput.focus();
            console.log('OTP input focused');
        } else {
            console.error('OTP input element not found');
        }
    }

    maskMobileNumber(mobile) {
        const normalized = this.normalizeMobileNumber(mobile);
        return `****${normalized.slice(-4)}`;
    }

    // ============================================================================
    // Event Listeners
    // ============================================================================

    initializeEventListeners() {
        // Auth form
        const authForm = document.getElementById('authForm');
        if (authForm) {
            authForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const mobileNumber = document.getElementById('mobileNumber').value;
                this.sendOTP(mobileNumber);
            });
        }

        // OTP form
        const otpForm = document.getElementById('otpForm');
        if (otpForm) {
            otpForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const mobileNumber = document.getElementById('mobileNumber').value;
                const otp = document.getElementById('otp').value;
                this.verifyOTP(mobileNumber, otp);
            });
        }

        // Resend OTP
        const resendBtn = document.getElementById('resendOtpBtn');
        if (resendBtn) {
            resendBtn.addEventListener('click', () => {
                const mobileNumber = document.getElementById('mobileNumber').value;
                this.sendOTP(mobileNumber);
            });
        }

        // Submit votes
        const submitBtn = document.getElementById('submitVotesBtn');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => {
                this.submitVotes();
            });
        }

        // Refresh results
        const refreshResultsBtn = document.getElementById('refreshResultsBtn');
        if (refreshResultsBtn) {
            refreshResultsBtn.addEventListener('click', () => {
                this.getResults(this.currentElectionId);
            });
        }

        // Auto-refresh toggle
        const autoRefreshCheckbox = document.getElementById('autoRefreshCheckbox');
        if (autoRefreshCheckbox) {
            autoRefreshCheckbox.addEventListener('change', () => {
                this.startAutoRefreshResults(this.currentElectionId);
            });
        }

        // Logout buttons
        ['logoutBtn', 'logoutFromResultsBtn', 'logoutFromSuccessBtn'].forEach((id) => {
            const btn = document.getElementById(id);
            if (btn) {
                btn.addEventListener('click', () => {
                    this.logout();
                });
            }
        });

        // OTP input auto-focus
        const otpInput = document.getElementById('otp');
        if (otpInput) {
            otpInput.addEventListener('input', (e) => {
                if (e.target.value.length === 6) {
                    const form = document.getElementById('otpForm');
                    if (form) {
                        form.dispatchEvent(new Event('submit', { bubbles: true }));
                    }
                }
            });
        }
    }

    logout() {
        this.authToken = null;
        this.currentElectionId = null;
        this.votes = {};
        clearInterval(this.resultRefreshInterval);

        document.getElementById('mobileNumber').value = '';
        document.getElementById('otp').value = '';

        this.showSection('authSection');
        this.showStatusBar('Logged out successfully');
    }
}

// ============================================================================
// Initialize Application
// ============================================================================

let votingClient;

document.addEventListener('DOMContentLoaded', () => {
    try {
        console.log('DOM Content Loaded - Initializing RWA Voting System');
        votingClient = new VotingClient();
        console.log('RWA Voting System initialized successfully');
        console.log('API Endpoint:', votingClient.API_ENDPOINT);
        
        // Verify sections exist
        console.log('Checking if sections exist:');
        console.log('authSection:', document.getElementById('authSection') ? 'FOUND' : 'NOT FOUND');
        console.log('otpSection:', document.getElementById('otpSection') ? 'FOUND' : 'NOT FOUND');
        console.log('electionSection:', document.getElementById('electionSection') ? 'FOUND' : 'NOT FOUND');
        console.log('votingSection:', document.getElementById('votingSection') ? 'FOUND' : 'NOT FOUND');
    } catch (error) {
        console.error('Failed to initialize RWA Voting System:', error);
        alert('Failed to initialize the application. Check browser console for details.');
    }
});
