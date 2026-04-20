import json
import sys
import os
from datetime import datetime, timezone, timedelta

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from utils import (
    normalize_mobile_number,
    validate_mobile_number,
    validate_election_id,
    validate_post_id,
    validate_candidate_id,
    create_response,
    error_response,
    success_response,
    get_env,
    log_event,
    mask_mobile_number,
)
from aws_clients import DynamoDBClient


def get_ist_timestamp():
    """Get current timestamp in IST timezone"""
    ist = timezone(timedelta(hours=5, minutes=30))
    return int(datetime.now(ist).timestamp())


def lambda_handler(event, context):
    """
    Cast a vote for a candidate in an election

    Request body:
    {
        "mobileNumber": "9876543210",
        "electionId": "election-2024",
        "postId": "1",
        "candidateId": "candidate-001"
    }

    Response:
    {
        "success": true,
        "data": {
            "message": "Vote cast successfully",
            "postId": "1"
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
        election_id = body.get("electionId", "").strip()
        post_id = body.get("postId", "").strip()
        candidate_id = body.get("candidateId", "").strip()

        # Validate inputs
        if not mobile_number:
            return error_response(400, "Mobile number is required", "MOBILE_REQUIRED")

        if not election_id:
            return error_response(400, "Election ID is required", "ELECTION_REQUIRED")

        if not post_id:
            return error_response(400, "Post ID is required", "POST_REQUIRED")

        if not candidate_id:
            return error_response(400, "Candidate ID is required", "CANDIDATE_REQUIRED")

        if not validate_mobile_number(mobile_number):
            return error_response(400, "Invalid mobile number format", "INVALID_MOBILE")

        if not validate_election_id(election_id):
            return error_response(400, "Invalid election ID format", "INVALID_ELECTION")

        if not validate_post_id(post_id):
            return error_response(400, "Invalid post ID (must be 1-7)", "INVALID_POST")

        if not validate_candidate_id(candidate_id):
            return error_response(
                400, "Invalid candidate ID format", "INVALID_CANDIDATE"
            )

        # Normalize mobile number
        normalized_number = normalize_mobile_number(mobile_number)

        # Get environment variables
        votes_table_name = get_env("VOTES_TABLE_NAME")
        elections_table_name = get_env("ELECTIONS_TABLE_NAME")
        candidates_table_name = get_env("CANDIDATES_TABLE_NAME")
        aws_region = get_env("AWS_REGION", "ap-south-1")

        # Initialize DynamoDB client
        db_client = DynamoDBClient(region=aws_region)

        # Step 1: Verify election exists and is active
        election = db_client.get_item(elections_table_name, {"electionId": election_id})

        if not election:
            log_event(
                "VOTE_FAILED",
                {"electionId": election_id, "reason": "ELECTION_NOT_FOUND"},
            )
            return error_response(404, "Election not found", "ELECTION_NOT_FOUND")

        # Check if election is currently active (using IST timezone)
        current_time_ist = get_ist_timestamp()
        start_time = int(election.get("startTime", 0))
        end_time = int(election.get("endTime", 0))

        if current_time_ist < start_time:
            log_event(
                "VOTE_FAILED",
                {"electionId": election_id, "reason": "ELECTION_NOT_STARTED"},
            )
            return error_response(
                400,
                "Election has not started yet (IST timezone)",
                "ELECTION_NOT_STARTED",
            )

        if current_time_ist > end_time:
            log_event(
                "VOTE_FAILED", {"electionId": election_id, "reason": "ELECTION_ENDED"}
            )
            return error_response(
                400, "Election has ended (IST timezone)", "ELECTION_ENDED"
            )

        # Step 2: Verify candidate exists
        post_key = f"{election_id}#{post_id}"
        candidate = db_client.get_item(
            candidates_table_name,
            {"electionId#postId": post_key, "candidateId": candidate_id},
        )

        if not candidate:
            log_event(
                "VOTE_FAILED",
                {
                    "electionId": election_id,
                    "postId": post_id,
                    "candidateId": candidate_id,
                    "reason": "CANDIDATE_NOT_FOUND",
                },
            )
            return error_response(404, "Candidate not found", "CANDIDATE_NOT_FOUND")

        # Step 3: Check if voter has already voted for this post (prevent duplicate voting)
        vote_key = f"{election_id}#{post_id}"
        existing_vote = db_client.get_item(
            votes_table_name,
            {"electionId#postId": vote_key, "mobileNumber": normalized_number},
        )

        if existing_vote:
            log_event(
                "VOTE_FAILED",
                {
                    "electionId": election_id,
                    "postId": post_id,
                    "mobileNumber": normalized_number,
                    "reason": "DUPLICATE_VOTE",
                },
                sensitive=True,
            )
            return error_response(
                400, "You have already voted for this post", "DUPLICATE_VOTE"
            )

        # Step 4: Record the vote with conditional write (avoid race conditions)
        vote_item = {
            "electionId#postId": vote_key,
            "mobileNumber": normalized_number,
            "candidateId": candidate_id,
            "timestamp": get_ist_timestamp(),
        }

        # Use conditional write to prevent duplicates in edge cases
        from boto3.dynamodb.conditions import Key, Attr

        try:
            from boto3.dynamodb.conditions import Attr

            table = db_client.dynamodb.Table(votes_table_name)

            table.put_item(
                Item=vote_item, ConditionExpression="attribute_not_exists(mobileNumber)"
            )

            log_event(
                "VOTE_CAST",
                {
                    "electionId": election_id,
                    "postId": post_id,
                    "candidateId": candidate_id,
                    "candidateName": candidate.get("candidateName", "Unknown"),
                    "mobileNumber": normalized_number,
                },
                sensitive=True,
            )

            return success_response(
                {
                    "message": "Vote cast successfully",
                    "postId": post_id,
                    "candidateName": candidate.get("candidateName", "Unknown"),
                }
            )

        except Exception as e:
            if "ConditionalCheckFailedException" in str(e):
                log_event(
                    "VOTE_FAILED",
                    {
                        "electionId": election_id,
                        "postId": post_id,
                        "reason": "DUPLICATE_VOTE_CONCURRENT",
                    },
                    sensitive=True,
                )
                return error_response(
                    400, "Vote already recorded for this post", "DUPLICATE_VOTE"
                )
            raise

    except ValueError as ve:
        print(f"Configuration error: {str(ve)}")
        return error_response(500, "Server configuration error", "CONFIG_ERROR")

    except Exception as e:
        print(f"Unexpected error in cast_vote: {str(e)}")
        log_event("CAST_VOTE_ERROR", {"error": str(e)})
        return error_response(500, "Internal server error", "INTERNAL_ERROR")
