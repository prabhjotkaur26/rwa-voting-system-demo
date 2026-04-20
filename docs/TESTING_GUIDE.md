# Testing Guide for RWA Voting System Enhancements

This guide provides step-by-step instructions to test all 4 enhancements implemented in the voting system.

## Prerequisites

Before testing, ensure you have:

1. **AWS Credentials Configured**
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, region (ap-south-1), and output format (json)
   ```

2. **Required Tools Installed**
   ```bash
   # Python 3.9+
   python3 --version
   
   # Terraform
   terraform --version
   
   # AWS CLI
   aws --version
   
   # curl (for API testing)
   curl --version
   ```

3. **Environment Variables Set**
   ```bash
   # For AWS operations
   export AWS_REGION=ap-south-1
   export AWS_PROFILE=default  # or your profile name
   
   # For local testing
   export ELECTION_ID=election-2024-01
   ```

---

## Phase 1: Infrastructure Deployment

### Step 1.1: Deploy Infrastructure with Terraform

```bash
cd terraform

# Validate configuration
terraform validate

# Plan deployment (review changes)
terraform plan -out=election.plan

# Apply changes (deploy to AWS)
terraform apply election.plan
```

**Expected Output**:
```
✓ AWS Provider configured
✓ DynamoDB tables created (4 total)
✓ Lambda functions packaged (7 total)
✓ HTTP API Gateway created
✓ API routes registered
```

### Step 1.2: Verify Table Creation

```bash
# Check if Voters table exists
aws dynamodb describe-table --table-name rwa-voting-voters-dev --region ap-south-1

# Check if Candidates table has new fields
aws dynamodb describe-table --table-name rwa-voting-candidates-dev --region ap-south-1

# Check if Votes table exists
aws dynamodb describe-table --table-name rwa-voting-votes-dev --region ap-south-1
```

**Expected Output**:
- [✓] rwa-voting-voters-dev with mobileNumber as PK
- [✓] rwa-voting-candidates-dev with imageUrl, party, bio attributes
- [✓] rwa-voting-votes-dev for vote records

---

## Phase 2: Test Enhancement 1 - Voter Verification

### Enhancement 1: Voter Verification Before OTP

This enhancement checks that the mobile number exists in the Voters table before sending OTP.

### Step 2.1: Import Sample Voter Data

```bash
# Navigate to project root
cd /path/to/rwa-voting-system

# Import sample voters (from samples/voters_import.csv)
python3 scripts/bulk_import_voters.py samples/voters_import.csv rwa-voting-voters-dev

# Expected output:
# ✓ Validation successful: 20 records found
# ✓ All mobile numbers valid
# ✓ Import completed: 20/20 records added
```

### Step 2.2: Test OTP Send - Registered Mobile

**Test Setup**: Use a mobile number from the voters import CSV

```bash
# Get a registered mobile number from samples/voters_import.csv
# Example: 9876543210

# Call send_otp API with registered mobile
curl -X POST https://<API_ID>.execute-api.ap-south-1.amazonaws.com/dev/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{
    "mobileNumber": "9876543210"
  }' | jq .
```

**Expected Response** (Success):
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

**Verification**:
- [✓] OTP generated in DynamoDB
- [✓] SMS sent to mobile number (can be monitored via SNS)

### Step 2.3: Test OTP Send - Unregistered Mobile

**Test Setup**: Use a mobile number NOT in the voters table

```bash
# Call send_otp API with unregistered mobile
curl -X POST https://<API_ID>.execute-api.ap-south-1.amazonaws.com/dev/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{
    "mobileNumber": "9999999999"
  }' | jq .
```

**Expected Response** (Failure):
```json
{
  "statusCode": 400,
  "body": {
    "errorCode": "VOTER_NOT_FOUND",
    "message": "Mobile number not registered for this election",
    "mobileNumber": "9999999999"
  }
}
```

**Verification**:
- [✓] Error code matches VOTER_NOT_FOUND
- [✓] No OTP generated for unregistered voters
- [✓] No SMS sent

### Step 2.4: Test Different Mobile Formats

The send_otp function should handle various mobile number formats:

```bash
# Test with +91 prefix
curl -X POST https://<API_ID>.execute-api.ap-south-1.amazonaws.com/dev/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "+919876543210"}' | jq .

# Test with 91 prefix (without +)
curl -X POST https://<API_ID>.execute-api.ap-south-1.amazonaws.com/dev/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "919876543210"}' | jq .

