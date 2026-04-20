import json
import sys
import os
import csv
import io
from datetime import datetime, timezone, timedelta

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
    """Get current datetime in IST timezone"""
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist)


def lambda_handler(event, context):
    """
    Export election results in CSV format

    Request parameters:
    {
        "electionId": "election-2024-01",
        "format": "csv"  # or "json"
    }

    Response:
    {
        "success": true,
        "data": {
            "filename": "election-2024-01-results.csv",
            "content": "Post,Candidate,Votes\n..."
        }
    }
    """
    try:
        # Get parameters
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            body = {}

        election_id = (
            body.get("electionId")
            or event.get("pathParameters", {}).get("electionId", "")
        ).strip()

        export_format = body.get("format", "html").lower()

        if not election_id:
            return error_response(400, "Election ID is required", "ELECTION_REQUIRED")

        if export_format not in ["csv", "json", "html"]:
            return error_response(
                400, "Format must be 'csv', 'json', or 'html'", "INVALID_FORMAT"
            )

        # Get environment variables
        votes_table_name = get_env("VOTES_TABLE_NAME")
        candidates_table_name = get_env("CANDIDATES_TABLE_NAME")
        aws_region = get_env("AWS_REGION", "ap-south-1")

        db_client = DynamoDBClient(region=aws_region)

        # Get all candidates for this election using scan with filter
        candidates_response = db_client.scan(
            candidates_table_name,
            filter_expression="begins_with(#pk, :election)",
            expression_attribute_names={"#pk": "electionId#postId"},
            expression_attribute_values={":election": election_id},
        )

        candidates_response = (
            candidates_response if isinstance(candidates_response, list) else []
        )

        # Group candidates by post
        posts_data = {}

        for candidate in candidates_response:
            election_post_id = candidate.get("electionId#postId", "")
            parts = election_post_id.split("#")
            if len(parts) == 2:
                post_id = parts[1]

                if post_id not in posts_data:
                    posts_data[post_id] = {
                        "postName": get_post_name(post_id),
                        "candidates": {},
                    }

                candidate_name = candidate.get("name", "Unknown")
                posts_data[post_id]["candidates"][candidate.get("candidateId")] = {
                    "name": candidate_name,
                    "votes": 0,
                }

        # Get all votes for this election using scan with filter
        votes_response = db_client.scan(
            votes_table_name,
            filter_expression="begins_with(#pk, :election)",
            expression_attribute_names={"#pk": "electionId#postId"},
            expression_attribute_values={":election": election_id},
        )

        votes_response = votes_response if isinstance(votes_response, list) else []

        # Count votes by candidate
        for vote in votes_response:
            election_post_id = vote.get("electionId#postId", "")
            candidate_id = vote.get("candidateId", "")
            parts = election_post_id.split("#")

            if len(parts) == 2:
                post_id = parts[1]

                if (
                    post_id in posts_data
                    and candidate_id in posts_data[post_id]["candidates"]
                ):
                    posts_data[post_id]["candidates"][candidate_id]["votes"] += 1

        # Generate output based on format
        if export_format == "csv":
            content = generate_csv(posts_data)
            filename = (
                f"{election_id}-results-{get_ist_timestamp().strftime('%Y%m%d_%H%M%S')}.csv"
            )
        elif export_format == "json":
            content = generate_json(posts_data)
            filename = (
                f"{election_id}-results-{get_ist_timestamp().strftime('%Y%m%d_%H%M%S')}.json"
            )
        else:  # html
            content = generate_html(posts_data)
            filename = (
                f"{election_id}-results-{get_ist_timestamp().strftime('%Y%m%d_%H%M%S')}.html"
            )

        log_event(
            "RESULTS_EXPORTED",
            {
                "electionId": election_id,
                "format": export_format,
                "totalPosts": len(posts_data),
                "filename": filename,
            },
        )

        return success_response(
            {
                "filename": filename,
                "content": content,
                "format": export_format,
                "timestamp": get_ist_timestamp().isoformat(),
            }
        )

    except Exception as e:
        print(f"Error in export_results: {str(e)}")
        log_event("EXPORT_RESULTS_ERROR", {"error": str(e)})
        return error_response(500, "Internal server error", "INTERNAL_ERROR")


