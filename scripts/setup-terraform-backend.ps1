# Terraform Remote Backend Setup Script (PowerShell)
# This script creates the necessary AWS resources for remote Terraform state management
# Run this BEFORE running terraform init, plan, or apply

param(
    [string]$CustomBucketName = "",
    [string]$AwsRegion = "ap-south-1"
)

$ErrorActionPreference = "Stop"

Write-Host "🔧 RWA Voting System - Terraform Remote Backend Setup" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# Generate bucket name with timestamp
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$bucketName = "rwa-voting-system-terraform-state-$timestamp"
$tableName = "rwa-voting-terraform-locks"

# Override with custom bucket name if provided
if ($CustomBucketName) {
    $bucketName = $CustomBucketName
}

# Check if AWS CLI is installed
Write-Host "Checking AWS CLI installation..."
try {
    $null = aws --version
    Write-Host "✓ AWS CLI is installed" -ForegroundColor Green
} catch {
    Write-Host "✗ AWS CLI is not installed" -ForegroundColor Red
    Write-Host "Please install AWS CLI: https://aws.amazon.com/cli/"
    exit 1
}

# Check AWS credentials
Write-Host "Checking AWS credentials..."
try {
    $accountId = aws sts get-caller-identity --query Account --output text
    Write-Host "✓ AWS Credentials OK (Account: $accountId)" -ForegroundColor Green
} catch {
    Write-Host "✗ AWS credentials not configured" -ForegroundColor Red
    Write-Host "Please run: aws configure"
    exit 1
}

Write-Host ""
Write-Host "📦 Step 1: Creating S3 bucket for Terraform state..." -ForegroundColor Yellow
Write-Host "Bucket Name: $bucketName"
Write-Host "Region: $AwsRegion"
Write-Host ""

# Check if bucket already exists
try {
    $null = aws s3 ls "s3://$bucketName" --region $AwsRegion 2>&1
    Write-Host "⚠ Bucket already exists: $bucketName" -ForegroundColor Yellow
} catch {
    Write-Host "Creating bucket: $bucketName"
    if ($AwsRegion -eq "ap-south-1") {
        aws s3 mb "s3://$bucketName" --region $AwsRegion
    } else {
        aws s3 mb "s3://$bucketName" --region $AwsRegion `
            --create-bucket-configuration LocationConstraint=$AwsRegion
    }
    Write-Host "✓ S3 bucket created" -ForegroundColor Green
}

Write-Host ""
Write-Host "🔄 Step 2: Enabling versioning on S3 bucket..." -ForegroundColor Yellow
aws s3api put-bucket-versioning `
    --bucket $bucketName `
    --versioning-configuration Status=Enabled `
    --region $AwsRegion
Write-Host "✓ Versioning enabled" -ForegroundColor Green

Write-Host ""
Write-Host "🔐 Step 3: Enabling encryption on S3 bucket..." -ForegroundColor Yellow
$encryptionConfig = @{
    Rules = @(
        @{
            ApplyServerSideEncryptionByDefault = @{
                SSEAlgorithm = "AES256"
            }
        }
    )
} | ConvertTo-Json

aws s3api put-bucket-encryption `
    --bucket $bucketName `
    --server-side-encryption-configuration $encryptionConfig `
    --region $AwsRegion
Write-Host "✓ Encryption enabled (AES256)" -ForegroundColor Green

Write-Host ""
Write-Host "🔒 Step 4: Blocking public access to S3 bucket..." -ForegroundColor Yellow
aws s3api put-public-access-block `
    --bucket $bucketName `
    --public-access-block-configuration `
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" `
    --region $AwsRegion
Write-Host "✓ Public access blocked" -ForegroundColor Green

Write-Host ""
Write-Host "🔗 Step 5: Creating DynamoDB table for state locking..." -ForegroundColor Yellow
Write-Host "Table Name: $tableName"
Write-Host ""

# Check if table exists
try {
    $null = aws dynamodb describe-table `
        --table-name $tableName `
        --region $AwsRegion 2>&1
    Write-Host "⚠ DynamoDB table already exists" -ForegroundColor Yellow
} catch {
    Write-Host "Creating DynamoDB table: $tableName"
    
    $attributeDefinitions = @'
[
    {
        "AttributeName": "LockID",
        "AttributeType": "S"
    }
]
'@

    $keySchema = @'
[
    {
        "AttributeName": "LockID",
        "KeyType": "HASH"
    }
]
'@

    aws dynamodb create-table `
        --table-name $tableName `
        --attribute-definitions $attributeDefinitions `
        --key-schema $keySchema `
        --billing-mode PAY_PER_REQUEST `
        --region $AwsRegion
    
    Write-Host "Waiting for table creation..."
    aws dynamodb wait table-exists `
        --table-name $tableName `
        --region $AwsRegion
    
    Write-Host "✓ DynamoDB table created" -ForegroundColor Green
}

Write-Host ""
Write-Host "=========================================================="
Write-Host "✅ Backend Setup Complete!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""

Write-Host "📝 Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Update terraform/backend.tf with the following values:"
Write-Host "   - bucket = '$bucketName'"
Write-Host "   - region = '$AwsRegion'"
Write-Host "   - dynamodb_table = '$tableName'"
Write-Host ""
Write-Host "2. Initialize Terraform:"
Write-Host "   cd terraform"
Write-Host "   terraform init"
Write-Host ""
Write-Host "3. Verify backend configuration:"
Write-Host "   terraform backend show"
Write-Host ""
Write-Host "📋 Backend Details:" -ForegroundColor Cyan
Write-Host "   S3 Bucket: $bucketName"
Write-Host "   Region: $AwsRegion"
Write-Host "   DynamoDB Table: $tableName"
Write-Host "   Encryption: Enabled (AES256)"
Write-Host "   Versioning: Enabled"
Write-Host "   Public Access: Blocked"
Write-Host ""
Write-Host "💡 Important Notes:" -ForegroundColor Yellow
Write-Host "   - Keep the S3 bucket name safe - you'll need it for team collaboration"
Write-Host "   - Don't commit backend.tf credentials in git"
Write-Host "   - Add bucket name to terraform/backend.tf"
Write-Host "   - DynamoDB prevents concurrent Terraform changes (state locking)"
Write-Host ""
Write-Host "🔗 More Info:" -ForegroundColor Cyan
Write-Host "   https://www.terraform.io/language/settings/backends/s3"
Write-Host ""
