# Troubleshooting Guide

Complete troubleshooting for common issues in the RWA Voting System.

## Table of Contents

1. [Deployment Issues](#deployment-issues)
2. [AWS Configuration](#aws-configuration)
3. [OTP Issues](#otp-issues)
4. [API Issues](#api-issues)
5. [Frontend Issues](#frontend-issues)
6. [Database Issues](#database-issues)
7. [Performance Issues](#performance-issues)
8. [Cost Issues](#cost-issues)

---

## Deployment Issues

### Terraform init fails: "No valid credential sources found"

**Symptom**: Error during `terraform init`

**Causes**:
- AWS credentials not configured
- Incorrect AWS access key/secret
- Expired credentials

**Solutions**:

```bash
# Option 1: Configure with CLI
aws configure
# Enter: Access Key ID, Secret Access Key, Region (ap-south-1), Output (json)

# Option 2: Use environment variables
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="ap-south-1"

# Option 3: Use AWS SSO
aws sso login --profile your-profile
export AWS_PROFILE=your-profile

# Verify credentials
aws sts get-caller-identity
```

**Prevention**: 
- Rotate credentials regularly
- Use IAM roles instead of long-lived keys
- Never commit credentials to Git

---

### Terraform plan shows "Access Denied" errors

**Symptom**: 
```
Error: creating IAM role: AccessDenied
```

**Causes**:
- IAM user lacks necessary permissions
- Organization policies blocking resources
- Trusted advisor restrictions

**Solutions**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iam:*",
        "lambda:*",
        "dynamodb:*",
        "apigateway:*",
        "sns:*",
        "s3:*",
        "logs:*"
      ],
      "Resource": "*"
    }
  ]
}
```

Request these permissions from your AWS account administrator.

---

### DynamoDB validation error: "Table already exists"

**Symptom**: 
```
Error: ValidationException: Table ... already exists
```

**Causes**:
- Running terraform apply twice
- Previous deployment not cleaned up
- Table name conflict with other projects

**Solutions**:

```bash
# Option 1: Import existing table
terraform import aws_dynamodb_table.votes arn:aws:dynamodb:region:account:table/name

# Option 2: Destroy and recreate
terraform destroy  # Destroys all resources
terraform apply    # Recreates everything

# Option 3: Change table names in variables.tf
variable "votes_table_name" {
  default = "votes-2024-unique-name"  # Add unique suffix
}
```

---

### Lambda function creation fails: "Payload file size exceeded"

**Symptom**:
```
Error: InvalidParameterValueException: Unzipped size must be less than 262144000 bytes
```

**Causes**:
- Lambda function code too large (>50MB unzipped)
- Dependencies not optimized

**Solutions**:

```bash
# Check zip sizes
ls -lh lambda/.build/

# Remove unnecessary dependencies
# In requirements-lambda.txt, keep only:
boto3  # Built-in, don't include
botocore  # Built-in, don't include

# Use Lambda Layers for shared code
terraform/modules/lambda/layers.tf  # Create separate layer
```

---

### API Gateway deployment fails: "Invalid API key"

**Symptom**:
```
Error: InvalidAPIKeyException
```

**Solutions**:

```bash
# Recreate API Gateway
terraform destroy -target=module.api_gateway
terraform apply -target=module.api_gateway

# Check API key exists
aws apigateway get-api-keys --region ap-south-1
```

---

## AWS Configuration

### S3 bucket name conflict: "A bucket with that name already exists"

**Symptom**: During terraform apply

**Causes**:
- S3 bucket names are globally unique
- Someone else owns that name
- Bucket from previous AWS account

**Solutions**:

In `terraform/terraform.tfvars`:
```hcl
# Use project + timestamp for uniqueness
s3_bucket_name = "rwa-voting-${var.environment}-${local.timestamp}"

# Or add random suffix
locals {
  random_suffix = random_id.bucket_suffix.hex
  bucket_name = "rwa-voting-${local.random_suffix}"
}
```

---

### VPC/Subnet errors: "Invalid availability zone"

**Symptom**:
```
Error: InvalidInput.NotFound: No such subnet
```

**Causes**:
- Lambda trying to use VPC from wrong region
- Availability zone not available in region

**Solutions**:

Lambda should NOT use VPC by default (not needed for this system):

In `terraform/modules/lambda/main.tf`:
```hcl
# Remove or comment out:
# vpc_config { ... }

# This allows Lambda to access DynamoDB and SNS without VPC overhead
```

---

## OTP Issues

### OTP never arrives: No SMS received

**Symptom**: 
- User requests OTP
- No SMS received on phone

**Causes**:
1. **SNS Sandbox Mode** (most common)
   - New AWS accounts start in SMS sandbox
   - Can only send to verified numbers
   
2. **Phone number not in sandbox**
   - Number not explicitly added
   
3. **SmsEndpoint not verified**
   - SNS topic configuration incomplete

4. **Insufficient SNS quota**
   - Monthly SMS limit exceeded

**Solutions**:

**Step 1: Check SNS Sandbox Status**
```bash
bash verify_deployment.sh [API_ENDPOINT]

# Or manually check
aws sns get-sms-attributes --attributes MonthlySpendLimit
aws sns get-sms-attributes --attributes DefaultSmsType

# Status output
# MonthlySpendLimit = $0 = Sandbox mode
# MonthlySpendLimit > $0 = Production mode
```

**Step 2: Add phone to sandbox (temporary testing)**
```bash
# Add verified phone numbers (max 100)
aws sns verify-phone-number-attribute \
    --phone-number +919876543210 \
    --region ap-south-1
```

**Step 3: Request sandbox removal (production)**
```bash
# AWS Support Console → Service Quota Increase
# Service: SNS
# Quota: SMS monthly spend limit
# Desired value: 10 (or higher)
# Use case: RWA election votingwit 500-1000 voters

# AWS processes requests within 24 hours
```

**Step 4: Enable Transactional SMS (optional)**
```bash
# In SNS topic:
aws sns set-sms-attributes \
    --attributes DefaultSmsType=Transactional \
    --region ap-south-1

# Transactional SMS:
# - Lower cost ($0.60 per SMS vs $0.75)
# - Higher priority delivery
# - No throttling
```

---

### OTP incorrectly formatted: Received multiple OTPs

**Symptom**:
```
Error: Too many requests - OTP already sent
```

Or receiving multiple OTPs for same number

**Causes**:
- User clicking "Send OTP" multiple times
- Frontend not disabling button during request

**Solutions**:

Frontend fix (app.js):
```javascript
async sendOTP() {
    if (this.otpSending) return;  // Prevent duplicate requests
    
    this.otpSending = true;
    
    try {
        const response = await this.apiCall('/auth/send-otp', {
            mobileNumber: this.currentMobileNumber
        });
        
        // Start timer for next request
        this.otpSendTimeout = 30;  // Wait 30 seconds
        this.startOTPTimer();
    } finally {
        this.otpSending = false;
    }
}
```

Backend fix (verification has rate limiting):
```python
# send_otp/index.py includes rate limiting
# Check if OTP was sent < 2 minutes ago
# If yes, return cached OTP without sending SMS again
```

---

### OTP expired before user enters it

**Symptom**:
```
Error: OTP_NOT_FOUND or OTP_EXPIRED
```

**Causes**:
- Default OTP timeout is 5 minutes
- User took longer to receive SMS
- User took longer to enter OTP

**Solutions**:

Increase OTP expiry in `terraform/variables.tf`:
```hcl
variable "otp_expiry_minutes" {
  description = "OTP validity period in minutes"
  type        = number
  default     = 5
  
  # Change to:
  default     = 10  # 10 minutes
}

terraform apply -var="otp_expiry_minutes=10"
```

Or implement resend mechanism:
```javascript
// Allow user to request new OTP after 2 minutes
this.resendOTPTime = 120;  // seconds
startResendTimer();
```

---

## API Issues

### POST request fails: CORS policy error

**Symptom**:
```
Access to XMLHttpRequest blocked by CORS policy
No 'Access-Control-Allow-Origin' header
```

**Causes**:
- API endpoint CORS not configured
- Frontend domain not whitelisted
- Request method not allowed

**Solutions**:

Check CORS configuration:
```bash
# Verify CORS is enabled
terraform output api_gateway_endpoint

# Test with curl (includes CORS headers)
curl -X POST https://api.example.com/auth/send-otp \
  -H "Origin: https://yourdomain.com" \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "9876543210"}'

# Response should include:
# Access-Control-Allow-Origin: *
```

Fix in Frontend (app.js):
```javascript
// Ensure correct API endpoint
getAPIEndpoint() {
    // Must be HTTPS in production
    return "https://your-api-id.execute-api.ap-south-1.amazonaws.com/prod";
}
```

Fix in Terraform (api_gateway/main.tf):
```hcl
cors_configuration {
  allow_headers = ["*"]
  allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
  allow_origins = ["*"]  # Or specific domain
  expose_headers = ["*"]
}
```

---

### API returns 500 error: "Internal Server Error"

**Symptom**:
```
Error: Internal Server Error (500)
```

**Solutions**:

Step 1: Check CloudWatch Logs
```bash
# List Lambda functions
aws lambda list-functions --region ap-south-1

# Get logs for specific function
aws logs tail /aws/lambda/rwa-voting-send-otp --follow

# Filter for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/rwa-voting-send-otp \
  --filter-pattern "ERROR"
```

Step 2: Common causes
```
Error: botocore.exceptions.ClientError - DynamoDB table not found
Fix: Verify table name in environment variables

Error: AttributeError - Missing environment variable
Fix: Check Lambda environment variables in AWS Console

Error: ValidationError - Invalid JSON
Fix: Verify request body format

Error: ThrottlingException - Rate limit exceeded
Fix: Increase API throttle limits or implement exponential backoff
```

---

### API returns 404: "Not Found"

**Symptom**:
```
Error: 404 Not Found
```

**Causes**:
- Wrong API endpoint
- Wrong path
- Lambda integration not configured

**Solutions**:

Verify endpoint:
```bash
# Get correct endpoint
terraform output api_gateway_endpoint
# Output: https://abc123.execute-api.ap-south-1.amazonaws.com/prod

# Test endpoint
curl https://abc123.execute-api.ap-south-1.amazonaws.com/prod/auth/send-otp
```

Check API routes:
```bash
aws apigateway get-resources \
  --rest-api-id abc123 \
  --region ap-south-1
```

---

### API returns 429: "Too Many Requests"

**Symptom**:
```
Error: 429 Too Many Requests
Retry-After: 60
```

**Causes**:
- Exceeded API throttle limit (2000 RPS, 5000 burst)
- Lambda concurrency limit
- DynamoDB throttling

**Solutions**:

Increase API throttle:
```hcl
# In api_gateway/main.tf
route_settings = {
  "POST /vote/cast-vote" = {
    throttle_settings = {
      rate_limit  = 5000  # 5000 requests/sec
      burst_limit = 10000 # 10000 burst
    }
  }
}
```

Implement exponential backoff in frontend:
```javascript
async apiCallWithRetry(endpoint, data, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await this.apiCall(endpoint, data);
        } catch (error) {
            if (error.status === 429 && i < maxRetries - 1) {
                await this.sleep(Math.pow(2, i) * 1000);  // Exponential backoff
                continue;
            }
            throw error;
        }
    }
}
```

---

## Frontend Issues

### Frontend not loading: Blank page

**Symptom**:
- Browser shows blank page
- Console shows errors

**Solutions**:

Check browser console (F12):
```
1. Open DevTools → Console tab
2. Check for JavaScript errors
3. Common errors:
   - "Cannot read property 'API_ENDPOINT' of undefined"
   - "app.js failed to load"
```

Verify file structure:
```bash
# Check files exist
ls -la frontend/
# Output should show: index.html, style.css, app.js

# Serve with Python
python -m http.server 8000

# Open in browser
# http://localhost:8000
```

---

### Mobile layout broken: Elements overlapping

**Symptom**:
- Elements overlap on phone
- Text too small
- Buttons not clickable

**Solutions**:

Add mobile viewport:
```html
<!-- In index.html <head> -->
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

Test responsive design:
```
Chrome/Firefox:
1. Open DevTools (F12)
2. Click device toolbar (mobile icon)
3. Select iPhone/Android device
4. Verify layout works
```

---

### Voting form doesn't submit

**Symptom**:
```
Click "Submit Votes" → Nothing happens
Or: "Form validation error"
```

**Causes**:
- API endpoint not configured
- Not all 7 posts selected
- Network error

**Solutions**:

Debug in browser console:
```javascript
// In DevTools Console
votingClient.API_ENDPOINT  // Should show URL
votingClient.votes        // Should show all 7 posts selected
votingClient.authToken    // Should have value
```

Check all posts selected:
```javascript
// All 7 posts must have selection
Posts:
  1. President ✓
  2. Vice President ✓
  3. Treasurer ✓
  4. Secretary ✓
  5. Joint Secretary ✓
  6. PR ✓
  7. Youth Member ✓
```

---

## Database Issues

### DynamoDB: Items not appearing in results

**Symptom**:
- Vote cast successfully
- Results show 0 votes
- Items not in table

**Causes**:
- Wrong table queried
- Partition key incorrect
- GSI not queried

**Solutions**:

Check DynamoDB data:
```bash
# List tables
aws dynamodb list-tables --region ap-south-1

# Scan votes table
aws dynamodb scan \
  --table-name rwa-voting-votes-dev \
  --region ap-south-1 \
  --limit 10

# Query results
aws dynamodb query \
  --table-name rwa-voting-votes-dev \
  --key-condition-expression "electionId = :eid AND attribute_exists(mobileNumber)" \
  --expression-attribute-values "{\":eid\": {\"S\": \"election-2024-01\"}}" \
  --region ap-south-1
```

---

### DynamoDB: Capacity exceeded

**Symptom**:
```
ProvisionedThroughputExceededException
ConstraintViolation - Provisioned throughput exceeded
```

**Causes**:
- Using provisioned capacity (not on-demand)
- Too many concurrent requests

**Solutions**:

Switch to on-demand:
```hcl
# In dynamodb/main.tf
billing_mode = "PAY_PER_REQUEST"  # On-demand

# Do NOT use provisioned
# read_capacity_units = 100
# write_capacity_units = 100
```

Apply changes:
```bash
terraform apply -target=module.dynamodb
```

---

## Performance Issues

### Results loading very slow

**Symptom**:
- Results page takes 10+ seconds to load
- Votes still being computed

**Causes**:
- Large number of votes
- Inefficient DynamoDB query
- Lambda cold start

**Solutions**:

Add caching:
```javascript
// Cache results for 10 seconds
if (this.cachedResults && 
    Date.now() - this.cachedResultsTime < 10000) {
    return this.cachedResults;
}

// Or pre-compute results in separate Lambda
```

Optimize DynamoDB queries:
```python
# Pre-compute results instead of scanning all votes
# Store in separate "Results" table, update every 30 seconds

result_table = dynamodb.Table('rwa-voting-results')
result_table.put_item(Item={
    'electionId': election_id,
    'timestamp': current_time,
    'results': computed_results  # Pre-computed
})
```

---

### Lambda functions timing out

**Symptom**:
```
Task timed out after 30.00 seconds
```

**Causes**:
- Default 30-second timeout too short
- DynamoDB query scanning too many items
- SNS call hanging

**Solutions**:

Increase timeout:
```hcl
# In terraform/variables.tf
variable "lambda_timeout_seconds" {
  default = 60  # Increased from 30
}
```

Optimize queries:
```python
# Inefficient - scans all items
response = votes_table.scan()

# Efficient - uses partition key
response = votes_table.query(
    KeyConditionExpression='electionId = :eid',
    ExpressionAttributeValues={':eid': 'election-2024-01'}
)
```

---

## Cost Issues

### Unexpected high AWS bill

**Symptom**:
- Bill higher than $5-10/month
- Costs increasing over time

**Common causes**:

1. **SNS costs (most likely)**
   - SMS charges $0.60-0.75 per message
   - Solution: Use email OTP instead

2. **DynamoDB provisioned capacity**
   - Using provisioned instead of on-demand
   - Solution: Switch to `PAY_PER_REQUEST`

3. **CloudWatch Logs**
   - Excessive logging
   - Solution: Reduce log level or set retention

4. **Data Transfer**
   - Cross-region data transfer costs
   - Solution: Keep all resources in same region

**Cost optimization**:

```bash
# Check DynamoDB pricing mode
aws dynamodb describe-table \
  --table-name rwa-voting-votes-dev \
  --region ap-south-1 \
  | grep BillingModeSummary

# Should show:
# "BillingMode": "PAY_PER_REQUEST"

# Not:
# "BillingMode": "PROVISIONED"
```

Make cost changes:
```hcl
# terraform/variables.tf
variable "otp_enabled" {
  default = false  # Disable SMS
}

variable "use_email_otp" {
  default = true   # Use cheaper email
}

# Will save ~$0.70 per voter!
```

---

## Need More Help?

- **AWS Console**: Check CloudWatch Logs and CloudWatch Metrics
- **AWS Support**: Premium support for urgent issues
- **Stack Overflow**: Tag with `aws-lambda`, `dynamodb`, `terraform`
- **GitHub Issues**: Report bugs and feature requests

---

**Last Updated**: 2024  
**Coverage**: 50+ common issues with solutions
