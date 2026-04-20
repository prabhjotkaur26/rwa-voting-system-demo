# Terraform Remote Backend Configuration

**Last Updated**: April 2026  
**Status**: ✅ Recommended for production environments

---

## Overview

This project is configured to use **AWS S3 + DynamoDB** as a remote backend for Terraform state management. This enables:

- ✅ **Team Collaboration** - Multiple team members can work on the same infrastructure
- ✅ **State Locking** - Prevents concurrent modifications (DynamoDB)
- ✅ **Disaster Recovery** - State versioning and backup in S3
- ✅ **Encryption** - All state data encrypted at rest
- ✅ **Auditability** - Clear state history and changes

---

## Current Configuration

### Default Backend Setup

```hcl
# terraform/backend.tf
terraform {
  backend "s3" {
    bucket         = "rwa-voting-system-terraform-state"
    key            = "terraform.tfstate"
    region         = "ap-south-1"
    encrypt        = true
    dynamodb_table = "rwa-voting-terraform-locks"
  }
}
```

### Components

| Component | Purpose | Details |
|-----------|---------|---------|
| **S3 Bucket** | State Storage | Stores `terraform.tfstate` with full version history |
| **Versioning** | Recovery | Allows rollback to previous states |
| **Encryption** | Security | AES256 encryption at rest |
| **DynamoDB Table** | State Locking | Prevents concurrent `terraform apply` operations |
| **Public Access Block** | Security | Prevents accidental public exposure |

---

## Quick Setup (First Time)

### Option A: Using Automated Script (Recommended)

#### All Platforms (Windows, macOS, Linux):

```bash
cd scripts
python3 setup_terraform_backend.py
```

**With custom region**:
```bash
python3 setup_terraform_backend.py --region us-west-2
```

**With custom bucket name**:
```bash
python3 setup_terraform_backend.py --bucket my-custom-bucket-name
```

**What the script does**:
1. ✅ Validates AWS CLI and credentials
2. ✅ Creates S3 bucket for state storage
3. ✅ Enables versioning on S3 bucket
4. ✅ Enables AES256 encryption
5. ✅ Blocks all public access
6. ✅ Creates DynamoDB table for state locking
7. ✅ Configures all security settings

**Exit after 5-10 minutes with bucket and table names**

---

### Option B: Manual Setup

If you prefer to set up manually, follow these steps:

#### Step 1: Create S3 Bucket

```bash
# Create bucket
aws s3 mb s3://rwa-voting-system-terraform-state-$(date +%s) \
  --region ap-south-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket rwa-voting-system-terraform-state-$(date +%s) \
  --versioning-configuration Status=Enabled
```

#### Step 2: Enable Encryption

```bash
aws s3api put-bucket-encryption \
  --bucket YOUR_BUCKET_NAME \
  --server-side-encryption-configuration '{
    "Rules": [
      {
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "AES256"
        }
      }
    ]
  }'
```

#### Step 3: Block Public Access

```bash
aws s3api put-public-access-block \
  --bucket YOUR_BUCKET_NAME \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

#### Step 4: Create DynamoDB Table

```bash
aws dynamodb create-table \
  --table-name rwa-voting-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

#### Step 5: Update backend.tf

Edit `terraform/backend.tf` and add your bucket name:

```hcl
terraform {
  backend "s3" {
    bucket         = "YOUR_BUCKET_NAME"        # ← Update this
    key            = "terraform.tfstate"
    region         = "ap-south-1"
    encrypt        = true
    dynamodb_table = "rwa-voting-terraform-locks"
  }
}
```

---

## Initialize Terraform with Remote Backend

```bash
cd terraform

# Initialize Terraform (will configure remote backend)
terraform init

# Verify backend configuration
terraform backend show

# Expected output shows S3 backend configured with state locking
```

---

## Using the Remote Backend

### Normal Workflow

```bash
cd terraform

# Plan (downloads state from S3)
terraform plan -out=plan.tfplan

# Apply (uploads new state to S3 after changes)
terraform apply plan.tfplan

# Destroy (updates state in S3)
terraform destroy
```

