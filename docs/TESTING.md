# Testing Guide - RWA Voting System

Complete testing procedures for the RWA Voting System.

## 🧪 Testing Overview

This guide covers:
- Unit testing for individual functions
- Integration testing for complete workflows
- Load testing for performance verification
- Security testing for vulnerabilities

## 📋 Pre-Testing Setup

1. **Deployment Complete**
   - All Terraform resources created
   - Lambda functions deployed
   - DynamoDB tables initialized
   - SNS topic configured

2. **Environment Variables**
   ```bash
   export API_ENDPOINT="https://xxxxx.execute-api.ap-south-1.amazonaws.com/prod"
   export AWS_REGION="ap-south-1"
   ```

3. **Tools Required**
   - curl or Postman
   - Python 3.11 (for load testing)
   - AWS CLI
   - jq (for JSON parsing, optional)

## 🚀 Quick Start Testing (5 minutes)

```bash
#!/bin/bash

API="https://your-api-id.execute-api.ap-south-1.amazonaws.com/prod"

# 1. Create election
echo "=== Creating election ==="
curl -X POST $API/admin/elections \
  -H "Content-Type: application/json" \
  -d '{
    "electionId": "quick-test-'"$(date +%s)"'",
    "electionName": "Quick Test",
    "startTime": '$(date +%s)',
    "endTime": '$(($(date +%s) + 3600))'
  }' | jq .

# 2. Add candidates
echo -e "\n=== Adding candidates ==="
curl -X POST $API/admin/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "electionId": "quick-test-'"$(date +%s)"'",
    "postId": "1",
    "candidates": [
      {"candidateId": "c1", "candidateName": "Candidate 1"},
      {"candidateId": "c2", "candidateName": "Candidate 2"}
    ]
  }' | jq .

# 3. Send OTP
echo -e "\n=== Sending OTP ==="
curl -X POST $API/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "9876543210"}' | jq .

# 4. Get results
echo -e "\n=== Getting results ==="
curl -X GET $API/results/quick-test-$(date +%s) | jq .
```

## ✅ Functional Testing

### Test 1: OTP Generation and Verification

**Steps:**
```bash
MOBILE="9876543210"
API="https://your-api.execute-api.ap-south-1.amazonaws.com/prod"

# Send OTP
echo "Sending OTP..."
curl -X POST $API/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "'$MOBILE'"}'

# Check CloudWatch logs for OTP (in test mode)
aws logs tail /aws/lambda/rwa-voting-send-otp-prod --follow &
sleep 2

# Verify with correct OTP
echo "Verifying OTP... (use OTP from logs)"
curl -X POST $API/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "'$MOBILE'", "otp": "123456"}'
```

**Expected Results:**
- OTP sent response: status 200
- OTP verified response: includes token
- Failed OTP attempts tracked
- Max 3 attempts before blocking

### Test 2: Election Lifecycle

**Steps:**
```bash
API="https://your-api.execute-api.ap-south-1.amazonaws.com/prod"
ELECTION_ID="test-election-$(date +%s%N)"
START_TIME=$(date +%s)
END_TIME=$((START_TIME + 3600))

# Create election
echo "Creating election..."
CREATE=$(curl -s -X POST $API/admin/elections \
  -H "Content-Type: application/json" \
  -d '{
    "electionId": "'$ELECTION_ID'",
    "electionName": "Test Election",
    "description": "For testing purposes",
    "startTime": '$START_TIME',
    "endTime": '$END_TIME'
  }')
echo $CREATE | jq .

# Verify election created
echo "Retrieving election results..."
curl -s -X GET $API/results/$ELECTION_ID | jq .

# Test voting before start (should fail)
echo "Testing vote before election start..."
# [Sleep or use future start time]
```

**Expected Results:**
- Election created successfully
- Results endpoint returns empty results
- Voting before start time returns error
- Voting after end time returns error

### Test 3: Candidate Management

