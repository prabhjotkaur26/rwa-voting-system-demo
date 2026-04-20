import json
import os
import re
import hashlib
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple


def generate_otp(length: int = 6) -> str:
    """Generate a random OTP"""
    return "".join(random.choices(string.digits, k=length))


def hash_mobile_number(mobile_number: str) -> str:
    """Hash mobile number for privacy"""
    return hashlib.sha256(mobile_number.encode()).hexdigest()


def validate_mobile_number(mobile_number: str) -> bool:
    """
    Validate Indian mobile number format
    Accepts: 10-digit, with +91 prefix, or 0-prefix
    """
    # Remove any spaces
    mobile = mobile_number.strip()

    # Pattern for valid Indian mobile numbers
    patterns = [
        r"^\d{10}$",  # 10 digits
        r"^\+91\d{10}$",  # +91 followed by 10 digits
        r"^0\d{10}$",  # 0 followed by 10 digits
        r"^91\d{10}$",  # 91 followed by 10 digits
    ]

    return any(re.match(pattern, mobile) for pattern in patterns)


def normalize_mobile_number(mobile_number: str) -> str:
    """
    Normalize mobile number to standard format (10 digits)
    """
    mobile = mobile_number.strip()

    # Remove +91 or 91 or 0 prefix and keep only 10 digits
    if mobile.startswith("+91"):
        return mobile[3:]
    elif mobile.startswith("91"):
        return mobile[2:]
    elif mobile.startswith("0"):
        return mobile[1:]

    return mobile


def validate_otp(otp: str) -> bool:
    """Validate OTP format"""
    return bool(re.match(r"^\d{6}$", otp))


def create_response(
    status_code: int, body: Dict[str, Any], headers: Dict[str, str] = None
) -> Dict:
    """Create a formatted API response"""
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    }

    if headers:
        default_headers.update(headers)

    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps(body),
    }


def error_response(status_code: int, message: str, error_code: str = None) -> Dict:
    """Create an error response"""
    body = {
        "success": False,
        "message": message,
    }

    if error_code:
        body["errorCode"] = error_code

    return create_response(status_code, body)


def success_response(data: Dict[str, Any], status_code: int = 200) -> Dict:
    """Create a success response"""
    body = {
        "success": True,
        "data": data,
    }

    return create_response(status_code, body)


def get_env(key: str, default: str = None) -> str:
    """Get environment variable safely"""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Environment variable {key} not found")
    return value


def get_ttl_timestamp(minutes: int) -> int:
    """Get TTL timestamp for DynamoDB"""
    expiry_time = datetime.utcnow() + timedelta(minutes=minutes)
    return int(expiry_time.timestamp())


def mask_mobile_number(mobile_number: str) -> str:
    """Mask mobile number for display (show last 4 digits)"""
    mobile = normalize_mobile_number(mobile_number)
    if len(mobile) >= 4:
        return f"****{mobile[-4:]}"
    return "****"


def validate_election_id(election_id: str) -> bool:
    """Validate election ID format"""
    return bool(re.match(r"^[a-zA-Z0-9_-]{3,32}$", election_id))


def validate_post_id(post_id: str) -> bool:
    """Validate post ID (1-7 for 7 posts)"""
    try:
        post_num = int(post_id)
        return 1 <= post_num <= 7
    except ValueError:
        return False


def validate_candidate_id(candidate_id: str) -> bool:
    """Validate candidate ID format"""
    return bool(re.match(r"^[a-zA-Z0-9_-]{3,32}$", candidate_id))


def log_event(
    event_type: str, details: Dict[str, Any], sensitive: bool = False
) -> None:
    """Log events with sensitive data masking"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "details": details,
    }

    if sensitive and "mobileNumber" in details:
        details["mobileNumber"] = mask_mobile_number(details["mobileNumber"])

    print(json.dumps(log_entry))