### Team Collaboration

**Multiple developers working on same infrastructure**:

```bash
# Developer 1
cd terraform
terraform plan -out=dev1.plan

# Developer 2
cd terraform
terraform plan -out=dev2.plan
# Gets automatic lock from DynamoDB
# Must wait for Developer 1 to finish

# Developer 1 applies
terraform apply dev1.plan
# Lock released, state updated in S3

# Developer 2 now applies
terraform apply dev2.plan
```

---

## State Locking

### How It Works

DynamoDB prevents concurrent modifications:

```
Developer A: terraform apply
├─ Acquires lock on LockID in DynamoDB
├─ Applies changes to AWS resources
├─ Updates state in S3
└─ Releases lock

Developer B: terraform apply (waits for lock)
└─ Acquires lock automatically when A releases
```

### View Locks

```bash
# List all locks
aws dynamodb scan \
  --table-name rwa-voting-terraform-locks \
  --region ap-south-1

# Delete stuck lock (emergency only!)
aws dynamodb delete-item \
  --table-name rwa-voting-terraform-locks \
  --key '{"LockID":{"S":"LOCK_ID_HERE"}}' \
  --region ap-south-1
```

---

## State Versioning & Recovery

### View State History

```bash
# List all state versions
aws s3api list-object-versions \
  --bucket YOUR_BUCKET_NAME \
  --prefix terraform.tfstate

# Download specific version
aws s3api get-object \
  --bucket YOUR_BUCKET_NAME \
  --key terraform.tfstate \
  --version-id VERSION_ID_HERE \
  terraform.tfstate.backup
```

### Rollback to Previous State

```bash
# 1. Download previous state version
aws s3api get-object \
  --bucket YOUR_BUCKET_NAME \
  --key terraform.tfstate \
  --version-id PREVIOUS_VERSION_ID \
  terraform.tfstate

# 2. Force unlock if needed
terraform force-unlock LOCK_ID

# 3. Verify changes
terraform plan

# 4. It will show what to rollback
```

---

## Migrating from Local to Remote State

If you already have local state and want to migrate:

```bash
cd terraform

# 1. Backup local state
cp terraform.tfstate terraform.tfstate.backup

# 2. Create backend.tf with remote configuration
# (Already done in this project)

# 3. Initialize Terraform (will offer to copy state)
terraform init

# When prompted: "Do you want to copy existing state to the new backend?"
# Answer: yes

# 4. Verify migration
terraform backend show

# 5. Remove local state (if migration successful)
rm -rf .terraform/
rm terraform.tfstate*
```

---

## Security Best Practices

### ✅ What We Do

- ✅ **Encryption at Rest**: AES256 on S3
- ✅ **Encryption in Transit**: HTTPS only
- ✅ **Access Control**: IAM policies limit access
- ✅ **Public Blocks**: All public access disabled
- ✅ **Versioning**: Full history maintained
- ✅ **Locking**: Concurrent changes prevented

### ⚠️ Additional Recommendations

1. **Restrict S3 Bucket Access**:

```bash
# Only allow specific AWS accounts
aws s3api put-bucket-policy \
  --bucket YOUR_BUCKET_NAME \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Principal": {
          "AWS": "arn:aws:iam::ACCOUNT_ID:root"
        },
        "Effect": "Allow",
        "Action": "s3:*",
        "Resource": [
          "arn:aws:s3:::YOUR_BUCKET_NAME",
          "arn:aws:s3:::YOUR_BUCKET_NAME/*"
        ]
      }
    ]
  }'
```

2. **Use IAM Roles** (not root credentials):

```bash
# Create IAM policy for Terraform
aws iam create-policy \
  --policy-name TerraformBackendPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "s3:ListBucket",
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ],
        "Resource": [
          "arn:aws:s3:::YOUR_BUCKET_NAME",
          "arn:aws:s3:::YOUR_BUCKET_NAME/*"
        ]
      },
      {
        "Effect": "Allow",
        "Action": [
          "dynamodb:DescribeTable",
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem"
        ],
        "Resource": "arn:aws:dynamodb:*:*:table/rwa-voting-terraform-locks"
      }
    ]
  }'
```

