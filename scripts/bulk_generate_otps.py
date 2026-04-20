#!/usr/bin/env python3
"""
Bulk OTP Generation Script for Election
Generates OTPs for all voters in an election with TTL set to election end time
"""

import sys
import os
import json
import random
import string
import argparse
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

# Add lambda lib to path for shared utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../lambda/lib"))

import boto3
from botocore.exceptions import ClientError


def generate_otp(length: int = 6) -> str:
    """Generate a random OTP"""
    return "".join(random.choices(string.digits, k=length))


def get_ist_timestamp():
    """Get current timestamp in IST timezone"""
    ist = timezone(timedelta(hours=5, minutes=30))
    return int(datetime.now(ist).timestamp())


class OTPGenerator:
    def __init__(self, aws_region: str = "ap-south-1"):
        """Initialize DynamoDB client and table names"""
        self.dynamodb = boto3.resource("dynamodb", region_name=aws_region)
        self.elections_table_name = "rwa-voting-elections-prod"
        self.voters_table_name = "rwa-voting-voters-prod"
        self.otp_table_name = "rwa-voting-otp-prod"

        # Initialize tables
        self.elections_table = self.dynamodb.Table(self.elections_table_name)
        self.voters_table = self.dynamodb.Table(self.voters_table_name)
        self.otp_table = self.dynamodb.Table(self.otp_table_name)

    def get_election(self, election_id: str) -> Dict[str, Any]:
        """Get election details by election ID"""
        try:
            response = self.elections_table.get_item(Key={"electionId": election_id})
            if "Item" not in response:
                raise ValueError(f"Election '{election_id}' not found")
            return response["Item"]
        except ClientError as e:
            raise Exception(f"Error fetching election: {str(e)}")

    def get_all_voters(self) -> List[Dict[str, Any]]:
        """Get all voters from voters table"""
        try:
            voters = []
            response = self.voters_table.scan()
            voters.extend(response.get("Items", []))

            # Handle pagination
            while "LastEvaluatedKey" in response:
                response = self.voters_table.scan(
                    ExclusiveStartKey=response["LastEvaluatedKey"]
                )
                voters.extend(response.get("Items", []))

            return voters
        except ClientError as e:
            raise Exception(f"Error fetching voters: {str(e)}")

    def generate_otps_for_election(
        self, election_id: str, dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Generate OTPs for all voters in an election

        Args:
            election_id: Election ID to generate OTPs for
            dry_run: If True, don't actually store OTPs, just show what would be done

        Returns:
            Dictionary with generation statistics
        """
        print(f"\n{'='*80}")
        print(f"Bulk OTP Generation for Election: {election_id}")
        print(f"{'='*80}\n")

        # Get election details
        print(f"[*] Fetching election details...")
        election = self.get_election(election_id)

        election_name = election.get("electionName", "Unknown")
        start_time = int(election.get("startTime", 0))
        end_time = int(election.get("endTime", 0))
        current_time_ist = get_ist_timestamp()

        # Display election info
        start_dt = datetime.fromtimestamp(start_time, tz=timezone.utc)
        end_dt = datetime.fromtimestamp(end_time, tz=timezone.utc)
        current_dt = datetime.fromtimestamp(current_time_ist, tz=timezone.utc)

        print(f"Election Name: {election_name}")
        print(f"Election ID: {election_id}")
        print(f"Start Time: {start_dt.strftime('%Y-%m-%d %H:%M:%S UTC')} (IST)")
        print(f"End Time:   {end_dt.strftime('%Y-%m-%d %H:%M:%S UTC')} (IST)")
        print(f"Current Time: {current_dt.strftime('%Y-%m-%d %H:%M:%S UTC')} (IST)")

        # Warn if election has ended
        if current_time_ist > end_time:
            print(f"\n⚠️  WARNING: Election has already ended!")
        elif current_time_ist < start_time:
            print(f"\n⚠️  WARNING: Election has not started yet!")

        # Get all voters
        print(f"\n[*] Fetching voters...")
        voters = self.get_all_voters()
        total_voters = len(voters)

        if total_voters == 0:
            print("❌ No voters found in the system")
            return {
                "success": False,
                "election_id": election_id,
                "total_voters": 0,
                "otps_generated": 0,
                "otps_failed": 0,
                "message": "No voters found",
            }

        print(f"Found {total_voters} voters\n")

        # Generate OTPs for each voter
        success_count = 0
        failed_count = 0
        otp_records = []
        failed_voters = []

        print(f"[*] Generating OTPs for each voter...")
        print(f"{'Mobile Number':<15} {'OTP':<8} {'Status':<10}")
        print(f"{'-'*35}")

        for voter in voters:
            try:
                mobile_number = voter.get("mobileNumber", "").strip()

                if not mobile_number:
                    failed_count += 1
                    failed_voters.append({"reason": "No mobile number", "voter": voter})
                    print(f"{mobile_number:<15} {'':<8} {'FAILED':<10}")
                    continue

                # Generate OTP
                otp = generate_otp()

                # Create OTP record with TTL set to election end time
                otp_item = {
                    "mobileNumber": mobile_number,
                    "otp": otp,
                    "createdAt": get_ist_timestamp(),
                    "ttl": end_time,  # TTL set to election end time
                    "attempts": 0,
                }

                otp_records.append(otp_item)
                success_count += 1
                print(f"{mobile_number:<15} {otp:<8} {'SUCCESS':<10}")

            except Exception as e:
                failed_count += 1
                failed_voters.append({"mobile": mobile_number, "error": str(e)})
                print(f"{mobile_number:<15} {'':<8} {'FAILED':<10}")

        # Store OTPs in DynamoDB
        print(f"\n[*] Storing OTPs in DynamoDB...")

        if not dry_run and success_count > 0:
            batch_written = 0
            batch_failed = 0

            with self.otp_table.batch_writer(
                overwrite_by_pkeys=["mobileNumber"]
            ) as batch:
                for otp_item in otp_records:
                    try:
                        batch.put_item(Item=otp_item)
                        batch_written += 1
                    except ClientError as e:
                        batch_failed += 1
                        print(
                            f"  ❌ Failed to write OTP for {otp_item['mobileNumber']}: {str(e)}"
                        )

            print(f"✅ Stored {batch_written} OTPs in rwa-voting-otp-prod")
            if batch_failed > 0:
                print(f"❌ Failed to store {batch_failed} OTPs")
        elif dry_run and success_count > 0:
            print(f"[DRY RUN] Would store {success_count} OTPs in rwa-voting-otp-prod")
        else:
            print("No OTPs to store")

        # Summary
        print(f"\n{'='*80}")
        print(f"OTP Generation Summary")
        print(f"{'='*80}")
        print(f"Total Voters:        {total_voters}")
        print(f"OTPs Generated:      {success_count}")
        print(f"Generation Failed:   {failed_count}")
        print(f"TTL Set To:          {end_dt.strftime('%Y-%m-%d %H:%M:%S UTC')} (IST)")
        print(f"Dry Run:             {'Yes' if dry_run else 'No'}")
        print(f"{'='*80}\n")

        # Show failed voters if any
        if failed_voters:
            print(f"Failed Voters ({len(failed_voters)}):")
            for failed in failed_voters[:10]:  # Show first 10 failures
                print(f"  - {failed}")
            if len(failed_voters) > 10:
                print(f"  ... and {len(failed_voters) - 10} more")

        return {
            "success": success_count > 0,
            "election_id": election_id,
            "election_name": election_name,
            "total_voters": total_voters,
            "otps_generated": success_count,
            "otps_failed": failed_count,
            "ttl_timestamp": end_time,
            "ttl_datetime": end_dt.isoformat(),
            "dry_run": dry_run,
            "failed_voters": failed_voters,
        }


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Bulk generate OTPs for all voters in an election"
    )
    parser.add_argument(
        "election_id",
        help="Election ID to generate OTPs for",
    )
    parser.add_argument(
        "--region",
        default="ap-south-1",
        help="AWS region (default: ap-south-1)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate without storing OTPs",
    )

    args = parser.parse_args()

    try:
        generator = OTPGenerator(aws_region=args.region)
        result = generator.generate_otps_for_election(
            election_id=args.election_id,
            dry_run=args.dry_run,
        )

        # Exit with appropriate code
        sys.exit(0 if result["success"] else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
