import json
import sys
import os
import hmac
import hashlib
from datetime import datetime, timedelta, timezone

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from utils import (
    create_response,
    error_response,
    success_response,
    get_env,
    log_event,
)


def get_ist_timestamp():
    """Get current timestamp in IST timezone"""
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist)


def lambda_handler(event, context):
    """
    Admin login authentication

    Request body:
    {
        "username": "admin",
        "password": "secure-password"
    }

    Response:
    {
        "success": true,
        "data": {
            "token": "generated-jwt-token",
            "expiresIn": 3600,
            "adminId": "admin-user-id"
        }
    }
    """
    try:
        # Parse request
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return error_response(400, "Invalid JSON in request body", "INVALID_JSON")

        username = body.get("username", "").strip()
        password = body.get("password", "").strip()

        # Validate inputs
        if not username:
            return error_response(400, "Username is required", "USERNAME_REQUIRED")

        if not password:
            return error_response(400, "Password is required", "PASSWORD_REQUIRED")

        # Get environment variables
        admin_username = get_env("ADMIN_USERNAME", "admin")
        admin_password_hash = get_env("ADMIN_PASSWORD_HASH", "")
        jwt_secret = get_env("JWT_SECRET", "rwa-voting-secret-key")
        token_expiry_hours = int(get_env("ADMIN_TOKEN_EXPIRY_HOURS", "24"))

        # Validate credentials against environment variables
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        if username != admin_username:
            log_event(
                "ADMIN_LOGIN_FAILED",
                {
                    "username": username,
                    "reason": "invalid_username",
                    "timestamp": get_ist_timestamp().isoformat(),
                },
            )
            return error_response(
                401, "Invalid username or password", "INVALID_CREDENTIALS"
            )

        # Check password (compare hashes)
        if not admin_password_hash:
            # If no hash is set in environment, use default password
            # In production, this should ALWAYS be set via environment variable
            default_hash = hashlib.sha256(b"Admin@123").hexdigest()
            if password_hash != default_hash:
                log_event(
                    "ADMIN_LOGIN_FAILED",
                    {
                        "username": username,
                        "reason": "invalid_password",
                        "timestamp": get_ist_timestamp().isoformat(),
                    },
                )
                return error_response(
                    401, "Invalid username or password", "INVALID_CREDENTIALS"
                )
        else:
            if password_hash != admin_password_hash:
                log_event(
                    "ADMIN_LOGIN_FAILED",
                    {
                        "username": username,
                        "reason": "invalid_password",
                        "timestamp": get_ist_timestamp().isoformat(),
                    },
                )
                return error_response(
                    401, "Invalid username or password", "INVALID_CREDENTIALS"
                )

        # Generate JWT token (simple implementation)
        # In production, use PyJWT library
        token_data = {
            "username": username,
            "adminId": "admin-001",
            "iat": int(get_ist_timestamp().timestamp()),
            "exp": int(
                (get_ist_timestamp() + timedelta(hours=token_expiry_hours)).timestamp()
            ),
        }

        # Create simple token (in production, use proper JWT)
        token = create_simple_token(token_data, jwt_secret)

        log_event(
            "ADMIN_LOGIN_SUCCESS",
            {
                "username": username,
                "adminId": "admin-001",
                "timestamp": get_ist_timestamp().isoformat(),
            },
        )

        return success_response(
            {
                "message": "Login successful",
                "token": token,
                "adminId": "admin-001",
                "username": username,
                "expiresIn": token_expiry_hours * 3600,
            }
        )

    except Exception as e:
        log_event(
            "ADMIN_LOGIN_ERROR",
            {
                "error": str(e),
                "timestamp": get_ist_timestamp().isoformat(),
            },
        )
        return error_response(500, f"Internal server error: {str(e)}", "SERVER_ERROR")


def create_simple_token(data: dict, secret: str) -> str:
    """
    Create a simple token using HMAC
    Note: Use PyJWT in production for proper JWT implementation

    Token format: data.signature
    """
    import json
    import base64

    # Encode data as JSON and convert to base64
    data_json = json.dumps(data, sort_keys=True)
    data_b64 = base64.urlsafe_b64encode(data_json.encode()).decode().rstrip("=")

    # Create signature using HMAC-SHA256
    signature = hmac.new(secret.encode(), data_b64.encode(), hashlib.sha256).hexdigest()

    # Combine data and signature
    token = f"{data_b64}.{signature}"

    return token


def verify_token(token: str, secret: str) -> dict:
    """
    Verify token and return payload
    Returns None if token is invalid or expired
    """
    import json
    import base64

    try:
        # Split token
        parts = token.split(".")
        if len(parts) != 2:
            return None

        data_b64, signature = parts

        # Verify signature
        expected_signature = hmac.new(
            secret.encode(), data_b64.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            return None

        # Decode data
        padding = 4 - (len(data_b64) % 4)
        data_b64 += "=" * padding
        data_json = base64.urlsafe_b64decode(data_b64).decode()
        data = json.loads(data_json)

        # Check expiration
        current_time = int(get_ist_timestamp().timestamp())
        if data.get("exp", 0) < current_time:
            return None

        return data

    except Exception as e:
        print(f"Token verification error: {str(e)}")
        return None
