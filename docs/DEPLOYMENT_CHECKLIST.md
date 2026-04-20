# Deployment Checklist - RWA Voting System Enhancements

**Intended For**: Backend/DevOps teams  
**Time Estimate**: 30-45 minutes  
**Prerequisites**: AWS CLI configured, Terraform installed, Python 3.9+

---

## Pre-Deployment Verification

### [ ] 1. Code Review

- [ ] Review all lambda functions in `lambda/functions/`
- [ ] Check Terraform modules in `terraform/modules/`
- [ ] Verify environment variable configurations
- [ ] Confirm no hardcoded secrets in code
- [ ] Review error handling in all functions

```bash
# Code quality check
find lambda/functions -name "*.py" -exec python3 -m py_compile {} \;
echo "✓ Python syntax valid"

# Terraform validation
cd terraform
terraform validate
echo "✓ Terraform syntax valid"
```

---

## Pre-Deployment Steps

### [ ] 2. Environment Setup

```bash
# Set region and environment
export AWS_REGION=ap-south-1
export ENVIRONMENT=dev  # or 'prod' for production
export PROJECT_NAME=rwa-voting
export AWS_PROFILE=default  # Your AWS profile
```

### [ ] 3. Backup Current Infrastructure

```bash
# Export current DynamoDB tables
for table in rwa-voting-candidates-dev rwa-voting-votes-dev rwa-voting-elections-dev; do
  echo "Backing up $table..."
  aws dynamodb create-backup --table-name "$table" --backup-name "$table-backup-$(date +%Y%m%d-%H%M%S)" --region $AWS_REGION
done

echo "✓ Backups created"

# List backups
aws dynamodb list-backups --table-name rwa-voting-candidates-dev --region $AWS_REGION
```

### [ ] 4. Infrastructure State Check

```bash
# Check current Terraform state
cd terraform
terraform state list

# Expected output should show existing resources:
# - aws_dynamodb_table.candidates
# - aws_dynamodb_table.votes
# - aws_dynamodb_table.elections
# - aws_lambda_function.send_otp
# - aws_lambda_function.verify_otp
# - ... (other existing resources)

echo "✓ Current state verified"
```

---

## Database Migration

### [ ] 5. Create New Voters Table

```bash
cd terraform

# Plan the new infrastructure
terraform plan -out=deployment.plan

# Review the plan output
cat deployment.plan | grep rwa-voting-voters-dev

# Expected: Created resource `aws_dynamodb_table.voters`
```

### [ ] 6. Apply Terraform Changes

```bash
# Apply infrastructure changes
terraform apply deployment.plan

# Expected output:
# aws_dynamodb_table.voters: Creating...
# aws_lambda_function.get_posts: Creating...
# aws_lambda_function.export_results: Creating...
# aws_lambda_function.bulk_upload_voters: Creating...
# ... (other changes)
# Apply complete! Resources added: 10

echo "✓ Infrastructure deployed"
```

### [ ] 7. Verify New Tables Created

```bash
# Verify Voters table
aws dynamodb describe-table \
  --table-name rwa-voting-voters-dev \
  --region $AWS_REGION \
  --query 'Table.TableStatus'

# Expected output: ACTIVE

# Check table schema
aws dynamodb describe-table \
  --table-name rwa-voting-voters-dev \
  --region $AWS_REGION \
  --query 'Table.KeySchema'

# Expected output:
# [
#     {
#         "AttributeName": "mobileNumber",
#         "KeyType": "HASH"
#     }
# ]

echo "✓ Voters table verified"
```

---

## Lambda Function Deployment

### [ ] 8. Verify Lambda Functions Created

```bash
# List all Lambda functions
aws lambda list-functions \
  --region $AWS_REGION \
  --query 'Functions[?starts_with(FunctionName, `voting`)].FunctionName' \
  --output table

# Expected to see:
# - voting-send-otp (modified)
# - voting-verify-otp
# - voting-cast-vote
# - voting-get-posts (NEW)
# - voting-export-results (NEW)
# - voting-bulk-upload-voters (NEW)
# - voting-add-candidates (modified)

# Test each new function
for fn in voting-get-posts voting-export-results voting-bulk-upload-voters; do
  echo "Testing $fn..."
  aws lambda invoke \
    --function-name $fn \
    --payload '{}' \
    --region $AWS_REGION \
    /tmp/$fn-test.json
  echo "✓ $fn invokable"
done
```