# Test with 0 prefix (Indian format)
curl -X POST https://<API_ID>.execute-api.ap-south-1.amazonaws.com/dev/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "09876543210"}' | jq .
```

**Expected Behavior**:
- [✓] All formats should be normalized to 10-digit number (9876543210)
- [✓] All should find the registered voter
- [✓] All should send OTP successfully

---

## Phase 3: Test Enhancement 2 - Conditional Election Posts

### Enhancement 2: Only Show Posts With >1 Candidate

This enhancement filters posts to show only those with 2 or more candidates.

### Step 3.1: Add Candidates to Election

First, add sample candidates with images:

```bash
# Use the sample candidates JSON
curl -X POST https://<API_ID>.execute-api.ap-south-1.amazonaws.com/dev/admin/candidates \
  -H "Content-Type: application/json" \
  -d @samples/candidates_with_images_sample.json | jq .
```

**Expected Response**:
```json
{
  "statusCode": 201,
  "body": {
    "message": "Candidates added successfully",
    "electionId": "election-2024-01",
    "postId": "1",
    "candidatesAdded": 3
  }
}
```

### Step 3.2: Add a Single Candidate Post (Should Not Appear)

```bash
# Add single candidate to a post
curl -X POST https://<API_ID>.execute-api.ap-south-1.amazonaws.com/dev/admin/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "electionId": "election-2024-01",
    "postId": "admin-post",
    "candidates": [
      {
        "candidateId": "admin-001",
        "candidateName": "Single Candidate",
        "mobileNumber": "9876543225",
        "imageUrl": "https://example.com/admin.jpg",
        "party": "Admin Committee",
        "bio": "Only candidate for this post"
      }
    ]
  }' | jq .
```

### Step 3.3: Get Posts with Filter (>1 Candidate)

```bash
# Call new get_posts endpoint
curl -X GET https://<API_ID>.execute-api.ap-south-1.amazonaws.com/dev/elections/election-2024-01/posts \
  -H "Content-Type: application/json" | jq .
```

**Expected Response**:
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
            "imageUrl": "https://example.com/rajesh.jpg",
            "party": "Green Party",
            "bio": "Community development expert"
          },
          // ... 2 more candidates
        ]
      },
      {
        "postId": "post-2",
        "postName": "Vice President",
        "candidateCount": 2,
        "candidates": [
          // ... 2 candidates
        ]
      }
      // Note: admin-post with only 1 candidate is NOT included
    ],
    "totalPosts": 6,
    "timestamp": "2024-01-15T10:35:00Z"
  }
}
```

**Verification**:
- [✓] Posts with >=2 candidates are included
- [✓] Posts with 1 candidate are excluded
- [✓] candidateCount field shows correct number
- [✓] All candidate fields including imageUrl are present

---

## Phase 4: Test Enhancement 3 - Candidate Pictures Display

### Enhancement 3: Display Candidate Images During Voting

### Step 4.1: Verify Images in Response

From Phase 3, verify that get_posts includes imageUrl:

```bash
# Extract just the candidate images
curl -s -X GET https://<API_ID>.execute-api.ap-south-1.amazonaws.com/dev/elections/election-2024-01/posts \
  | jq '.body.posts[0].candidates[] | {candidateName, imageUrl}'
```

**Expected Output**:
```json
{
  "candidateName": "Rajesh Kumar",
  "imageUrl": "https://example.com/rajesh.jpg"
}
```

### Step 4.2: Frontend Integration Test

Test that images load in the voting UI:

**In your frontend application**:

```javascript
// Fetch posts with images
fetch('/elections/election-2024-01/posts')
  .then(res => res.json())
  .then(data => {
    data.posts.forEach(post => {
      post.candidates.forEach(candidate => {
        // Render candidate card with image
        const card = document.createElement('div');
        card.className = 'candidate-card';
        card.innerHTML = `
          <img src="${candidate.imageUrl}" alt="${candidate.candidateName}">
          <h3>${candidate.candidateName}</h3>
          <p>${candidate.party}</p>
          <p>${candidate.bio}</p>
          <input type="radio" name="post-${post.postId}" value="${candidate.candidateId}">
        `;
        container.appendChild(card);
      });
    });
  });
```

**Verification Manual Tests**:
- [✓] Images load without errors
- [✓] Images display with correct aspect ratio (3:4)
- [✓] Images are responsive on mobile devices
- [✓] Broken image URLs show fallback/placeholder
- [✓] Candidate names and party info display alongside images

---

---

## Phase 5: Test Enhancement 4 - Export Results

