#!/usr/bin/env python3
"""
Bulk Voter Import Script for RWA Voting System
Imports voter data from CSV file into DynamoDB voters table

Usage:
    python ./scripts/bulk_import_voters.py ./samples/voters_import.csv rwa-voting-voters-prod --region ap-south-1

CSV Format:
    flatNumber,name,mobileNumber,email,area
    A-101,John Doe,9876543210,john@example.com,Tower A
    A-102,Jane Smith,9876543211,jane@example.com,Tower A
"""

import csv
import boto3
import sys
import argparse
import time
from datetime import datetime
from typing import List, Dict, Any


class VoterImporter:
    def __init__(self, table_name: str, region: str = "ap-south-1"):
        """Initialize DynamoDB client and table"""
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table = self.dynamodb.Table(table_name)
        self.table_name = table_name
        self.region = region

    def validate_mobile(self, mobile: str) -> bool:
        """Validate Indian mobile number format"""
        mobile = mobile.strip()

        # Check format: 10 digits, +91 + 10 digits, 0 + 10 digits, or 91 + 10 digits
        if mobile.isdigit() and len(mobile) == 10:
            return True
        if mobile.startswith("+91") and len(mobile) == 13:
            return True
        if mobile.startswith("0") and len(mobile) == 11 and mobile[1:].isdigit():
            return True
        if mobile.startswith("91") and len(mobile) == 12 and mobile[2:].isdigit():
            return True

        return False

    def normalize_mobile(self, mobile: str) -> str:
        """Normalize mobile to 10 digits"""
        mobile = mobile.strip()

        if mobile.startswith("+91"):
            return mobile[3:]
        elif mobile.startswith("91"):
            return mobile[2:]
        elif mobile.startswith("0"):
            return mobile[1:]

        return mobile

    def import_from_csv(self, csv_file: str) -> Dict[str, Any]:
        """Import voter data from CSV file"""
        results = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "errors": [],
            "warnings": [],
        }

        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                if not reader.fieldnames:
                    results["errors"].append("CSV file is empty")
                    return results

                required_fields = {"flatNumber", "name", "mobileNumber"}
                if not required_fields.issubset(set(reader.fieldnames or [])):
                    results["errors"].append(
                        f"CSV must contain columns: {', '.join(required_fields)}"
                    )
                    return results

                for row_idx, row in enumerate(
                    reader, start=2
                ):  # Start at 2 (skip header)
                    try:
                        # Extract fields
                        flat_number = row.get("flatNumber", "").strip()
                        name = row.get("name", "").strip()
                        mobile_number = row.get("mobileNumber", "").strip()
                        email = row.get("email", "").strip() if "email" in row else ""
                        area = row.get("area", "").strip() if "area" in row else ""

                        results["total"] += 1

                        # Validate required fields
                        if not flat_number:
                            results["failed"] += 1
                            results["errors"].append(
                                f"Row {row_idx}: Flat number missing"
                            )
                            continue

                        if not name:
                            results["failed"] += 1
                            results["errors"].append(f"Row {row_idx}: Name missing")
                            continue

                        if not mobile_number:
                            results["failed"] += 1
                            results["errors"].append(
                                f"Row {row_idx}: Mobile number missing"
                            )
                            continue

                        # Validate mobile format
                        if not self.validate_mobile(mobile_number):
                            results["failed"] += 1
                            results["errors"].append(
                                f"Row {row_idx}: Invalid mobile format: {mobile_number}"
                            )
                            continue

                        # Normalize mobile
                        normalized_mobile = self.normalize_mobile(mobile_number)

                        # Create voter item
                        voter_item = {
                            "mobileNumber": normalized_mobile,
                            "flatNumber": flat_number,
                            "name": name,
                            "uploadedAt": int(time.time()),
                        }

                        # Add optional fields
                        if email:
                            voter_item["email"] = email
                        if area:
                            voter_item["area"] = area

                        # Store in DynamoDB
                        self.table.put_item(Item=voter_item)
                        results["success"] += 1

                        # Print progress every 10 rows
                        if results["success"] % 10 == 0:
                            print(f"✓ Imported {results['success']} voters...")

                    except Exception as row_error:
                        results["failed"] += 1
                        results["errors"].append(f"Row {row_idx}: {str(row_error)}")

        except FileNotFoundError:
            results["errors"].append(f"CSV file not found: {csv_file}")
        except Exception as file_error:
            results["errors"].append(f"Error reading CSV: {str(file_error)}")

        return results

    def import_from_list(self, voters: List[Dict[str, str]]) -> Dict[str, Any]:
        """Import voter data from list of dictionaries"""
        results = {
            "total": len(voters),
            "success": 0,
            "failed": 0,
            "errors": [],
        }

        for idx, voter in enumerate(voters):
            try:
                # Extract fields
                flat_number = voter.get("flatNumber", "").strip()
                name = voter.get("name", "").strip()
                mobile_number = voter.get("mobileNumber", "").strip()
                email = voter.get("email", "").strip() if "email" in voter else ""
                area = voter.get("area", "").strip() if "area" in voter else ""

                # Validate required fields
                if not flat_number or not name or not mobile_number:
                    results["failed"] += 1
                    results["errors"].append(f"Entry {idx}: Missing required fields")
                    continue

                # Validate mobile format
                if not self.validate_mobile(mobile_number):
                    results["failed"] += 1
                    results["errors"].append(
                        f"Entry {idx}: Invalid mobile format: {mobile_number}"
                    )
                    continue

                # Normalize mobile
                normalized_mobile = self.normalize_mobile(mobile_number)

                # Create voter item
                voter_item = {
                    "mobileNumber": normalized_mobile,
                    "flatNumber": flat_number,
                    "name": name,
                    "uploadedAt": int(time.time()),
                }

                # Add optional fields
                if email:
                    voter_item["email"] = email
                if area:
                    voter_item["area"] = area

                # Store in DynamoDB
                self.table.put_item(Item=voter_item)
                results["success"] += 1

            except Exception as item_error:
                results["failed"] += 1
                results["errors"].append(f"Entry {idx}: {str(item_error)}")

        return results

    def verify_import(self) -> int:
        """Verify number of voters in table"""
        try:
            response = self.table.scan(Select="COUNT")
            return response["Count"]
        except Exception as e:
            print(f"Error verifying import: {str(e)}")
            return -1


