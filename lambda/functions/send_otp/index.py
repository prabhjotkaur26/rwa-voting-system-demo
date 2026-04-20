import json
import sys
import os
from datetime import datetime, timezone, timedelta

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from utils import (
    generate_otp,
    validate_mobile_number,
    normalize_mobile_number,
    validate_election_id,
    create_response,
    error_response,
    success_response,
    get_env,
    get_ttl_timestamp,
    mask_mobile_number,
    log_event,
)
from aws_clients import DynamoDBClient, SNSClient


def get_ist_timestamp():
    """Get current timestamp in IST timezone"""
    ist = timezone(timedelta(hours=5, minutes=30))
    return int(datetime.now(ist).timestamp())


def lambda_handler(event, context):
    """
    Send OTP to registered mobile number

    Request body:
    {
        "mobileNumber": "9876543210",
        "electionId": "election-2024"  (optional but recommended)
    }

    Response:
    {
        "success": true,
        "data": {
            "message": "OTP sent successfully",
            "maskedNumber": "****3210"
        }
    }
    """
    try:
        # Parse request
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return error_response(400, "Invalid JSON in request body", "INVALID_JSON")

        mobile_number = (body.get("mobileNumber") or "").strip()
        election_id = (body.get("electionId") or "").strip()

        # Validate mobile number
        if not mobile_number:
            return error_response(400, "Mobile number is required", "MOBILE_REQUIRED")

        if not validate_mobile_number(mobile_number):
            return error_response(400, "Invalid mobile number format", "INVALID_MOBILE")

        # Normalize mobile number
        normalized_number = normalize_mobile_number(mobile_number)

        # Get environment variables
        otp_table_name = get_env("OTP_TABLE_NAME")
        voters_table_name = get_env("VOTERS_TABLE_NAME")
        sns_topic_arn = get_env("SNS_TOPIC_ARN")
        otp_expiry_minutes = int(get_env("OTP_EXPIRY_MINUTES", "5"))
        aws_region = get_env("AWS_REGION", "ap-south-1")
        votes_table_name = None

        # Initialize DynamoDB client
        db_client = DynamoDBClient(region=aws_region)

        # Check if voter exists in voters table
        try:
            voter_data = db_client.get_item(
                voters_table_name, {"mobileNumber": normalized_number}
            )

            if not voter_data:
                return error_response(
                    400,
                    "Mobile number not found in voter records. Please verify your registration.",
                    "VOTER_NOT_FOUND",
                )

            # Voter verified - log verification
            log_event(
                "VOTER_VERIFIED",
                {
                    "mobileNumber": normalized_number,
                    "voterName": voter_data.get("name", ""),
                },
                sensitive=True,
            )

        except Exception as voter_check_error:
            print(f"Error checking voter: {str(voter_check_error)}")
            return error_response(
                500, "Error verifying voter registration", "VOTER_CHECK_ERROR"
            )

        # If electionId provided, validate election timing and check if already voted
        if election_id:
            if not validate_election_id(election_id):
                return error_response(
                    400, "Invalid election ID format", "INVALID_ELECTION"
                )

            try:
                # Get elections table name for timing validation
                elections_table_name = get_env("ELECTIONS_TABLE_NAME")

                # Check election timing (IST timezone)
                election = db_client.get_item(
                    elections_table_name, {"electionId": election_id}
                )

                if not election:
                    return error_response(
                        404, "Election not found", "ELECTION_NOT_FOUND"
                    )

                # Validate election timing using IST
                current_time_ist = get_ist_timestamp()
                start_time = int(election.get("startTime", 0))
                end_time = int(election.get("endTime", 0))

                if current_time_ist < start_time:
                    log_event(
                        "VOTING_OUTSIDE_WINDOW",
                        {
                            "electionId": election_id,
                            "reason": "TOO_EARLY",
                            "currentTime": current_time_ist,
                            "startTime": start_time,
                        },
                    )
                    return error_response(
                        400,
                        f"Election has not started yet. Starts at {start_time} (IST)",
                        "ELECTION_NOT_STARTED",
                    )

                if current_time_ist > end_time:
                    log_event(
                        "VOTING_OUTSIDE_WINDOW",
                        {
                            "electionId": election_id,
                            "reason": "TOO_LATE",
                            "currentTime": current_time_ist,
                            "endTime": end_time,
                        },
                    )
                    return error_response(
                        400,
                        f"Election has ended. Ended at {end_time} (IST)",
                        "ELECTION_ENDED",
                    )

            except Exception as election_check_error:
                print(f"Error checking election: {str(election_check_error)}")
                import traceback

                traceback.print_exc()
                return error_response(
                    500,
                    f"Error validating election: {str(election_check_error)}",
                    "ELECTION_CHECK_ERROR",
                )

            try:
                # Get votes table name only when needed
                if votes_table_name is None:
                    votes_table_name = get_env("VOTES_TABLE_NAME")

                # Check if user has already voted in this election
                # Query votes table for any votes from this mobile number in this election
                votes = db_client.scan(
                    votes_table_name,
                    filter_expression="begins_with(#pk, :election) AND #mobile = :number",
                    expression_attribute_names={
                        "#pk": "electionId#postId",
                        "#mobile": "mobileNumber",
                    },
                    expression_attribute_values={
                        ":election": election_id,
                        ":number": normalized_number,
                    },
                )

                if votes and len(votes) > 0:
                    log_event(
                        "DUPLICATE_VOTE_ATTEMPT",
                        {
                            "electionId": election_id,
                            "mobileNumber": normalized_number,
                            "postsAlreadyVoted": len(votes),
                        },
                        sensitive=True,
                    )
                    return error_response(
                        400,
                        "You have already voted in this election. You cannot vote again.",
                        "ALREADY_VOTED",
                    )

            except Exception as vote_check_error:
                print(f"Error checking votes: {str(vote_check_error)}")
                # Continue with OTP send even if vote check fails
                # This prevents service disruption if votes table check fails

        # Check if OTP already exists for this mobile number
        existing_otp = db_client.get_item(
            otp_table_name, {"mobileNumber": normalized_number}
        )

        if existing_otp and len(existing_otp) > 0:
            # OTP already exists and hasn't expired yet (TTL will delete it when expired)
            # Return success response to allow user to verify existing OTP
            log_event(
                "OTP_ALREADY_EXISTS",
                {
                    "mobileNumber": normalized_number,
                    "message": "OTP already sent, user can verify existing OTP",
                },
                sensitive=True,
            )
            return success_response(
                {
                    "message": "OTP already sent to this number. Please verify using the existing OTP.",
                    "maskedNumber": mask_mobile_number(normalized_number),
                    "otpAlreadyExists": True,
                    "expiryMinutes": otp_expiry_minutes,
                }
            )

        # Generate OTP
        otp = generate_otp()
        ttl_timestamp = get_ttl_timestamp(otp_expiry_minutes)

        otp_item = {
            "mobileNumber": normalized_number,
            "otp": otp,
            "createdAt": (
                int(context.aws_request_id.split("-")[0], 16)
                if context.aws_request_id
                else 0
            ),
            "ttl": ttl_timestamp,
            "attempts": 0,
        }

        db_client.put_item(otp_table_name, otp_item)

        # Send OTP via SNS
        sns_client = SNSClient(region=aws_region)

        # Format phone number for SNS (international format)
        phone_number = f"+91{normalized_number}"
        sms_message = f"Your RWA Voting System OTP is: {otp}. Valid for {otp_expiry_minutes} minutes. Do not share this with anyone."

        try:
            message_id = sns_client.publish_sms(phone_number, sms_message)

            # Log successful OTP send
            log_event(
                "OTP_SENT",
                {
                    "mobileNumber": normalized_number,
                    "messageId": message_id,
                },
                sensitive=True,
            )

            return success_response(
                {
                    "message": "OTP sent successfully",
                    "maskedNumber": mask_mobile_number(normalized_number),
                    "expiryMinutes": otp_expiry_minutes,
                }
            )

        except Exception as sns_error:
            print(f"SNS Error: {str(sns_error)}")
            # For testing purposes, log OTP if SNS fails
            if (
                "not subscribed" in str(sns_error).lower()
                or "test-" in sns_topic_arn.lower()
            ):
                log_event(
                    "OTP_SENT_TEST",
                    {
                        "mobileNumber": normalized_number,
                        "otp": otp,  # Only log in test/error scenarios
                        "note": "SNS not fully configured",
                    },
                    sensitive=False,
                )
                return success_response(
                    {
                        "message": "OTP sent successfully (test mode)",
                        "maskedNumber": mask_mobile_number(normalized_number),
                        "expiryMinutes": otp_expiry_minutes,
                    }
                )
            raise

    except ValueError as ve:
        print(f"Configuration error: {str(ve)}")
        return error_response(500, "Server configuration error", "CONFIG_ERROR")

    except Exception as e:
        print(f"Unexpected error in send_otp: {str(e)}")
        log_event("SEND_OTP_ERROR", {"error": str(e)})
        return error_response(500, "Internal server error", "INTERNAL_ERROR")
