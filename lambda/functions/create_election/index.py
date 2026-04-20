import json
import sys
import os
from datetime import datetime, timezone, timedelta

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


def get_ist_timestamp():
    """Get current timestamp in IST timezone"""
    ist = timezone(timedelta(hours=5, minutes=30))
    return int(datetime.now(ist).timestamp())


def lambda_handler(event, context):
    """
    Create a new election

    Request body:
    {
        "electionId": "election-2024",
        "electionName": "Board Election 2024",
        "description": "Annual board elections",
        "startTime": 1234567890,  # Unix timestamp
        "endTime": 1234571490     # Unix timestamp
    }

    Response:
    {
        "success": true,
        "data": {
            "message": "Election created successfully",
            "electionId": "election-2024"
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
        election_name = body.get("electionName", "").strip()
        description = body.get("description", "").strip()
        start_time = body.get("startTime")
        end_time = body.get("endTime")

        # Validate inputs
        if not election_id:
            return error_response(
                400, "Election ID is required", "ELECTION_ID_REQUIRED"
            )

        if not validate_election_id(election_id):
            return error_response(
                400,
                "Invalid election ID format (3-32 alphanumeric, dash, underscore)",
                "INVALID_ELECTION_ID",
            )

        if not election_name:
            return error_response(
                400, "Election name is required", "ELECTION_NAME_REQUIRED"
            )

        if not isinstance(start_time, (int, float)) or start_time <= 0:
            return error_response(
                400, "Start time must be a valid Unix timestamp", "INVALID_START_TIME"
            )

        if not isinstance(end_time, (int, float)) or end_time <= 0:
            return error_response(
                400, "End time must be a valid Unix timestamp", "INVALID_END_TIME"
            )

        if end_time <= start_time:
            return error_response(
                400, "End time must be after start time", "INVALID_TIME_RANGE"
            )

        # Get environment variables
        elections_table_name = get_env("ELECTIONS_TABLE_NAME")
        aws_region = get_env("AWS_REGION", "ap-south-1")

        # Initialize DynamoDB client
        db_client = DynamoDBClient(region=aws_region)

        # Check if election already exists
        existing_election = db_client.get_item(
            elections_table_name, {"electionId": election_id}
        )

        if existing_election:
            log_event(
                "ELECTION_CREATE_FAILED",
                {"electionId": election_id, "reason": "ELECTION_ALREADY_EXISTS"},
            )
            return error_response(
                409, "Election with this ID already exists", "ELECTION_EXISTS"
            )

        # Create election
        election_item = {
            "electionId": election_id,
            "electionName": election_name,
            "description": description or "",
            "startTime": int(start_time),
            "endTime": int(end_time),
            "createdAt": get_ist_timestamp(),
            "status": "scheduled",
            "resultsVisible": False,
        }

        db_client.put_item(elections_table_name, election_item)

        log_event(
            "ELECTION_CREATED",
            {
                "electionId": election_id,
                "electionName": election_name,
                "startTime": int(start_time),
                "endTime": int(end_time),
            },
        )

        return success_response(
            {
                "message": "Election created successfully",
                "electionId": election_id,
                "electionName": election_name,
            },
            status_code=201,
        )

    except ValueError as ve:
        print(f"Configuration error: {str(ve)}")
        return error_response(500, "Server configuration error", "CONFIG_ERROR")

    except Exception as e:
        print(f"Unexpected error in create_election: {str(e)}")
        log_event("CREATE_ELECTION_ERROR", {"error": str(e)})
        return error_response(500, "Internal server error", "INTERNAL_ERROR")
