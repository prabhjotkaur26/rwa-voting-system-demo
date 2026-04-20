import json
import sys
import os
from datetime import datetime, timezone, timedelta

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from utils import (
    validate_election_id,
    validate_post_id,
    validate_candidate_id,
    create_response,
    error_response,
    success_response,
    get_env,
    log_event,
)
from aws_clients import DynamoDBClient


def get_ist_timestamp():
    """Get current timestamp in IST timezone"""
    ist = timezone(timedelta(hours=5, minutes=30))
    return int(datetime.now(ist).timestamp())


def lambda_handler(event, context):
    """
    Add candidates to a post in an election

    Request body:
    {
        "electionId": "election-2024",
        "postId": "1",
        "candidates": [
            {
                "candidateId": "candidate-001",
                "candidateName": "John Doe",
                "imageUrl": "https://...",
                "party": "Party A",
                "bio": "Description"
            }
        ]
    }

    Response:
    {
        "success": true,
        "data": {
            "message": "Candidates added successfully",
            "electionId": "election-2024",
            "postId": "1",
            "candidatesAdded": 2
        }
    }
    """
    try:
        # Parse request
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return error_response(400, "Invalid JSON in request body", "INVALID_JSON")

        election_id = body.get("electionId", "").strip()
        post_id = body.get("postId", "").strip()
        candidates = body.get("candidates", [])

        # Validate inputs
        if not election_id:
            return error_response(400, "Election ID is required", "ELECTION_REQUIRED")

        if not post_id:
            return error_response(400, "Post ID is required", "POST_REQUIRED")

        if not candidates or not isinstance(candidates, list):
            return error_response(
                400, "Candidates list is required", "CANDIDATES_REQUIRED"
            )

        if not validate_election_id(election_id):
            return error_response(400, "Invalid election ID format", "INVALID_ELECTION")

        if not validate_post_id(post_id):
            return error_response(400, "Invalid post ID (must be 1-7)", "INVALID_POST")

        if len(candidates) > 20:
            return error_response(
                400, "Maximum 20 candidates per post", "TOO_MANY_CANDIDATES"
            )

        # Validate each candidate
        for candidate in candidates:
            if not isinstance(candidate, dict):
                return error_response(
                    400, "Each candidate must be an object", "INVALID_CANDIDATE_FORMAT"
                )

            candidate_id = candidate.get("candidateId", "").strip()
            candidate_name = candidate.get("candidateName", "").strip()

            if not candidate_id or not candidate_name:
                return error_response(
                    400,
                    "Each candidate must have candidateId and candidateName",
                    "MISSING_CANDIDATE_FIELDS",
                )

            if not validate_candidate_id(candidate_id):
                return error_response(
                    400,
                    f"Invalid candidate ID format: {candidate_id}",
                    "INVALID_CANDIDATE_ID",
                )

        # Get environment variables
        elections_table_name = get_env("ELECTIONS_TABLE_NAME")
        candidates_table_name = get_env("CANDIDATES_TABLE_NAME")
        aws_region = get_env("AWS_REGION", "ap-south-1")

        # Initialize DynamoDB client
        db_client = DynamoDBClient(region=aws_region)

        # Verify election exists
        election = db_client.get_item(elections_table_name, {"electionId": election_id})

        if not election:
            log_event(
                "CANDIDATES_ADD_FAILED",
                {"electionId": election_id, "reason": "ELECTION_NOT_FOUND"},
            )
            return error_response(404, "Election not found", "ELECTION_NOT_FOUND")

        # Add candidates
        post_key = f"{election_id}#{post_id}"
        added_count = 0

        for candidate in candidates:
            candidate_id = candidate.get("candidateId", "").strip()
            candidate_name = candidate.get("candidateName", "").strip()

            # Check if candidate already exists
            existing_candidate = db_client.get_item(
                candidates_table_name,
                {"electionId#postId": post_key, "candidateId": candidate_id},
            )

            if not existing_candidate:
                candidate_item = {
                    "electionId#postId": post_key,
                    "candidateId": candidate_id,
                    "name": candidate_name,
                    "electionId": election_id,
                    "postId": post_id,
                    "createdAt": get_ist_timestamp(),
                }

                # Add optional fields
                if "imageUrl" in candidate:
                    candidate_item["imageUrl"] = candidate.get("imageUrl", "").strip()

                if "party" in candidate:
                    candidate_item["party"] = candidate.get("party", "").strip()

                if "bio" in candidate:
                    candidate_item["bio"] = candidate.get("bio", "").strip()

                db_client.put_item(candidates_table_name, candidate_item)
                added_count += 1

        log_event(
            "CANDIDATES_ADDED",
            {
                "electionId": election_id,
                "postId": post_id,
                "candidatesAdded": added_count,
                "totalCandidates": len(candidates),
            },
        )

        return success_response(
            {
                "message": "Candidates added successfully",
                "electionId": election_id,
                "postId": post_id,
                "candidatesAdded": added_count,
            },
            status_code=201,
        )

    except ValueError as ve:
        print(f"Configuration error: {str(ve)}")
        return error_response(500, "Server configuration error", "CONFIG_ERROR")

    except Exception as e:
        print(f"Unexpected error in add_candidates: {str(e)}")
        log_event("ADD_CANDIDATES_ERROR", {"error": str(e)})
        return error_response(500, "Internal server error", "INTERNAL_ERROR")
