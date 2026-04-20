output "lambda_role_arn" {
  value = module.iam.lambda_execution_role_arn
}

output "sns_topic_arn" {
  value = module.sns.sns_topic_arn
}

output "dynamodb_tables" {
  value = {
    votes      = module.dynamodb.votes_table_name
    otp        = module.dynamodb.otp_table_name
    candidates = module.dynamodb.candidates_table_name
    elections  = module.dynamodb.elections_table_name
    voters     = module.dynamodb.voters_table_name
  }
}