### [ ] 9. Check Environment Variables

```bash
# Verify send_otp has VOTERS_TABLE_NAME
aws lambda get-function-configuration \
  --function-name voting-send-otp \
  --region $AWS_REGION \
  --query 'Environment.Variables' \
  --output json | jq '.VOTERS_TABLE_NAME'

# Expected: "rwa-voting-voters-dev"

# Verify get_posts has required variables
aws lambda get-function-configuration \
  --function-name voting-get-posts \
  --region $AWS_REGION \
  --query 'Environment.Variables' | jq '.CANDIDATES_TABLE_NAME'

# Expected: "rwa-voting-candidates-dev"

echo "✓ Environment variables configured"
```

### [ ] 10. Verify Lambda Permissions

```bash
# Check API Gateway permissions for new functions
aws lambda get-policy \
  --function-name voting-get-posts \
  --region $AWS_REGION

# Should show ApiGateway permission statement
# Statement with Principal: apigateway.amazonaws.com

echo "✓ Lambda permissions verified"
```

---

## API Gateway Configuration

### [ ] 11. Verify New API Routes

```bash
# Get API ID
API_ID=$(terraform output -raw api_gateway_api_id)
echo "API ID: $API_ID"

# List all routes
aws apigatewayv2 get-routes \
  --api-id $API_ID \
  --region $AWS_REGION \
  --query 'Items[?contains(RouteKey, `posts`) || contains(RouteKey, `export`) || contains(RouteKey, `bulk-upload`)].{RouteKey,Target}' \
  --output table

# Expected routes:
# GET /elections/{electionId}/posts
# POST /results/{electionId}/export
# POST /admin/voters/bulk-upload

echo "✓ API routes configured"
```

### [ ] 12. Test API Endpoints (Not Yet Live)

```bash
# Get API endpoint
API_ENDPOINT=$(terraform output -raw api_gateway_api_endpoint)
echo "API Endpoint: $API_ENDPOINT"

# Test GET /elections/test/posts (should fail - no auth)
curl -X GET $API_ENDPOINT/dev/elections/test/posts \
  -H "Content-Type: application/json" \
  2>/dev/null | jq '.statusCode'

# Expected: 401 (Unauthorized)

echo "✓ API endpoints responding"
```

---

## Data Import

### [ ] 13. Prepare Voter Data

```bash
# Review sample voter CSV
cat samples/voters_import.csv | head -10

# Expected format:
# mobileNumber,flatNumber,name,email,area
# 9876543210,101,Rajesh Kumar,rajesh@example.com,Tower A
# ...

# If using custom CSV, validate format
python3 -c "
import csv
with open('your_voters.csv', 'r') as f:
    reader = csv.DictReader(f)
    count = 0
    for row in reader:
        count += 1
        if count <= 5:
            print(row)
    print(f'Total rows: {count}')
"

echo "✓ Voter data prepared"
```

### [ ] 14. Import Voter Data

```bash
# Using sample data
python3 scripts/bulk_import_voters.py \
  samples/voters_import.csv \
  rwa-voting-voters-dev \
  --region $AWS_REGION

# Expected output:
# ✓ Validation successful: 20 records found
# ✓ Connecting to DynamoDB (rwa-voting-voters-dev)
# ✓ Processing records...
# ✓ Import completed: 20/20 records imported

# Or using your own CSV
python3 scripts/bulk_import_voters.py \
  path/to/your_voters.csv \
  rwa-voting-voters-dev \
  --region $AWS_REGION

echo "✓ Voter data imported"
```

### [ ] 15. Verify Voter Import

```bash
# Count voters in table
aws dynamodb scan \
  --table-name rwa-voting-voters-dev \
  --region $AWS_REGION \
  --select COUNT \
  --query 'Count'

# Expected: 20 (or your record count)

# Sample a voter record
aws dynamodb scan \
  --table-name rwa-voting-voters-dev \
  --region $AWS_REGION \
  --limit 1 \
  --output json | jq '.Items[0]'

# Expected output shows voter structure
echo "✓ Voter data verified"
```