### Enhancement 4: Results Exportable in CSV/JSON

### Step 5.1: Export Results as CSV

```bash
# Export election results as CSV
curl -X POST https://<API_ID>.execute-api.ap-south-1.amazonaws.com/dev/results/election-2024-01/export \
  -H "Content-Type: application/json" \
  -d '{
    "format": "csv"
  }' | jq .
```

**Expected Response**:
```json
{
  "statusCode": 200,
  "body": {
    "format": "csv",
    "filename": "election-2024-01-results-2024-01-15.csv",
    "content": "Post,Candidate,Votes\nPresident,Rajesh Kumar,15\nPresident,Priya Sharma,12\nVice President,Neha Patel,18\n...",
    "timestamp": "2024-01-15T10:40:00Z"
  }
}
```

### Step 5.2: Export Results as JSON

```bash
# Export election results as JSON
curl -X POST https://<API_ID>.execute-api.ap-south-1.amazonaws.com/dev/results/election-2024-01/export \
  -H "Content-Type: application/json" \
  -d '{
    "format": "json"
  }' | jq .
```

**Expected Response**:
```json
{
  "statusCode": 200,
  "body": {
    "format": "json",
    "filename": "election-2024-01-results-2024-01-15.json",
    "content": {
      "electionId": "election-2024-01",
      "exportedAt": "2024-01-15T10:40:00Z",
      "posts": [
        {
          "postName": "President",
          "results": [
            {
              "candidateName": "Rajesh Kumar",
              "party": "Green Party",
              "votes": 15,
              "percentage": 33.33
            },
            {
              "candidateName": "Priya Sharma",
              "party": "Citizens Forum",
              "votes": 12,
              "percentage": 26.67
            }
          ]
        }
      ]
    },
    "timestamp": "2024-01-15T10:40:00Z"
  }
}
```

### Step 5.3: Download and Verify Export Files

```bash
# Download CSV export
curl -X POST https://<API_ID>.execute-api.ap-south-1.amazonaws.com/dev/results/election-2024-01/export \
  -H "Content-Type: application/json" \
  -d '{"format": "csv"}' \
  | jq -r '.body.content' > election-results.csv

# View the CSV file
cat election-results.csv

# Download JSON export
curl -X POST https://<API_ID>.execute-api.ap-south-1.amazonaws.com/dev/results/election-2024-01/export \
  -H "Content-Type: application/json" \
  -d '{"format": "json"}' \
  | jq -r '.body.content' > election-results.json | jq . election-results.json
```

### Step 5.4: Frontend Integration for Export

```javascript
// Add export button handler
async function exportResults(format) {
  const response = await fetch(
    `/results/election-2024-01/export`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ format: format })
    }
  );
  
  const data = await response.json();
  const filename = data.body.filename;
  const content = data.body.content;
  
  // Create downloadable file
  const element = document.createElement('a');
  element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(content));
  element.setAttribute('download', filename);
  element.style.display = 'none';
  document.body.appendChild(element);
  element.click();
  document.body.removeChild(element);
}

// Usage
document.getElementById('export-csv-btn').onclick = () => exportResults('csv');
document.getElementById('export-json-btn').onclick = () => exportResults('json');
```

---

## Phase 7: Integration Testing

### Complete End-to-End Workflow

1. **Vote Casting Flow**
   ```bash
   # 1. Send OTP to registered voter
   curl -X POST .../auth/send-otp -d '{"mobileNumber": "9876543210"}'
   
   # 2. Verify OTP and get token
   curl -X POST .../auth/verify-otp -d '{"mobileNumber": "9876543210", "otp": "123456"}'
   
   # 3. Get voting posts
   curl -X GET .../elections/election-2024-01/posts
   
   # 4. Cast vote
   curl -X POST .../elections/election-2024-01/votes \
     -H "Authorization: Bearer <token>" \
     -d '{"postId": "1", "candidateId": "pres-001"}'
   
   # 5. Try to view results (blocked if candidate)
   curl -X GET .../elections/election-2024-01/results
   
   # 6. Admin exports results
   curl -X POST .../results/election-2024-01/export -d '{"format": "csv"}'
   ```

2. **Verification Checklist**
   - [✓] Unregistered voters blocked at OTP stage
   - [✓] Single-candidate posts don't appear
   - [✓] Candidate images display correctly
   - [✓] Candidate voters blocked from results
   - [✓] Results available in CSV and JSON
   - [✓] All data is consistent

---

## Phase 8: Troubleshooting

### Common Issues

