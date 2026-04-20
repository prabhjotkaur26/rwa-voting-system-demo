# RWA Voting System - Enhancement Implementation Guide

## Overview

This guide documents the enhancements implemented in this version:

1. **Voter Verification** - Mobile numbers must exist in registered voter data
2. **Conditional Election Posts** - Only posts with >1 candidate appear in voting
3. **Candidate Pictures** - Display photos during voting
4. **Exportable Results** - Export election results in CSV/JSON formats

---

## 1. Voter Verification Enhancement

###  What Changed

**Before**: Anyone with a valid mobile format could send OTP  
**After**: Mobile must exist in the voter registration database

### Implementation

**Database**: New `Voters` table created with:
- `mobileNumber` (PK) - 10-digit number
- `flatNumber` - Flat/house number
- `name` - Voter name
- `email` (optional) - Voter email
- `area` (optional) - Area/society name

**Lambda Function**: `send_otp` updated to:
```python
# 1. Validate mobile format
# 2. Check if mobile exists in Voters table
#   ├─ If YES: Generate and send OTP
#   └─ If NO: Return error "VOTER_NOT_FOUND"
# 3. Send OTP via SNS
```

### Deployment Steps

#### Step 1: Create Voters Table

The Voters table is automatically created when you run:

```bash
cd terraform
terraform apply
```

#### Step 2: Populate Voter Data

**Option A: Using Lambda Function (Admin API)**

```bash
curl -X POST https://your-api.com/admin/voters/bulk-upload \
  -H "Content-Type: application/json" \
  -d '{
    "voters": [
      {
        "flatNumber": "A-101",
        "name": "John Doe",
        "mobileNumber": "9876543210",
        "email": "john@example.com",
        "area": "Tower A"
      },
      {
        "flatNumber": "B-205",
        "name": "Jane Smith",
        "mobileNumber": "9876543211",
        "area": "Tower B"
      }
    ]
  }'
```

**Option B: Direct DynamoDB Insert (AWS Console)**

1. Open AWS DynamoDB → Tables → `rwa-voting-voters-env`
2. Click "Explore table items"
3. Click "Create item"
4. Add items with structure:
   ```json
   {
     "mobileNumber": "9876543210",
     "flatNumber": "A-101",
     "name": "John Doe",
     "email": "john@example.com",
     "area": "Tower A"
   }
   ```

**Option C: Bulk Import Script**

Create file `import_voters.py`:

```python
import json
import boto3
import sys

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('rwa-voting-voters-dev')  # Change table name

voters_data = [
    {"flatNumber": "A-101", "name": "John Doe", "mobileNumber": "9876543210"},
    {"flatNumber": "A-102", "name": "Jane Smith", "mobileNumber": "9876543211"},
    # Add more voters
]

for voter in voters_data:
    table.put_item(Item={
        'mobileNumber': voter['mobileNumber'],
        'flatNumber': voter['flatNumber'],
        'name': voter['name']
    })
    print(f"Added: {voter['name']}")

print(f"Total voters added: {len(voters_data)}")
```

Run:
```bash
python import_voters.py
```

### Testing

**Test Valid Voter** (exists in table):
```bash
curl -X POST https://your-api.com/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "9876543210"}'

# Response: 200 OK - OTP sent successfully
```

**Test Invalid Voter** (not in table):
```bash
curl -X POST https://your-api.com/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "9999999999"}'

# Response: 400 Bad Request
# Error: VOTER_NOT_FOUND
# Message: "Mobile number not found in voter records"
```

### Database Schema Update

**New Table Created Automatically**

```
voters-table/
├─ PK: mobileNumber (String, 10 digits)
├─ Attributes:
│  ├── flatNumber (String) - Flat/house number
│  ├── name (String) - Full name
│  ├── email (String, optional)
│  ├── area (String, optional)
│  └── uploadedAt (Number) - Timestamp
├─ GSI: flatNumber-index (for searching by flat)
└─ PITR: Enabled (Point-in-time recovery)
```

---

## 2. Conditional Election Posts

### What Changed

**Before**: All 7 posts shown in voting, even if only 1 candidate applied  
**After**: Only posts with >1 candidates display for voting

### Implementation

**New Endpoint**: `GET /elections/{electionId}/posts`

```json
Response:
{
  "success": true,
  "data": {
    "posts": [
      {
        "postId": "post-1",
        "postName": "President",
        "candidates": [...],
        "candidateCount": 2
      }
      // Only posts with >1 candidate shown
    ]
  }
}
```