**Steps:**
```bash
API="https://your-api.execute-api.ap-south-1.amazonaws.com/prod"
ELECTION_ID="test-candidates-$(date +%s)"

# Create election first
curl -s -X POST $API/admin/elections \
  -H "Content-Type: application/json" \
  -d '{
    "electionId": "'$ELECTION_ID'",
    "electionName": "Candidate Test",
    "startTime": '$(date +%s)',
    "endTime": '$(($(date +%s) + 3600))'
  }' > /dev/null

# Add candidates to post 1
echo "Adding candidates to post 1..."
curl -X POST $API/admin/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "electionId": "'$ELECTION_ID'",
    "postId": "1",
    "candidates": [
      {"candidateId": "cand-001", "candidateName": "John Doe"},
      {"candidateId": "cand-002", "candidateName": "Jane Smith"},
      {"candidateId": "cand-003", "candidateName": "Bob Johnson"}
    ]
  }' | jq .

# Verify candidates in results
echo "Retrieving results with candidates..."
curl -s -X GET $API/results/$ELECTION_ID | jq '.data.results."1".candidates'
```

**Expected Results:**
- Candidates added successfully
- Results show all candidates with 0 votes
- Maximum 20 candidates per post enforced

### Test 4: Voting Process

**Steps:**
```bash
API="https://your-api.execute-api.ap-south-1.amazonaws.com/prod"
ELECTION_ID="test-voting-$(date +%s)"
MOBILE="9876543210"

# Setup: Create election and candidates
# ... (see previous tests)

# Authenticate voter
echo "Sending OTP..."
curl -s -X POST $API/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "'$MOBILE'"}' > /dev/null

# Verify OTP (check logs for actual OTP)
echo "Verifying OTP..."
curl -s -X POST $API/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "'$MOBILE'", "otp": "123456"}' > /dev/null

# Cast vote for post 1
echo "Casting vote for post 1..."
curl -X POST $API/vote/cast-vote \
  -H "Content-Type: application/json" \
  -d '{
    "mobileNumber": "'$MOBILE'",
    "electionId": "'$ELECTION_ID'",
    "postId": "1",
    "candidateId": "cand-001"
  }' | jq .

# Try to vote again (should fail)
echo "Attempting duplicate vote..."
curl -X POST $API/vote/cast-vote \
  -H "Content-Type: application/json" \
  -d '{
    "mobileNumber": "'$MOBILE'",
    "electionId": "'$ELECTION_ID'",
    "postId": "1",
    "candidateId": "cand-002"
  }' | jq .

# Vote for different post (should succeed)
echo "Voting for post 2..."
curl -X POST $API/vote/cast-vote \
  -H "Content-Type: application/json" \
  -d '{
    "mobileNumber": "'$MOBILE'",
    "electionId": "'$ELECTION_ID'",
    "postId": "2",
    "candidateId": "cand-004"
  }' | jq .
```

**Expected Results:**
- Vote cast successfully for post 1
- Duplicate vote for same post rejected
- Vote for different post accepted
- Results updated in real-time

### Test 5: Results Retrieval

**Steps:**
```bash
API="https://your-api.execute-api.ap-south-1.amazonaws.com/prod"
ELECTION_ID="test-results-$(date +%s)"

# Setup election with multiple votes
# ... (see previous tests)

# Get results
echo "Retrieving election results..."
curl -s -X GET $API/results/$ELECTION_ID | jq '{
  electionId: .data.electionId,
  electionName: .data.electionName,
  totalPosts: (.data.results | keys | length),
  post1Votes: .data.results."1".totalVotes
}'

# Get specific post results
echo "Post 1 candidates and votes..."
curl -s -X GET $API/results/$ELECTION_ID | jq '.data.results."1"'
```

**Expected Results:**
- All 7 posts returned
- Vote counts are accurate
- Candidates sorted by vote count
- Total votes per post correct

## 🔒 Security Testing

### Test 1: Invalid Mobile Number Format

```bash
API="https://your-api.execute-api.ap-south-1.amazonaws.com/prod"

# Invalid formats
INVALID_NUMBERS=(
  "123"              # Too short
  "98765432101"      # Too long
  "abcdefghij"       # Non-numeric
  "9876 543 210"     # Spaces
)

for num in "${INVALID_NUMBERS[@]}"; do
  echo "Testing: $num"
  curl -X POST $API/auth/send-otp \
    -H "Content-Type: application/json" \
    -d '{"mobileNumber": "'$num'"}' | jq '.errorCode'
done
```

