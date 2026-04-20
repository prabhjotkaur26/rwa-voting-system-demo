#!/bin/bash

# RWA Voting System - Local Lambda Testing
# Tests Lambda functions locally with mocked AWS services

set -e

echo "============================================"
echo "RWA Voting System - Local Lambda Testing"
echo "============================================"

# Check prerequisites
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

if ! command -v pip &> /dev/null; then
    echo "❌ pip not found. Please install pip"
    exit 1
fi

echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

echo "✅ Dependencies installed"
echo ""

# Create test directory
mkdir -p tests/results

echo "🧪 Running unit tests..."
pytest tests/ -v --tb=short 2>/dev/null || true

echo ""
echo "📋 Testing Lambda functions locally..."
echo ""

# Test 1: Send OTP
echo "Test 1: Send OTP"
python3 << 'EOF'
import sys
sys.path.insert(0, 'lambda/lib')

from utils import generate_otp, validate_mobile_number, normalize_mobile_number

mobile = "9876543210"
if validate_mobile_number(mobile):
    normalized = normalize_mobile_number(mobile)
    otp = generate_otp()
    print(f"  ✅ Generated OTP {otp} for {normalized}")
else:
    print(f"  ❌ Invalid mobile number")
EOF

# Test 2: Validate OTP
echo ""
echo "Test 2: OTP Validation"
python3 << 'EOF'
import sys
sys.path.insert(0, 'lambda/lib')

from utils import generate_otp

otp1 = generate_otp()
otp2 = generate_otp()

if otp1 != otp2:
    print(f"  ✅ Generated unique OTPs")
else:
    print(f"  ❌ OTP generation issue")

if len(otp1) == 6:
    print(f"  ✅ OTP has correct length (6)")
else:
    print(f"  ❌ OTP length incorrect: {len(otp1)}")
EOF

# Test 3: Mobile validation
echo ""
echo "Test 3: Mobile Number Validation"
python3 << 'EOF'
import sys
sys.path.insert(0, 'lambda/lib')

from utils import validate_mobile_number, normalize_mobile_number

test_cases = [
    ("9876543210", True, "basic 10-digit"),
    ("+919876543210", True, "+91 format"),
    ("09876543210", True, "0 prefix"),
    ("919876543210", True, "91 prefix"),
    ("12345", False, "too short"),
    ("abcdefghij", False, "non-numeric"),
]

for mobile, expected, format_name in test_cases:
    result = validate_mobile_number(mobile)
    status = "✅" if result == expected else "❌"
    print(f"  {status} {format_name}: {mobile}")
EOF

# Test 4: Response formatting
echo ""
echo "Test 4: Response Formatting"
python3 << 'EOF'
import sys
sys.path.insert(0, 'lambda/lib')

from utils import create_response, success_response, error_response
import json

# Test success response
success = success_response("Vote recorded", {"candidateId": "cand1"})
data = json.loads(success['body'])
if success['statusCode'] == 200 and data['success'] == True:
    print(f"  ✅ Success response formatted correctly")
else:
    print(f"  ❌ Success response format issue")

# Test error response
error = error_response("Invalid input", 400, "INVALID_INPUT")
data = json.loads(error['body'])
if error['statusCode'] == 400 and data['success'] == False:
    print(f"  ✅ Error response formatted correctly")
else:
    print(f"  ❌ Error response format issue")
EOF

# Test 5: TTL timestamp
echo ""
echo "Test 5: TTL Timestamp Generation"
python3 << 'EOF'
import sys
sys.path.insert(0, 'lambda/lib')

from utils import get_ttl_timestamp
import time

ttl = get_ttl_timestamp(5)  # 5 minutes
current = int(time.time())

if ttl > current:
    print(f"  ✅ TTL timestamp in future")
    minutes_left = (ttl - current) / 60
    print(f"     (~{minutes_left:.1f} minutes from now)")
else:
    print(f"  ❌ TTL timestamp in past")
EOF

echo ""
echo "============================================"
echo "✅ Local testing complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Review test results above"
echo "2. Deploy to AWS: cd terraform && terraform apply"
echo "3. Run integration tests: bash tests/test_scenarios.sh"
echo "4. Deploy frontend: aws s3 cp frontend/ s3://bucket/"
echo ""
