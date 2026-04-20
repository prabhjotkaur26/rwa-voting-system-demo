# RWA Voting System - Complete API Reference

**API Version**: 2.0  
**Last Updated**: January 2024  
**Base URL**: `https://<API_ID>.execute-api.ap-south-1.amazonaws.com/dev`

---

## Table of Contents

1. [Authentication Endpoints](#authentication-endpoints)
2. [Voting Endpoints](#voting-endpoints)
3. [Admin Endpoints](#admin-endpoints)
4. [Results Endpoints](#results-endpoints) - NEW
5. [Error Codes](#error-codes)
6. [Authentication](#authentication)

---

## Authentication Endpoints

### 1. Send OTP

Sends a one-time password to a registered voter's mobile number. **ENHANCED: Now verifies voter is registered before sending OTP.**

**Endpoint**: `POST /auth/send-otp`

**Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "mobileNumber": "9876543210"
}
```

**Response (Success - 200)**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "OTP sent successfully",
    "mobileNumber": "9876543210",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

**Response (Voter Not Found - 400)** - NEW:
```json
{
  "statusCode": 400,
  "body": {
    "errorCode": "VOTER_NOT_FOUND",
    "message": "Mobile number not registered for this election",
    "mobileNumber": "9876543210"
  }
}
```

**Response (Invalid Format - 400)**:
```json
{
  "statusCode": 400,
  "body": {
    "errorCode": "INVALID_MOBILE_FORMAT",
    "message": "Invalid mobile number format",
    "example": "9876543210 or +919876543210"
  }
}
```

**Mobile Format Accepted**:
- 10-digit format: `9876543210`
- With +91 prefix: `+919876543210`
- With 91 prefix: `919876543210`
- With 0 prefix: `09876543210`

**Notes**:
- OTP valid for 15 minutes
- Maximum 3 OTP requests per mobile per hour
- Voter must exist in `rwa-voting-voters-dev` table
- SMS sent via AWS SNS

---

### 2. Verify OTP

Verifies the OTP and returns authentication token.

**Endpoint**: `POST /auth/verify-otp`

**Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "mobileNumber": "9876543210",
  "otp": "123456"
}
```

**Response (Success - 200)**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "OTP verified successfully",
    "mobileNumber": "9876543210",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 3600,
    "tokenType": "Bearer"
  }
}
```

**Response (Invalid OTP - 401)**:
```json
{
  "statusCode": 401,
  "body": {
    "errorCode": "INVALID_OTP",
    "message": "Invalid or expired OTP",
    "attemptsRemaining": 2
  }
}
```

**Notes**:
- Token valid for 1 hour
- Token type: JWT
- Maximum 5 incorrect attempts before lockout (15 min)
- Include token in Authorization header: `Bearer <token>`

---

## Voting Endpoints

### 3. Get Election Posts with Candidates

Retrieves all election posts with their candidates. **ENHANCED: Only returns posts with >1 candidate.**

**Endpoint**: `GET /elections/{electionId}/posts`

**Path Parameters**:
- `electionId` (string): Election identifier (e.g., `election-2024-01`)

**Headers**:
```
Content-Type: application/json
Authorization: Bearer <token>
```

**Response (Success - 200)**:
```json
{
  "statusCode": 200,
  "body": {
    "electionId": "election-2024-01",
    "posts": [
      {
        "postId": "post-1",
        "postName": "President",
        "candidateCount": 3,
        "candidates": [
          {
            "candidateId": "pres-001",
            "candidateName": "Rajesh Kumar",
            "party": "Green Party",
            "bio": "Community development expert",
            "imageUrl": "https://s3.amazonaws.com/candidates/rajesh.jpg"
          },
          {
            "candidateId": "pres-002",
            "candidateName": "Priya Sharma",
            "party": "Citizens Forum",
            "bio": "Welfare advocate",
            "imageUrl": "https://s3.amazonaws.com/candidates/priya.jpg"
          },
          {
            "candidateId": "pres-003",
            "candidateName": "Amit Singh",
            "party": "Unity Movement",
            "bio": "Safety and transparency",
            "imageUrl": "https://s3.amazonaws.com/candidates/amit.jpg"
          }
        ]
      },
      {
        "postId": "post-2",
        "postName": "Vice President",
        "candidateCount": 2,
        "candidates": [
          {
            "candidateId": "vp-001",
            "candidateName": "Neha Patel",
            "party": "Community Service",
            "bio": "Resident welfare",
            "imageUrl": "https://s3.amazonaws.com/candidates/neha.jpg"
          },
          {
            "candidateId": "vp-002",
            "candidateName": "Vikram Gupta",
            "party": "Progressive Alliance",
            "bio": "Financial management",
            "imageUrl": "https://s3.amazonaws.com/candidates/vikram.jpg"
          }
        ]
      }
    ],
    "totalPosts": 2,
    "timestamp": "2024-01-15T10:35:00Z"
  }
}
```

**Response (Not Found - 404)**:
```json
{
  "statusCode": 404,
  "body": {
    "errorCode": "ELECTION_NOT_FOUND",
    "message": "Election not found",
    "electionId": "election-2024-01"
  }
}
```

**Key Features - NEW**:
- `imageUrl` field included for each candidate (ENHANCEMENT 3)
- Only posts with >1 candidate returned (ENHANCEMENT 2)
- `candidateCount` field shows number of candidates
- Filtered server-side, no frontend logic needed
- Includes `party` and `bio` fields for detailed info

**Notes**:
- Authentication required
- Maximum 7 posts per election
- Candidates ordered by candidateId
- Image URLs are ready for direct display

---

### 4. Cast Vote

Records a vote for a candidate in an election post.

**Endpoint**: `POST /elections/{electionId}/votes`

**Path Parameters**:
- `electionId` (string): Election identifier

**Headers**:
```
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body**:
```json
{
  "postId": "post-1",
  "candidateId": "pres-001"
}
```

**Response (Success - 201)**:
```json
{
  "statusCode": 201,
  "body": {
    "message": "Vote recorded successfully",
    "electionId": "election-2024-01",
    "postId": "post-1",
    "candidateId": "pres-001",
    "candidateName": "Rajesh Kumar",
    "timestamp": "2024-01-15T10:40:00Z"
  }
}
```

**Response (Duplicate Vote - 409)**:
```json
{
  "statusCode": 409,
  "body": {
    "errorCode": "VOTE_ALREADY_CAST",
    "message": "You have already voted for this post",
    "postId": "post-1",
    "previousVote": "pres-001"
  }
}
```

**Response (Invalid Post - 400)**:
```json
{
  "statusCode": 400,
  "body": {
    "errorCode": "INVALID_POST",
    "message": "Post not found",
    "postId": "post-1"
  }
}
```

**Notes**:
- One vote per post per voter
- Duplicate votes prevented
- Vote recorded with timestamp and voter mobile (hashed)
- Cannot modify vote after casting
- Vote data stored in `rwa-voting-votes-dev` table

---

### 5. Get Election Results

Retrieves current voting results for an election.

**Endpoint**: `GET /elections/{electionId}/results`

**Path Parameters**:
- `electionId` (string): Election identifier

**Headers**:
```
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Parameters** (query string):
- `includeCandidateDetails` (boolean, optional): Include full candidate info (default: false)

**Response (Success - 200)**:
```json
{
  "statusCode": 200,
  "body": {
    "electionId": "election-2024-01",
    "results": [
      {
        "postId": "post-1",
        "postName": "President",
        "candidates": [
          {
            "candidateId": "pres-001",
            "candidateName": "Rajesh Kumar",
            "votes": 45,
            "percentage": 50.56
          },
          {
            "candidateId": "pres-002",
            "candidateName": "Priya Sharma",
            "votes": 35,
            "percentage": 39.33
          },
          {
            "candidateId": "pres-003",
            "candidateName": "Amit Singh",
            "votes": 9,
            "percentage": 10.11
          }
        ],
        "totalVotes": 89,
        "leadingCandidate": {
          "candidateId": "pres-001",
          "candidateName": "Rajesh Kumar",
          "votes": 45
        }
      }
    ],
    "totalVotesCast": 89,
    "timestamp": "2024-01-15T10:45:00Z"
  }
}
```

**Notes**:
- Real-time data
- Sorted by vote count descending
- Percentages calculated per post
- Leading candidate indicated

---

## Admin Endpoints

### 6. Add Candidates

Adds candidates to election posts. **ENHANCED: Now accepts imageUrl, party, and bio fields.**

**Endpoint**: `POST /admin/candidates`

**Headers**:
```
Content-Type: application/json
Authorization: Bearer <admin-token>
x-api-key: <ADMIN_API_KEY>
```

**Request Body**:
```json
{
  "electionId": "election-2024-01",
  "postId": "post-1",
  "candidates": [
    {
      "candidateId": "pres-001",
      "candidateName": "Rajesh Kumar",
      "mobileNumber": "9876543210",
      "imageUrl": "https://s3.amazonaws.com/candidates/rajesh.jpg",
      "party": "Green Party",
      "bio": "15 years in community development"
    }
  ]
}
```

**Response (Success - 201)**:
```json
{
  "statusCode": 201,
  "body": {
    "message": "Candidates added successfully",
    "electionId": "election-2024-01",
    "postId": "post-1",
    "candidatesAdded": 1,
    "timestamp": "2024-01-15T10:50:00Z"
  }
}
```

**Request Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| electionId | string | Yes | Election identifier |
| postId | string | Yes | Post identifier |
| candidateId | string | Yes | Unique candidate ID |
| candidateName | string | Yes | Candidate full name |
| mobileNumber | string | Yes | Contact mobile |
| imageUrl | string | No | NEW: Candidate photo URL (ENHANCEMENT 3) |
| party | string | No | NEW: Political party/group |
| bio | string | No | NEW: Short biography |

**Response (Invalid Election - 404)**:
```json
{
  "statusCode": 404,
  "body": {
    "errorCode": "ELECTION_NOT_FOUND",
    "message": "Election not found",
    "electionId": "election-2024-01"
  }
}
```

**Notes**:
- Admin authentication required
- Candidates table supports up to 10 candidates per post
- Image URL can be S3, CDN, or any public URL
- Optional fields (imageUrl, party, bio) can be omitted
- Backward compatible with old format (without new fields)

---

### 7. Bulk Upload Voters

Batch imports voter registration data from CSV. **NEW ENHANCEMENT 1**

**Endpoint**: `POST /admin/voters/bulk-upload`

**Headers**:
```
Content-Type: application/json
Authorization: Bearer <admin-token>
x-api-key: <ADMIN_API_KEY>
```

**Request Body**:
```json
{
  "voters": [
    {
      "mobileNumber": "9876543210",
      "flatNumber": "101",
      "name": "Rajesh Kumar",
      "email": "rajesh@example.com",
      "area": "Tower A"
    }
  ]
}
```

**Alternative: CSV File Upload** (use script):
```bash
python3 scripts/bulk_import_voters.py samples/voters_import.csv rwa-voting-voters-dev
```

**Response (Success - 200)**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Bulk upload completed",
    "totalRecords": 100,
    "successful": 98,
    "failed": 2,
    "errors": [
      {
        "row": 12,
        "mobileNumber": "invalid",
        "error": "Invalid mobile number format"
      },
      {
        "row": 45,
        "mobileNumber": "9876543245",
        "error": "Duplicate mobile number"
      }
    ],
    "timestamp": "2024-01-15T11:00:00Z"
  }
}
```

**Voter Fields**:

| Field | Type | Required | Format |
|-------|------|----------|--------|
| mobileNumber | string | Yes | 10-digit or +91/91/0 prefix |
| flatNumber | string | Yes | Apartment/House number |
| name | string | Yes | Full name |
| email | string | No | Valid email |
| area | string | No | Building/Tower name |

**CSV Format**:
```csv
mobileNumber,flatNumber,name,email,area
9876543210,101,Rajesh Kumar,rajesh@example.com,Tower A
9876543211,102,Priya Sharma,priya@example.com,Tower A
9876543212,201,Amit Singh,amit@example.com,Tower B
```

**Mobile Format Handling**:
- `9876543210` (10-digit) ✓
- `+919876543210` (+91 prefix) ✓
- `919876543210` (91 prefix) ✓
- `09876543210` (0 prefix) ✓
- All normalized to 10-digit format internally

**Validation**:
- Checks mobile number format
- Validates required fields
- Prevents duplicate entries
- Reports specific errors with row numbers

**Notes**:
- Admin authentication required
- Recommended: 100-1000 records per upload
- Larger batches use Python script for better performance
- Errors don't stop processing of other records
- All successful records committed even if some fail

---

## Results Endpoints

### 8. Export Election Results

Exports election results in CSV or JSON format. **NEW ENHANCEMENT 5**

**Endpoint**: `POST /results/{electionId}/export`

**Path Parameters**:
- `electionId` (string): Election identifier

**Headers**:
```
Content-Type: application/json
Authorization: Bearer <admin-token>
x-api-key: <ADMIN_API_KEY>
```

**Request Body**:
```json
{
  "format": "csv"
}
```

**Request Parameters**:

| Field | Type | Required | Options | Default |
|-------|------|----------|---------|---------|
| format | string | Yes | "csv", "json" | N/A |
| includeDetails | boolean | No | true, false | false |

**Response (CSV Format - 200)**:
```json
{
  "statusCode": 200,
  "body": {
    "format": "csv",
    "filename": "election-2024-01-results-2024-01-15-104500.csv",
    "content": "Post,Candidate,Party,Votes,Percentage\nPresident,Rajesh Kumar,Green Party,45,50.56\nPresident,Priya Sharma,Citizens Forum,35,39.33\nPresident,Amit Singh,Unity Movement,9,10.11\nVice President,Neha Patel,Community Service,50,56.18\nVice President,Vikram Gupta,Progressive Alliance,39,43.82\n",
    "totalRecords": 5,
    "timestamp": "2024-01-15T10:45:00Z"
  }
}
```

**Response (JSON Format - 200)**:
```json
{
  "statusCode": 200,
  "body": {
    "format": "json",
    "filename": "election-2024-01-results-2024-01-15-104500.json",
    "content": {
      "electionId": "election-2024-01",
      "exportedAt": "2024-01-15T10:45:00Z",
      "totalVotesCast": 89,
      "posts": [
        {
          "postId": "post-1",
          "postName": "President",
          "totalVotes": 89,
          "candidates": [
            {
              "candidateId": "pres-001",
              "candidateName": "Rajesh Kumar",
              "party": "Green Party",
              "votes": 45,
              "percentage": 50.56
            },
            {
              "candidateId": "pres-002",
              "candidateName": "Priya Sharma",
              "party": "Citizens Forum",
              "votes": 35,
              "percentage": 39.33
            },
            {
              "candidateId": "pres-003",
              "candidateName": "Amit Singh",
              "party": "Unity Movement",
              "votes": 9,
              "percentage": 10.11
            }
          ]
        },
        {
          "postId": "post-2",
          "postName": "Vice President",
          "totalVotes": 89,
          "candidates": [
            {
              "candidateId": "vp-001",
              "candidateName": "Neha Patel",
              "party": "Community Service",
              "votes": 50,
              "percentage": 56.18
            },
            {
              "candidateId": "vp-002",
              "candidateName": "Vikram Gupta",
              "party": "Progressive Alliance",
              "votes": 39,
              "percentage": 43.82
            }
          ]
        }
      ]
    },
    "timestamp": "2024-01-15T10:45:00Z"
  }
}
```

**CSV Columns**:
- Post: Election post name
- Candidate: Candidate name
- Party: Political party/affiliation
- Votes: Number of votes received
- Percentage: Vote percentage (2 decimal places)

**JSON Structure**:
- Top-level: electionId, exportedAt, totalVotesCast
- Posts array with postId, postName, totalVotes
- Candidates array under each post with details
- Sorted by post name, then by votes descending

**Features**:
- Real-time data snapshot
- Filename includes timestamp
- CSV suitable for Excel/Sheets
- JSON suitable for programmatic use
- Candidates sorted by votes descending

**Notes**:
- Admin authentication required
- Exports current state (live data)
- No historical exports stored
- File content in response body (not downloaded)
- Use frontend to create downloadable files

---

## Error Codes

### Authentication Errors

| Code | HTTP | Description | Cause |
|------|------|-------------|-------|
| VOTER_NOT_FOUND | 400 | Mobile number not registered | Mobile not in Voters table |
| INVALID_MOBILE_FORMAT | 400 | Invalid mobile format | Wrong format or non-numeric |
| INVALID_OTP | 401 | OTP invalid/expired | Wrong OTP or expired (15 min) |
| TOKEN_EXPIRED | 401 | Authentication token expired | Token older than 1 hour |
| UNAUTHORIZED | 401 | Missing/invalid token | Token not provided or invalid |

### Voting Errors

| Code | HTTP | Description | Cause |
|------|------|-------------|-------|
| ELECTION_NOT_FOUND | 404 | Election doesn't exist | Invalid electionId |
| INVALID_POST | 400 | Post doesn't exist | Invalid postId |
| INVALID_CANDIDATE | 400 | Candidate doesn't exist | Invalid candidateId |
| VOTE_ALREADY_CAST | 409 | Vote already cast for post | Duplicate vote attempt |
| GENERAL_ERROR | 500 | Server error | See CloudWatch logs |

### Admin Errors

| Code | HTTP | Description | Cause |
|------|------|-------------|-------|
| FORBIDDEN | 403 | No admin access | Missing x-api-key or invalid |
| INVALID_REQUEST | 400 | Malformed request | Missing required fields |
| DUPLICATE_MOBILE | 400 | Mobile already registered | Voter exists in table |
| VALIDATION_FAILED | 400 | Data validation failed | See error details |

### Restriction Errors

| Code | HTTP | Description | Cause |
|------|------|-------------|-------|
| POST_EXCLUDED | 400 | Post has <2 candidates | Cannot vote for single-candidate post |

---

## Authentication

### Bearer Token Authentication

Include token in request headers:

```
Authorization: Bearer <token>
```

**Token Format**: JWT (JSON Web Token)  
**Token Validity**: 1 hour  
**Refresh**: Request new token via verify_otp

### Admin Authentication

Admin endpoints require both:

1. **Bearer Token** (from voter login OR admin token)
   ```
   Authorization: Bearer <admin-token>
   ```

2. **API Key** (static)
   ```
   x-api-key: <ADMIN_API_KEY>
   ```

**Admin API Key**: Request from backend team (stored in AWS Secrets Manager)

---

## Rate Limiting

### API Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| POST /auth/send-otp | 3 | Per hour per mobile |
| POST /auth/verify-otp | 5 attempts | 15 min lockout after failure |
| POST /elections/{id}/votes | Unlimited | Per voter per post (prevented by duplicate check) |
| GET /elections/{id}/posts | 100 | Per minute |
| GET /elections/{id}/results | 100 | Per minute |
| POST /results/{id}/export | 10 | Per minute |
| POST /admin/voters/bulk-upload | 1 | Per minute |

---

## Pagination

Results endpoints support pagination for large datasets:

```
GET /elections/{electionId}/posts?limit=20&offset=0
```

**Parameters**:
- `limit`: Number of records (default: 50, max: 100)
- `offset`: Starting position (default: 0)

**Response**:
```json
{
  "data": [...],
  "limit": 20,
  "offset": 0,
  "total": 156,
  "hasMore": true
}
```

---

## CORS Headers

All responses include CORS headers:

```
Access-Control-Allow-Origin: https://yourdomain.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization, x-api-key
Access-Control-Max-Age: 3600
```

---

## Examples

### Complete Voting Flow

```bash
# 1. Send OTP to registered voter
curl -X POST https://api.example.com/dev/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "9876543210"}'

# Response: OTP sent to mobile

# 2. Verify OTP and get token
curl -X POST https://api.example.com/dev/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "mobileNumber": "9876543210",
    "otp": "123456"
  }' | jq '.body.token' > token.txt

# 3. Get voting posts
TOKEN=$(cat token.txt)
curl -X GET https://api.example.com/dev/elections/election-2024-01/posts \
  -H "Authorization: Bearer $TOKEN"

# 4. Cast vote
curl -X POST https://api.example.com/dev/elections/election-2024-01/votes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "postId": "post-1",
    "candidateId": "pres-001"
  }'

# 5. View results (blocked if candidate)
curl -X GET https://api.example.com/dev/elections/election-2024-01/results \
  -H "Authorization: Bearer $TOKEN"

# 6. Admin exports results
curl -X POST https://api.example.com/dev/results/election-2024-01/export \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "x-api-key: your-secret-key" \
  -d '{"format": "csv"}' > results.csv
```

---

## Changelog

### Version 2.0 (NEW ENHANCEMENTS)

**New Endpoints**:
- POST /elections/{id}/posts (filtering) - Gets posts with >1 candidate
- POST /admin/voters/bulk-upload - Batch voter import
- POST /results/{id}/export - CSV/JSON export

**Enhanced Endpoints**:
- POST /auth/send-otp - Now checks Voters table
- POST /admin/candidates - Now accepts imageUrl, party, bio

**New Features**:
1. Voter verification before OTP
2. Conditional posts (>1 candidate only)
3. Candidate images in voting UI
4. Exportable results

**Backward Compatibility**:
- All old endpoints still work
- New fields in candidates are optional
- Voter table separate from existing data

### Version 1.0 (Original)

- Initial authentication implementation
- Basic voting functionality
- Admin candidate management
- Results viewing

---

For support, contact: backend-team@example.com  
For API issues, check CloudWatch logs at: `/aws/lambda/voting-*`