---

## Candidate Data Setup

### [ ] 16. Add Candidates with Images

```bash
# Using sample candidates JSON
curl -X POST $API_ENDPOINT/dev/admin/candidates \
  -H "Content-Type: application/json" \
  -H "x-api-key: $ADMIN_API_KEY" \
  -d @samples/candidates_with_images_sample.json

# Expected response: 201 Created
# {
#   "message": "Candidates added successfully",
#   "candidatesAdded": 7
# }

echo "✓ Candidates added with images"
```

### [ ] 17. Verify Candidates in Database

```bash
# Count candidates
aws dynamodb scan \
  --table-name rwa-voting-candidates-dev \
  --region $AWS_REGION \
  --select COUNT

# Expected: >0

# View candidate with image
aws dynamodb scan \
  --table-name rwa-voting-candidates-dev \
  --region $AWS_REGION \
  --limit 1 \
  --output json | jq '.Items[0]'

# Should show imageUrl, party, bio fields
echo "✓ Candidates verified with image fields"
```

---

## Functionality Testing

### [ ] 18. Test Voter Verification (Enhancement 1)

```bash
# Get a registered mobile from voters
REGISTERED_MOBILE="9876543210"
UNREGISTERED_MOBILE="9999999999"

# Test with registered mobile
echo "Testing registered mobile..."
curl -X POST $API_ENDPOINT/dev/auth/send-otp \
  -H "Content-Type: application/json" \
  -d "{\"mobileNumber\": \"$REGISTERED_MOBILE\"}" \
  | jq '.statusCode'

# Expected: 200

# Test with unregistered mobile
echo "Testing unregistered mobile..."
curl -X POST $API_ENDPOINT/dev/auth/send-otp \
  -H "Content-Type: application/json" \
  -d "{\"mobileNumber\": \"$UNREGISTERED_MOBILE\"}" \
  | jq '.body.errorCode'

# Expected: "VOTER_NOT_FOUND"

echo "✓ Voter verification working"
```

### [ ] 19. Test Conditional Posts (Enhancement 2)

```bash
# Get posts endpoint should only return posts with >1 candidate
echo "Testing conditional posts..."

# First, get a token (use test user)
TOKEN=$(curl -s -X POST $API_ENDPOINT/dev/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "9876543210", "otp": "123456"}' \
  | jq -r '.body.token')

# Get posts
curl -X GET "$API_ENDPOINT/dev/elections/election-2024-01/posts" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.body.posts | length'

# Expected: 6 (posts with >1 candidate, not single-candidate posts)

# Verify all posts have >1 candidate
curl -X GET "$API_ENDPOINT/dev/elections/election-2024-01/posts" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.body.posts[] | select(.candidateCount < 2)'

# Expected: empty output (no posts with <2 candidates)

echo "✓ Conditional posts working"
```

### [ ] 20. Test Candidate Pictures (Enhancement 3)

```bash
# Verify imageUrl in posts response
TOKEN=$(curl -s -X POST $API_ENDPOINT/dev/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "9876543210", "otp": "123456"}' \
  | jq -r '.body.token')

curl -X GET "$API_ENDPOINT/dev/elections/election-2024-01/posts" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.body.posts[0].candidates[0].imageUrl'

# Expected: URL like "https://s3.amazonaws.com/candidates/rajesh.jpg"

echo "✓ Candidate pictures available"
```

### [ ] 21. Test Export Results (Enhancement 4)

```bash
# Export as CSV
echo "Testing CSV export..."
curl -X POST "$API_ENDPOINT/dev/results/election-2024-01/export" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $ADMIN_API_KEY" \
  -d '{"format": "csv"}' \
  | jq '.body.format'

# Expected: "csv"

# Export as JSON
echo "Testing JSON export..."
curl -X POST "$API_ENDPOINT/dev/results/election-2024-01/export" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $ADMIN_API_KEY" \
  -d '{"format": "json"}' \
  | jq '.body.format'

# Expected: "json"

echo "✓ Export functionality working"
```

---

## Documentation Verification

### [ ] 22. Documentation Complete

