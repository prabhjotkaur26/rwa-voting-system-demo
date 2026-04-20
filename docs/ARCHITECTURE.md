# Architecture and Data Design - RWA Voting System

## High-Level Architecture

### Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Layer (Mobile/Web)                      │
│                  Single Page Application (React/Vue)             │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS/REST
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway (HTTP API)                         │
│                  Cost-optimized, CORS enabled                     │
├─────────────────────────────────────────────────────────────────┤
│  POST    /auth/send-otp        │  GET     /results/{electionId} │
│  POST    /auth/verify-otp      │  POST    /admin/elections      │
│  POST    /vote/cast-vote       │  POST    /admin/candidates     │
└────────┬──────────┬────────────┬──────────┬──────────┬──────────┘
         │          │            │          │          │
         ▼          ▼            ▼          ▼          ▼
    ┌────────┐┌────────┐┌──────────┐┌──────────┐┌──────────┐
    │SendOTP ││VerifyOTP││CastVote ││GetResults││CreateElec│
    │Lambda  ││Lambda  ││Lambda   ││Lambda   ││Lambda   │
    └────┬───┘└────┬───┘└────┬─────┘└────┬─────┘└────┬─────┘
         │         │          │          │           │
         └─────────┼──────────┼──────────┼───────────┘
                   ▼
         ┌──────────────────────┐
         │   DynamoDB Tables    │
         ├──────────────────────┤
         │  • Votes Table       │
         │  • OTP Table (TTL)   │
         │  • Candidates Table  │
         │  • Elections Table   │
         └────────┬─────────────┘
                  │
    ┌─────────────┼──────────────┐
    ▼             ▼              ▼