**Lambda Function**: `get_posts` 

```python
# 1. Query all candidates for election
# 2. Group by post
# 3. Filter posts with >1 candidates
# 4. Return filtered list
```

### Frontend Integration

Update your `app.js` to use new endpoint:

```javascript
// Instead of hardcoded posts
async loadVotingPosts(electionId) {
    const response = await this.apiCall(
        `/elections/${electionId}/posts`,
        'GET'
    );
    
    if (response.success) {
        return response.data.posts;  // Only posts with >1 candidate
    }
}
```

### Testing

```bash
curl -X GET https://your-api.com/elections/election-2024-01/posts
```

Expected response shows only posts with multiple candidates:
```json
{
  "success": true,
  "data": {
    "posts": [
      {
        "postId": "post-1",
        "postName": "President",
        "candidateCount": 3,
        "candidates": [...]
      },
      {
        "postId": "post-3",
        "postName": "Treasurer",
        "candidateCount": 2,
        "candidates": [...]
      }
      // Posts with only 1 candidate are NOT included
    ]
  }
}
```

---

## 3. Candidate Pictures

### What Changed

**Before**: Only candidate names displayed  
**After**: Profile pictures shown for each candidate during voting

### Implementation

**Updated Database**: Candidates table now includes:
- `imageUrl` - URL to candidate's photo
- `party` - Political party (optional)
- `bio` - Candidate biography (optional)

**Updated Endpoint**: `POST /admin/candidates` now accepts:

```json
{
  "electionId": "election-2024-01",
  "postId": "1",
  "candidates": [
    {
      "candidateId": "cand-001",
      "candidateName": "John Doe",
      "imageUrl": "https://example.com/photos/john.jpg",
      "party": "Party A",
      "bio": "Experienced in community development"
    }
  ]
}
```

### Adding Candidate Pictures

**Method 1: Upload to S3 and Reference**

```bash
# 1. Upload image to S3
aws s3 cp john.jpg s3://my-bucket/candidates/john.jpg --acl public-read

# 2. Get public URL
# https://my-bucket.s3.amazonaws.com/candidates/john.jpg

# 3. Add candidate with imageUrl
curl -X POST https://your-api.com/admin/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "electionId": "election-2024-01",
    "postId": "1",
    "candidates": [
      {
        "candidateId": "cand-001",
        "candidateName": "John Doe",
        "imageUrl": "https://my-bucket.s3.amazonaws.com/candidates/john.jpg"
      }
    ]
  }'
```

**Method 2: Use External URL**

```bash
curl -X POST https://your-api.com/admin/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "electionId": "election-2024-01",
    "postId": "1",
    "candidates": [
      {
        "candidateId": "cand-001",
        "candidateName": "John Doe",
        "imageUrl": "https://example.com/council-members/john.jpg"
      }
    ]
  }'
```

### Frontend Display

Update `index.html` voting section:

```html
<div class="candidate-card">
  <img src="{imageUrl}" alt="{candidateName}" class="candidate-image">
  <h4>{candidateName}</h4>
  <p class="candidate-bio">{bio}</p>
  <p class="candidate-party">{party}</p>
</div>
```

Update `app.js`:

```javascript
displayCandidates(post) {
    const candidatesHtml = post.candidates.map(candidate => `
        <div class="candidate-card">
            ${candidate.imageUrl ? `<img src="${candidate.imageUrl}" alt="${candidate.name}">` : ''}
            <h4>${candidate.name}</h4>
            ${candidate.bio ? `<p class="bio">${candidate.bio}</p>` : ''}
            ${candidate.party ? `<p class="party">${candidate.party}</p>` : ''}
        </div>
    `).join('');
    
    return candidatesHtml;
}
```

### Image Requirements

- **Format**: JPG, PNG, WebP
- **Size**: Up to 10MB per image (recommended: 500KB)
- **Dimensions**: 300x400px recommended (aspect ratio: 3:4)
- **Accessibility**: Always include alt text
- **Hosting**: S3, CDN, or public URL

---

## 4. Exportable Results

### What Changed

**New**: Election results can be exported in CSV or JSON formats

### Implementation

**New Endpoint**: `POST /results/{electionId}/export`

```bash
curl -X POST https://your-api.com/results/election-2024-01/export \
  -H "Content-Type: application/json" \
  -d '{"format": "csv"}'
```

**Response**:

