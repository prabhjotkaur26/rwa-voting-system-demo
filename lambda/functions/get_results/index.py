import json
import sys
import os
import time
from collections import defaultdict

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


def lambda_handler(event, context):
    """
    Get election results (vote counts per candidate per post)

    Request:
    GET /results/{electionId}

    Response:
    {
        "success": true,
        "data": {
            "electionId": "election-2024",
            "electionName": "Board Election 2024",
            "results": {
                "1": {  # Post ID
                    "postName": "President",
                    "candidates": [
                        {
                            "candidateId": "candidate-001",
                            "candidateName": "John Doe",
                            "votes": 45
                        },
                        ...
                    ],
                    "totalVotes": 120
                },
                ...
            }
        }
    }
    """
    try:
        # Get election ID from path parameters
        path_parameters = event.get("pathParameters", {})
        election_id = (
            path_parameters.get("electionId", "").strip() if path_parameters else ""
        )

        if not election_id:
            return error_response(400, "Election ID is required", "ELECTION_REQUIRED")

        if not validate_election_id(election_id):
            return error_response(400, "Invalid election ID format", "INVALID_ELECTION")

        # Get environment variables
        votes_table_name = get_env("VOTES_TABLE_NAME")
        elections_table_name = get_env("ELECTIONS_TABLE_NAME")
        candidates_table_name = get_env("CANDIDATES_TABLE_NAME")
        aws_region = get_env("AWS_REGION", "ap-south-1")

        # Initialize DynamoDB client
        db_client = DynamoDBClient(region=aws_region)

        # Step 1: Verify election exists
        election = db_client.get_item(elections_table_name, {"electionId": election_id})

        if not election:
            log_event(
                "RESULTS_FAILED",
                {"electionId": election_id, "reason": "ELECTION_NOT_FOUND"},
            )
            return error_response(404, "Election not found", "ELECTION_NOT_FOUND")

        # Step 2: Fetch all candidates for this election
        candidates_by_post = {}
        for post_id in range(1, 8):  # 7 posts
            post_key = f"{election_id}#{post_id}"
            candidates = db_client.query(
                candidates_table_name,
                "#pk = :post_key",
                {":post_key": post_key},
                {"#pk": "electionId#postId"},
            )

            candidates_by_post[str(post_id)] = {
                "candidates": candidates,
                "totalVotes": 0,
            }

        # Step 3: Fetch all votes for this election and count
        votes_list = (
            db_client.query(
                votes_table_name,
                "begins_with(electionId#postId, :prefix)",
                {":prefix": f"{election_id}#"},
                index_name="electionId-index",
            )
            if "electionId-index" in election.get("_metadata", {})
            else []
        )

        # Alternative: Scan all votes and filter (less efficient but works)
        vote_counts = defaultdict(lambda: defaultdict(int))

        # Query votes for each post
        for post_id in range(1, 8):
            post_key = f"{election_id}#{post_id}"
            votes = db_client.query(
                votes_table_name,
                "#pk = :post_key",
                {":post_key": post_key},
                {"#pk": "electionId#postId"},
            )

            for vote in votes:
                candidate_id = vote.get("candidateId")
                vote_counts[str(post_id)][candidate_id] += 1

        # Step 4: Build results with candidate names and vote counts
        results = {}

        for post_id in range(1, 8):
            post_id_str = str(post_id)
            candidates_list = candidates_by_post[post_id_str]["candidates"]

            post_name = {
                "1": "President",
                "2": "Vice President",
                "3": "General Secretary",
                "4": "Finance Secretary",
                "5": "Joint Secretary",
                "6": "Executive Member 1",
                "7": "Executive Member 2",
            }.get(post_id_str, f"Post {post_id_str}")

            candidates_result = []
            total_votes = 0

            for candidate in candidates_list:
                candidate_id = candidate.get("candidateId")
                votes = vote_counts[post_id_str].get(candidate_id, 0)

                candidates_result.append(
                    {
                        "candidateId": candidate_id,
                        "candidateName": candidate.get("name")
                        or candidate.get("candidateName", "Unknown"),
                        "votes": votes,
                    }
                )
                total_votes += votes

            # Sort candidates by votes (descending)
            candidates_result.sort(key=lambda x: x["votes"], reverse=True)

            results[post_id_str] = {
                "postName": post_name,
                "candidates": candidates_result,
                "totalVotes": total_votes,
            }

        log_event(
            "RESULTS_FETCHED",
            {
                "electionId": election_id,
                "electionName": election.get("electionName", "Unknown"),
            },
        )

        return success_response(
            {
                "electionId": election_id,
                "electionName": election.get("electionName", "Unknown"),
                "results": results,
                "timestamp": int(time.time()),
            }
        )

    except ValueError as ve:
        print(f"Configuration error: {str(ve)}")
        return error_response(500, "Server configuration error", "CONFIG_ERROR")

    except Exception as e:
        print(f"Unexpected error in get_results: {str(e)}")
        log_event("RESULTS_ERROR", {"error": str(e)})
        return error_response(500, "Internal server error", "INTERNAL_ERROR")
