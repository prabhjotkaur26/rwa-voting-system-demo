# CORS and Elections Endpoint Fix

## Problem Analysis

### Error 1: CORS Policy Block
```
Access to fetch at 'https://vxvqzxd6rb.execute-api.ap-south-1.amazonaws.com/prod/elections' 
from origin 'http://rwa-voting-frontend-prod-750035244407.s3-website.ap-south-1.amazonaws.com' 
has been blocked by CORS policy
```

**Root Cause**: 404 error takes precedence over CORS checks in browsers.

### Error 2: 404 Not Found
```
GET https://vxvqzxd6rb.execute-api.ap-south-1.amazonaws.com/prod/elections net::ERR_FAILED 404
```

**Root Cause**: The API Gateway did NOT have a route for `GET /elections` (public endpoint)
- Existing route was `GET /admin/elections` (admin-only)
- Frontend was calling `/elections`
- This caused a 404, blocking the request before CORS headers could be returned

## Solution

### Fixed API Gateway Configuration

Added new public endpoint in `terraform/modules/api_gateway/main.tf`:

```hcl
# GET /elections - Public endpoint to list available elections
resource "aws_apigatewayv2_route" "get_elections_public_route" {
  api_id    = aws_apigatewayv2_api.voting_api.id
  route_key = "GET /elections"
  target    = "integrations/${aws_apigatewayv2_integration.get_elections_integration.id}"
}

# GET /admin/elections - Admin endpoint (deprecated, use /elections instead)
resource "aws_apigatewayv2_route" "get_elections_route" {
  api_id    = aws_apigatewayv2_api.voting_api.id
  route_key = "GET /admin/elections"
  target    = "integrations/${aws_apigatewayv2_integration.get_elections_integration.id}"
}
```

## API Routes Verified

All frontend API calls now have corresponding routes:

| Endpoint | Method | Status | Route |
|----------|--------|--------|-------|
| `/auth/send-otp` | POST | ✅ | POST /auth/send-otp |
| `/auth/verify-otp` | POST | ✅ | POST /auth/verify-otp |
| `/elections` | GET | ✅ FIXED | GET /elections |
| `/elections/{electionId}/posts` | GET | ✅ | GET /elections/{electionId}/posts |
| `/vote/cast-vote` | POST | ✅ | POST /vote/cast-vote |
| `/results/{electionId}` | GET | ✅ | GET /results/{electionId} |

## Deployment Steps

### 1. Navigate to Terraform directory
```bash
cd c:\PythonWork\rwa-voting-system\terraform
```

### 2. Plan the changes
```bash
terraform plan
```

### 3. Apply the changes
```bash
terraform apply -auto-approve
```

### 4. The output will show the updated API endpoint
```
Outputs:
api_endpoint = "https://vxvqzxd6rb.execute-api.ap-south-1.amazonaws.com/prod"
```

### 5. Test the endpoint (optional)
```bash
curl https://vxvqzxd6rb.execute-api.ap-south-1.amazonaws.com/prod/elections
```

## Why This Works

1. **CORS is already configured** in API Gateway with:
   - `allow_origins = ["*"]` (allows all origins)
   - Custom headers and methods allowed
   - Max age: 86400 seconds

2. **New route added** for `GET /elections` path
   - Uses same Lambda function as `/admin/elections`
   - Now publicly accessible to voters
   - CORS headers will be returned for valid routes

3. **No breaking changes**:
   - `/admin/elections` still works (backward compatibility)
   - Frontend code doesn't need changes
   - All other routes remain unchanged

## Expected Result

After deployment, when user verifies OTP:
1. ✅ Request to `/elections` returns 200 OK (not 404)
2. ✅ CORS headers included in response
3. ✅ Browser allows the response
4. ✅ Elections list displays in UI
5. ✅ Voting workflow continues normally
