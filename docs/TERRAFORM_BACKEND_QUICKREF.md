# Terraform Remote Backend - Quick Reference

**Status**: Remote S3 backend configured (not yet initialized)  
**Region**: ap-south-1  
**Setup Time**: 5-10 minutes  

---

## 🚀 Quick Start (Copy & Paste)

### Step 1: Run Setup Script

#### **All Platforms (Windows, macOS, Linux)**
```bash
cd scripts
python3 setup_terraform_backend.py
```

#### **Custom Region**
```bash
cd scripts
python3 setup_terraform_backend.py --region us-west-2
```

#### **Custom Bucket Name**
```bash
cd scripts
python3 setup_terraform_backend.py --bucket my-custom-bucket
```

### Step 2: Initialize Terraform

```bash
cd terraform
terraform init
# When asked: "Do you want to copy existing state...?"
# Answer: YES
```

### Step 3: Verify

```bash
terraform backend show
# Should show S3 bucket and DynamoDB table
```

---

## 📋 What Gets Created

| Resource | Name | Purpose |
|----------|------|---------|
| **S3 Bucket** | `rwa-voting-system-terraform-state-*` | Stores state files |
| **DynamoDB Table** | `rwa-voting-terraform-locks` | Prevents concurrent changes |

---

## 🔧 Core Configuration

**File**: `terraform/backend.tf`

```hcl
terraform {
  backend "s3" {
    bucket         = "rwa-voting-system-terraform-state-1234567890"
    key            = "terraform.tfstate"
    region         = "ap-south-1"
    encrypt        = true                        # AES256 encryption
    dynamodb_table = "rwa-voting-terraform-locks" # State locking
  }
}
```

---

## 👥 Team Workflow

```bash
# Developer A
terraform plan && terraform apply
# Locks state, uploads changes

# Developer B (automatic wait)
terraform plan && terraform apply
# Waits for lock, then proceeds

# Both have same state ✅
```

---

## 🔐 Security Features

✅ **Encryption At Rest** - AES256  
✅ **Encryption In Transit** - HTTPS  
✅ **State Locking** - Prevents conflicts  
✅ **Public Access** - Blocked  
✅ **Versioning** - Full history  

---

## ⚠️ Common Issues

### "Error acquiring the state lock"

```bash
# Check locks
aws dynamodb scan --table-name rwa-voting-terraform-locks

# Force unlock (emergency only)
terraform force-unlock LOCK_ID
```

### "AccessDenied" error

```bash
# Verify credentials
aws sts get-caller-identity

# Check bucket access
aws s3 ls s3://YOUR_BUCKET_NAME
```

### "Backend initialization required"

```bash
# Reset and reinit
cd terraform
rm -rf .terraform/
terraform init
```

---

## 📊 Normal Operations

```bash
cd terraform

# Plan changes
terraform plan -out=plan.tfplan

# Review output, then apply
terraform apply plan.tfplan

# Destroy infrastructure
terraform destroy
```

---

## 🔄 State Management

### **Backup State**
```bash
# Automatic: S3 versioning maintains history
# Manual: Download from S3 console
```

### **Restore State**
```bash
# List versions
aws s3api list-object-versions --bucket YOUR_BUCKET_NAME --prefix terraform.tfstate

# Restore from version
aws s3api get-object --bucket YOUR_BUCKET_NAME --key terraform.tfstate --version-id VERSION_ID terraform.tfstate.restore
```

### **Update State**
```bash
# Don't edit directly!
# Use terraform commands instead:
terraform import RESOURCE_TYPE.NAME RESOURCE_ID
terraform state list
terraform state show RESOURCE_NAME
```

---

## 💰 Cost Estimate

| Item | Cost/Month |
|------|-----------|
| S3 Storage (state) | ~$0.02 |
| S3 Versioning | ~$0.10 |
| DynamoDB (on-demand) | ~$0.00 |
| **Total** | **~$0.12** |

Very inexpensive for team collaboration!

---

## 📌 Important Notes

⚠️ **DO NOT commit state files to git**
```bash
# .gitignore already includes:
terraform/.terraform/
terraform/terraform.tfstate*
.terraform.lock.hcl
```

⚠️ **DO NOT delete S3 bucket** (contains your infrastructure state)

⚠️ **DO NOT manually edit state files** (use terraform commands)

✅ **DO commit backend.tf** (safe, no credentials)

✅ **DO share bucket name with team** (needed for terraform init)

---

## 🎯 Next Steps

1. ✅ Run setup script
2. ✅ Run `terraform init`
3. ✅ Verify with `terraform backend show`
4. ✅ Run `terraform plan`
5. ✅ Run `terraform apply`
6. ✅ Share bucket name with team

---

## 📚 Full Documentation

See [TERRAFORM_BACKEND.md](./TERRAFORM_BACKEND.md) for:
- Detailed setup instructions
- Manual configuration (AWS CLI commands)
- State versioning and recovery
- Security best practices
- Troubleshooting guide
- Cost analysis

---

**Status**: Ready to use  
**Last Updated**: April 2026  
**Questions?** See TERRAFORM_BACKEND.md or run `terraform -help`
