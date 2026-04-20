# Admin Panel Quick Start & Testing Guide

## 🚀 Quick Access

### Links
- **Voter Interface**: http://rwa-voting-frontend-prod-750035244407.s3-website.ap-south-1.amazonaws.com/
- **Admin Panel**: http://rwa-voting-frontend-prod-750035244407.s3-website.ap-south-1.amazonaws.com/admin.html
- **API Endpoint**: https://vxvqzxd6rb.execute-api.ap-south-1.amazonaws.com/prod

---

## 📊 Testing the System

### Test 1: Voter Registration & OTP Flow

```bash
# Step 1: Send OTP
curl -X POST https://vxvqzxd6rb.execute-api.ap-south-1.amazonaws.com/prod/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{
    "mobileNumber": "9876543210"
  }'

# Expected Response:
# {
#   "statusCode": 200,
#   "body": {
#     "message": "OTP sent successfully",
#     "data": {
#       "mobileNumber": "9876543210",
#       "expiresIn": 300
#     }
#   }
# }
```

### Test 2: Verify OTP

```bash
# Step 2: Verify OTP (use OTP from DynamoDB otp-prod table)
curl -X POST https://vxvqzxd6rb.execute-api.ap-south-1.amazonaws.com/prod/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "mobileNumber": "9876543210",
    "otp": "123456"
  }'

# Expected Response:
# {
#   "statusCode": 200,
#   "body": {
#     "message": "OTP verified successfully",
#     "data": {
#       "token": "generated-token",
#       "mobileNumber": "9876543210"
#     }
#   }
# }
```

### Test 3: List Posts for Election

```bash
# Get posts available for an election
curl https://vxvqzxd6rb.execute-api.ap-south-1.amazonaws.com/prod/elections/q4-2024-election/posts

# Expected Response:
# [
#   {
#     "postId": "president",
#     "postName": "President",
#     "candidates": [...]
#   },
#   ...
# ]
```

### Test 4: Cast Vote

```bash
curl -X POST https://vxvqzxd6rb.execute-api.ap-south-1.amazonaws.com/prod/vote/cast-vote \
  -H "Content-Type: application/json" \
  -d '{
    "mobileNumber": "9876543210",
    "electionId": "q4-2024-election",
    "votes": {
      "president": "candidate1-id",
      "vice-president": "candidate2-id"
    }
  }'

# Expected Response:
# {
#   "statusCode": 200,
#   "body": {
#     "message": "Vote recorded successfully",
#     "data": {
#       "voteId": "generated-id",
#       "timestamp": "2024-01-15T10:30:00Z"
#     }
#   }
# }
```

### Test 5: Get Election Results

```bash
curl https://vxvqzxd6rb.execute-api.ap-south-1.amazonaws.com/prod/results/q4-2024-election

# Expected Response:
# {
#   "statusCode": 200,
#   "body": {
#     "electionId": "q4-2024-election",
#     "posts": {
#       "president": {
#         "postName": "President",
#         "candidates": [
#           {
#             "candidateName": "John Doe",
#             "votes": 45
#           },
#           ...
#         ]
#       },
#       ...
#     }
#   }
# }
```

### Test 6: Admin - Create Election

```bash
curl -X POST https://vxvqzxd6rb.execute-api.ap-south-1.amazonaws.com/prod/admin/elections \
  -H "Content-Type: application/json" \
  -d '{
    "electionId": "test-election-2024",
    "electionName": "Test RWA Elections 2024",
    "description": "Testing the system"
  }'

# Note: Elections are currently mocked in admin.js
# To enable live API calls, uncomment the apiCall in admin.js
```

### Test 7: Admin - Add Candidates

```bash
curl -X POST https://vxvqzxd6rb.execute-api.ap-south-1.amazonaws.com/prod/admin/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "electionId": "q4-2024-election",
    "postId": "president",
    "candidateName": "John Doe",
    "description": "Experienced leader with 10 years in RWA"
  }'
```

### Test 8: Admin - Bulk Upload Voters

```bash
curl -X POST https://vxvqzxd6rb.execute-api.ap-south-1.amazonaws.com/prod/admin/voters/bulk-upload \
  -H "Content-Type: application/json" \
  -d '{
    "voters": [
      {
        "mobileNumber": "9876543210",
        "name": "John Doe",
        "flatNumber": "A-101",
        "area": "Tower A"
      },
      {
        "mobileNumber": "9876543211",
        "name": "Jane Smith",
        "flatNumber": "B-205",
        "area": "Tower B"
      }
    ]
  }'
```

### Test 9: Export Results

```bash
curl -X POST https://vxvqzxd6rb.execute-api.ap-south-1.amazonaws.com/prod/results/q4-2024-election/export \
  -H "Content-Type: application/json" \
  -d '{
    "format": "csv"
  }'

# Expected Response:
# {
#   "statusCode": 200,
#   "body": {
#     "message": "Results exported successfully",
#     "downloadUrl": "s3://bucket/results.csv"
#   }
# }
```

---

## 💾 Testing with DynamoDB

### View Elections
```bash
aws dynamodb scan \
  --table-name elections-prod \
  --region ap-south-1
```

### View Candidates
```bash
aws dynamodb scan \
  --table-name candidates-prod \
  --region ap-south-1
```

### View Votes (Caution: Returns all votes!)
```bash
aws dynamodb scan \
  --table-name votes-prod \
  --region ap-south-1 \
  --limit 10  # Limit to 10 items
```

### View OTP Attempts
```bash
aws dynamodb scan \
  --table-name otp-prod \
  --region ap-south-1
```

### View Voters
```bash
aws dynamodb scan \
  --table-name voters-prod \
  --region ap-south-1
```

### Query Vote Count for Election

