# API Design - RWA Voting System

Complete API specification for all endpoints.

## Base URL

```
https://{api-id}.execute-api.{region}.amazonaws.com/prod
```

Example:
```
https://abc123def.execute-api.ap-south-1.amazonaws.com/prod
```

## Authentication

Most endpoints require a mobile number. For voting, you need:
1. Verified mobile number via OTP

No API key required for this version. In production, implement:
- JWT tokens
- API keys
- AWS Cognito

## Response Format

### Success Response (2xx)

```json
{
  "success": true,
  "data": {
    // Endpoint-specific data
  }
}
```

### Error Response (4xx, 5xx)

```json
{
  "success": false,
  "message": "Human-readable error message",
  "errorCode": "ERROR_CODE_CONSTANT"
}
```

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| INVALID_JSON | 400 | Request body is not valid JSON |
| MOBILE_REQUIRED | 400 | Mobile number not provided |
| INVALID_MOBILE | 400 | Mobile number format invalid |
| OTP_REQUIRED | 400 | OTP not provided |
| INVALID_OTP_FORMAT | 400 | OTP must be 6 digits |
| OTP_NOT_FOUND | 400 | OTP expired or not found |
| INVALID_OTP | 400 | OTP mismatch |
| MAX_ATTEMPTS | 400 | Maximum OTP attempts exceeded |
| ELECTION_REQUIRED | 400 | Election ID not provided |
| INVALID_ELECTION | 400 | Election ID format invalid |
| ELECTION_NOT_FOUND | 404 | Election doesn't exist |
| ELECTION_NOT_STARTED | 400 | Election hasn't started yet |
| ELECTION_ENDED | 400 | Election has ended |
| POST_REQUIRED | 400 | Post ID not provided |
| INVALID_POST | 400 | Post ID invalid (must be 1-7) |
| CANDIDATE_REQUIRED | 400 | Candidate ID not provided |
| INVALID_CANDIDATE | 400 | Candidate ID format invalid |
| CANDIDATE_NOT_FOUND | 404 | Candidate not found |
| DUPLICATE_VOTE | 400 | Voter already voted for this post |
| CONFIG_ERROR | 500 | Server configuration error |
| INTERNAL_ERROR | 500 | Internal server error |

## Endpoints

### 1. Send OTP

Generate and send OTP to a mobile number via SMS.

```http
POST /auth/send-otp
```

**Request Body:**
```json
{
  "mobileNumber": "9876543210"
}
```

**Mobile Number Format:**
- 10 digits: `9876543210`
- With +91: `+919876543210`
- With country code: `919876543210`
- With 0 prefix: `09876543210`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "OTP sent successfully",
    "maskedNumber": "****3210",
    "expiryMinutes": 5
  }
}
```

**Error Response (400):**
```json
{
  "success": false,
  "message": "Invalid mobile number format",
  "errorCode": "INVALID_MOBILE"
}
```

**cURL Example:**
```bash
curl -X POST https://api.example.com/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "9876543210"}'
```

**Notes:**
- OTP expires after configured minutes (default: 5)
- Single OTP per mobile number (previous OTP invalidated)
- SMS delivery may take 1-5 seconds

---

### 2. Verify OTP

Verify the OTP sent to mobile number.

```http
POST /auth/verify-otp
```

**Request Body:**
```json
{
  "mobileNumber": "9876543210",
  "otp": "123456"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "OTP verified successfully",
    "token": "9876543210",
    "maskedNumber": "****3210"
  }
}
```

**Error Responses:**

OTP not found (400):
```json
{
  "success": false,
  "message": "OTP not found or expired",
  "errorCode": "OTP_NOT_FOUND"
}
```

Invalid OTP (400):
```json
{
  "success": false,
  "message": "Invalid OTP",
  "errorCode": "INVALID_OTP"
}
```

Max attempts exceeded (400):
```json
{
  "success": false,
  "message": "Maximum OTP attempts exceeded. Request a new OTP.",
  "errorCode": "MAX_ATTEMPTS"
}
```

**cURL Example:**
```bash
curl -X POST https://api.example.com/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "mobileNumber": "9876543210",
    "otp": "123456"
  }'
```

**Notes:**
- OTP becomes single-use after verification
- 3 failed attempts trigger cooldown
- Token is the normalized mobile number

---

### 3. Cast Vote

Cast a vote for a candidate in a post.

```http
POST /vote/cast-vote
```

**Request Body:**
```json
{
  "mobileNumber": "9876543210",
  "electionId": "election-2024",
  "postId": "1",
  "candidateId": "candidate-001"
}
```

**Parameters:**
- `mobileNumber`: Verified mobile number
- `electionId`: Election identifier
- `postId`: Post number (1-7)
- `candidateId`: Unique candidate identifier

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "Vote cast successfully",
    "postId": "1",
    "candidateName": "John Doe"
  }
}
```

**Error Responses:**

Election not found (404):
```json
{
  "success": false,
  "message": "Election not found",
  "errorCode": "ELECTION_NOT_FOUND"
}
```

Election not started (400):
```json
{
  "success": false,
  "message": "Election has not started yet",
  "errorCode": "ELECTION_NOT_STARTED"
}
```

