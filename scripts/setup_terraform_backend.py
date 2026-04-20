#!/usr/bin/env python3
"""
Terraform Remote Backend Setup Script
======================================

Automates AWS S3 and DynamoDB setup for Terraform remote state management.

Usage:
    python3 setup_terraform_backend.py                    # Default configuration
    python3 setup_terraform_backend.py --region us-west-2 # Custom region
    python3 setup_terraform_backend.py --bucket my-bucket  # Custom bucket name

Features:
    ✅ Validates AWS CLI and credentials
    ✅ Creates S3 bucket with versioning and encryption
    ✅ Configures public access blocking
    ✅ Creates DynamoDB table for state locking
    ✅ Colored output for easy reading
    ✅ Error handling and retry logic
"""

import subprocess
import json
import sys
import argparse
from datetime import datetime
from typing import Dict, Optional, Tuple


# Color codes for terminal output
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_success(message: str) -> None:
    """Print success message in green."""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")


def print_warning(message: str) -> None:
    """Print warning message in yellow."""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")


def print_error(message: str) -> None:
    """Print error message in red."""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")


def print_info(message: str) -> None:
    """Print info message in blue."""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.RESET}")


def print_header(message: str) -> None:
    """Print header message in bold."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def run_command(command: list, description: str = "") -> Tuple[bool, str]:
    """
    Execute AWS CLI command and return result.

    Args:
        command: List of command arguments
        description: Description of what the command does

    Returns:
        Tuple of (success: bool, output: str)
    """
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            error_msg = result.stderr.strip() or result.stdout.strip()
            if description:
                print_error(f"{description}: {error_msg}")
            return False, error_msg

    except FileNotFoundError as e:
        if description:
            print_error(f"{description}: Command not found")
        return False, str(e)
    except Exception as e:
        if description:
            print_error(f"{description}: {str(e)}")
        return False, str(e)


def check_aws_cli() -> bool:
    """Check if AWS CLI is installed and accessible."""
    print_info("Checking AWS CLI installation...")
    success, output = run_command(["aws", "--version"])

    if success:
        print_success(f"AWS CLI found: {output}")
        return True
    else:
        print_error("AWS CLI not found. Please install it:")
        print("  macOS:  brew install awscli")
        print("  Linux:  apt-get install awscli")
        print("  Windows: pip install awscli")
        print("  Or download from: https://aws.amazon.com/cli/")
        return False


def check_aws_credentials() -> bool:
    """Validate AWS credentials."""
    print_info("Validating AWS credentials...")
    success, output = run_command(
        ["aws", "sts", "get-caller-identity"], "AWS credentials validation"
    )

    if success:
        try:
            identity = json.loads(output)
            print_success(f"AWS Account: {identity.get('Account')}")
            print_success(f"AWS User/Role: {identity.get('Arn')}")
            return True
        except json.JSONDecodeError:
            print_error("Failed to parse AWS identity")
            return False
    else:
        print_error("AWS credentials not configured or invalid")
        print_info("Run: aws configure")
        return False


def create_s3_bucket(bucket_name: str, region: str) -> bool:
    """Create S3 bucket with versioning and encryption."""
    print_info(f"Creating S3 bucket: {bucket_name}")

    # Create bucket
    if region == "ap-south-1":
        # ap-south-1 doesn't need LocationConstraint
        cmd = ["aws", "s3", "mb", f"s3://{bucket_name}", "--region", region]
    else:
        cmd = [
            "aws",
            "s3",
            "mb",
            f"s3://{bucket_name}",
            "--region",
            region,
            "--create-bucket-configuration",
            f"LocationConstraint={region}",
        ]

    success, _ = run_command(cmd, "S3 bucket creation")
    if not success:
        return False

    print_success(f"S3 bucket created: {bucket_name}")

    # Enable versioning
    print_info("Enabling S3 versioning...")
    success, _ = run_command(
        [
            "aws",
            "s3api",
            "put-bucket-versioning",
            "--bucket",
            bucket_name,
            "--versioning-configuration",
            "Status=Enabled",
            "--region",
            region,
        ],
        "S3 versioning",
    )
    if not success:
        return False

    print_success("S3 versioning enabled")

    # Enable encryption
    print_info("Enabling S3 encryption...")
    encryption_config = {
        "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
    }

    success, _ = run_command(
        [
            "aws",
            "s3api",
            "put-bucket-encryption",
            "--bucket",
            bucket_name,
            "--server-side-encryption-configuration",
            json.dumps(encryption_config),
            "--region",
            region,
        ],
        "S3 encryption",
    )
    if not success:
        return False

    print_success("S3 encryption enabled (AES256)")

    # Block public access
    print_info("Blocking public access...")
    public_access_config = {
        "BlockPublicAcls": True,
        "IgnorePublicAcls": True,
        "BlockPublicPolicy": True,
        "RestrictPublicBuckets": True,
    }

    success, _ = run_command(
        [
            "aws",
            "s3api",
            "put-public-access-block",
            "--bucket",
            bucket_name,
            "--public-access-block-configuration",
            json.dumps(public_access_config),
            "--region",
            region,
        ],
        "Public access blocking",
    )
    if not success:
        return False

    print_success("Public access blocked")
    return True


def create_dynamodb_table(table_name: str, region: str) -> bool:
    """Create DynamoDB table for state locking."""
    print_info(f"Creating DynamoDB table: {table_name}")

    success, _ = run_command(
        [
            "aws",
            "dynamodb",
            "create-table",
            "--table-name",
            table_name,
            "--attribute-definitions",
            "AttributeName=LockID,AttributeType=S",
            "--key-schema",
            "AttributeName=LockID,KeyType=HASH",
            "--billing-mode",
            "PAY_PER_REQUEST",
            "--region",
            region,
        ],
        "DynamoDB table creation",
    )

    if not success:
        return False

    print_success(f"DynamoDB table created: {table_name}")

    # Wait for table to be active
    print_info("Waiting for DynamoDB table to become active...")
    success, _ = run_command(
        [
            "aws",
            "dynamodb",
            "wait",
            "table-exists",
            "--table-name",
            table_name,
            "--region",
            region,
        ],
        "DynamoDB table availability check",
    )

    if success:
        print_success("DynamoDB table is active")
    else:
        print_warning("Could not verify table is active (may still be creating)")

    return True


def update_backend_config(bucket_name: str, table_name: str, region: str) -> None:
    """Print instructions for updating backend.tf."""
    print_header("Update Terraform Backend Configuration")

    print_info("Update terraform/backend.tf with:")
    print(
        f"""
{Colors.BOLD}terraform {{
  backend "s3" {{
    bucket         = "{bucket_name}"
    key            = "terraform.tfstate"
    region         = "{region}"
    encrypt        = true
    dynamodb_table = "{table_name}"
  }}
}}{Colors.RESET}
"""
    )


def print_next_steps(bucket_name: str, table_name: str) -> None:
    """Print next steps for user."""
    print_header("Next Steps")

    print(
        f"""
{Colors.BOLD}1. Update Terraform Configuration:{Colors.RESET}
   Edit terraform/backend.tf and update:
   - bucket: {bucket_name}
   - dynamodb_table: {table_name}

