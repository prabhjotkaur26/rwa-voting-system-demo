import json
import sys
import os
from decimal import Decimal

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from utils import (
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
    Get list of all elections

    Request:
    GET /admin/elections

    Response:
    {
        "success": true,
        "data": [
            {
                "electionId": "election-2024",
                "electionName": "Board Election 2024",
                "description": "Annual board elections",
                "startTime": 1234567890,
                "endTime": 1234571490,
                "status": "scheduled|active|ended",
                "createdAt": 1234567800,
                "resultsVisible": false
            },
            ...
        ]
    }
    """
    try:
        # Get environment variables
        elections_table_name = get_env("ELECTIONS_TABLE_NAME")

        # Initialize DynamoDB client
        db_client = DynamoDBClient(region="ap-south-1")

        # Scan all elections
        try:
            elections = db_client.scan(elections_table_name)
        except Exception as scan_error:
            print(f"DynamoDB scan error: {str(scan_error)}")
            log_event("SCAN_ELECTIONS_ERROR", {"error": str(scan_error)})
            # Return empty list instead of error - table might not have data yet
            return success_response([])

        # Convert to list and sort by creation date (newest first)
        elections_list = list(elections) if elections else []
        elections_list.sort(key=lambda x: x.get("createdAt", 0), reverse=True)

        # Convert Decimal objects to native Python types for JSON serialization
        elections_list = [convert_decimal(e) for e in elections_list]

        log_event(
            "ELECTIONS_FETCHED",
            {"count": len(elections_list)},
        )

        return success_response(elections_list)

    except ValueError as ve:
        print(f"Configuration error: {str(ve)}")
        return error_response(500, "Server configuration error", "CONFIG_ERROR")

    except Exception as e:
        print(f"Unexpected error in get_elections: {str(e)}")
        log_event("GET_ELECTIONS_ERROR", {"error": str(e)})
        return error_response(500, "Internal server error", "INTERNAL_ERROR")