```bash
# Check all documentation files
echo "Checking documentation..."

[ -f docs/ENHANCEMENTS.md ] && echo "✓ ENHANCEMENTS.md exists" || echo "✗ ENHANCEMENTS.md missing"
[ -f docs/API_REFERENCE.md ] && echo "✓ API_REFERENCE.md exists" || echo "✗ API_REFERENCE.md missing"
[ -f docs/TESTING_GUIDE.md ] && echo "✓ TESTING_GUIDE.md exists" || echo "✗ TESTING_GUIDE.md missing"

# Check script files
[ -f scripts/bulk_import_voters.py ] && echo "✓ bulk_import_voters.py exists" || echo "✗ bulk_import_voters.py missing"
[ -f samples/voters_import.csv ] && echo "✓ voters_import.csv exists" || echo "✗ voters_import.csv missing"
[ -f samples/candidates_with_images_sample.json ] && echo "✓ candidates_with_images_sample.json exists" || echo "✗ candidates_with_images_sample.json missing"

echo "✓ All documentation present"
```

---

## CloudWatch Monitoring

### [ ] 23. Configure CloudWatch Alerts

```bash
# Check CloudWatch logs for new functions
for fn in send_otp get_posts export_results bulk_upload_voters; do
  aws logs describe-log-groups \
    --log-group-name-prefix "/aws/lambda/voting-$fn" \
    --region $AWS_REGION
  echo "✓ Log group for voting-$fn exists"
done

# Create alarm for high error rate (optional)
aws cloudwatch put-metric-alarm \
  --alarm-name voting-lambda-errors \
  --alarm-description "Alert on Lambda errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=voting-send-otp \
  --region $AWS_REGION

echo "✓ CloudWatch alarms configured"
```

### [ ] 24. Monitor Logs

```bash
# Tail logs for new functions
aws logs tail /aws/lambda/voting-get-posts --follow --region $AWS_REGION &
aws logs tail /aws/lambda/voting-export-results --follow --region $AWS_REGION &

# In another terminal, trigger some API calls to generate logs
# Logs should appear in real-time

echo "✓ Logs monitored"
```

---

## Performance Testing

### [ ] 25. Load Test API

```bash
# Test GET /posts endpoint
echo "Load testing GET /posts..."
ab -n 100 -c 10 -H "Authorization: Bearer $TOKEN" \
  "$API_ENDPOINT/dev/elections/election-2024-01/posts"

# Expected:
# - Requests per second: >50
# - Failed requests: 0
# - Average time: <200ms

# Test export endpoint
echo "Load testing export endpoint..."
ab -n 50 -c 5 -p export-payload.json -T application/json \
  "$API_ENDPOINT/dev/results/election-2024-01/export"

# Expected:
# - Requests per second: >20
# - Failed requests: 0
# - Average time: <500ms

echo "✓ Performance acceptable"
```

---

## Production Readiness

### [ ] 26. Backup Complete State

```bash
# Backup DynamoDB with new Voters table
aws dynamodb create-backup \
  --table-name rwa-voting-voters-dev \
  --backup-name rwa-voting-voters-deployment-$(date +%Y%m%d-%H%M%S) \
  --region $AWS_REGION

# Backup Terraform state
cp terraform/terraform.tfstate terraform/terraform.tfstate.backup.$(date +%Y%m%d-%H%M%S)

# Backup to S3 (recommended)
aws s3 cp terraform/terraform.tfstate s3://your-backup-bucket/terraform-state-backup/

echo "✓ Complete backup created"
```

### [ ] 27. Create Rollback Plan

```bash
cat > ROLLBACK_PLAN.md << 'EOF'
# Rollback Procedure

## If Deployment Fails

1. Destroy new resources:
   ```bash
   terraform destroy -target aws_dynamodb_table.voters
   terraform destroy -target aws_lambda_function.get_posts
   terraform destroy -target aws_lambda_function.export_results
   terraform destroy -target aws_lambda_function.bulk_upload_voters
   ```

2. Restore previous state:
   ```bash
   aws s3 cp s3://your-backup-bucket/terraform-state-backup/terraform.tfstate.backup terraform/
   terraform refresh
   ```

3. Restore database from backup:
   ```bash
   aws dynamodb restore-table-from-backup \
     --target-table-name rwa-voting-voters-dev \
     --backup-arn <backup-arn>
   ```

## If Running but Issues Occur

1. Disable new endpoints in API Gateway
2. Revert Lambda functions to previous version
3. Roll back database migration

## Contact
- Backend team email
- AWS support ticket
EOF

echo "✓ Rollback plan created"
```