**Expected Result:** All return INVALID_MOBILE error

### Test 2: OTP Expiry

```bash
API="https://your-api.execute-api.ap-south-1.amazonaws.com/prod"
MOBILE="9876543210"

# Send OTP
curl -s -X POST $API/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "'$MOBILE'"}' > /dev/null

# Wait for OTP expiry (5 minutes by default)
echo "Waiting for OTP to expire (5 minutes)..."
sleep 300

# Try to verify expired OTP
echo "Verifying expired OTP..."
curl -X POST $API/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "'$MOBILE'", "otp": "123456"}' | jq '.errorCode'
```

**Expected Result:** OTP_NOT_FOUND error

### Test 3: Injection Attack Prevention

```bash
API="https://your-api.execute-api.ap-south-1.amazonaws.com/prod"

# Test SQL injection
curl -X POST $API/admin/elections \
  -H "Content-Type: application/json" \
  -d '{
    "electionId": "test123; DROP TABLE --",
    "electionName": "Test",
    "startTime": '$(date +%s)',
    "endTime": '$(($(date +%s) + 3600))'
  }' | jq .

# Test XSS
curl -X POST $API/admin/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "electionId": "test",
    "postId": "1",
    "candidates": [
      {
        "candidateId": "<script>alert(1)</script>",
        "candidateName": "<img src=x onerror='alert(1)'>"
      }
    ]
  }' | jq .
```

**Expected Result:** Invalid format errors (special characters rejected)

### Test 4: Rate Limiting

```bash
API="https://your-api.execute-api.ap-south-1.amazonaws.com/prod"

# Send rapid requests
for i in {1..100}; do
  curl -s -X POST $API/auth/send-otp \
    -H "Content-Type: application/json" \
    -d '{"mobileNumber": "98765432'$i'"}' &
done
wait

# Check for 429 (Too Many Requests) responses
```

**Expected Result:**
- First 2000 requests within rate limit succeed or fail with expected errors
- Requests beyond 5000 burst limit get 429

## ⚡ Load Testing

### Simple Load Test (Python)

```python
# load_test.py
import concurrent.futures
import requests
import time
import random

API_ENDPOINT = "https://your-api.execute-api.ap-south-1.amazonaws.com/prod"
ELECTION_ID = "load-test-" + str(int(time.time()))
NUM_VOTERS = 100
NUM_THREADS = 10

def setup_election():
    """Create election and candidates"""
    response = requests.post(
        f"{API_ENDPOINT}/admin/elections",
        json={
            "electionId": ELECTION_ID,
            "electionName": "Load Test",
            "startTime": int(time.time()),
            "endTime": int(time.time()) + 3600
        }
    )
    print(f"Election created: {response.status_code}")
    
    # Add candidates to all posts
    for post_id in range(1, 8):
        candidates = [
            {"candidateId": f"c{post_id}-{i}", "candidateName": f"Candidate {i}"}
            for i in range(1, 6)
        ]
        requests.post(
            f"{API_ENDPOINT}/admin/candidates",
            json={
                "electionId": ELECTION_ID,
                "postId": str(post_id),
                "candidates": candidates
            }
        )

def vote_workflow(voter_id):
    """Simulate complete voting workflow"""
    mobile = f"{9000000000 + voter_id}"
    
    try:
        # Send OTP
        requests.post(
            f"{API_ENDPOINT}/auth/send-otp",
            json={"mobileNumber": mobile},
            timeout=5
        )
        
        # Verify OTP (using dummy OTP for load test)
        requests.post(
            f"{API_ENDPOINT}/auth/verify-otp",
            json={"mobileNumber": mobile, "otp": "000000"},
            timeout=5
        )
        
        # Cast votes for all posts
        for post_id in range(1, 8):
            candidate_id = f"c{post_id}-{random.randint(1, 5)}"
            response = requests.post(
                f"{API_ENDPOINT}/vote/cast-vote",
                json={
                    "mobileNumber": mobile,
                    "electionId": ELECTION_ID,
                    "postId": str(post_id),
                    "candidateId": candidate_id
                },
                timeout=5
            )
            
            if response.status_code != 200:
                print(f"Vote failed for voter {voter_id}: {response.status_code}")
                return False
        
        return True
    
    except Exception as e:
        print(f"Error for voter {voter_id}: {str(e)}")
        return False

if __name__ == "__main__":
    print("Setting up election...")
    setup_election()
    time.sleep(2)
    
    print(f"Starting load test with {NUM_VOTERS} voters...")
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        results = list(executor.map(vote_workflow, range(NUM_VOTERS)))
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    successful = sum(results)
    failed = NUM_VOTERS - successful
    
    print(f"\n=== Load Test Results ===")
    print(f"Total voters: {NUM_VOTERS}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(successful/NUM_VOTERS)*100:.1f}%")
    print(f"Time elapsed: {elapsed:.2f}s")
    print(f"Requests/sec: {(NUM_VOTERS * 7) / elapsed:.2f}")  # 7 votes per voter
    
    # Get final results
    response = requests.get(f"{API_ENDPOINT}/results/{ELECTION_ID}")
    results = response.json()["data"]["results"]
    total_votes = sum(r["totalVotes"] for r in results.values())
    print(f"Total votes recorded: {total_votes}")
```