def print_results(results: Dict[str, Any], table_name: str):
    """Print import results summary"""
    print("\n" + "=" * 60)
    print(f"VOTER IMPORT RESULTS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"Table Name: {table_name}")
    print(f"Total Processed: {results['total']}")
    print(f"Successfully Imported: {results['success']}")
    print(f"Failed: {results['failed']}")

    if results.get("warnings"):
        print("\nWarnings:")
        for warning in results["warnings"][:5]:  # Show first 5
            print(f"  ⚠ {warning}")
        if len(results["warnings"]) > 5:
            print(f"  ... and {len(results['warnings']) - 5} more")

    if results.get("errors"):
        print("\nErrors:")
        for error in results["errors"][:5]:  # Show first 5
            print(f"  ✗ {error}")
        if len(results["errors"]) > 5:
            print(f"  ... and {len(results['errors']) - 5} more")

    print("=" * 60 + "\n")

    return results["failed"] == 0


def main():
    parser = argparse.ArgumentParser(
        description="Import voter data to RWA Voting System DynamoDB table",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import from CSV file
  python3 bulk_import_voters.py voters.csv rwa-voting-voters-dev

  # Import from CSV with custom region
  python3 bulk_import_voters.py voters.csv rwa-voting-voters-prod --region ap-south-1
        """,
    )

    parser.add_argument(
        "csv_file",
        help="Path to CSV file with voter data",
    )
    parser.add_argument(
        "table_name",
        help="DynamoDB table name (e.g., rwa-voting-voters-dev)",
    )
    parser.add_argument(
        "--region",
        default="ap-south-1",
        help="AWS region (default: ap-south-1)",
    )

    args = parser.parse_args()

    try:
        # Initialize importer
        importer = VoterImporter(args.table_name, args.region)

        print(f"\n📝 Starting voter import...")
        print(f"   File: {args.csv_file}")
        print(f"   Table: {args.table_name}")
        print(f"   Region: {args.region}\n")

        # Import data
        results = importer.import_from_csv(args.csv_file)

        # Print results
        success = print_results(results, args.table_name)

        # Verify
        if success and results["success"] > 0:
            total_voters = importer.verify_import()
            print(f"✓ Total voters in table: {total_voters}")

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\n❌ Import cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