---

## Final Verification

### [ ] 28. Production Checklist

- [ ] All infrastructure deployed successfully
- [ ] Voters table created and populated
- [ ] All Lambda functions deployed
- [ ] API Gateway routes configured
- [ ] Candidate images stored
- [ ] All tests passing
- [ ] CloudWatch monitoring active
- [ ] Documentation complete
- [ ] Backups verified
- [ ] Rollback plan ready

### [ ] 29. Notify Teams

```bash
cat > DEPLOYMENT_SUMMARY.txt << 'EOF'
🎉 RWA Voting System - Enhancements Deployed

Deployment Date: $(date)
Status: SUCCESS ✓

New Features:
✓ Voter verification before OTP
✓ Conditional election posts (>1 candidate)
✓ Candidate pictures display
✓ Results export (CSV/JSON)

Infrastructure Changes:
✓ New DynamoDB Voters table
✓ 3 new Lambda functions
✓ 4 new API endpoints
✓ Updated existing functions

Documentation:
✓ ENHANCEMENTS.md - Feature guide
✓ API_REFERENCE.md - Complete API docs
✓ TESTING_GUIDE.md - Test procedures

Data:
✓ 20+ voter records imported
✓ Candidate images uploaded
✓ Sample data for testing

Next Steps:
1. Update frontend code to use new endpoints
2. Display candidate images in voting UI
3. Add export button to results view
4. Run end-to-end testing
5. Deploy frontend update

Contact: backend-team@example.com
EOF

cat DEPLOYMENT_SUMMARY.txt

echo "✓ Deployment complete!"
```

---

## Post-Deployment Monitoring (First 24 Hours)

### Monitor These Metrics:

```bash
# Lambda execution time and errors
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --statistics Maximum,Average,Minimum \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --dimensions Name=FunctionName,Value=voting-send-otp \
  --region $AWS_REGION

# DynamoDB read/write capacity
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedWriteCapacityUnits \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --dimensions Name=TableName,Value=rwa-voting-voters-dev \
  --region $AWS_REGION
```

### Daily for First Week:

- [ ] Review CloudWatch logs for errors
- [ ] Check DynamoDB metrics
- [ ] Monitor Lambda performance
- [ ] Verify all endpoints operational
- [ ] Track voter verification success rate

---

## Troubleshooting

**Issue**: Voters table not creating
```bash
# Check Terraform state
terraform state show aws_dynamodb_table.voters

# Check DynamoDB directly
aws dynamodb list-tables --region $AWS_REGION | grep voters
```

**Issue**: Lambda functions not invoking
```bash
# Check function code
aws lambda get-function-code --function-name voting-get-posts --region $AWS_REGION

# Test invocation
aws lambda invoke --function-name voting-get-posts --payload '{}' /tmp/output.json --region $AWS_REGION
cat /tmp/output.json
```

**Issue**: API routes not working
```bash
# Check route configuration
aws apigatewayv2 get-routes --api-id $API_ID --query "Items[?contains(RouteKey, 'posts')]" --region $AWS_REGION

# Check Lambda permissions
aws lambda list-permissions --function-name voting-get-posts --region $AWS_REGION
```

---

## Sign-Off

**Deployed By**: ________________________  
**Date**: ____________________________  
**Time**: ____________________________  
**Environment**: Production / Staging / Dev  
**Approved By**: _______________________  

**Checksum of Deployed Code**:
```bash
find terraform -name "*.tf" -exec cat {} \; | sha256sum
find lambda -name "*.py" -exec cat {} \; | sha256sum
```

---

**Deployment successful! 🎉**

For ongoing support, refer to [API_REFERENCE.md](API_REFERENCE.md) and [TESTING_GUIDE.md](TESTING_GUIDE.md)