┌────────┐   ┌──────────┐   ┌──────────┐
│  SNS   │   │CloudWatch│   │   S3     │
│(SMS)   │   │(Logs)    │   │(Frontend)│
└────────┘   └──────────┘   └──────────┘
```

## Component Architecture

### 1. API Gateway (Entry Point)

**Purpose**: Route requests to appropriate Lambda functions

**Configuration**:
- Type: HTTP API (cheaper than REST API)
- Throttling: 2000 RPS normal, 5000 burst
- CORS: Enabled for all origins
- Logging: CloudWatch integration
- Authentication: Mobile OTP-based

**Routes**:
- `/auth/*` - Authentication endpoints
- `/vote/*` - Voting endpoints
- `/results/*` - Results retrieval
- `/admin/*` - Admin operations

### 2. Lambda Functions (Microservices)

Each function is independent, scalable, and stateless.

#### Function: send_otp
```
Trigger: POST /auth/send-otp
Payload: { mobileNumber: string }
Process:
  1. Validate mobile number
  2. Generate 6-digit OTP
  3. Store in DynamoDB with TTL
  4. Send via SNS SMS
Returns: { success, maskedNumber, expiryMinutes }
```

#### Function: verify_otp
```
Trigger: POST /auth/verify-otp
Payload: { mobileNumber, otp }
Process:
  1. Validate inputs
  2. Retrieve OTP from DynamoDB
  3. Compare with provided OTP
  4. Delete OTP (single-use)
  5. Generate auth token
Returns: { success, token }
```

#### Function: cast_vote
```
Trigger: POST /vote/cast-vote
Payload: { mobileNumber, electionId, postId, candidateId }
Process:
  1. Validate all parameters
  2. Check election timing (active)
  3. Verify candidate exists
  4. Check for duplicate vote
  5. Store vote with conditional write
Returns: { success, candidateName }
Security: Prevents duplicate voting at DB level
```

#### Function: get_results
```
Trigger: GET /results/{electionId}
Payload: Path parameter electionId
Process:
  1. Validate election exists
  2. Query all candidates
  3. Count votes per candidate
  4. Sort by vote count
  5. Return structured results
Returns: { electionId, results: { postId: { candidates, totalVotes } } }
```

#### Function: create_election
```
Trigger: POST /admin/elections
Payload: { electionId, electionName, startTime, endTime }
Process:
  1. Validate election doesn't exist
  2. Validate time parameters
  3. Store election metadata
Returns: { success, electionId }
```

#### Function: add_candidates
```
Trigger: POST /admin/candidates
Payload: { electionId, postId, candidates[] }
Process:
  1. Verify election exists
  2. Validate candidate data
  3. Store candidates in batch
Returns: { success, candidatesAdded }
```

### 3. DynamoDB Tables

#### Votes Table
```
PrimaryKey: electionId#postId (Hash) + mobileNumber (Range)

Attributes:
  {
    "electionId#postId": "election-2024#1",
    "mobileNumber": "9876543210",
    "candidateId": "cand-001",
    "timestamp": 1707859200
  }

GSI (Global Secondary Index):
  Name: electionId-index
  Hash: electionId
  Purpose: Query all votes in an election

Throughput: On-demand (scales automatically)
Backup: Point-in-time recovery enabled
TTL: None (votes permanent until election ends)
```

**Why this design:**
- Primary key prevents duplicate votes (mobileNumber unique per post)
- GSI enables results computation across all posts
- On-demand pricing scales with usage
- No excessive scans needed

#### OTP Table
```
PrimaryKey: mobileNumber (Hash only)

Attributes:
  {
    "mobileNumber": "9876543210",
    "otp": "123456",
    "createdAt": 1707859200,
    "ttl": 1707860100,
    "attempts": 0
  }

TTL:
  Attribute: ttl
  Automatic expiry: 5 minutes (configurable)

Throughput: On-demand
Purpose: Temporary OTP storage with automatic cleanup
```

**Design decisions:**
- Single item per phone number (overwrites previous OTP)
- TTL attribute auto-deletes expired OTPs (no manual cleanup)
- Attempts counter prevents brute force (max 3 attempts)

#### Candidates Table
```
PrimaryKey: electionId#postId (Hash) + candidateId (Range)

Attributes:
  {
    "electionId#postId": "election-2024#1",
    "candidateId": "cand-001",
    "candidateName": "John Doe",
    "electionId": "election-2024",
    "postId": "1",
    "createdAt": 1707859200
  }

Throughput: On-demand
Purpose: Store candidates per post per election
```

#### Elections Table
```
PrimaryKey: electionId (Hash only)

Attributes:
  {
    "electionId": "election-2024",
    "electionName": "Q4 2024 Board Elections",
    "description": "Annual elections",
    "startTime": 1707859200,
    "endTime": 1707945600,
    "createdAt": 1707859200,
    "status": "ongoing",
    "resultsVisible": false
  }

Throughput: On-demand
Backup: Point-in-time recovery enabled
Purpose: Election metadata and timing
```

## Data Flow

### Complete Voting Workflow

```
1. Voter Access
   User -> Opens frontend -> Loads static HTML/CSS/JS from S3

2. Authentication
   User -> Enters mobile number
   Frontend -> POST /auth/send-otp
   Lambda -> Validates, generates OTP, sends SMS via SNS
   DynamoDB -> Stores OTP with TTL
   User -> Receives SMS, enters OTP
   Frontend -> POST /auth/verify-otp
   Lambda -> Validates, deletes OTP, returns token
   Frontend -> Stores token, shows voting interface

3. Voting
   User -> Selects candidates for 7 posts
   Frontend -> For each post: POST /vote/cast-vote
   Lambda -> For each vote:
     - Validates election is active
     - Checks candidate exists
     - Checks no duplicate vote exists
     - DynamoDB conditional write (fails if duplicate)
     - Returns success
   DynamoDB -> Each vote creates new item in Votes table
   Frontend -> Shows success

4. Results
   User/Anyone -> Opens results page
   Frontend -> GET /results/{electionId}
   Lambda -> Queries candidates and votes
   Lambda -> Counts votes per candidate
   Lambda -> Returns sorted results
   Frontend -> Displays live vote counts
   (Optional) Frontend auto-refreshes every 5-10 seconds
```

## Security Design

### OTP Security

**Generation**:
- 6-digit random OTP (000000-999999)
- Cryptographically secure random
- No predictable patterns

**Storage**:
- Stored hashed in DynamoDB
- TTL automatically deletes after 5 minutes
- Single-use: Deleted after successful verification
- Max 3 failed attempts: Blocks further attempts

**Delivery**:
- Via AWS SNS SMS (encrypted in transit)
- No OTP in logs or responses
- Phone number masked in responses

### Vote Security

**Validation**:
- Election ID verified to exist
- Post ID validated (1-7)
- Candidate ID verified to exist
- All inputs type-checked and sanitized

**Duplicate Prevention**:
- DynamoDB conditional write: `attribute_not_exists(mobileNumber)`
- Fails if mobile number already voted for post
- Prevents race conditions at DB level

**Anonymity**:
- Vote stored with mobile reference but results don't map back
- No voter name/personal data in vote record
- Only vote count per candidate revealed

**Access Control**:
- Lambda execution role has minimal permissions
- Only required DynamoDB operations allowed
- SNS publish restricted to voting topic
- CloudWatch logging sanitized (mobile numbers masked)

## Performance Optimization

### Read Optimization

**Results Retrieval**:
```
Traditional approach (Stream-based): DynamoDB Streams + Lambda + aggregation
  - Continuous processing
  - Real-time updates
  - Costs: Multiple Lambda invocations, stream processing

Our approach (On-demand):
  - Query votes table when results requested
  - Count per candidate in Lambda memory
  - Return sorted results
  - Cost: Single read query + Lambda invocation
  - Speed: 200-500ms for 1000 votes
```

**Index Strategy**:
```
Votes Table:
  Primary: electionId#postId + mobileNumber
    -> Fast: Prevent duplicate votes
  GSI: electionId only
    -> Fast: Get all votes for election
    -> Used for: Results, audits
```

### Lambda Optimization

**Memory Allocation**:
- 256 MB default (good balance)
- Can reduce to 128 MB for 50% cost savings
- Most functions execute in < 500ms

**Cold Start**:
- Python 3.11 is faster than other runtimes
- No third-party dependencies (only boto3)
- Minimal package size (~100 KB)

**Timeout**:
- 30 seconds (sufficient for all operations)
- Most complete within 2-5 seconds

## Scalability

### Handling Growth

**100 voters**:
- DynamoDB: 700 write operations (100 × 7 posts)
- Lambda: 1000+ invocations
- Cost: Minimal (all within free tier)

**1,000 voters**:
- DynamoDB: 7000 write operations
- Lambda: 10,000+ invocations
- Cost: < $1/month

**10,000 voters (peak hour)**:
- DynamoDB: 70,000 writes
- API Gateway: Handle traffic (5000 RPS burst ok)
- Lambda: Concurrent invocations ~100-200
- Cost: $10-20 for event

**Bottleneck**: SNS SMS delivery (not compute)

### Scaling Strategy

1. **For compute**: Use Lambda layers, optimize code
2. **For storage**: Use DynamoDB provisioned capacity or archive old elections
3. **For votes**: Use DynamoDB Global Tables for multi-region
4. **For frontend**: Use CloudFront CDN

## Monitoring and Logging

### Metrics

**Lambda**:
- Duration (should be < 1 second average)
- Invocations (count per endpoint)
- Errors (should be 0-1%)
- Throttles (should be 0)

**DynamoDB**:
- ConsumedReadCapacity
- ConsumedWriteCapacity
- UserErrors
- SystemErrors

**API Gateway**:
- 4XX errors (validation failures, expected)
- 5XX errors (should be 0-1%)
- Latency (should be < 1 second)

### Logging

**What we log**:
- API requests (method, path, status)
- Lambda execution (start, end, duration)
- Errors (full stack, not sensitive data)

**What we don't log**:
- OTPs (security risk)
- Full mobile numbers (privacy)
- Vote details (anonymity)
- Request/response bodies (performance)

**Retention**: 7 days (configurable)

## Cost Implications

### Per-Request Cost Breakdown

**OTP Send:**
- Lambda: $0.0000002 (invocation) + $0.0000167 (0.1GB-s)
- SNS: $0.0112 (India SMS)
- **Total: ~$0.013**

**Vote Cast:**
- Lambda: $0.0000002 + $0.0000167
- DynamoDB: $0.0000006 (write) + $0.00000125 (3-5 reads)
- **Total: ~$0.00002**

**Results Fetch:**
- Lambda: $0.0000002 + $0.0000167
- DynamoDB: $0.00000125 per read (depends on items)
- **Total: ~$0.00002-0.0001**

## Future Enhancements

### Performance
- DynamoDB DAX caching layer
- ElastiCache for session management
- CloudFront CDN for frontend

### Features
- Email OTP (free alternative to SMS)
- JWT tokens (instead of mobile-based)
- Multi-language support
- Result export to CSV/PDF

### Security
- AWS KMS for encryption
- VPC endpoints for private access
- WAF for API protection
- Audit logging with encryption

### Scale
- Global Tables for multi-region
- Lambda@Edge for latency reduction
- Event-driven architecture (SNS/SQS)

---

**Last Updated**: 2024
**Architecture Version**: 1.0