Election ended (400):
```json
{
  "success": false,
  "message": "Election has ended",
  "errorCode": "ELECTION_ENDED"
}
```

Duplicate vote (400):
```json
{
  "success": false,
  "message": "You have already voted for this post",
  "errorCode": "DUPLICATE_VOTE"
}
```

**cURL Example:**
```bash
curl -X POST https://api.example.com/vote/cast-vote \
  -H "Content-Type: application/json" \
  -d '{
    "mobileNumber": "9876543210",
    "electionId": "election-2024",
    "postId": "1",
    "candidateId": "candidate-001"
  }'
```

**Notes:**
- One vote per post per voter
- Vote cast times prevent voting outside election window
- Voting is anonymous (no mapping between vote and voter)
- Vote cannot be changed after casting

---

### 4. Get Results

Retrieve live election results.

```http
GET /results/{electionId}
```

**Path Parameters:**
- `electionId`: Election identifier

**Response (200):**
```json
{
  "success": true,
  "data": {
    "electionId": "election-2024",
    "electionName": "Board Election 2024",
    "results": {
      "1": {
        "postName": "President",
        "candidates": [
          {
            "candidateId": "candidate-001",
            "candidateName": "John Doe",
            "votes": 45
          },
          {
            "candidateId": "candidate-002",
            "candidateName": "Jane Smith",
            "votes": 32
          }
        ],
        "totalVotes": 77
      },
      "2": {
        "postName": "Vice President",
        "candidates": [
          {
            "candidateId": "candidate-003",
            "candidateName": "Robert Brown",
            "votes": 28
          }
        ],
        "totalVotes": 28
      }
      // ... posts 3-7
    },
    "timestamp": 1707859200
  }
}
```

**Error Response (404):**
```json
{
  "success": false,
  "message": "Election not found",
  "errorCode": "ELECTION_NOT_FOUND"
}
```

**cURL Example:**
```bash
curl -X GET https://api.example.com/results/election-2024
```

**Post IDs:**
```
1: President
2: Vice President
3: General Secretary
4: Treasurer
5: Sports Secretary
6: Cultural Secretary
7: Social Secretary
```

**Notes:**
- Results are real-time (computed on request)
- Updated instantly after each vote
- No caching applied
- Candidates sorted by vote count (descending)

---

### 5. Create Election (Admin)

Create a new election.

```http
POST /admin/elections
```

**Request Body:**
```json
{
  "electionId": "election-2024",
  "electionName": "Board Election 2024",
  "description": "Annual board elections for the association",
  "startTime": 1707859200,
  "endTime": 1707945600
}
```

**Parameters:**
- `electionId`: Unique identifier (3-32 chars, alphanumeric, dash, underscore)
- `electionName`: Display name
- `description`: Optional description
- `startTime`: Unix timestamp (election start)
- `endTime`: Unix timestamp (election end)

**Time Format Example:**
```python
import time
from datetime import datetime, timedelta

# Election starts now, ends in 24 hours
start_time = int(time.time())
end_time = int(time.time()) + (24 * 60 * 60)
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "message": "Election created successfully",
    "electionId": "election-2024",
    "electionName": "Board Election 2024"
  }
}
```

**Error Response (409):**
```json
{
  "success": false,
  "message": "Election with this ID already exists",
  "errorCode": "ELECTION_EXISTS"
}
```

**cURL Example:**
```bash
curl -X POST https://api.example.com/admin/elections \
  -H "Content-Type: application/json" \
  -d '{
    "electionId": "election-2024",
    "electionName": "Board Election 2024",
    "description": "Annual board elections",
    "startTime": 1707859200,
    "endTime": 1707945600
  }'
```

**Notes:**
- Election ID must be unique
- Time must be Unix timestamps (seconds)
- Cannot create election with same ID twice

---

### 6. Add Candidates (Admin)

Add candidates to a post in an election.

```http
POST /admin/candidates
```

**Request Body:**
```json
{
  "electionId": "election-2024",
  "postId": "1",
  "candidates": [
    {
      "candidateId": "candidate-001",
      "candidateName": "John Doe"
    },
    {
      "candidateId": "candidate-002",
      "candidateName": "Jane Smith"
    },
    {
      "candidateId": "candidate-003",
      "candidateName": "Robert Brown"
    }
  ]
}
```

**Parameters:**
- `electionId`: Election identifier
- `postId`: Post number (1-7)
- `candidates`: Array of candidate objects
  - `candidateId`: Unique candidate identifier
  - `candidateName`: Candidate name

**Response (201):**
```json
{
  "success": true,
  "data": {
    "message": "Candidates added successfully",
    "electionId": "election-2024",
    "postId": "1",
    "candidatesAdded": 3
  }
}
```

**Error Responses:**

Election not found (404):
```json
{
  "success": false,
  "message": "Election not found",
  "errorCode": "ELECTION_NOT_FOUND"
}
```

Too many candidates (400):
```json
{
  "success": false,
  "message": "Maximum 20 candidates per post",
  "errorCode": "TOO_MANY_CANDIDATES"
}
```