**Issue 1: Voter not found error on registered mobile**

```bash
# Verify voter exists in table
aws dynamodb get-item \
  --table-name rwa-voting-voters-dev \
  --key '{"mobileNumber": {"S": "9876543210"}}' \
  --region ap-south-1

# If not found, re-import voters
python3 scripts/bulk_import_voters.py samples/voters_import.csv rwa-voting-voters-dev --verify
```

**Issue 2: Images not displaying in frontend**

```bash
# Check image URLs are valid
curl -I https://example.com/candidates/rajesh.jpg
# Should return 200 OK

# Update imageUrl in candidates
curl -X POST .../admin/candidates \
  -d '{"imageUrl": "https://valid-url.com/image.jpg"}'
```

**Issue 3: Export endpoint returns empty results**

```bash
# Verify votes exist in table
aws dynamodb scan \
  --table-name rwa-voting-votes-dev \
  --region ap-south-1

# Check exported content size
curl -X POST .../results/election-2024-01/export \
  -d '{"format": "json"}' \
  | jq '.body.content | length'
```

**Issue 4: API Gateway 404 errors for new endpoints**

```bash
# Verify deployment completed
aws apigatewayv2 get-routes --api-id <API_ID> --region ap-south-1

# Check if routes exist
aws apigatewayv2 get-routes --api-id <API_ID> | grep "posts\|export\|bulk-upload"
```

---

## Performance Benchmarks

Expected performance metrics:

| Operation | Response Time | Notes |
|-----------|---------------|-------|
| Send OTP | <500ms | Includes DynamoDB voter check + SNS SMS trigger |
| Get Posts | <200ms | Queries candidates table, filters in memory |
| Cast Vote | <300ms | Duplicate check + DynamoDB write |
| Export Results | <1000ms | Queries votes and candidates tables |
| Bulk Upload Voters | Varies | ~100-200 records/second depending on network |

---

## Monitoring and Logging

### CloudWatch Logs

```bash
# View send_otp logs
aws logs tail /aws/lambda/voting-send-otp --follow --region ap-south-1

# View get_posts logs
aws logs tail /aws/lambda/voting-get-posts --follow --region ap-south-1

# View export_results logs
aws logs tail /aws/lambda/voting-export-results --follow --region ap-south-1

# View bulk_upload_voters logs
aws logs tail /aws/lambda/voting-bulk-upload-voters --follow --region ap-south-1
```

### CloudWatch Metrics

```bash
# Check Lambda invocation count
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=voting-send-otp \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-16T00:00:00Z \
  --period 3600 \
  --statistics Sum \
  --region ap-south-1
```

---

## Test Results Summary

After completing all tests, fill in this checklist:

### Enhancement 1: Voter Verification
- [ ] Registered mobile receives OTP
- [ ] Unregistered mobile shows VOTER_NOT_FOUND error
- [ ] Different mobile formats work correctly (+91, 91, 0-prefix)
- [ ] No SMS sent to unregistered mobiles

### Enhancement 2: Conditional Posts
- [ ] get_posts endpoint exists and responds
- [ ] Single-candidate posts excluded from results
- [ ] Multi-candidate posts included
- [ ] candidateCount field is accurate

### Enhancement 3: Candidate Pictures
- [ ] Images appear in get_posts endpoint
- [ ] Images display in voting UI
- [ ] Images are responsive
- [ ] Broken images show gracefully

### Enhancement 4: Result Restriction
- [ ] Non-candidates can view results
- [ ] Candidates viewing results see message
- [ ] Logic correctly identifies candidates
- [ ] Restriction works after voting

### Enhancement 5: Result Export
- [ ] CSV export works
- [ ] JSON export works
- [ ] Filenames include timestamp
- [ ] Content is properly formatted
- [ ] Frontend can download files

---

## Final Verification

Once all tests pass, your enhancements are production-ready! 🎉

```bash
# Final infrastructure health check
aws dynamodb describe-table --table-name rwa-voting-voters-dev --query 'Table.TableStatus'
# Should return: "ACTIVE"

aws dynamodb describe-table --table-name rwa-voting-candidates-dev --query 'Table.TableStatus'
# Should return: "ACTIVE"

# Count records
aws dynamodb scan --table-name rwa-voting-voters-dev --select COUNT --region ap-south-1

# Verify deployment timestamp
terraform output -raw deployment_timestamp
```

For support, refer to [ENHANCEMENTS.md](ENHANCEMENTS.md) or check Lambda logs in CloudWatch.
