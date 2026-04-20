output "api_gateway_endpoint" {
  description = "API Gateway endpoint URL"
  value       = module.api_gateway.api_endpoint
}

output "dynamodb_tables" {
  description = "DynamoDB table names"
  value = {
    votes_table        = module.dynamodb.votes_table_name
    otp_table          = module.dynamodb.otp_table_name
    candidates_table   = module.dynamodb.candidates_table_name
    elections_table    = module.dynamodb.elections_table_name
  }
}

output "lambda_functions" {
  description = "Lambda function names"
  value = {
    send_otp           = module.lambda.send_otp_function_name
    verify_otp         = module.lambda.verify_otp_function_name
    cast_vote          = module.lambda.cast_vote_function_name
    get_results        = module.lambda.get_results_function_name
    create_election    = module.lambda.create_election_function_name
    add_candidates     = module.lambda.add_candidates_function_name
  }
}

output "sns_topic_arn" {
  description = "SNS topic ARN for sending OTPs"
  value       = module.sns.sns_topic_arn
}

output "iam_role_arn" {
  description = "IAM role ARN for Lambda execution"
  value       = module.iam.lambda_execution_role_arn
}

output "s3_bucket_name" {
  description = "S3 bucket name for frontend hosting (if enabled)"
  value       = try(module.s3[0].bucket_name, null)
}
 
output "s3_bucket_website_endpoint" {
  description = "S3 bucket website endpoint (if enabled) - HTTP only, use s3_bucket_website_endpoint_https instead"
  value       = try(module.s3[0].website_endpoint, null)
}

output "s3_bucket_website_endpoint_https" {
  description = "CloudFront HTTPS endpoint for secure access on all devices (recommended)"
  value       = try("https://${module.cloudfront[0].domain_name}", null)
}

output "deployment_region" {
  description = "AWS region where resources are deployed"
  value       = var.aws_region
}

output "project_environment" {
  description = "Project environment"
  value       = var.environment
}
