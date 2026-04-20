variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "send_otp_function_arn" {
  type = string
}

variable "send_otp_function_name" {
  type = string
}

variable "verify_otp_function_arn" {
  type = string
}

variable "verify_otp_function_name" {
  type = string
}

variable "cast_vote_function_arn" {
  type = string
}

variable "cast_vote_function_name" {
  type = string
}

variable "get_results_function_arn" {
  type = string
}

variable "get_results_function_name" {
  type = string
}

variable "create_election_function_arn" {
  type = string
}

variable "create_election_function_name" {
  type = string
}

variable "add_candidates_function_arn" {
  type = string
}

variable "add_candidates_function_name" {
  type = string
}

variable "get_posts_function_arn" {
  type = string
}

variable "get_posts_function_name" {
  type = string
}

variable "export_results_function_arn" {
  type = string
}

variable "export_results_function_name" {
  type = string
}

variable "bulk_upload_voters_function_arn" {
  type = string
}

variable "bulk_upload_voters_function_name" {
  type = string
}

variable "admin_login_function_arn" {
  type = string
}

variable "admin_login_function_name" {
  type = string
}

variable "admin_stats_function_arn" {
  type = string
}

variable "admin_stats_function_name" {
  type = string
}

variable "get_elections_function_arn" {
  type = string
}

variable "get_elections_function_name" {
  type = string
}

variable "get_candidates_function_arn" {
  type = string
}

variable "get_candidates_function_name" {
  type = string
}

variable "throttling_burst_limit" {
  type = number
}

variable "throttling_rate_limit" {
  type = number
}

variable "enable_cors" {
  type = bool
}

variable "allowed_origins" {
  type = list(string)
}

# HTTP API (more cost-effective than REST API)
resource "aws_apigatewayv2_api" "voting_api" {
  name          = "${var.project_name}-voting-api-${var.environment}"
  protocol_type = "HTTP"

  cors_configuration {
    allow_credentials = false
    allow_headers     = ["content-type", "x-amz-date", "authorization", "x-api-key", "x-amz-security-token"]
    allow_methods     = ["*"]
    allow_origins     = var.allowed_origins
    expose_headers    = ["date", "x-amzn-requestid"]
    max_age           = 86400
  }
}

# Stage
resource "aws_apigatewayv2_stage" "voting_api_stage" {
  api_id      = aws_apigatewayv2_api.voting_api.id
  name        = var.environment
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      timestamp      = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      integrationLatency = "$context.integration.latency"
    })
  }
}

# CloudWatch log group for API logs
resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/apigateway/${var.project_name}-${var.environment}"
  retention_in_days = 7
}