**Run Load Test:**
```bash
python load_test.py
```

**Expected Results:**
- 95%+ success rate for 100 concurrent voters
- Average response time < 1 second
- All 700 votes (100 voters × 7 posts) recorded

## 📊 Performance Testing

### Measure API Response Times

```bash
#!/bin/bash

API="https://your-api-id.execute-api.ap-south-1.amazonaws.com/prod"

echo "Measuring response times..."
echo -e "\nOTP Send:"
curl -w "Total: %{time_total}s\n" \
  -X POST $API/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "9876543210"}' -o /dev/null -s

echo -e "\nOTP Verify:"
curl -w "Total: %{time_total}s\n" \
  -X POST $API/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "9876543210", "otp": "123456"}' -o /dev/null -s

echo -e "\nCast Vote:"
curl -w "Total: %{time_total}s\n" \
  -X POST $API/vote/cast-vote \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "9876543210", "electionId": "test", "postId": "1", "candidateId": "c1"}' \
  -o /dev/null -s

echo -e "\nGet Results:"
curl -w "Total: %{time_total}s\n" \
  -X GET $API/results/test -o /dev/null -s
```

**Expected Results:**
- OTP Send: 1-2 seconds (includes SNS)
- OTP Verify: < 500ms
- Cast Vote: 300-800ms (depends on election validation)
- Get Results: 500ms-1s (depends on vote count)

## ✔️ Testing Checklist

- [ ] OTP generation tested
- [ ] OTP expiry tested
- [ ] OTP max attempts tested
- [ ] Election creation tested
- [ ] Candidate addition tested
- [ ] Vote casting tested
- [ ] Duplicate vote prevention tested
- [ ] Election timing tested
- [ ] Results retrieval tested
- [ ] Invalid input handling tested
- [ ] SQL injection tested
- [ ] XSS protection tested
- [ ] Rate limiting tested
- [ ] Load test completed
- [ ] Response times acceptable
- [ ] Error codes correct
- [ ] CORS headers correct

## 📝 Test Report Template

```
=== RWA Voting System Test Report ===
Date: YYYY-MM-DD
Tester: Name
Environment: AWS Region, Environment (dev/prod)

Functional Tests: PASS/FAIL
- OTP Management: PASS
- Election Management: PASS
- Voting Process: PASS
- Results: PASS

Security Tests: PASS/FAIL
- Input Validation: PASS
- Injection Prevention: PASS
- Rate Limiting: PASS

Performance Tests: PASS/FAIL
- Response Times: PASS
- Load Capacity: 100 concurrent users
- Peak QPS: X requests/second

Issues Found:
1. [Description]
2. [Description]

Sign-off: _____________
```

---

**Test Environment**: AWS Free Tier  
**Last Run**: [Date]  
**Status**: All tests passing
