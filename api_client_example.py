#!/usr/bin/env python3
"""
API Quick Reference - Python Client
Demonstrates how to interact with the RWA Voting API

Usage:
    python3 api_client_example.py
"""

import requests
import json
import time
from typing import Dict, Any


class RWAVotingClient:
    """Simple client for RWA Voting API"""

    def __init__(self, api_endpoint: str):
        """Initialize with API endpoint"""
        self.api_endpoint = api_endpoint.rstrip("/")
        self.session = requests.Session()
        self.auth_token = None

    def _make_request(
        self, method: str, endpoint: str, data: Dict = None
    ) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.api_endpoint}/{endpoint}"
        headers = {"Content-Type": "application/json"}

        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        try:
            if method == "GET":
                response = self.session.get(url, headers=headers)
            elif method == "POST":
                response = self.session.post(url, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_otp(self, mobile_number: str) -> Dict[str, Any]:
        """Request OTP"""
        return self._make_request(
            "POST", "auth/send-otp", {"mobileNumber": mobile_number}
        )

    def verify_otp(self, mobile_number: str, otp: str) -> Dict[str, Any]:
        """Verify OTP and get auth token"""
        result = self._make_request(
            "POST", "auth/verify-otp", {"mobileNumber": mobile_number, "otp": otp}
        )

        if result.get("success") and "token" in result.get("data", {}):
            self.auth_token = result["data"]["token"]

        return result

    def cast_vote(
        self, election_id: str, post_id: str, candidate_id: str
    ) -> Dict[str, Any]:
        """Cast a vote"""
        return self._make_request(
            "POST",
            "vote/cast-vote",
            {"electionId": election_id, "postId": post_id, "candidateId": candidate_id},
        )

    def get_results(self, election_id: str) -> Dict[str, Any]:
        """Get election results"""
        return self._make_request("GET", f"results/{election_id}")

    def create_election(
        self, election_id: str, name: str, start_time: str, end_time: str
    ) -> Dict[str, Any]:
        """Create new election (admin only)"""
        return self._make_request(
            "POST",
            "elections/create",
            {
                "electionId": election_id,
                "name": name,
                "startTime": start_time,
                "endTime": end_time,
            },
        )

    def add_candidates(
        self, election_id: str, post_id: str, candidates: list
    ) -> Dict[str, Any]:
        """Add candidates to post"""
        return self._make_request(
            "POST",
            "elections/add-candidates",
            {"electionId": election_id, "postId": post_id, "candidates": candidates},
        )


# ============================================================================
# Quick Reference Examples
# ============================================================================


def example_basic_flow():
    """Complete voting flow example"""

    # Configure API endpoint
    API_ENDPOINT = "https://your-api-id.execute-api.ap-south-1.amazonaws.com/prod"
    client = RWAVotingClient(API_ENDPOINT)

    print("=" * 60)
    print("RWA VOTING SYSTEM - API QUICK REFERENCE")
    print("=" * 60)
    print()

    # Step 1: Send OTP
    print("1️⃣  SEND OTP")
    print("-" * 60)
    mobile = "9876543210"
    response = client.send_otp(mobile)
    print(f"Request: POST /auth/send-otp")
    print(f"Data: {{'mobileNumber': '{mobile}'}}")
    print(f"Response: {json.dumps(response, indent=2)}")
    print()

    # Step 2: Verify OTP (simulated)
    print("2️⃣  VERIFY OTP")
    print("-" * 60)
    otp = "123456"  # Would receive via SMS in real scenario
    response = client.verify_otp(mobile, otp)
    print(f"Request: POST /auth/verify-otp")
    print(f"Data: {{'mobileNumber': '{mobile}', 'otp': '{otp}'}}")
    print(f"Response: {json.dumps(response, indent=2)}")
    print()

    # Step 3: Cast Vote
    print("3️⃣  CAST VOTE")
    print("-" * 60)
    vote_data = {
        "electionId": "election-2024-01",
        "postId": "post-1",
        "candidateId": "cand-001",
    }
    response = client.cast_vote(**vote_data)
    print(f"Request: POST /vote/cast-vote")
    print(f"Data: {json.dumps(vote_data, indent=2)}")
    print(f"Response: {json.dumps(response, indent=2)}")
    print()

    # Step 4: Get Results
    print("4️⃣  GET RESULTS")
    print("-" * 60)
    response = client.get_results("election-2024-01")
    print(f"Request: GET /results/election-2024-01")
    print(f"Response (truncated):")
    if response.get("success"):
        print(f"  - Total posts: {len(response.get('data', {}).get('posts', []))}")
        print(f"  - Posts data available")
    print(f"Full Response: {json.dumps(response, indent=2)[:500]}...")
    print()


def example_curl_commands():
    """cURL command examples"""

    API = "https://your-api-id.execute-api.ap-south-1.amazonaws.com/prod"

    print("=" * 60)
    print("CURL COMMAND EXAMPLES")
    print("=" * 60)
    print()

    print("1. SEND OTP:")
    print(
        f"""curl -X POST {API}/auth/send-otp \\
  -H "Content-Type: application/json" \\
  -d '{{"mobileNumber": "9876543210"}}'
"""
    )

    print("2. VERIFY OTP:")
    print(
        f"""curl -X POST {API}/auth/verify-otp \\
  -H "Content-Type: application/json" \\
  -d '{{"mobileNumber": "9876543210", "otp": "123456"}}'
"""
    )

    print("3. CAST VOTE:")
    print(
        f"""curl -X POST {API}/vote/cast-vote \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -d '{{
    "electionId": "election-2024-01",
    "postId": "post-1", 
    "candidateId": "cand-001"
  }}'
"""
    )

    print("4. GET RESULTS:")
    print(
        f"""curl -X GET {API}/results/election-2024-01 \\
  -H "Content-Type: application/json"
"""
    )


def example_postman_collection():
    """Generate Postman collection JSON"""

    collection = {
        "info": {
            "name": "RWA Voting API",
            "description": "Complete API for RWA voting system",
            "version": "1.0.0",
        },
        "item": [
            {
                "name": "Send OTP",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {"mode": "raw", "raw": '{"mobileNumber": "9876543210"}'},
                    "url": {
                        "raw": "{{api_url}}/auth/send-otp",
                        "path": ["auth", "send-otp"],
                    },
                },
            },
            {
                "name": "Verify OTP",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {
                        "mode": "raw",
                        "raw": '{"mobileNumber": "9876543210", "otp": "123456"}',
                    },
                    "url": {
                        "raw": "{{api_url}}/auth/verify-otp",
                        "path": ["auth", "verify-otp"],
                    },
                },
            },
            {
                "name": "Cast Vote",
                "request": {
                    "method": "POST",
                    "header": [
                        {"key": "Content-Type", "value": "application/json"},
                        {"key": "Authorization", "value": "Bearer {{auth_token}}"},
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": '{"electionId": "election-2024-01", "postId": "post-1", "candidateId": "cand-001"}',
                    },
                    "url": {
                        "raw": "{{api_url}}/vote/cast-vote",
                        "path": ["vote", "cast-vote"],
                    },
                },
            },
            {
                "name": "Get Results",
                "request": {
                    "method": "GET",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "url": {
                        "raw": "{{api_url}}/results/election-2024-01",
                        "path": ["results", "election-2024-01"],
                    },
                },
            },
        ],
        "variable": [
            {
                "key": "api_url",
                "value": "https://your-api-id.execute-api.ap-south-1.amazonaws.com/prod",
            },
            {"key": "auth_token", "value": ""},
        ],
    }

    return collection


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--curl":
        example_curl_commands()
    elif len(sys.argv) > 1 and sys.argv[1] == "--postman":
        collection = example_postman_collection()
        print(json.dumps(collection, indent=2))
    else:
        # Print instructions
        print("RWA VOTING API - Python Client Example")
        print()
        print("Description:")
        print("  This script demonstrates how to use the RWA Voting API")
        print()
        print("Usage:")
        print("  1. Regular output (example flow):")
        print("     python3 api_client_example.py")
        print()
        print("  2. cURL commands:")
        print("     python3 api_client_example.py --curl")
        print()
        print("  3. Postman collection (JSON):")
        print("     python3 api_client_example.py --postman")
        print()
        print("Setup:")
        print("  1. Update API_ENDPOINT with your AWS API Gateway URL")
        print("  2. Install requests: pip install requests")
        print("  3. Run the examples")
        print()
        print("For more details, see docs/API_DESIGN.md")
