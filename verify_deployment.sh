#!/bin/bash

# ============================================================================
# RWA Voting System - Deployment Verification Script
# ============================================================================
# This script verifies all AWS resources have been deployed correctly

set -e

API_ENDPOINT="${1:?Usage: ./verify_deployment.sh <api-endpoint>}"

echo "=================================================="
echo "RWA Voting System - Deployment Verification"
echo "=================================================="
echo "API Endpoint: $API_ENDPOINT"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_code=$4
    local description=$5

    echo -n "Testing $description... "

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$API_ENDPOINT$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$API_ENDPOINT$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi

    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "$expected_code" ]; then
        echo -e "${GREEN}PASS${NC} (HTTP $http_code)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}FAIL${NC} (Expected HTTP $expected_code, got $http_code)"
        echo "Response: $body"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo "Step 1: Testing API Endpoints"
echo "==========================================="

# Test health (if implemented)
echo ""
echo "Authentication Endpoints:"
test_endpoint "POST" "/auth/send-otp" \
    '{"mobileNumber": "9876543210"}' \
    "200" "Send OTP"

test_endpoint "POST" "/auth/verify-otp" \
    '{"mobileNumber": "9876543210", "otp": "000000"}' \
    "400" "Verify OTP (invalid OTP expected)"

echo ""
echo "Election Management (Admin):"
current_time=$(date +%s)
end_time=$((current_time + 3600))

test_endpoint "POST" "/admin/elections" \
    "{\"electionId\": \"verify-test-$current_time\", \"electionName\": \"Verification Test\", \"startTime\": $current_time, \"endTime\": $end_time}" \
    "201" "Create Election"

echo ""
echo "Results Endpoint:"
test_endpoint "GET" "/results/verify-test-$current_time" \
    "" \
    "200" "Get Results"

echo ""
echo "Step 2: Verifying AWS Services"
echo "==========================================="

# Check Lambda functions
echo ""
echo "Lambda Functions:"
for func in send-otp verify-otp cast-vote get-results create-election add-candidates; do
    if aws lambda get-function --function-name rwa-voting-$func-prod --region ap-south-1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} rwa-voting-$func-prod"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} rwa-voting-$func-prod (not found)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
done

# Check DynamoDB tables
echo ""
echo "DynamoDB Tables:"
for table in votes otp candidates elections; do
    if aws dynamodb describe-table --table-name rwa-voting-$table-prod --region ap-south-1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} rwa-voting-$table-prod"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} rwa-voting-$table-prod (not found)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
done

# Check SNS topic
echo ""
echo "SNS Configuration:"
if aws sns list-topics --region ap-south-1 | grep -q "voting-otp-topic"; then
    echo -e "${GREEN}✓${NC} SNS topic configured"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠${NC} SNS topic not found (may not be configured)"
fi

echo ""
echo "=================================================="
echo "Summary"
echo "=================================================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! System is ready.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please review the issues above.${NC}"
    exit 1
fi
