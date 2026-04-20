output "send_otp_function_arn" {
  value = aws_lambda_function.send_otp.arn
}

output "send_otp_function_name" {
  value = aws_lambda_function.send_otp.function_name
}

output "verify_otp_function_arn" {
  value = aws_lambda_function.verify_otp.arn
}

output "verify_otp_function_name" {
  value = aws_lambda_function.verify_otp.function_name
}

output "cast_vote_function_arn" {
  value = aws_lambda_function.cast_vote.arn
}

output "cast_vote_function_name" {
  value = aws_lambda_function.cast_vote.function_name
}

output "get_results_function_arn" {
  value = aws_lambda_function.get_results.arn
}

output "get_results_function_name" {
  value = aws_lambda_function.get_results.function_name
}

output "create_election_function_arn" {
  value = aws_lambda_function.create_election.arn
}

output "create_election_function_name" {
  value = aws_lambda_function.create_election.function_name
}

output "add_candidates_function_arn" {
  value = aws_lambda_function.add_candidates.arn
}

output "add_candidates_function_name" {
  value = aws_lambda_function.add_candidates.function_name
}
