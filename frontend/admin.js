// RWA Voting System - Admin Panel JavaScript

class AdminApp {
    constructor() {
        this.API_ENDPOINT = this.getAPIEndpoint();
        this.adminToken = null;
        this.adminUser = null;
        this.elections = [];
        this.candidates = [];
        this.isLoggedIn = false;

        // Check if already logged in
        this.checkAuthStatus();
    }

    // ============================================================================
    // Timezone Helper Methods (IST)
    // ============================================================================

    /**
     * Convert datetime-local input (browser local time) to IST Unix timestamp
     * This ensures elections are always created with IST times
     */
    convertDatetimeToISTTimestamp(datetimeLocalValue) {
        if (!datetimeLocalValue) return 0;
        
        // Parse the datetime-local value and interpret it as IST time
        // User enters "2026-04-18T17:30" - we treat this as 17:30 IST on 2026-04-18
        // IST is UTC+5:30, so we add "+05:30" to the ISO string
        const istDateTime = datetimeLocalValue + ":00+05:30";
        const date = new Date(istDateTime);
        
        return Math.floor(date.getTime() / 1000); // Return Unix timestamp
    }

    /**
     * Format Unix timestamp to IST readable format
     */
    formatTimestampToIST(timestamp) {
        if (!timestamp) return 'N/A';
        const date = new Date(timestamp * 1000);
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
    // Authentication Methods
    // ============================================================================

    checkAuthStatus() {
        const token = localStorage.getItem('adminToken');
        const user = localStorage.getItem('adminUser');

        if (token && user) {
            this.adminToken = token;
            this.adminUser = JSON.parse(user);
            this.isLoggedIn = true;
            this.showAdminPanel();
        } else {
            this.showLoginModal();
        }
    }

    showLoginModal() {
        document.getElementById('loginModal').classList.remove('hidden');
        document.querySelector('.admin-container').style.display = 'none';
    }

    showAdminPanel() {
        document.getElementById('loginModal').classList.add('hidden');
        document.querySelector('.admin-container').style.display = 'flex';
        document.getElementById('adminUser').textContent = `👤 ${this.adminUser.username}`;
        this.initializeEventListeners();
        this.loadElections();
        this.loadCandidates();
        this.loadDashboardStats();
    }

    async handleLogin(event) {
        event.preventDefault();

        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value.trim();
        const errorDiv = document.getElementById('loginError');

        if (!username || !password) {
            this.showLoginError('Please enter username and password');
            return;
        }

        this.showSpinner(true);

        try {
            const response = await this.apiCall('/admin/auth/login', 'POST', {
                username,
                password,
            });

            if (response.data && response.data.token) {
                // Store token and user info
                localStorage.setItem('adminToken', response.data.token);
                localStorage.setItem('adminUser', JSON.stringify({
                    username: response.data.username,
                    adminId: response.data.adminId,
                    expiresAt: Date.now() + (response.data.expiresIn * 1000),
                }));

                this.adminToken = response.data.token;
                this.adminUser = {
                    username: response.data.username,
                    adminId: response.data.adminId,
                };
                this.isLoggedIn = true;

                // Clear form
                document.getElementById('loginForm').reset();
                
                // Show admin panel
                this.showAdminPanel();
            } else {
                this.showLoginError('Login failed. Please try again.');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showLoginError(error.message || 'Invalid credentials. Please try again.');
        } finally {
            this.showSpinner(false);
        }
    }

    showLoginError(message) {
        const errorDiv = document.getElementById('loginError');
        errorDiv.textContent = message;
        errorDiv.classList.add('show');
        setTimeout(() => {
            errorDiv.classList.remove('show');
        }, 5000);
    }

    logout() {
        localStorage.removeItem('adminToken');
        localStorage.removeItem('adminUser');
        this.adminToken = null;
        this.adminUser = null;
        this.isLoggedIn = false;
        window.location.reload();
    }

    // ============================================================================
    // Configuration Methods
    // ============================================================================

    getAPIEndpoint() {
        const saved = localStorage.getItem('apiEndpoint');
        if (saved) return saved;
        return "https://vxvqzxd6rb.execute-api.ap-south-1.amazonaws.com/prod";
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

            // Add auth token if logged in
            if (this.adminToken) {
                options.headers['Authorization'] = `Bearer ${this.adminToken}`;
            }

            if (body) {
                options.body = JSON.stringify(body);
            }

            const response = await fetch(`${this.API_ENDPOINT}${endpoint}`, options);
            const data = await response.json();

            if (!response.ok) {
                // Check for authentication errors
                if (response.status === 401) {
                    this.logout();
                    throw new Error('Session expired. Please login again');
                }
                throw new Error(data.message || `API Error: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // ============================================================================
    // Dashboard Methods
    // ============================================================================

    async loadDashboardStats() {
        this.showSpinner(true);
        try {
            const result = await this.apiCall('/admin/stats', 'GET');

            if (result.data) {
                const stats = result.data;
                document.getElementById('activeElectionsCount').textContent = stats.activeElections || 0;
                document.getElementById('totalVotersCount').textContent = stats.totalVoters || 0;
                document.getElementById('totalVotesCount').textContent = stats.totalVotesCast || 0;
                document.getElementById('totalCandidatesCount').textContent = stats.totalCandidates || 0;
                
                // Show participation rate if available
                if (stats.voterParticipationRate !== undefined) {
                    const participationDiv = document.querySelector('[data-stat="participation"]');
                    if (participationDiv) {
                        participationDiv.innerHTML = `
                            <h4>Voter Participation</h4>
                            <p style="font-size: 2rem; color: #667eea; margin: 0.5rem 0;">
                                ${stats.voterParticipationRate}%
                            </p>
                            <p style="color: #666; font-size: 0.9rem;">
                                ${stats.totalVotesCast} of ${stats.totalVoters} voters
                            </p>
                        `;
                    }
                }
            }

            console.log('Dashboard stats loaded');
        } catch (error) {
            console.error('Error loading dashboard stats:', error);
            this.showAlert('dashboardAlert', `Failed to load stats: ${error.message}`, 'error');
        } finally {
            this.showSpinner(false);
        }
    }

    async refreshDashboard() {
        await this.loadDashboardStats();
    }

    // ============================================================================
    // Elections Methods
    // ============================================================================

    async loadElections() {
        try {
            const result = await this.apiCall('/admin/elections', 'GET');
            
            // Handle response - data might be in result.data or directly in result
            this.elections = result.data || result || [];
            
            this.displayElections();
            this.populateElectionSelects();
        } catch (error) {
            console.error('Error loading elections:', error);
            this.elections = [];
            this.displayElections();
            this.showAlert('electionAlert', `Error loading elections: ${error.message}`, 'error');
        }
    }

    displayElections() {
        const container = document.getElementById('activeElectionsList');
        if (this.elections.length === 0) {
            container.innerHTML = '<p style="color: #999;">No elections created yet</p>';
            return;
        }

        container.innerHTML = `
            <table class="admin-table">
                <thead>
                    <tr>
                        <th>Election ID</th>
                        <th>Name</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${this.elections
                        .map(
                            (election) => `
                        <tr>
                            <td><code>${election.electionId}</code></td>
                            <td>${election.electionName}</td>
                            <td>
                                <select onchange="adminApp.updateElectionStatus('${election.electionId}', this.value)" style="padding: 0.3rem 0.5rem; border-radius: 4px;">
                                    <option value="active" ${election.status === 'active' ? 'selected' : ''}>Active</option>
                                    <option value="inactive" ${election.status === 'inactive' ? 'selected' : ''}>Inactive</option>
                                    <option value="ended" ${election.status === 'ended' ? 'selected' : ''}>Ended</option>
                                </select>
                            </td>
                            <td>
                                <button class="admin-btn" style="padding: 0.3rem 0.8rem; font-size: 0.85rem; margin-right: 0.3rem;" onclick="adminApp.editElection('${election.electionId}')">Edit</button>
                                <button class="admin-btn admin-danger" style="padding: 0.3rem 0.8rem; font-size: 0.85rem;" onclick="adminApp.deleteElection('${election.electionId}')">Delete</button>
                            </td>
                        </tr>
                    `
                        )
                        .join('')}
                </tbody>
            </table>
        `;
    }

    populateElectionSelects() {
        const selects = [
            'candidateElectionId',
            'resultsElectionId',
        ];

        selects.forEach((selectId) => {
            const select = document.getElementById(selectId);
            if (select) {
                select.innerHTML = '<option value="">Select an election...</option>';
                this.elections.forEach((election) => {
                    const option = document.createElement('option');
                    option.value = election.electionId;
                    option.textContent = election.electionName;
                    select.appendChild(option);
                });
            }
        });
    }

    async createElection() {
        const electionId = document.getElementById('electionId').value;
        const electionName = document.getElementById('electionName').value;
        const description = document.getElementById('electionDescription').value;
        const startTimeStr = document.getElementById('electionStartTime').value;
        const endTimeStr = document.getElementById('electionEndTime').value;

        if (!electionId || !electionName || !startTimeStr || !endTimeStr) {
            this.showAlert('electionAlert', 'Please fill in all required fields', 'error');
            return;
        }

        // Convert datetime-local inputs to IST Unix timestamps
        const startTime = this.convertDatetimeToISTTimestamp(startTimeStr);
        const endTime = this.convertDatetimeToISTTimestamp(endTimeStr);

        if (startTime <= 0 || endTime <= 0) {
            this.showAlert('electionAlert', 'Please enter valid date and time', 'error');
            return;
        }

        if (endTime <= startTime) {
            this.showAlert('electionAlert', 'End time must be after start time', 'error');
            return;
        }

        this.showSpinner(true);
        try {
            // Use existing /admin/elections endpoint
            const result = await this.apiCall('/admin/elections', 'POST', {
                electionId,
                electionName,
                description,
                startTime,
                endTime,
            });

            this.showAlert('electionAlert', 'Election created successfully', 'success');
            document.getElementById('createElectionForm').reset();
            
            // Reload elections
            await this.loadElections();
        } catch (error) {
            console.error('Error creating election:', error);
            this.showAlert('electionAlert', `Error: ${error.message}`, 'error');
        } finally {
            this.showSpinner(false);
        }
    }

    async updateElectionStatus(electionId, status) {
        try {
            // Use existing /admin/elections endpoint
            await this.apiCall(`/admin/elections/${electionId}`, 'PUT', {
                status,
            });
            await this.loadElections();
        } catch (error) {
            console.error('Error updating election status:', error);
            this.showAlert('electionAlert', `Error: ${error.message}`, 'error');
        }
    }

    async editElection(electionId) {
        const election = this.elections.find(e => e.electionId === electionId);
        if (!election) {
            this.showAlert('electionAlert', 'Election not found', 'error');
            return;
        }

        const newName = prompt('Edit election name:', election.electionName);
        if (newName && newName !== election.electionName) {
            this.showSpinner(true);
            try {
                // Use existing /admin/elections endpoint
                await this.apiCall(`/admin/elections/${electionId}`, 'PUT', {
                    electionName: newName,
                });
                await this.loadElections();
                this.showAlert('electionAlert', 'Election updated successfully', 'success');
            } catch (error) {
                console.error('Error updating election:', error);
                this.showAlert('electionAlert', `Error: ${error.message}`, 'error');
            } finally {
                this.showSpinner(false);
            }
        }
    }

    async deleteElection(electionId) {
        if (!confirm('Are you sure you want to delete this election?')) {
            return;
        }

        this.showSpinner(true);
        try {
            // Use existing /admin/elections endpoint
            await this.apiCall(`/admin/elections/${electionId}`, 'DELETE');
            this.showAlert('electionAlert', 'Election deleted successfully', 'success');
            await this.loadElections();
        } catch (error) {
            console.error('Error deleting election:', error);
            this.showAlert('electionAlert', `Error: ${error.message}`, 'error');
        } finally {
            this.showSpinner(false);
        }
    }

    // ============================================================================
    // Candidates Methods
    // ============================================================================

    async addCandidate() {
        const electionId = document.getElementById('candidateElectionId').value;
        const postId = document.getElementById('postId').value;
        const candidateName = document.getElementById('candidateName').value;
        const imageUrl = document.getElementById('candidateImageUrl').value;
        const description = document.getElementById('candidateDescription').value;

        if (!electionId || !postId || !candidateName) {
            this.showAlert('candidateAlert', 'Please fill in all required fields', 'error');
            return;
        }

        this.showSpinner(true);
        try {
            // Generate candidate ID - keep it short (within 32 chars)
            // Format: cand-{timestamp} (example: cand-1776531941569)
            const candidateId = `cand-${Date.now()}`;

            // Send in the format expected by backend: candidates array
            const result = await this.apiCall('/admin/candidates', 'POST', {
                electionId,
                postId,
                candidates: [
                    {
                        candidateId,
                        candidateName,
                        imageUrl: imageUrl || undefined,
                        bio: description || undefined
                    }
                ]
            });

            this.showAlert('candidateAlert', 'Candidate added successfully', 'success');
            document.getElementById('addCandidateForm').reset();
            
            // Reload candidates list
            await this.loadCandidates();
        } catch (error) {
            console.error('Error adding candidate:', error);
            this.showAlert('candidateAlert', `Error: ${error.message}`, 'error');
        } finally {
            this.showSpinner(false);
        }
    }

    async loadCandidates() {
        try {
            const result = await this.apiCall('/admin/candidates', 'GET');
            
            // Handle response - data might be in result.data or directly in result
            this.candidates = result.data || result || [];
            
            this.displayCandidates();
        } catch (error) {
            console.error('Error loading candidates:', error);
            this.candidates = [];
            this.displayCandidates();
            console.log('Note: GET /admin/candidates endpoint may not be deployed yet');
        }
    }

    displayCandidates() {
        const container = document.getElementById('candidatesList');
        if (this.candidates.length === 0) {
            container.innerHTML = '<p style="color: #999;">No candidates added yet</p>';
            return;
        }

        const candidatesByElection = {};
        this.candidates.forEach(c => {
            if (!candidatesByElection[c.electionId]) {
                candidatesByElection[c.electionId] = [];
            }
            candidatesByElection[c.electionId].push(c);
        });

        let html = '';
        Object.entries(candidatesByElection).forEach(([electionId, candidates]) => {
            html += `<div style="margin-bottom: 2rem;">
                <h4>${electionId}</h4>
                <table class="admin-table">
                    <thead>
                        <tr>
                            <th>Post</th>
                            <th>Name</th>
                            <th>Candidate ID</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${candidates.map(c => `
                            <tr>
                                <td>${c.postId}</td>
                                <td>${c.name || c.candidateName || '-'}</td>
                                <td>${c.candidateId || '-'}</td>
                                <td>
                                    <button class="admin-btn" style="padding: 0.3rem 0.8rem; font-size: 0.85rem;" onclick="adminApp.viewCandidate('${c.candidateId}')">View</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>`;
        });
        
        container.innerHTML = html || '<p style="color: #999;">No candidates added yet</p>';
    }

    async viewCandidate(candidateId) {
        const candidate = this.candidates.find(c => c.candidateId === candidateId);
        if (candidate) {
            const details = `
Candidate ID: ${candidate.candidateId}
Name: ${candidate.name || candidate.candidateName || 'N/A'}
Post: ${candidate.postId || 'N/A'}
Election: ${candidate.electionId || 'N/A'}
Image: ${candidate.imageUrl || 'N/A'}
Bio: ${candidate.bio || candidate.description || 'N/A'}
Created (IST): ${this.formatTimestampToIST(candidate.createdAt)}
            `;
            alert(details);
        }
    }

    async editCandidate(candidateId) {
        const candidate = this.candidates.find(c => c.candidateId === candidateId);
        if (!candidate) {
            this.showAlert('candidateAlert', 'Candidate not found', 'error');
            return;
        }

        const newName = prompt('Edit candidate name:', candidate.candidateName);
        if (newName && newName !== candidate.candidateName) {
            this.showSpinner(true);
            try {
                // Use existing /admin/candidates endpoint
                await this.apiCall(`/admin/candidates/${candidateId}`, 'PUT', {
                    candidateName: newName,
                });
                await this.loadCandidates();
                this.showAlert('candidateAlert', 'Candidate updated successfully', 'success');
            } catch (error) {
                console.error('Error updating candidate:', error);
                this.showAlert('candidateAlert', `Error: ${error.message}`, 'error');
            } finally {
                this.showSpinner(false);
            }
        }
    }

    async deleteCandidate(candidateId) {
        if (!confirm('Are you sure you want to delete this candidate?')) {
            return;
        }

        this.showSpinner(true);
        try {
            // Use existing /admin/candidates endpoint
            await this.apiCall(`/admin/candidates/${candidateId}`, 'DELETE');
            this.showAlert('candidateAlert', 'Candidate deleted successfully', 'success');
            await this.loadCandidates();
        } catch (error) {
            console.error('Error deleting candidate:', error);
            this.showAlert('candidateAlert', `Error: ${error.message}`, 'error');
        } finally {
            this.showSpinner(false);
        }
    }

    // ============================================================================
    // Results Methods
    // ============================================================================

    async loadElectionResults() {
        const electionId = document.getElementById('resultsElectionId').value;
        if (!electionId) {
            this.showAlert('resultsContainer', 'Please select an election', 'error');
            return;
        }

        this.showSpinner(true);
        try {
            console.log('Loading results for:', electionId);

            const result = await this.apiCall(`/results/${electionId}`, 'GET');
            // Extract results from the API response structure
            const resultsData = result.data?.results || result.results || result;
            this.displayResults(resultsData);
        } catch (error) {
            console.error('Error loading results:', error);
            document.getElementById('resultsContainer').innerHTML = `
                <div class="alert alert-error">
                    Error loading results: ${error.message}
                </div>
            `;
        } finally {
            this.showSpinner(false);
        }
    }

    displayResults(results) {
        const container = document.getElementById('resultsContainer');

        const html = `
            <div style="margin-bottom: 2rem;">
                <h2>Election Results</h2>
                ${Object.entries(results)
                    .map(([postId, post]) => this.createResultHTML(postId, post))
                    .join('')}
            </div>
            <button class="export-btn" onclick="adminApp.exportResults()">📊 Export Results</button>
        `;

        container.innerHTML = html;
    }

    createResultHTML(postId, post) {
        const maxVotes = Math.max(...post.candidates.map((c) => c.votes || 0), 1);

        return `
            <div class="admin-card" style="margin-bottom: 1rem;">
                <h3>${postId}. ${post.postName || 'Position'}</h3>
                <p style="color: #666; margin-bottom: 1rem;">Total votes: ${post.totalVotes || 0}</p>
                ${post.candidates
                    .map((candidate) => {
                        const percentage = maxVotes > 0 ? ((candidate.votes || 0) / maxVotes) * 100 : 0;
                        return `
                    <div style="margin-bottom: 1rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <strong>${candidate.candidateName}</strong>
                            <span>${candidate.votes || 0} votes (${Math.round(percentage)}%)</span>
                        </div>
                        <div style="background: #e2e8f0; height: 24px; border-radius: 4px; overflow: hidden;">
                            <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); height: 100%; width: ${percentage}%;"></div>
                        </div>
                    </div>
                `;
                    })
                    .join('')}
            </div>
        `;
    }

    async exportResults() {
        const electionId = document.getElementById('resultsElectionId').value;
        if (!electionId) {
            alert('Please select an election');
            return;
        }

        this.showSpinner(true);
        try {
            // Request HTML format for export
            const result = await this.apiCall(`/results/${electionId}/export`, 'POST', {
                format: 'html'
            });

            const htmlContent = result.data?.content || result.content;
            const filename = result.data?.filename || result.filename || `election-results-${Date.now()}.html`;

            // Validate we got content
            if (!htmlContent || typeof htmlContent !== 'string' || htmlContent.length === 0) {
                throw new Error('No content received from server');
            }

            // Create blob from HTML content
            const blob = new Blob([htmlContent], { type: 'text/html; charset=utf-8' });
            
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            // Keep .html extension - browsers can open HTML files directly
            link.download = filename || 'election-results.html';
            
            // Trigger download
            document.body.appendChild(link);
            link.click();
            
            // Cleanup after a short delay to ensure download starts
            setTimeout(() => {
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
            }, 100);

            this.showAlert('resultsContainer', 'Results exported successfully! Your HTML file has been downloaded. You can open it in any browser or print it to PDF.', 'success');
        } catch (error) {
            console.error('Error exporting results:', error);
            const errorMsg = error.message || 'Unknown error occurred';
            this.showAlert('resultsContainer', `Error exporting results: ${errorMsg}`, 'error');
            alert(`Error exporting results: ${errorMsg}`);
        } finally {
            this.showSpinner(false);
        }
    }

    // ============================================================================
    // UI Methods
    // ============================================================================

    initializeEventListeners() {
        // Panel navigation
        document.querySelectorAll('.nav-btn').forEach((btn) => {
            btn.addEventListener('click', (e) => {
                const panelId = e.target.dataset.panel;
                this.showPanel(panelId);

                // Update active button
                document.querySelectorAll('.nav-btn').forEach((b) => b.classList.remove('active'));
                e.target.classList.add('active');
            });
        });

        // Form submissions
        const createElectionForm = document.getElementById('createElectionForm');
        if (createElectionForm) {
            createElectionForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.createElection();
            });
        }

        const addCandidateForm = document.getElementById('addCandidateForm');
        if (addCandidateForm) {
            addCandidateForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addCandidate();
            });
        }

