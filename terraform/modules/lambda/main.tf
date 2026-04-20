# Create a temporary directory for Lambda code
locals {
  lambda_build_dir = "${path.root}/lambda"

  send_otp_zip      = "${local.lambda_build_dir}/.build/send_otp.zip"
  verify_otp_zip    = "${local.lambda_build_dir}/.build/verify_otp.zip"
  cast_vote_zip     = "${local.lambda_build_dir}/.build/cast_vote.zip"
  get_results_zip   = "${local.lambda_build_dir}/.build/get_results.zip"
  create_election_zip = "${local.lambda_build_dir}/.build/create_election.zip"
  add_candidates_zip  = "${local.lambda_build_dir}/.build/add_candidates.zip"
  get_posts_zip     = "${local.lambda_build_dir}/.build/get_posts.zip"
  export_results_zip = "${local.lambda_build_dir}/.build/export_results.zip"
  bulk_upload_voters_zip = "${local.lambda_build_dir}/.build/bulk_upload_voters.zip"
  get_elections_zip = "${local.lambda_build_dir}/.build/get_elections.zip"
  get_candidates_zip = "${local.lambda_build_dir}/.build/get_candidates.zip"
  admin_login_zip = "${local.lambda_build_dir}/.build/admin_login.zip"
  admin_stats_zip = "${local.lambda_build_dir}/.build/admin_stats.zip"
}

# Build Lambda packages
resource "null_resource" "build_lambda_functions" {
  provisioner "local-exec" {
    command = "python ${path.root}/lambda/build_functions.py"
  }
}

# 🔥 COMMON FIX PATTERN
# source_code_hash = fileexists(...) ? filebase64sha256(...) : null

# -------------------------------
# Send OTP
# -------------------------------
resource "aws_lambda_function" "send_otp" {
  filename         = local.send_otp_zip
  function_name    = "${var.project_name}-send-otp-${var.environment}"
  role             = var.execution_role_arn
  handler          = "index.lambda_handler"
  runtime          = "python3.11"
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory

  source_code_hash = fileexists(local.send_otp_zip) ? filebase64sha256(local.send_otp_zip) : null

  depends_on = [null_resource.build_lambda_functions]

  environment {
    variables = {
      OTP_TABLE_NAME       = var.otp_table_name
      VOTERS_TABLE_NAME    = var.voters_table_name
      VOTES_TABLE_NAME     = var.votes_table_name
      ELECTIONS_TABLE_NAME = var.elections_table_name
      SNS_TOPIC_ARN        = var.sns_topic_arn
      OTP_EXPIRY_MINUTES   = tostring(var.otp_expiry_minutes)
    }
  }
}

# -------------------------------
# Verify OTP
# -------------------------------
resource "aws_lambda_function" "verify_otp" {
  filename         = local.verify_otp_zip
  function_name    = "${var.project_name}-verify-otp-${var.environment}"
  role             = var.execution_role_arn
  handler          = "index.lambda_handler"
  runtime          = "python3.11"
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory

  source_code_hash = fileexists(local.verify_otp_zip) ? filebase64sha256(local.verify_otp_zip) : null

  depends_on = [null_resource.build_lambda_functions]

  environment {
    variables = {
      OTP_TABLE_NAME = var.otp_table_name
    }
  }
}

# -------------------------------
# Cast Vote
# -------------------------------
resource "aws_lambda_function" "cast_vote" {
  filename         = local.cast_vote_zip
  function_name    = "${var.project_name}-cast-vote-${var.environment}"
  role             = var.execution_role_arn
  handler          = "index.lambda_handler"
  runtime          = "python3.11"
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory

  source_code_hash = fileexists(local.cast_vote_zip) ? filebase64sha256(local.cast_vote_zip) : null

  depends_on = [null_resource.build_lambda_functions]

  environment {
    variables = {
      VOTES_TABLE_NAME      = var.votes_table_name
      ELECTIONS_TABLE_NAME  = var.elections_table_name
      CANDIDATES_TABLE_NAME = var.candidates_table_name
    }
  }
}

# -------------------------------
# Get Results
# -------------------------------
resource "aws_lambda_function" "get_results" {
  filename         = local.get_results_zip
  function_name    = "${var.project_name}-get-results-${var.environment}"
  role             = var.execution_role_arn
  handler          = "index.lambda_handler"
  runtime          = "python3.11"
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory

  source_code_hash = fileexists(local.get_results_zip) ? filebase64sha256(local.get_results_zip) : null

  depends_on = [null_resource.build_lambda_functions]

  environment {
    variables = {
      VOTES_TABLE_NAME      = var.votes_table_name
      ELECTIONS_TABLE_NAME  = var.elections_table_name
      CANDIDATES_TABLE_NAME = var.candidates_table_name
    }
  }
}

# -------------------------------
# Create Election
# -------------------------------
resource "aws_lambda_function" "create_election" {
  filename         = local.create_election_zip
  function_name    = "${var.project_name}-create-election-${var.environment}"
  role             = var.execution_role_arn
  handler          = "index.lambda_handler"
  runtime          = "python3.11"
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory

  source_code_hash = fileexists(local.create_election_zip) ? filebase64sha256(local.create_election_zip) : null

  depends_on = [null_resource.build_lambda_functions]

  environment {
    variables = {
      ELECTIONS_TABLE_NAME = var.elections_table_name
    }
  }
}

# -------------------------------
# Add Candidates
# -------------------------------
resource "aws_lambda_function" "add_candidates" {
  filename         = local.add_candidates_zip
  function_name    = "${var.project_name}-add-candidates-${var.environment}"
  role             = var.execution_role_arn
  handler          = "index.lambda_handler"
  runtime          = "python3.11"
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory

  source_code_hash = fileexists(local.add_candidates_zip) ? filebase64sha256(local.add_candidates_zip) : null

  depends_on = [null_resource.build_lambda_functions]

  environment {
    variables = {
      ELECTIONS_TABLE_NAME  = var.elections_table_name
      CANDIDATES_TABLE_NAME = var.candidates_table_name
    }
  }
}