def generate_csv(posts_data: dict) -> str:
    """Generate CSV format results"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["Post", "Candidate", "Votes"])

    # Data rows
    for post_id in sorted(posts_data.keys()):
        post = posts_data[post_id]
        post_name = post["postName"]

        # Sort candidates by votes (descending)
        sorted_candidates = sorted(
            post["candidates"].items(),
            key=lambda x: x[1]["votes"],
            reverse=True,
        )

        for candidate_id, candidate_data in sorted_candidates:
            writer.writerow(
                [
                    post_name,
                    candidate_data["name"],
                    candidate_data["votes"],
                ]
            )

    return output.getvalue()


def generate_json(posts_data: dict) -> str:
    """Generate JSON format results"""
    output = {}

    for post_id in sorted(posts_data.keys()):
        post = posts_data[post_id]

        # Sort candidates by votes (descending)
        sorted_candidates = sorted(
            post["candidates"].items(),
            key=lambda x: x[1]["votes"],
            reverse=True,
        )

        output[post["postName"]] = [
            {
                "candidateId": candidate_id,
                "name": candidate_data["name"],
                "votes": candidate_data["votes"],
            }
            for candidate_id, candidate_data in sorted_candidates
        ]

    return json.dumps(output, indent=2)


def generate_html(posts_data: dict) -> str:
    """Generate HTML format results for PDF export"""
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Election Results</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            color: #333;
        }
        h1 {
            text-align: center;
            color: #2c3e50;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        .post-section {
            margin-top: 30px;
            page-break-inside: avoid;
            border-left: 4px solid #667eea;
            padding-left: 15px;
        }
        .post-name {
            font-size: 20px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 15px;
        }
        .total-votes {
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
        }
        .candidate-row {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #eee;
            align-items: center;
        }
        .candidate-name {
            font-weight: 500;
            flex-grow: 1;
        }
        .vote-count {
            background: #f0f0f0;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            color: #667eea;
        }
        .progress-bar {
            background: #e2e8f0;
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 8px;
            flex-grow: 1;
            margin-right: 10px;
        }
        .progress-fill {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            height: 100%;
            transition: width 0.3s ease;
        }
        .timestamp {
            text-align: center;
            color: #999;
            font-size: 12px;
            margin-top: 40px;
            border-top: 1px solid #ddd;
            padding-top: 20px;
        }
        @media print {
            body { margin: 0; }
            .post-section { page-break-inside: avoid; }
        }
    </style>
</head>
<body>
    <h1>Election Results</h1>
"""

    # Generate content for each post
    for post_id in sorted(posts_data.keys()):
        post = posts_data[post_id]
        post_name = post["postName"]
        total_votes = sum(c["votes"] for c in post["candidates"].values())

        # Sort candidates by votes (descending)
        sorted_candidates = sorted(
            post["candidates"].items(),
            key=lambda x: x[1]["votes"],
            reverse=True,
        )

        html += f"""    <div class="post-section">
        <div class="post-name">{post_id}. {post_name}</div>
        <div class="total-votes">Total Votes: {total_votes}</div>
"""

        # Calculate max votes for progress bar
        max_votes = (
            max([c["votes"] for c in post["candidates"].values()])
            if sorted_candidates
            else 1
        )

        for candidate_id, candidate_data in sorted_candidates:
            votes = candidate_data["votes"]
            percentage = (votes / max_votes * 100) if max_votes > 0 else 0

            html += f"""        <div class="candidate-row">
            <div style="flex-grow: 1;">
                <div class="candidate-name">{candidate_data["name"]}</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {percentage}%;"></div>
                </div>
            </div>
            <div class="vote-count">{votes}</div>
        </div>
"""

        html += "    </div>\n"

    html += f"""    <div class="timestamp">
        Generated on: {get_ist_timestamp().strftime('%d-%m-%Y %H:%M:%S IST')}
    </div>
</body>
</html>"""

    return html


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