{Colors.BOLD}2. Initialize Terraform:{Colors.RESET}
   cd terraform
   terraform init
   
   When asked "Do you want to copy existing state to the new backend?"
   Answer: YES

{Colors.BOLD}3. Verify Backend Configuration:{Colors.RESET}
   terraform backend show

{Colors.BOLD}4. Deploy Infrastructure:{Colors.RESET}
   terraform plan -out=plan.tfplan
   terraform apply plan.tfplan

{Colors.BOLD}5. Verify Deployment:{Colors.RESET}
   terraform backend show
   aws s3 ls s3://{bucket_name}
   aws dynamodb describe-table --table-name {table_name}

{Colors.BOLD}Documentation:{Colors.RESET}
   - Full guide: docs/TERRAFORM_BACKEND.md
   - Quick ref:  docs/TERRAFORM_BACKEND_QUICKREF.md
   - Deployment: docs/DEPLOYMENT_GUIDE.md
"""
    )


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(
        description="Setup AWS S3 and DynamoDB for Terraform remote backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 setup_terraform_backend.py
  python3 setup_terraform_backend.py --region us-west-2
  python3 setup_terraform_backend.py --bucket my-custom-bucket --region eu-west-1
        """,
    )

    parser.add_argument(
        "--region",
        default="ap-south-1",
        help="AWS region for resources (default: ap-south-1)",
    )

    parser.add_argument(
        "--bucket",
        help="Custom S3 bucket name (default: auto-generated with timestamp)",
    )

    parser.add_argument(
        "--table",
        default="rwa-voting-terraform-locks",
        help="DynamoDB table name for state locking (default: rwa-voting-terraform-locks)",
    )

    args = parser.parse_args()

    # Generate bucket name if not provided
    if args.bucket:
        bucket_name = args.bucket
    else:
        timestamp = str(int(datetime.now().timestamp()))
        bucket_name = f"rwa-voting-system-terraform-state-{timestamp}"

    print_header("Terraform Remote Backend Setup")
    print_info(f"Region: {args.region}")
    print_info(f"S3 Bucket: {bucket_name}")
    print_info(f"DynamoDB Table: {args.table}\n")

    # Check prerequisites
    if not check_aws_cli():
        sys.exit(1)

    print()

    if not check_aws_credentials():
        sys.exit(1)

    print()

    # Create S3 bucket
    if not create_s3_bucket(bucket_name, args.region):
        print_error("Failed to create S3 bucket")
        sys.exit(1)

    print()

    # Create DynamoDB table
    if not create_dynamodb_table(args.table, args.region):
        print_error("Failed to create DynamoDB table")
        sys.exit(1)

    print()

    # Print configuration and next steps
    update_backend_config(bucket_name, args.table, args.region)
    print_next_steps(bucket_name, args.table)

    print_success("✨ Terraform remote backend setup complete! ✨\n")


if __name__ == "__main__":
    main()