# Lambda permissions for API Gateway
resource "aws_lambda_permission" "api_gateway_send_otp" {
  statement_id  = "AllowAPIGatewaySendOTP"
  action        = "lambda:InvokeFunction"
  function_name = var.send_otp_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.voting_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_verify_otp" {
  statement_id  = "AllowAPIGatewayVerifyOTP"
  action        = "lambda:InvokeFunction"
  function_name = var.verify_otp_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.voting_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_cast_vote" {
  statement_id  = "AllowAPIGatewayCastVote"
  action        = "lambda:InvokeFunction"
  function_name = var.cast_vote_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.voting_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_get_results" {
  statement_id  = "AllowAPIGatewayGetResults"
  action        = "lambda:InvokeFunction"
  function_name = var.get_results_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.voting_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_create_election" {
  statement_id  = "AllowAPIGatewayCreateElection"
  action        = "lambda:InvokeFunction"
  function_name = var.create_election_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.voting_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_add_candidates" {
  statement_id  = "AllowAPIGatewayAddCandidates"
  action        = "lambda:InvokeFunction"
  function_name = var.add_candidates_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.voting_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_get_posts" {
  statement_id  = "AllowAPIGatewayGetPosts"
  action        = "lambda:InvokeFunction"
  function_name = var.get_posts_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.voting_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_export_results" {
  statement_id  = "AllowAPIGatewayExportResults"
  action        = "lambda:InvokeFunction"
  function_name = var.export_results_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.voting_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_bulk_upload_voters" {
  statement_id  = "AllowAPIGatewayBulkUploadVoters"
  action        = "lambda:InvokeFunction"
  function_name = var.bulk_upload_voters_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.voting_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_admin_login" {
  statement_id  = "AllowAPIGatewayAdminLogin"
  action        = "lambda:InvokeFunction"
  function_name = var.admin_login_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.voting_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_admin_stats" {
  statement_id  = "AllowAPIGatewayAdminStats"
  action        = "lambda:InvokeFunction"
  function_name = var.admin_stats_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.voting_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_get_elections" {
  statement_id  = "AllowAPIGatewayGetElections"
  action        = "lambda:InvokeFunction"
  function_name = var.get_elections_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.voting_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_get_candidates" {
  statement_id  = "AllowAPIGatewayGetCandidates"
  action        = "lambda:InvokeFunction"
  function_name = var.get_candidates_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.voting_api.execution_arn}/*/*"
}

# API Routes and Integrations
# POST /auth/send-otp
resource "aws_apigatewayv2_integration" "send_otp_integration" {
  api_id             = aws_apigatewayv2_api.voting_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = var.send_otp_function_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "send_otp_route" {
  api_id    = aws_apigatewayv2_api.voting_api.id
  route_key = "POST /auth/send-otp"
  target    = "integrations/${aws_apigatewayv2_integration.send_otp_integration.id}"
}

# POST /auth/verify-otp
resource "aws_apigatewayv2_integration" "verify_otp_integration" {
  api_id             = aws_apigatewayv2_api.voting_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = var.verify_otp_function_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "verify_otp_route" {
  api_id    = aws_apigatewayv2_api.voting_api.id
  route_key = "POST /auth/verify-otp"
  target    = "integrations/${aws_apigatewayv2_integration.verify_otp_integration.id}"
}

# POST /vote/cast-vote
resource "aws_apigatewayv2_integration" "cast_vote_integration" {
  api_id             = aws_apigatewayv2_api.voting_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = var.cast_vote_function_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "cast_vote_route" {
  api_id    = aws_apigatewayv2_api.voting_api.id
  route_key = "POST /vote/cast-vote"
  target    = "integrations/${aws_apigatewayv2_integration.cast_vote_integration.id}"
}

# GET /results/{electionId}
resource "aws_apigatewayv2_integration" "get_results_integration" {
  api_id             = aws_apigatewayv2_api.voting_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = var.get_results_function_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "get_results_route" {
  api_id    = aws_apigatewayv2_api.voting_api.id
  route_key = "GET /results/{electionId}"
  target    = "integrations/${aws_apigatewayv2_integration.get_results_integration.id}"
}

# POST /admin/elections
resource "aws_apigatewayv2_integration" "create_election_integration" {
  api_id             = aws_apigatewayv2_api.voting_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = var.create_election_function_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "create_election_route" {
  api_id    = aws_apigatewayv2_api.voting_api.id
  route_key = "POST /admin/elections"
  target    = "integrations/${aws_apigatewayv2_integration.create_election_integration.id}"
}

# POST /admin/candidates
resource "aws_apigatewayv2_integration" "add_candidates_integration" {
  api_id             = aws_apigatewayv2_api.voting_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = var.add_candidates_function_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "add_candidates_route" {
  api_id    = aws_apigatewayv2_api.voting_api.id
  route_key = "POST /admin/candidates"
  target    = "integrations/${aws_apigatewayv2_integration.add_candidates_integration.id}"
}

# GET /elections/{electionId}/posts
resource "aws_apigatewayv2_integration" "get_posts_integration" {
  api_id             = aws_apigatewayv2_api.voting_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = var.get_posts_function_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "get_posts_route" {
  api_id    = aws_apigatewayv2_api.voting_api.id
  route_key = "GET /elections/{electionId}/posts"
  target    = "integrations/${aws_apigatewayv2_integration.get_posts_integration.id}"
}

# POST /results/{electionId}/export
resource "aws_apigatewayv2_integration" "export_results_integration" {
  api_id             = aws_apigatewayv2_api.voting_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = var.export_results_function_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "export_results_route" {
  api_id    = aws_apigatewayv2_api.voting_api.id
  route_key = "POST /results/{electionId}/export"
  target    = "integrations/${aws_apigatewayv2_integration.export_results_integration.id}"
}

# POST /admin/voters/bulk-upload
resource "aws_apigatewayv2_integration" "bulk_upload_voters_integration" {
  api_id             = aws_apigatewayv2_api.voting_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = var.bulk_upload_voters_function_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "bulk_upload_voters_route" {
  api_id    = aws_apigatewayv2_api.voting_api.id
  route_key = "POST /admin/voters/bulk-upload"
  target    = "integrations/${aws_apigatewayv2_integration.bulk_upload_voters_integration.id}"
}

# POST /admin/auth/login
resource "aws_apigatewayv2_integration" "admin_login_integration" {
  api_id             = aws_apigatewayv2_api.voting_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = var.admin_login_function_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "admin_login_route" {
  api_id    = aws_apigatewayv2_api.voting_api.id
  route_key = "POST /admin/auth/login"
  target    = "integrations/${aws_apigatewayv2_integration.admin_login_integration.id}"
}

# GET /admin/stats
resource "aws_apigatewayv2_integration" "admin_stats_integration" {
  api_id             = aws_apigatewayv2_api.voting_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = var.admin_stats_function_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "admin_stats_route" {
  api_id    = aws_apigatewayv2_api.voting_api.id
  route_key = "GET /admin/stats"
  target    = "integrations/${aws_apigatewayv2_integration.admin_stats_integration.id}"
}

# GET /elections - Public endpoint and admin endpoint
resource "aws_apigatewayv2_integration" "get_elections_integration" {
  api_id             = aws_apigatewayv2_api.voting_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = var.get_elections_function_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "get_elections_public_route" {
  api_id    = aws_apigatewayv2_api.voting_api.id
  route_key = "GET /elections"
  target    = "integrations/${aws_apigatewayv2_integration.get_elections_integration.id}"
}

resource "aws_apigatewayv2_route" "get_elections_route" {
  api_id    = aws_apigatewayv2_api.voting_api.id
  route_key = "GET /admin/elections"
  target    = "integrations/${aws_apigatewayv2_integration.get_elections_integration.id}"
}

# GET /admin/candidates
resource "aws_apigatewayv2_integration" "get_candidates_integration" {
  api_id             = aws_apigatewayv2_api.voting_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = var.get_candidates_function_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "get_candidates_route" {
  api_id    = aws_apigatewayv2_api.voting_api.id
  route_key = "GET /admin/candidates"
  target    = "integrations/${aws_apigatewayv2_integration.get_candidates_integration.id}"
}

output "api_endpoint" {
  value = aws_apigatewayv2_stage.voting_api_stage.invoke_url
}

output "api_id" {
  value = aws_apigatewayv2_api.voting_api.id
}
