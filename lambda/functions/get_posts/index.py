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
)
from aws_clients import DynamoDBClient


def lambda_handler(event, context):
    """
    Get election posts with candidate lists (only posts with >1 candidate)

    Request parameters:
    {
        "electionId": "election-2024-01"
    }

    Response:
    {
        "success": true,
        "data": {
            "posts": [
                {
                    "postId": "post-1",
                    "postName": "President",
                    "candidates": [
                        {
                            "candidateId": "cand-001",
                            "name": "John Doe",
                            "imageUrl": "https://...",
                            "party": "Party A"
                        }
                    ],
                    "candidateCount": 2
                }
            ]
        }
    }
    """
    try:
        # Get election ID from path parameters
        election_id = event.get("pathParameters", {}).get("electionId", "").strip()

        if not election_id:
            return error_response(400, "Election ID is required", "ELECTION_REQUIRED")

        # Get environment variables
        candidates_table_name = get_env("CANDIDATES_TABLE_NAME")
        aws_region = get_env("AWS_REGION", "ap-south-1")

        db_client = DynamoDBClient(region=aws_region)

        # Get all candidates for this election using SCAN with filter
        # (partition key is electionId#postId, so we need to scan and filter by election)
        candidates_response = db_client.scan(
            candidates_table_name,
            filter_expression="begins_with(#pk, :election)",
            expression_attribute_names={"#pk": "electionId#postId"},
            expression_attribute_values={":election": election_id},
        )

        if not candidates_response:
            return success_response({"posts": []})

        candidates_response = (
            candidates_response if isinstance(candidates_response, list) else []
        )

        # Group candidates by post
        posts_map = {}

        for candidate in candidates_response:
            election_post_id = candidate.get("electionId#postId", "")
            # Extract post ID (assumes format: electionId#postId)
            parts = election_post_id.split("#")
            if len(parts) == 2:
                post_id = parts[1]

                if post_id not in posts_map:
                    posts_map[post_id] = {
                        "postId": post_id,
                        "postName": get_post_name(post_id),
                        "candidates": [],
                    }

                posts_map[post_id]["candidates"].append(
                    {
                        "candidateId": candidate.get("candidateId"),
                        "name": candidate.get("name", ""),
                        "imageUrl": candidate.get("imageUrl", ""),
                        "party": candidate.get("party", ""),
                        "bio": candidate.get("bio", ""),
                    }
                )

        # Filter posts with >1 candidates and sort
        filtered_posts = [
            {
                **post,
                "candidateCount": len(post["candidates"]),
            }
            for post in posts_map.values()
            if len(post["candidates"]) > 1
        ]

        # Sort by post ID
        filtered_posts.sort(key=lambda x: x["postId"])

        log_event(
            "GET_POSTS",
            {
                "electionId": election_id,
                "totalPosts": len(posts_map),
                "electablePosts": len(filtered_posts),
            },
        )

        return success_response({"posts": filtered_posts})

    except Exception as e:
        print(f"Error in get_posts: {str(e)}")
        log_event("GET_POSTS_ERROR", {"error": str(e)})
        return error_response(500, "Internal server error", "INTERNAL_ERROR")


def get_post_name(post_id: str) -> str:
    """Map post ID to post name"""
    post_names = {
        "1": "President",
        "2": "Vice President",
        "3": "General Secretary",
        "4": "Finance Secretary",
        "5": "Joint Secretary",
        "6": "Executive Member 1",
        "7": "Executive Member 2",
        # Also handle post- prefix format
        "post-1": "President",
        "post-2": "Vice President",
        "post-3": "General Secretary",
        "post-4": "Finance Secretary",
        "post-5": "Joint Secretary",
        "post-6": "Executive Member 1",
        "post-7": "Executive Member 2",
    }
    return post_names.get(post_id, post_id)