        const bulkImportForm = document.getElementById('bulkImportForm');
        if (bulkImportForm) {
            bulkImportForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleBulkImport();
            });
        }

        // Logout button
        const logoutBtn = document.getElementById('adminLogoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                this.logout();
            });
        }
    }

    showPanel(panelId) {
        // Hide all panels
        document.querySelectorAll('.admin-panel').forEach((panel) => {
            panel.classList.remove('active');
        });

        // Show target panel
        const panel = document.getElementById(panelId);
        if (panel) {
            panel.classList.add('active');
            console.log('Showing panel:', panelId);

            // Load fresh data if needed
            if (panelId === 'dashboard') {
                this.loadDashboardStats();
            } else if (panelId === 'candidates') {
                this.loadCandidates();
            }
        }
    }

    showSpinner(show) {
        const spinner = document.getElementById('adminLoadingSpinner');
        if (spinner) {
            spinner.style.display = show ? 'flex' : 'none';
        }
    }

    showAlert(elementId, message, type = 'info') {
        const element = document.getElementById(elementId);
        if (!element) return;

        element.innerHTML = message;
        element.className = `alert alert-${type}`;
        element.style.display = 'block';

        if (type === 'success') {
            setTimeout(() => {
                element.style.display = 'none';
            }, 5000);
        }
    }

    async handleBulkImport() {
        const file = document.getElementById('voterFile').files[0];
        if (!file) {
            this.showAlert('bulkImportAlert', 'Please select a CSV file', 'error');
            return;
        }

        const reader = new FileReader();
        reader.onload = async (e) => {
            try {
                const csv = e.target.result;
                const lines = csv.split('\n');
                const voters = [];

                // Parse CSV (basic implementation)
                for (let i = 1; i < lines.length; i++) {
                    const line = lines[i].trim();
                    if (!line) continue;

                    const [phone, name, unit] = line.split(',').map((f) => f.trim());
                    if (phone && name) {
                        voters.push({ phone, name, unit });
                    }
                }

                console.log(`Parsed ${voters.length} voters from CSV`);
                this.showAlert('bulkImportAlert', `Parsed ${voters.length} voters. Use Python script for actual import.`, 'info');
            } catch (error) {
                console.error('Error parsing CSV:', error);
                this.showAlert('bulkImportAlert', `Error parsing CSV: ${error.message}`, 'error');
            }
        };

        reader.readAsText(file);
    }
}

// ============================================================================
// Initialize Application
// ============================================================================

let adminApp;

document.addEventListener('DOMContentLoaded', () => {
    try {
        console.log('Admin Panel initializing');
        adminApp = new AdminApp();

        // Handle login form submission
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                adminApp.handleLogin(e);
            });
        }
    } catch (error) {
        console.error('Failed to initialize admin panel:', error);
        alert('Failed to initialize admin panel');
    }
});
