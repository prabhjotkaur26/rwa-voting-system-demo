import json
import sys
import os
from datetime import datetime, timezone, timedelta
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


def get_ist_timestamp():
    """Get current timestamp in IST timezone"""
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist)


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert DynamoDB Decimal to int"""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    """
    Get admin dashboard statistics

    Request: GET /admin/stats

    Response:
    {
        "success": true,
        "data": {
            "activeElections": 2,
            "totalVoters": 500,
            "totalVotesCast": 350,
            "totalCandidates": 45,
            "voterParticipationRate": 70,
            "lastUpdated": "2024-04-17T10:30:00Z"
        }
    }
    """
    try:
        # Get environment variables
        elections_table = get_env("ELECTIONS_TABLE_NAME")
        candidates_table = get_env("CANDIDATES_TABLE_NAME")
        voters_table = get_env("VOTERS_TABLE_NAME")
        votes_table = get_env("VOTES_TABLE_NAME")
        aws_region = get_env("AWS_REGION", "ap-south-1")

        # Initialize DynamoDB client
        db_client = DynamoDBClient(region=aws_region)

        # Get table objects for scanning
        elections_tbl = db_client.get_table(elections_table)
        candidates_tbl = db_client.get_table(candidates_table)
        voters_tbl = db_client.get_table(voters_table)
        votes_tbl = db_client.get_table(votes_table)

        # Count active elections
        active_elections = 0
        try:
            elections_response = elections_tbl.scan(
                FilterExpression="attribute_exists(electionId)"
            )
            active_elections = elections_response.get("Count", 0)
        except Exception as e:
            log_event("STATS_ERROR_ELECTIONS", {"error": str(e)})
            active_elections = 0

        # Count total voters
        total_voters = 0
        try:
            voters_response = voters_tbl.scan(
                FilterExpression="attribute_exists(mobileNumber)"
            )
            total_voters = voters_response.get("Count", 0)
        except Exception as e:
            log_event("STATS_ERROR_VOTERS", {"error": str(e)})
            total_voters = 0

        # Count total candidates
        total_candidates = 0
        try:
            candidates_response = candidates_tbl.scan(
                FilterExpression="attribute_exists(candidateId)"
            )
            total_candidates = candidates_response.get("Count", 0)
        except Exception as e:
            log_event("STATS_ERROR_CANDIDATES", {"error": str(e)})
            total_candidates = 0

        # Count total votes cast
        total_votes_cast = 0
        try:
            votes_response = votes_tbl.scan(FilterExpression="attribute_exists(voteId)")
            total_votes_cast = votes_response.get("Count", 0)
        except Exception as e:
            log_event("STATS_ERROR_VOTES", {"error": str(e)})
            total_votes_cast = 0

        # Calculate participation rate
        participation_rate = (
            round((total_votes_cast / total_voters * 100), 2) if total_voters > 0 else 0
        )

        # Log stats retrieval
        log_event(
            "ADMIN_STATS_RETRIEVED",
            {
                "activeElections": active_elections,
                "totalVoters": total_voters,
                "totalVotesCast": total_votes_cast,
                "totalCandidates": total_candidates,
                "timestamp": get_ist_timestamp().isoformat(),
            },
        )

        return success_response(
            {
                "activeElections": active_elections,
                "totalVoters": total_voters,
                "totalVotesCast": total_votes_cast,
                "totalCandidates": total_candidates,
                "voterParticipationRate": participation_rate,
                "lastUpdated": get_ist_timestamp().isoformat(),
            }
        )

    except Exception as e:
        log_event(
            "ADMIN_STATS_ERROR",
            {
                "error": str(e),
                "timestamp": get_ist_timestamp().isoformat(),
            },
        )
        return error_response(
            500, f"Failed to retrieve statistics: {str(e)}", "STATS_ERROR"
        )
