locals {
  project = "${var.project_name}-${var.environment}"
}

# IAM Module
module "iam" {
  source = "./modules/iam"

  project_name = var.project_name
  environment  = var.environment
  sns_topic_arn = module.sns.sns_topic_arn
  dynamodb_arns = [
    module.dynamodb.votes_table_arn,
    module.dynamodb.otp_table_arn,
    module.dynamodb.candidates_table_arn,
    module.dynamodb.elections_table_arn,
    module.dynamodb.voters_table_arn,
  ]

  depends_on = [module.sns, module.dynamodb]
}

# DynamoDB Module
module "dynamodb" {
  source = "./modules/dynamodb"

  project_name              = var.project_name
  environment               = var.environment
  otp_expiry_minutes        = var.otp_expiry_minutes
  read_capacity             = var.dynamodb_read_capacity
  write_capacity            = var.dynamodb_write_capacity
}

# SNS Module
module "sns" {
  source = "./modules/sns"

  project_name = var.project_name
  environment  = var.environment
  topic_name   = var.sns_topic_name
}

# Lambda Module
module "lambda" {
  source = "./modules/lambda"

  project_name              = var.project_name
  environment               = var.environment
  lambda_timeout            = var.lambda_timeout
  lambda_memory             = var.lambda_memory
  execution_role_arn        = module.iam.lambda_execution_role_arn
  
  # DynamoDB table properties
  votes_table_name          = module.dynamodb.votes_table_name
  otp_table_name            = module.dynamodb.otp_table_name
  candidates_table_name     = module.dynamodb.candidates_table_name
  elections_table_name      = module.dynamodb.elections_table_name
  voters_table_name         = module.dynamodb.voters_table_name
  
  # SNS topic
  sns_topic_arn             = module.sns.sns_topic_arn
  
  # Environment variables
  otp_expiry_minutes        = var.otp_expiry_minutes
  aws_region                = var.aws_region

  depends_on = [module.iam, module.dynamodb, module.sns]
}

# API Gateway Module
module "api_gateway" {
  source = "./modules/api_gateway"

  project_name              = var.project_name
  environment               = var.environment
  
  # Lambda functions
  send_otp_function_arn     = module.lambda.send_otp_function_arn
  send_otp_function_name    = module.lambda.send_otp_function_name
  verify_otp_function_arn   = module.lambda.verify_otp_function_arn
  verify_otp_function_name  = module.lambda.verify_otp_function_name
  cast_vote_function_arn    = module.lambda.cast_vote_function_arn
  cast_vote_function_name   = module.lambda.cast_vote_function_name
  get_results_function_arn  = module.lambda.get_results_function_arn
  get_results_function_name = module.lambda.get_results_function_name
  create_election_function_arn    = module.lambda.create_election_function_arn
  create_election_function_name   = module.lambda.create_election_function_name
  add_candidates_function_arn     = module.lambda.add_candidates_function_arn
  add_candidates_function_name    = module.lambda.add_candidates_function_name
  get_posts_function_arn          = module.lambda.get_posts_function_arn
  get_posts_function_name         = module.lambda.get_posts_function_name
  export_results_function_arn     = module.lambda.export_results_function_arn
  export_results_function_name    = module.lambda.export_results_function_name
  bulk_upload_voters_function_arn     = module.lambda.bulk_upload_voters_function_arn
  bulk_upload_voters_function_name    = module.lambda.bulk_upload_voters_function_name
  admin_login_function_arn            = module.lambda.admin_login_function_arn
  admin_login_function_name           = module.lambda.admin_login_function_name
  admin_stats_function_arn            = module.lambda.admin_stats_function_arn
  admin_stats_function_name           = module.lambda.admin_stats_function_name
  get_elections_function_arn          = module.lambda.get_elections_function_arn
  get_elections_function_name         = module.lambda.get_elections_function_name
  get_candidates_function_arn         = module.lambda.get_candidates_function_arn
  get_candidates_function_name        = module.lambda.get_candidates_function_name
  
  # API settings
  throttling_burst_limit    = var.api_throttling_burst_limit
  throttling_rate_limit     = var.api_throttling_rate_limit
  enable_cors               = var.enable_cors
  allowed_origins           = var.allowed_origins

  depends_on = [module.lambda]
}

# S3 Module (optional - uncomment to enable)
module "s3" {
  source = "./modules/s3"
  count       = 1 # Change to 0 to disable
  project_name = var.project_name
  environment  = var.environment
}

# CloudFront Module for HTTPS support
module "cloudfront" {
  source = "./modules/cloudfront"
  count  = 1 # Enable when S3 module is enabled
  
  project_name       = var.project_name
  environment        = var.environment
  s3_bucket_name     = module.s3[0].bucket_name
  s3_website_endpoint = module.s3[0].website_endpoint
  s3_bucket_arn      = module.s3[0].bucket_arn
  
  depends_on = [module.s3]
}