```json
{
  "success": true,
  "data": {
    "filename": "election-2024-01-results-20240101_120000.csv",
    "content": "Post,Candidate,Votes\nPresident,John Doe,45\nPresident,Jane Smith,38\n...",
    "format": "csv"
  }
}
```

### Usage Examples

**Export as CSV**:

```bash
curl -X POST https://your-api.com/results/election-2024-01/export \
  -H "Content-Type: application/json" \
  -d '{"format": "csv"}' \
  > results.csv
```

**Export as JSON**:

```bash
curl -X POST https://your-api.com/results/election-2024-01/export \
  -H "Content-Type: application/json" \
  -d '{"format": "json"}' \
  > results.json
```

### CSV Format

```
Post,Candidate,Votes
President,John Doe,45
President,Jane Smith,38
President,Bob Wilson,32
Vice President,Alice Brown,55
Vice President,Charlie Davis,42
...
```

### JSON Format

```json
{
  "President": [
    {"candidateId": "cand-001", "name": "John Doe", "votes": 45},
    {"candidateId": "cand-002", "name": "Jane Smith", "votes": 38},
    {"candidateId": "cand-003", "name": "Bob Wilson", "votes": 32}
  ],
  "Vice President": [
    {"candidateId": "cand-004", "name": "Alice Brown", "votes": 55},
    {"candidateId": "cand-005", "name": "Charlie Davis", "votes": 42}
  ]
}
```

### Frontend Integration

Add export button to results section in `index.html`:

```html
<div id="resultsExportSection" class="section" style="display: none;">
    <h2>Export Results</h2>
    <button onclick="votingClient.exportResults('csv')" class="btn btn-primary">
        Download as CSV
    </button>
    <button onclick="votingClient.exportResults('json')" class="btn btn-primary">
        Download as JSON
    </button>
</div>
```

Add to `app.js`:

```javascript
async exportResults(format = 'csv') {
    try {
        this.showSpinner(true);
        
        const response = await this.apiCall(
            `/results/${this.currentElectionId}/export`,
            'POST',
            { format }
        );
        
        if (response.success) {
            const content = response.data.content;
            const filename = response.data.filename;
            
            // Create blob and download
            const blob = new Blob([content], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            
            this.showMessage(
                'statusBar',
                `Results exported as ${format.toUpperCase()}`,
                'success'
            );
        }
    } catch (error) {
        console.error('Export error:', error);
        this.showMessage('statusBar', 'Error exporting results', 'error');
    } finally {
        this.showSpinner(false);
    }
}
```

---

## New API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/send-otp` | POST | Send OTP (now checks voter exists) |
| `/elections/{electionId}/posts` | GET | Get posts with >1 candidates |
| `/admin/candidates` | POST | Add candidates (with images) |
| `/results/{electionId}/export` | POST | Export results (CSV/JSON) |
| `/admin/voters/bulk-upload` | POST | Bulk import voter data |

---

## Deployment Checklist

- [ ] Run `terraform apply` to create new tables and endpoints
- [ ] Populate voters table with voter data
- [ ] Update Lambda IAM policies (automatic)
- [ ] Update API Gateway routes (automatic)
- [ ] Test voter verification endpoint
- [ ] Test get-posts endpoint
- [ ] Add candidate photos
- [ ] Update frontend code for candidate images
- [ ] Test export results endpoint

---

## Troubleshooting

### Error: "VOTER_NOT_FOUND"
- **Cause**: Mobile number not in voters table
- **Solution**: Add mobile to voters table using bulk-upload or DynamoDB console

### No candidates shown in voting
- **Cause**: No posts have >1 candidates
- **Solution**: Add at least 2 candidates per post using add-candidates endpoint

### Candidate images not displaying
- **Cause**: Invalid image URL or CORS issues
- **Solution**: Verify URL is public, use S3 with public ACL

### Export returns blank file
- **Cause**: No votes recorded yet
- **Solution**: Cast votes first, then export

---

## API Documentation Updates

See [docs/API_DESIGN.md](../docs/API_DESIGN.md) for complete endpoint specifications.

**New endpoints documented**:
- GET /elections/{electionId}/posts
- POST /results/{electionId}/export
- POST /admin/voters/bulk-upload

---

## See Also

- [DEPLOYMENT_GUIDE.md](../docs/DEPLOYMENT_GUIDE.md) - Complete deployment instructions
- [TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md) - Common issues and solutions
- [README.md](../README.md) - Project overview
