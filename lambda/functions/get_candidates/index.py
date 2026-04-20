import json
import sys
import os
from decimal import Decimal

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from utils import (
    validate_election_id,
    create_response,
    error_response,
    success_response,
    get_env,
    log_event,
)
from aws_clients import DynamoDBClient


def convert_decimal(obj):
    """Convert Decimal objects from DynamoDB to native Python types."""
    if isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal(item) for item in obj]
    return obj


def lambda_handler(event, context):
    """
    Get list of candidates (optionally filtered by election)

    Request:
    GET /admin/candidates
    GET /admin/candidates?electionId=election-2024

    Response:
    {
        "success": true,
        "data": [
            {
                "candidateId": "candidate-001",
                "electionId": "election-2024",
                "postId": "1",
                "candidateName": "John Doe",
                "description": "Experienced leader",
                "bio": "...",
                "email": "john@example.com",
                "phone": "+1234567890",
                "imageUrl": "https://...",
                "createdAt": 1234567800
            },
            ...
        ]
    }
    """
    try:
        # Get optional election filter from query parameters
        query_params = event.get("queryStringParameters", {}) or {}
        election_filter = (
            query_params.get("electionId", "").strip() if query_params else ""
        )

        # Validate election ID if provided
        if election_filter and not validate_election_id(election_filter):
            return error_response(400, "Invalid election ID format", "INVALID_ELECTION")

        # Get environment variables
        candidates_table_name = get_env("CANDIDATES_TABLE_NAME")

        # Initialize DynamoDB client
        db_client = DynamoDBClient(region="ap-south-1")

        # Scan candidates table
        try:
            candidates = db_client.scan(candidates_table_name)
        except Exception as scan_error:
            print(f"DynamoDB scan error: {str(scan_error)}")
            log_event("SCAN_CANDIDATES_ERROR", {"error": str(scan_error)})
            # Return empty list instead of error
            return success_response([])

        # Filter by election if specified
        candidates_list = list(candidates) if candidates else []

        if election_filter:
            candidates_list = [
                c for c in candidates_list if c.get("electionId") == election_filter
            ]

        # Sort by post ID and creation date
        candidates_list.sort(
            key=lambda x: (
                (
                    int(x.get("postId", "0"))
                    if isinstance(x.get("postId"), str)
                    else x.get("postId", 0)
                ),
                x.get("createdAt", 0),
            )
        )

        # Convert Decimal objects to native Python types for JSON serialization
        candidates_list = [convert_decimal(c) for c in candidates_list]

        log_event(
            "CANDIDATES_FETCHED",
            {"count": len(candidates_list), "election": election_filter or "all"},
        )

        return success_response(candidates_list)

    except ValueError as ve:
        print(f"Configuration error: {str(ve)}")
        return error_response(500, "Server configuration error", "CONFIG_ERROR")

    except Exception as e:
        print(f"Unexpected error in get_candidates: {str(e)}")
        log_event("GET_CANDIDATES_ERROR", {"error": str(e)})
        return error_response(500, "Internal server error", "INTERNAL_ERROR")
