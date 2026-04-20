import json
import sys
import os

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from utils import (
    create_response,
    error_response,
    success_response,
    get_env,
    log_event,
    validate_mobile_number,
    normalize_mobile_number,
)
from aws_clients import DynamoDBClient


def lambda_handler(event, context):
    """
    Bulk upload voter data to voters table

    Request body:
    {
        "voters": [
            {
                "flatNumber": "A-101",
                "name": "John Doe",
                "mobileNumber": "9876543210"
            }
        ]
    }

    Response:
    {
        "success": true,
        "data": {
            "totalUploaded": 10,
            "successCount": 10,
            "failureCount": 0,
            "errors": []
        }
    }
    """
    try:
        # Parse request
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return error_response(400, "Invalid JSON in request body", "INVALID_JSON")

        voters_list = body.get("voters", [])

        if not voters_list:
            return error_response(400, "Voters list is required", "VOTERS_REQUIRED")

        if not isinstance(voters_list, list):
            return error_response(400, "Voters must be a list", "INVALID_FORMAT")

        # Get environment variables
        voters_table_name = get_env("VOTERS_TABLE_NAME")
        aws_region = get_env("AWS_REGION", "ap-south-1")

        db_client = DynamoDBClient(region=aws_region)

        success_count = 0
        failure_count = 0
        errors = []

        # Process each voter
        for idx, voter in enumerate(voters_list):
            try:
                # Validate required fields
                flat_number = voter.get("flatNumber", "").strip()
                name = voter.get("name", "").strip()
                mobile_number = voter.get("mobileNumber", "").strip()

                if not flat_number:
                    errors.append(
                        {
                            "index": idx,
                            "error": "Flat/House number is required",
                            "voter": voter,
                        }
                    )
                    failure_count += 1
                    continue

                if not name:
                    errors.append(
                        {
                            "index": idx,
                            "error": "Name is required",
                            "voter": voter,
                        }
                    )
                    failure_count += 1
                    continue

                if not mobile_number:
                    errors.append(
                        {
                            "index": idx,
                            "error": "Mobile number is required",
                            "voter": voter,
                        }
                    )
                    failure_count += 1
                    continue

                # Validate mobile number
                if not validate_mobile_number(mobile_number):
                    errors.append(
                        {
                            "index": idx,
                            "error": "Invalid mobile number format",
                            "voter": voter,
                        }
                    )
                    failure_count += 1
                    continue

                # Normalize mobile number
                normalized_number = normalize_mobile_number(mobile_number)

                # Create voter record
                voter_item = {
                    "flatNumber": flat_number,
                    "mobileNumber": normalized_number,
                    "name": name,
                    "uploadedAt": int(__import__("time").time()),
                }

                # Add optional fields if present
                if "email" in voter:
                    voter_item["email"] = voter.get("email", "").strip()

                if "area" in voter:
                    voter_item["area"] = voter.get("area", "").strip()

                # Store in DynamoDB
                db_client.put_item(voters_table_name, voter_item)

                success_count += 1

            except Exception as item_error:
                print(f"Error processing voter {idx}: {str(item_error)}")
                errors.append(
                    {
                        "index": idx,
                        "error": str(item_error),
                        "voter": voter,
                    }
                )
                failure_count += 1

        log_event(
            "BULK_VOTER_UPLOAD",
            {
                "totalVoters": len(voters_list),
                "successCount": success_count,
                "failureCount": failure_count,
            },
        )

        return success_response(
            {
                "totalUploaded": len(voters_list),
                "successCount": success_count,
                "failureCount": failure_count,
                "errors": errors if errors else [],
            }
        )

    except ValueError as ve:
        print(f"Configuration error: {str(ve)}")
        return error_response(500, "Server configuration error", "CONFIG_ERROR")

    except Exception as e:
        print(f"Error in bulk_upload_voters: {str(e)}")
        log_event("BULK_UPLOAD_ERROR", {"error": str(e)})
        return error_response(500, "Internal server error", "INTERNAL_ERROR")