```bash
aws dynamodb query \
  --table-name votes-prod \
  --key-condition-expression "electionId = :eid" \
  --expression-attribute-values '{
    ":eid": {"S": "q4-2024-election"}
  }' \
  --region ap-south-1
```

---

## 🔍 Monitoring & Logs

### Check Lambda Logs

```bash
# View recent logs
aws logs tail /aws/lambda/rwa-voting-send-otp-prod --follow --region ap-south-1

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/rwa-voting-send-otp-prod \
  --filter-pattern "ERROR" \
  --region ap-south-1
```

### Monitor All Lambda Functions

```bash
# List all functions
aws lambda list-functions --region ap-south-1 --query 'Functions[*].[FunctionName,LastModified]' --output table

# Get function details
aws lambda get-function --function-name rwa-voting-send-otp-prod --region ap-south-1
```

### Check API Gateway Metrics

```bash
# View API Gateway logs (if configured)
aws logs describe-log-groups \
  --log-group-name-prefix /aws/apigateway/ \
  --region ap-south-1
```

---

## 🔧 Admin Panel Testing

### Step 1: Open Admin Panel
```
URL: http://rwa-voting-frontend-prod-750035244407.s3-website.ap-south-1.amazonaws.com/admin.html
```

### Step 2: Test Dashboard
- ✅ Should show stat boxes
- ✅ Refresh button should update stats
- ✅ Alert messages should appear

### Step 3: Test Elections Management
- ✅ Click "Elections" tab
- ✅ Fill in election ID, name, description
- ✅ Click "Create Election" button
- ✅ Success message should appear
- ✅ New election should appear in list

### Step 4: Test Candidates Management
- ✅ Click "Candidates" tab
- ✅ Select election from dropdown
- ✅ Select post from dropdown (1-7)
- ✅ Enter candidate name and bio
- ✅ Click "Add Candidate" button
- ✅ Success message should appear

### Step 5: Test Voters Import
- ✅ Click "Voters" tab
- ✅ Create sample CSV file:
  ```csv
  mobileNumber,name,flatNumber,area
  9876543210,John Doe,A-101,Tower A
  9876543211,Jane Smith,B-205,Tower B
  ```
- ✅ Click "Choose File" and select CSV
- ✅ Click "Upload" button
- ✅ Check parsing message

### Step 6: Test Results Viewing
- ✅ Click "Results" tab
- ✅ Select election from dropdown
- ✅ Click "Load Results"
- ✅ Should show vote counts and percentages
- ✅ Click "Export Results" button

---

## 🐛 Debugging Tips

### Frontend Console
1. Press `F12` to open Developer Tools
2. Go to "Console" tab
3. Look for any error messages
4. Check network requests in "Network" tab

### Common Issues & Solutions

**Issue**: Admin panel shows blank screen
```
Solution:
1. Hard refresh (Ctrl+F5)
2. Check browser console for errors
3. Check if admin.html exists in S3
4. Check S3 bucket permissions
```

**Issue**: API calls return 502 Bad Gateway
```
Solution:
1. Check Lambda function logs: aws logs tail /aws/lambda/function-name --follow
2. Verify Lambda has proper IAM permissions
3. Check if Lambda timeout is sufficient (usually 30s)
4. Verify environment variables are set
```

**Issue**: OTP not sent to mobile
```
Solution:
1. Check SNS topic exists in ap-south-1
2. Verify IAM policy allows SNS:Publish with Resource: "*"
3. Check mobile number format (should be 10 digits)
4. Check CloudWatch logs for SNS errors
5. Verify mobile is in voters-prod table
```

**Issue**: DynamoDB Throttling
```
Solution:
1. Check current DynamoDB capacity: aws dynamodb describe-table --table-name votes-prod
2. Increase provisioned throughput or use PAY_PER_REQUEST
3. Consider adding DynamoDB auto-scaling
```

---

## 📈 Performance Testing

### Simple Load Test (10 concurrent requests)
```bash
for i in {1..10}; do
  curl -X POST https://vxvqzxd6rb.execute-api.ap-south-1.amazonaws.com/prod/auth/send-otp \
    -H "Content-Type: application/json" \
    -d "{\"mobileNumber\": \"987654321$i\"}" &
done
```

### Check Lambda Concurrent Executions
```bash
aws lambda get-account-settings --region ap-south-1
```

### Monitor DynamoDB Consumed Capacity
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedWriteCapacityUnits \
  --dimensions Name=TableName,Value=votes-prod \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 300 \
  --statistics Sum \
  --region ap-south-1
```

---

## 🚀 Deployment Checklist

Before production deployment:

- [ ] Test all 9 Lambda functions
- [ ] Verify all API endpoints
- [ ] Test admin panel CRUD operations
- [ ] Test voter voting flow end-to-end
- [ ] Check CloudWatch monitoring
- [ ] Review IAM policies
- [ ] Test SNS SMS delivery
- [ ] Load test with expected concurrent users
- [ ] Verify S3 website hosting
- [ ] Check CORS configuration
- [ ] Test election results export
- [ ] Verify DynamoDB backups configured
- [ ] Document all secret keys and credentials
- [ ] Create admin runbook
- [ ] Train admins on system operation

---

## 📞 Support

For issues:
1. Check `docs/TROUBLESHOOTING.md` for common problems
2. Review CloudWatch logs
3. Check API Gateway logs
4. Verify Lambda function permissions
5. Test endpoints with curl/Postman

For feature requests or enhancements:
- See `docs/ENHANCEMENTS.md` 
- See `ADMIN_PANEL_SETUP.md` for missing components

---

**Last Updated**: 2024  
**System Version**: 1.0.0  
**Admin Panel Version**: 1.0.0