**cURL Example:**
```bash
curl -X POST https://api.example.com/admin/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "electionId": "election-2024",
    "postId": "1",
    "candidates": [
      {
        "candidateId": "candidate-001",
        "candidateName": "John Doe"
      },
      {
        "candidateId": "candidate-002",
        "candidateName": "Jane Smith"
      }
    ]
  }'
```

**Notes:**
- Maximum 20 candidates per post
- Candidate IDs must be unique within a post
- Duplicate candidates are skipped
- Candidates can be added before election starts

---

## Rate Limiting

API Gateway has default throttling:
- **Burst limit**: 5000 requests per second
- **Rate limit**: 2000 requests per second

Exceeding limits returns 429 (Too Many Requests).

**Per-endpoint recommendations:**
- `/auth/send-otp`: 1 per minute per mobile number (implement client-side)
- `/vote/cast-vote`: 1 per post per mobile number (enforced server-side)

---

## CORS Headers

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: Content-Type, X-Amz-Date, Authorization
Access-Control-Allow-Methods: GET, POST, OPTIONS
```

---

## Example Workflow

### Complete Election Workflow

```bash
#!/bin/bash
API="https://api.example.com"

# 1. Create election
ELECTION=$(curl -s -X POST $API/admin/elections \
  -H "Content-Type: application/json" \
  -d '{
    "electionId": "rwa-2024-q1",
    "electionName": "Q1 2024 Elections",
    "startTime": '$(($(date +%s) + 3600))',
    "endTime": '$(($(date +%s) + 86400))'
  }')
echo "Election created: $ELECTION"

# 2. Add candidates
CANDIDATES=$(curl -s -X POST $API/admin/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "electionId": "rwa-2024-q1",
    "postId": "1",
    "candidates": [
      {"candidateId": "c001", "candidateName": "Alice"},
      {"candidateId": "c002", "candidateName": "Bob"}
    ]
  }')
echo "Candidates added: $CANDIDATES"

# 3. Send OTP
OTP_RESPONSE=$(curl -s -X POST $API/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "9876543210"}')
echo "OTP sent to: $OTP_RESPONSE"

# 4. Verify OTP (replace with actual OTP from SMS/logs)
VERIFY=$(curl -s -X POST $API/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "9876543210", "otp": "123456"}')
echo "OTP verified: $VERIFY"

# 5. Cast vote
VOTE=$(curl -s -X POST $API/vote/cast-vote \
  -H "Content-Type: application/json" \
  -d '{
    "mobileNumber": "9876543210",
    "electionId": "rwa-2024-q1",
    "postId": "1",
    "candidateId": "c001"
  }')
echo "Vote cast: $VOTE"

# 6. Get results
RESULTS=$(curl -s -X GET $API/results/rwa-2024-q1)
echo "Results: $RESULTS"
```

---

## Testing Tools

### Postman Collection

Import this into Postman:

```json
{
  "info": {
    "name": "RWA Voting API",
    "version": "1.0"
  },
  "item": [
    {
      "name": "Send OTP",
      "request": {
        "method": "POST",
        "header": [
          {"key": "Content-Type", "value": "application/json"}
        ],
        "body": {
          "raw": "{\"mobileNumber\": \"9876543210\"}"
        },
        "url": "{{baseUrl}}/auth/send-otp"
      }
    },
    {
      "name": "Verify OTP",
      "request": {
        "method": "POST",
        "header": [
          {"key": "Content-Type", "value": "application/json"}
        ],
        "body": {
          "raw": "{\"mobileNumber\": \"9876543210\", \"otp\": \"123456\"}"
        },
        "url": "{{baseUrl}}/auth/verify-otp"
      }
    }
  ]
}
```

### Python Client Example

```python
import requests
import json

class VotingAPIClient:
    def __init__(self, base_url):
        self.base_url = base_url
    
    def send_otp(self, mobile_number):
        response = requests.post(
            f"{self.base_url}/auth/send-otp",
            json={"mobileNumber": mobile_number}
        )
        return response.json()
    
    def verify_otp(self, mobile_number, otp):
        response = requests.post(
            f"{self.base_url}/auth/verify-otp",
            json={"mobileNumber": mobile_number, "otp": otp}
        )
        return response.json()
    
    def cast_vote(self, mobile_number, election_id, post_id, candidate_id):
        response = requests.post(
            f"{self.base_url}/vote/cast-vote",
            json={
                "mobileNumber": mobile_number,
                "electionId": election_id,
                "postId": post_id,
                "candidateId": candidate_id
            }
        )
        return response.json()
    
    def get_results(self, election_id):
        response = requests.get(
            f"{self.base_url}/results/{election_id}"
        )
        return response.json()

# Usage
client = VotingAPIClient("https://api.example.com")
client.send_otp("9876543210")
```

---

## Migration Guide (if using different backend)

All endpoints follow REST conventions:
- GET for retrieval
- POST for creation/mutation
- Standard HTTP status codes
- JSON request/response

Implement these exactly as specified for compatibility.

---

## Versioning

Current API version: v1 (no version prefix)

Future versions will use `/v2/` prefix for backward compatibility.

---

**Last Updated**: 2024
