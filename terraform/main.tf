locals {
  project = "${var.project_name}-${var.environment}"
}

# DynamoDB
module "dynamodb" {
  source = "./modules/dynamodb"

  project_name       = var.project_name
  environment        = var.environment
  otp_expiry_minutes = var.otp_expiry_minutes
  read_capacity      = var.dynamodb_read_capacity
  write_capacity     = var.dynamodb_write_capacity
}

# SNS
module "sns" {
  source = "./modules/sns"

  project_name = var.project_name
  environment  = var.environment
  topic_name   = var.sns_topic_name
}

# IAM
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
}

# Lambda
module "lambda" {
  source = "./modules/lambda"

  project_name       = var.project_name
  environment        = var.environment
  lambda_timeout     = var.lambda_timeout
  lambda_memory      = var.lambda_memory
  execution_role_arn = module.iam.lambda_execution_role_arn

  votes_table_name      = module.dynamodb.votes_table_name
  otp_table_name        = module.dynamodb.otp_table_name
  candidates_table_name = module.dynamodb.candidates_table_name
  elections_table_name  = module.dynamodb.elections_table_name
  voters_table_name     = module.dynamodb.voters_table_name

  sns_topic_arn      = module.sns.sns_topic_arn
  otp_expiry_minutes = var.otp_expiry_minutes
  aws_region         = var.aws_region
}
