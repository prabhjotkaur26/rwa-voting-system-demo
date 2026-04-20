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

module "api_gateway" {
  source = "./modules/api_gateway"

  project_name = var.project_name
  environment  = var.environment

  send_otp_function_arn     = module.lambda.send_otp_function_arn
  send_otp_function_name    = module.lambda.send_otp_function_name
  verify_otp_function_arn   = module.lambda.verify_otp_function_arn
  verify_otp_function_name  = module.lambda.verify_otp_function_name
  cast_vote_function_arn    = module.lambda.cast_vote_function_arn
  cast_vote_function_name   = module.lambda.cast_vote_function_name
  get_results_function_arn  = module.lambda.get_results_function_arn
  get_results_function_name = module.lambda.get_results_function_name
  create_election_function_arn  = module.lambda.create_election_function_arn
  create_election_function_name = module.lambda.create_election_function_name
  add_candidates_function_arn   = module.lambda.add_candidates_function_arn
  add_candidates_function_name  = module.lambda.add_candidates_function_name
}
