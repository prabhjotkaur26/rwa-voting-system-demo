#!/bin/bash

# Terraform Remote Backend Setup Script
# This script creates the necessary AWS resources for remote Terraform state management
# Run this BEFORE running terraform init, plan, or apply

set -e

echo "🔧 RWA Voting System - Terraform Remote Backend Setup"
echo "=========================================================="
echo ""

# Variables
BUCKET_NAME="rwa-voting-system-terraform-state-$(date +%s)"
TABLE_NAME="rwa-voting-terraform-locks"
AWS_REGION="${AWS_REGION:-ap-south-1}"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}✗ AWS CLI is not installed${NC}"
    echo "Please install AWS CLI: https://aws.amazon.com/cli/"
    exit 1
fi

# Check AWS credentials
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}✗ AWS credentials not configured${NC}"
    echo "Please run: aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS Credentials OK (Account: $ACCOUNT_ID)${NC}"
echo ""

# Step 1: Create S3 bucket
echo "📦 Step 1: Creating S3 bucket for Terraform state..."
echo "Bucket Name: $BUCKET_NAME"
echo "Region: $AWS_REGION"
echo ""

# Check if bucket name is provided
read -p "Use random bucket name above? (y/n) [y]: " USE_RANDOM
USE_RANDOM=${USE_RANDOM:-y}

if [[ "$USE_RANDOM" != "y" && "$USE_RANDOM" != "Y" ]]; then
    read -p "Enter custom bucket name (must be globally unique): " CUSTOM_BUCKET
    BUCKET_NAME="$CUSTOM_BUCKET"
fi

# Create bucket
if aws s3 ls "s3://$BUCKET_NAME" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "Creating bucket: $BUCKET_NAME"
    if [ "$AWS_REGION" = "ap-south-1" ]; then
        aws s3 mb "s3://$BUCKET_NAME" --region "$AWS_REGION"
    else
        aws s3 mb "s3://$BUCKET_NAME" --region "$AWS_REGION" \
            --create-bucket-configuration LocationConstraint="$AWS_REGION"
    fi
    echo -e "${GREEN}✓ S3 bucket created${NC}"
else
    echo -e "${YELLOW}⚠ Bucket already exists: $BUCKET_NAME${NC}"
fi
echo ""

# Step 2: Enable versioning on S3 bucket
echo "🔄 Step 2: Enabling versioning on S3 bucket..."
aws s3api put-bucket-versioning \
    --bucket "$BUCKET_NAME" \
    --versioning-configuration Status=Enabled \
    --region "$AWS_REGION"
echo -e "${GREEN}✓ Versioning enabled${NC}"
echo ""

# Step 3: Enable encryption on S3 bucket
echo "🔐 Step 3: Enabling encryption on S3 bucket..."
aws s3api put-bucket-encryption \
    --bucket "$BUCKET_NAME" \
    --server-side-encryption-configuration '{
        "Rules": [
            {
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }
        ]
    }' \
    --region "$AWS_REGION"
echo -e "${GREEN}✓ Encryption enabled (AES256)${NC}"
echo ""

# Step 4: Block public access
echo "🔒 Step 4: Blocking public access to S3 bucket..."
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
    --region "$AWS_REGION"
echo -e "${GREEN}✓ Public access blocked${NC}"
echo ""

# Step 5: Create DynamoDB table for state locking
echo "🔗 Step 5: Creating DynamoDB table for state locking..."
echo "Table Name: $TABLE_NAME"
echo ""

# Check if table exists
TABLE_EXISTS=$(aws dynamodb describe-table \
    --table-name "$TABLE_NAME" \
    --region "$AWS_REGION" 2>&1 || true)

if [[ ! $TABLE_EXISTS =~ "TableStatus" ]]; then
    echo "Creating DynamoDB table: $TABLE_NAME"
    
    aws dynamodb create-table \
        --table-name "$TABLE_NAME" \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "$AWS_REGION"
    
    # Wait for table to be created
    echo "Waiting for table creation..."
    aws dynamodb wait table-exists \
        --table-name "$TABLE_NAME" \
        --region "$AWS_REGION"
    
    echo -e "${GREEN}✓ DynamoDB table created${NC}"
else
    echo -e "${YELLOW}⚠ DynamoDB table already exists${NC}"
fi
echo ""

# Step 6: Create terraform.tfvars if it doesn't exist
echo "⚙️  Step 6: Checking terraform.tfvars..."
if [ ! -f "terraform.tfvars" ]; then
    if [ -f "terraform.tfvars.example" ]; then
        cp terraform.tfvars.example terraform.tfvars
        echo -e "${GREEN}✓ Created terraform.tfvars from example${NC}"
        echo "⚠️  Please edit terraform.tfvars with your values"
    fi
else
    echo -e "${GREEN}✓ terraform.tfvars already exists${NC}"
fi
echo ""

# Summary
echo "=========================================================="
echo "✅ Backend Setup Complete!"
echo "=========================================================="
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Update backend.tf with your configured values:"
echo "   - bucket: $BUCKET_NAME"
echo "   - region: $AWS_REGION"
echo "   - dynamodb_table: $TABLE_NAME"
echo ""
echo "2. Update terraform/backend.tf:"
echo "   - Bucket name: $BUCKET_NAME"
echo "   - Region: $AWS_REGION"
echo "   - DynamoDB table: $TABLE_NAME"
echo ""
echo "3. Initialize Terraform:"
echo "   cd terraform"
echo "   terraform init"
echo ""
echo "4. Verify backend configuration:"
echo "   terraform backend show"
echo ""
echo "📋 Backend Details:"
echo "   S3 Bucket: $BUCKET_NAME"
echo "   Region: $AWS_REGION"
echo "   DynamoDB Table: $TABLE_NAME"
echo "   Encryption: Enabled (AES256)"
echo "   Versioning: Enabled"
echo "   Public Access: Blocked"
echo ""
echo "💡 Important Notes:"
echo "   - Keep the S3 bucket name safe - you'll need it for team collaboration"
echo "   - Don't commit backend.tf credentials in git"
echo "   - Add bucket name to terraform/backend.tf"
echo "   - DynamoDB prevents concurrent Terraform changes (state locking)"
echo ""
echo "🔗 More Info:"
echo "   https://www.terraform.io/language/settings/backends/s3"
echo ""
