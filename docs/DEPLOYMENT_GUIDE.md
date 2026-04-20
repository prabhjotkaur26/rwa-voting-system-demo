# Deployment Guide - RWA Voting System

Complete step-by-step guide to deploy the RWA Voting System on AWS.

## ✅ Prerequisites

1. **AWS Account**
   - Free Tier eligible account recommended
   - Sufficient IAM permissions to create Lambda, DynamoDB, SNS, API Gateway

2. **Local Tools**
   - Terraform v1.0+ ([Download](https://www.terraform.io/downloads))
   - AWS CLI v2+ ([Download](https://aws.amazon.com/cli/))
   - Python 3.11+ (for local testing)
   - Git (for version control)

3. **AWS Credentials**
   - AWS Access Key ID and Secret Access Key
   - Or AWS SSO configuration

## 🔐 Remote Terraform Backend Setup (NEW!)

**⚠️ IMPORTANT**: Before deploying, set up remote state storage for team collaboration.

### Prerequisites for Remote Backend
- AWS Account access
- AWS CLI installed and configured
- S3 and DynamoDB services available in your region

### Quick Setup

#### Option A: Automated Setup with Python (Recommended)

```bash
# All platforms (Windows, macOS, Linux)
cd scripts
python3 setup_terraform_backend.py

# Custom region
python3 setup_terraform_backend.py --region us-west-2

# Custom bucket name
python3 setup_terraform_backend.py --bucket my-custom-bucket-name
```

The script creates:
- ✅ S3 bucket for Terraform state storage
- ✅ DynamoDB table for state locking
- ✅ Encryption and versioning enabled
- ✅ Cross-platform support

#### Option B: Manual Setup

For detailed manual setup instructions, see [TERRAFORM_BACKEND.md](./TERRAFORM_BACKEND.md#option-b-manual-setup).

### Why Remote Backend?

| Benefit | Impact |
|---------|--------|
| **Team Collaboration** | Multiple developers work on same infrastructure |
| **State Locking** | Prevents concurrent changes (DynamoDB) |
| **Disaster Recovery** | Full state history and versioning (S3) |
| **Security** | Encrypted state storage and access control |

**Cost**: ~$0.12-0.25/month for state storage and locking

---

## 🎯 Step-by-Step Deployment

### Step 1: Setup Remote Terraform Backend

**⚠️ IMPORTANT**: Run backend setup from the scripts directory:

```bash
cd scripts
python3 setup_terraform_backend.py
```

**Output**: Get your S3 bucket name and DynamoDB table name
```
✅ S3 Bucket Created: rwa-voting-system-terraform-state-1681234567
✅ DynamoDB Table Created: rwa-voting-terraform-locks
✅ Now run: cd ../terraform && terraform init
```

### 2. Clone Repository

```bash
cd c:\PythonWork\rwa-voting-system
# Repository is already prepared locally
```

### 3. Configure AWS Credentials

```bash
# Method 1: Using AWS CLI
aws configure
# Enter Access Key ID
# Enter Secret Access Key
# Default region: ap-south-1
# Default output format: json

# Method 2: Using AWS SSO (recommended for teams)
aws sso configure
```

Verify configuration:
```bash
aws sts get-caller-identity
```

### 4. Prepare Terraform Variables

```bash
cd terraform
```

Create `terraform.tfvars` file:

```hcl
# terraform.tfvars
aws_region                = "ap-south-1"          # Change as needed
environment               = "prod"                # or "dev", "staging"
project_name              = "rwa-voting"
sns_topic_name            = "voting-otp-topic"
lambda_timeout            = 30
lambda_memory             = 256
otp_expiry_minutes        = 5
api_throttling_burst_limit = 5000
api_throttling_rate_limit  = 2000
enable_cors               = true
allowed_origins           = ["*"]  # Restrict in production

tags = {
  Project    = "RWA Voting System"
  Team       = "Tech Team"
  CostCenter = "Operations"
}
```

**Important Variables:**
- `aws_region`: Choose region closest to users (ap-south-1, ap-south-1, etc.)
- `environment`: Use `dev` for testing, `prod` for production
- `otp_expiry_minutes`: OTP validity period (default: 5 minutes)
- `api_throttling_rate_limit`: Maximum requests per second

### 5. Initialize Terraform

```bash
terraform init
```

This downloads required providers and initializes the backend.

**Output should include:**
```
Terraform has been successfully configured!
```

### 6. Plan Deployment

```bash
terraform plan -out=tfplan
```

Review the output to see all resources that will be created:
- IAM roles (1)
- DynamoDB tables (4)
- SNS topic (1)
- Lambda functions (6)
- API Gateway (1)

### 7. Apply Configuration

```bash
terraform apply tfplan
```

Wait for deployment to complete (~2-3 minutes).

**Output will include:**
```
Apply complete! Resources added, changed: X

Outputs:
api_gateway_endpoint = "https://xxxxx.execute-api.ap-south-1.amazonaws.com/prod"
dynamodb_tables = tomap({...})
lambda_functions = tomap({...})
sns_topic_arn = "arn:aws:sns:..."
...
```

**Save important outputs:**
```bash
terraform output > deployment_info.txt
```

### 8. Verify Deployment

Check all resources are created:

```bash
# Check Lambda functions
aws lambda list-functions --region ap-south-1 | grep rwa-voting

# Check DynamoDB tables
aws dynamodb list-tables --region ap-south-1

# Check SNS topics
aws sns list-topics --region ap-south-1

# Check API Gateway
aws apigatewayv2 get-apis --region ap-south-1
```

### 9. Configure SNS for SMS

By default, SNS is in sandbox mode (only test numbers work).

#### Option A: Request SMS Sandbox Removal (Recommended)

1. Go to AWS SNS Console
2. Left menu → SMS preferences
3. Under "SMS sandbox", click "Request SMS sandbox removal"
4. Fill form: "Production use for RWA election voting system"
5. Amazon reviews and approves (usually within 24 hours)

#### Option B: Add Test Numbers (for testing)

1. Go to AWS SNS Console
2. Left menu → SMS preferences
3. Under "SMS sandbox console"
4. Click "Add phone number"
5. Enter test phone number in E.164 format: +911234567890

### 10. Deploy Frontend (Optional)

#### Option A: Using S3 static hosting

```bash
# Get S3 bucket name from Terraform output
export BUCKET_NAME=$(terraform output -raw s3_bucket_name)

# Upload frontend files
aws s3 cp ../frontend/ s3://$BUCKET_NAME/ --recursive --include "*.html" --include "*.css" --include "*.js"

# Get website endpoint
terraform output s3_bucket_website_endpoint
# Visit: http://bucket-name.s3-website.ap-south-1.amazonaws.com
```

#### Option B: Using local backend

Keep frontend files locally and use API endpoint from Terraform output.

### 11. Test the System

```bash
# Set API endpoint
export API_ENDPOINT=$(terraform output -raw api_gateway_endpoint)
echo "API Endpoint: $API_ENDPOINT"

# Quick test
curl $API_ENDPOINT/admin/elections \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"electionId": "test-2024", "electionName": "Test"}'
```

See [TESTING.md](TESTING.md) for detailed tests.

## 🔧 Post-Deployment Configuration

### 1. Enable CloudWatch Detailed Monitoring (optional)

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name rwa-voting-lambda-errors \
  --alarm-description "Alert on Lambda errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold
```

### 2. Set Up Cost Alerts

```bash
# Create SNS topic for billing alerts
aws sns create-topic --name rwa-voting-billing-alerts

# Set up AWS Billing alerts in AWS Console:
# AWS Console → Billing → Billing preferences → Alert preferences
```

### 3. Enable VPC Endpoints (optional, reduces costs)

For production deployments with high volume:

```bash
# Add VPC endpoint for DynamoDB in terraform/main.tf
# Reduces data transfer costs
```

### 4. Configure Custom Domain (optional)

```bash
# 1. Create certificate in ACM for your domain
aws acm request-certificate --domain-name voting.yourdomain.com

# 2. Approve certificate via email

# 3. Create API Gateway custom domain name:
# AWS Console → API Gateway → Custom domain names → Create

# 4. Add CNAME record in your DNS provider
```

## 📊 Monitoring and Logs

### View Lambda Logs

```bash
# Get recent logs
aws logs tail /aws/lambda/rwa-voting-send-otp-prod --follow

# Get logs from specific time
aws logs tail /aws/lambda/rwa-voting-send-otp-prod --since 10m
```

### View DynamoDB Metrics

```bash
# AWS Console → DynamoDB → Monitoring
# Check:
# - Consumed capacity
# - Request latency
# - Throttled requests
```

### Create CloudWatch Dashboard

```bash
# Navigate to CloudWatch → Dashboards → Create dashboard
# Add widgets for:
# - Lambda invocations and duration
# - API Gateway requests
# - DynamoDB consumed capacity
# - SNS messages sent
```

## 🔄 Updating Deployment

### Update Lambda Code

```bash
# Edit lambda/functions/send_otp/index.py
# Then:
terraform apply -var="force_update=$(date +%s)"
```

### Update Terraform Configuration

```bash
# Edit terraform variables or configurations
# Then:
terraform plan
terraform apply
```

### Rollback Deployment

```bash
# If something went wrong:
terraform destroy -auto-approve  # Removes ALL resources

# Reapply:
terraform apply
```

⚠️ **Warning**: `terraform destroy` removes all resources including databases if remote state exists.

## 🌍 Multi-Region Deployment

To deploy in multiple AWS regions:

```bash
# Create separate workspaces
terraform workspace new prod-us
terraform workspace new prod-ap

# Switch between workspaces
terraform workspace select prod-us

# Plan and apply for each region
```

## 💾 Backup and Disaster Recovery

### Enable DynamoDB Point-in-Time Recovery

Already enabled for Elections and Votes tables. To restore:

```bash
# AWS Console → DynamoDB → Tables → rwa-voting-elections-prod
# → Point-in-time recovery → Restore table
# Select restore time and point-in-time recovery window
```

### Export DynamoDB Data

```bash
# Export votes for audit
aws dynamodb scan --table-name rwa-voting-votes-prod \
  --output json > votes_backup.json

# Export elections
aws dynamodb scan --table-name rwa-voting-elections-prod \
  --output json > elections_backup.json
```

## 🧹 Cleanup

To remove all resources and avoid charges:

```bash
# Remove S3 frontend (if deployed)
aws s3 rm s3://rwa-voting-frontend-prod-xxxxx --recursive

# Destroy Terraform resources
terraform destroy

# Verify deletion
aws ec2 describe-instances
aws lambda list-functions
```

## ❌ Troubleshooting Deployment

### Terraform Error: "AccessDenied"

**Solution**: Check IAM permissions
```bash
aws iam get-user
aws iam list-attached-user-policies --user-name your-user
```

Required permissions:
- lambda:CreateFunction
- dynamodb:CreateTable
- apigateway:*
- sns:CreateTopic
- iam:CreateRole
- iam:PutRolePolicy

### Lambda Initialization Failed

**Solution**: Check Python runtime
```bash
# Ensure Python 3.11 compatible code
python3 -m py_compile lambda/functions/*/index.py
```

### DynamoDB Quota Exceeded

**Solution**: Check account limits
```bash
aws service-quotas list-service-quotas --service-code dynamodb
```

### SNS SMS Not Sending

**Solution**: 
1. Verify SMS sandbox status
2. Check phone number format (E.164)
3. Review SNS logs in CloudWatch

### API Returning 500 Errors

**Solution**:
1. Check Lambda logs: `aws logs tail /aws/lambda/...`
2. Verify environment variables
3. Check DynamoDB table existence

## ✅ Deployment Checklist

- [ ] AWS credentials configured
- [ ] Terraform variables file created
- [ ] Terraform initialized
- [ ] Resources created successfully
- [ ] API endpoint obtained
- [ ] Lambda functions verified
- [ ] DynamoDB tables created
- [ ] SNS topic configured
- [ ] Frontend deployed (optional)
- [ ] Test election created successfully
- [ ] OTP sent and verified successfully
- [ ] Vote cast successfully
- [ ] Results retrieved successfully
- [ ] CloudWatch logs configured
- [ ] Backup strategy implemented
- [ ] Cost monitoring enabled

## 🚀 Next Steps

1. **Test the system** → See [TESTING.md](TESTING.md)
2. **Deploy frontend** → See frontend/README.md
3. **Configure admin panel** → See frontend/admin.html
4. **Review API Design** → See [API_DESIGN.md](API_DESIGN.md)
5. **Monitor costs** → See [COST_ESTIMATION.md](COST_ESTIMATION.md)

## 📞 Support

For issues:
1. Check CloudWatch logs
2. Review AWS error messages
3. Check Terraform state: `terraform show`
4. Consult AWS documentation for specific services

---

**Deployment Time**: ~5-10 minutes  
**Post-deployment Verification**: ~5 minutes  
**Total Time to Operational**: ~15 minutes
