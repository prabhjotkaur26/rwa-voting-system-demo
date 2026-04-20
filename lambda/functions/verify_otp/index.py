import json
import sys
import os

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from utils import (
    validate_mobile_number,
    normalize_mobile_number,
    validate_otp,
    create_response,
    error_response,
    success_response,
    get_env,
    log_event,
    mask_mobile_number,
)
from aws_clients import DynamoDBClient


def lambda_handler(event, context):
    """
    Verify OTP sent to mobile number

    Request body:
    {
        "mobileNumber": "9876543210",
        "otp": "123456"
    }

    Response:
    {
        "success": true,
        "data": {
            "message": "OTP verified successfully",
            "token": "auth_token_here"
        }
    }
    """
    try:
        # Parse request
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return error_response(400, "Invalid JSON in request body", "INVALID_JSON")

        mobile_number = body.get("mobileNumber", "").strip()
        otp = body.get("otp", "").strip()

        # Validate inputs
        if not mobile_number:
            return error_response(400, "Mobile number is required", "MOBILE_REQUIRED")

        if not otp:
            return error_response(400, "OTP is required", "OTP_REQUIRED")

        if not validate_mobile_number(mobile_number):
            return error_response(400, "Invalid mobile number format", "INVALID_MOBILE")

        if not validate_otp(otp):
            return error_response(400, "OTP must be 6 digits", "INVALID_OTP_FORMAT")

        # Normalize mobile number
        normalized_number = normalize_mobile_number(mobile_number)

        # Get environment variables
        otp_table_name = get_env("OTP_TABLE_NAME")
        aws_region = get_env("AWS_REGION", "ap-south-1")

        # Retrieve OTP from DynamoDB
        db_client = DynamoDBClient(region=aws_region)

        stored_otp = db_client.get_item(
            otp_table_name, {"mobileNumber": normalized_number}
        )

        if not stored_otp:
            log_event(
                "OTP_VERIFY_FAILED",
                {"mobileNumber": normalized_number, "reason": "OTP_NOT_FOUND"},
                sensitive=True,
            )
            return error_response(400, "OTP not found or expired", "OTP_NOT_FOUND")

        # Verify OTP
        stored_otp_value = stored_otp.get("otp", "")

        if stored_otp_value != otp:
            # Increment attempts
            attempts = stored_otp.get("attempts", 0) + 1

            if attempts >= 3:
                # Delete OTP after 3 failed attempts
                db_client.delete_item(
                    otp_table_name, {"mobileNumber": normalized_number}
                )
                log_event(
                    "OTP_VERIFY_FAILED",
                    {
                        "mobileNumber": normalized_number,
                        "reason": "MAX_ATTEMPTS_EXCEEDED",
                        "attempts": attempts,
                    },
                    sensitive=True,
                )
                return error_response(
                    400,
                    "Maximum OTP attempts exceeded. Request a new OTP.",
                    "MAX_ATTEMPTS",
                )

            # Update attempts
            db_client.update_item(
                otp_table_name,
                {"mobileNumber": normalized_number},
                "SET attempts = :attempts",
                {":attempts": attempts},
            )

            log_event(
                "OTP_VERIFY_FAILED",
                {
                    "mobileNumber": normalized_number,
                    "reason": "OTP_MISMATCH",
                    "attempts": attempts,
                },
                sensitive=True,
            )
            return error_response(400, "Invalid OTP", "INVALID_OTP")

        # OTP verified successfully
        # Delete OTP from DynamoDB (single use only)
        db_client.delete_item(otp_table_name, {"mobileNumber": normalized_number})

        # Generate authentication token (in production, use JWT)
        # For now, we'll use the normalized mobile number as identifier
        auth_token = normalized_number

        log_event(
            "OTP_VERIFIED",
            {
                "mobileNumber": normalized_number,
            },
            sensitive=True,
        )

        return success_response(
            {
                "message": "OTP verified successfully",
                "token": auth_token,
                "maskedNumber": mask_mobile_number(normalized_number),
            }
        )

    except ValueError as ve:
        print(f"Configuration error: {str(ve)}")
        return error_response(500, "Server configuration error", "CONFIG_ERROR")

    except Exception as e:
        print(f"Unexpected error in verify_otp: {str(e)}")
        log_event("VERIFY_OTP_ERROR", {"error": str(e)})
        return error_response(500, "Internal server error", "INTERNAL_ERROR")