3. **Enable MFA Delete** (optional, maximum security):

```bash
# Requires MFA to delete state versions
aws s3api put-bucket-versioning \
  --bucket YOUR_BUCKET_NAME \
  --versioning-configuration Status=Enabled,MFADelete=Enabled \
  --mfa "SERIAL_NUMBER TOKEN"
```

---

## Troubleshooting

### Issue: "Error acquiring the state lock"

**Cause**: Another operation is using the state  
**Solution**:

```bash
# Check if lock exists
aws dynamodb scan --table-name rwa-voting-terraform-locks

# Force unlock (use with caution!)
terraform force-unlock LOCK_ID
```

### Issue: "Error refreshing state: AccessDenied"

**Cause**: IAM permissions missing  
**Solution**:

```bash
# Verify bucket access
aws s3 ls s3://YOUR_BUCKET_NAME

# Check IAM permissions
aws iam get-user
aws iam list-attached-user-policies --user-name YOUR_USERNAME
```

### Issue: "Backend initialization required"

**Cause**: backend.tf exists but not initialized  
**Solution**:

```bash
cd terraform
rm -rf .terraform/
terraform init
```

### Issue: State file corruption

**Cause**: Unexpected interruption during apply  
**Solution**:

```bash
# 1. List versions
aws s3api list-object-versions \
  --bucket YOUR_BUCKET_NAME \
  --prefix terraform.tfstate

# 2. Restore from backup
aws s3api get-object \
  --bucket YOUR_BUCKET_NAME \
  --key terraform.tfstate \
  --version-id VERSION_ID \
  terraform.tfstate

# 3. Re-initialize
terraform init
```

---

## Cost Impact

### Estimated Monthly Cost

| Service | Usage | Cost |
|---------|-------|------|
| **S3** | 100 MB state file | ~$0.02 |
| **S3 Versioning** | 10 versions × 100 MB | ~$0.10 |
| **DynamoDB** | On-demand (locking) | ~$0.00-0.10 |
| **Total** | - | **~$0.12-0.25/month** |

Very cost-efficient for team collaboration!

---

## Migration Checklist

- [ ] Run setup script (automated or manual)
- [ ] Verify S3 bucket created
- [ ] Verify DynamoDB table created
- [ ] Update backend.tf with bucket name
- [ ] Run `terraform init`
- [ ] Verify `terraform backend show`
- [ ] Delete local state (if migrating)
- [ ] Test `terraform plan` works
- [ ] Commit backend configuration (without credentials)
- [ ] Share bucket name with team

---

## Next Steps

1. **Setup Backend**: Run the setup script
2. **Configure Terraform**: Update backend.tf
3. **Initialize**: Run `terraform init`
4. **Deploy**: Run `terraform apply`
5. **Share**: Send bucket name to team members

---

## References

- [Terraform S3 Backend Documentation](https://www.terraform.io/language/settings/backends/s3)
- [AWS S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)
- [Terraform State Locking](https://www.terraform.io/language/state/locking)

---

## FAQ

**Q: Can I use different region?**  
A: Yes, update `region` in backend.tf and `$AwsRegion` in scripts

**Q: What if bucket name is taken?**  
A: S3 bucket names must be globally unique - timestamp ensures uniqueness

**Q: Can I migrate from local to remote state?**  
A: Yes, `terraform init` will offer to copy existing state

**Q: What if state gets corrupted?**  
A: Versioning allows rollback to any previous state version

**Q: How do I backup the state?**  
A: S3 versioning maintains full history - download any version as backup

**Q: Can I switch backends later?**  
A: Yes, `terraform init` with new backend.tf configuration

---

**Created**: April 2026  
**Updated**: April 2026  
**Maintained By**: RWA Voting System Team
