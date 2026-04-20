variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "lambda_timeout" {
  type = number
}

variable "lambda_memory" {
  type = number
}

variable "execution_role_arn" {
  type = string
}

variable "votes_table_name" {
  type = string
}

variable "otp_table_name" {
  type = string
}

variable "candidates_table_name" {
  type = string
}

variable "elections_table_name" {
  type = string
}

variable "voters_table_name" {
  type = string
}

variable "sns_topic_arn" {
  type = string
}

variable "otp_expiry_minutes" {
  type = number
}

variable "aws_region" {
  type = string
}

# Create a temporary directory for Lambda code
locals {
  lambda_functions = [
    "send_otp",
    "verify_otp",
    "cast_vote",
    "get_results",
    "create_election",
    "add_candidates"
  ]
  lambda_build_dir = "${path.module}/../../../lambda"
}

# Build Lambda function packages with shared lib files
resource "null_resource" "build_lambda_functions" {
  triggers = {
    build_script = filemd5("${local.lambda_build_dir}/build_functions.py")
    utils_lib    = filemd5("${local.lambda_build_dir}/lib/utils.py")
    aws_clients  = filemd5("${local.lambda_build_dir}/lib/aws_clients.py")
    send_otp     = filemd5("${local.lambda_build_dir}/functions/send_otp/index.py")
    verify_otp   = filemd5("${local.lambda_build_dir}/functions/verify_otp/index.py")
    cast_vote    = filemd5("${local.lambda_build_dir}/functions/cast_vote/index.py")
    get_results  = filemd5("${local.lambda_build_dir}/functions/get_results/index.py")
    admin_login  = filemd5("${local.lambda_build_dir}/functions/admin_login/index.py")
    admin_stats  = filemd5("${local.lambda_build_dir}/functions/admin_stats/index.py")
    get_elections = filemd5("${local.lambda_build_dir}/functions/get_elections/index.py")
    get_candidates = filemd5("${local.lambda_build_dir}/functions/get_candidates/index.py")
  }

  provisioner "local-exec" {
    command = "python ${local.lambda_build_dir}/build_functions.py"
  }
}

# Helper function to get zip file path
locals {
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

# Send OTP Lambda
resource "aws_lambda_function" "send_otp" {
  filename            = local.send_otp_zip
  function_name       = "${var.project_name}-send-otp-${var.environment}"
  role                = var.execution_role_arn
  handler             = "index.lambda_handler"
  runtime             = "python3.11"
  timeout             = var.lambda_timeout
  memory_size         = var.lambda_memory
  source_code_hash    = filebase64sha256(local.send_otp_zip)
  depends_on          = [null_resource.build_lambda_functions]

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

# Verify OTP Lambda
resource "aws_lambda_function" "verify_otp" {
  filename            = local.verify_otp_zip
  function_name       = "${var.project_name}-verify-otp-${var.environment}"
  role                = var.execution_role_arn
  handler             = "index.lambda_handler"
  runtime             = "python3.11"
  timeout             = var.lambda_timeout
  memory_size         = var.lambda_memory
  source_code_hash    = filebase64sha256(local.verify_otp_zip)
  depends_on          = [null_resource.build_lambda_functions]

  environment {
    variables = {
      OTP_TABLE_NAME = var.otp_table_name
    }
  }
}

# Cast Vote Lambda
resource "aws_lambda_function" "cast_vote" {
  filename            = local.cast_vote_zip
  function_name       = "${var.project_name}-cast-vote-${var.environment}"
  role                = var.execution_role_arn
  handler             = "index.lambda_handler"
  runtime             = "python3.11"
  timeout             = var.lambda_timeout
  memory_size         = var.lambda_memory
  source_code_hash    = filebase64sha256(local.cast_vote_zip)
  depends_on          = [null_resource.build_lambda_functions]

  environment {
    variables = {
      VOTES_TABLE_NAME      = var.votes_table_name
      ELECTIONS_TABLE_NAME  = var.elections_table_name
      CANDIDATES_TABLE_NAME = var.candidates_table_name
    }
  }
}

# Get Results Lambda
resource "aws_lambda_function" "get_results" {
  filename            = local.get_results_zip
  function_name       = "${var.project_name}-get-results-${var.environment}"
  role                = var.execution_role_arn
  handler             = "index.lambda_handler"
  runtime             = "python3.11"
  timeout             = var.lambda_timeout
  memory_size         = var.lambda_memory
  source_code_hash    = filebase64sha256(local.get_results_zip)
  depends_on          = [null_resource.build_lambda_functions]

  environment {
    variables = {
      VOTES_TABLE_NAME      = var.votes_table_name
      ELECTIONS_TABLE_NAME  = var.elections_table_name
      CANDIDATES_TABLE_NAME = var.candidates_table_name
    }
  }
}

# Create Election Lambda
resource "aws_lambda_function" "create_election" {
  filename            = local.create_election_zip
  function_name       = "${var.project_name}-create-election-${var.environment}"
  role                = var.execution_role_arn
  handler             = "index.lambda_handler"
  runtime             = "python3.11"
  timeout             = var.lambda_timeout
  memory_size         = var.lambda_memory
  source_code_hash    = filebase64sha256(local.create_election_zip)
  depends_on          = [null_resource.build_lambda_functions]

  environment {
    variables = {
      ELECTIONS_TABLE_NAME = var.elections_table_name
    }
  }
}

# Add Candidates Lambda
resource "aws_lambda_function" "add_candidates" {
  filename            = local.add_candidates_zip
  function_name       = "${var.project_name}-add-candidates-${var.environment}"
  role                = var.execution_role_arn
  handler             = "index.lambda_handler"
  runtime             = "python3.11"
  timeout             = var.lambda_timeout
  memory_size         = var.lambda_memory
  source_code_hash    = filebase64sha256(local.add_candidates_zip)
  depends_on          = [null_resource.build_lambda_functions]

  environment {
    variables = {
      ELECTIONS_TABLE_NAME  = var.elections_table_name
      CANDIDATES_TABLE_NAME = var.candidates_table_name
    }
  }
}

# Get Posts Lambda (with filtering for >1 candidate)
resource "aws_lambda_function" "get_posts" {
  filename            = local.get_posts_zip
  function_name       = "${var.project_name}-get-posts-${var.environment}"
  role                = var.execution_role_arn
  handler             = "index.lambda_handler"
  runtime             = "python3.11"
  timeout             = var.lambda_timeout
  memory_size         = var.lambda_memory
  source_code_hash    = filebase64sha256(local.get_posts_zip)
  depends_on          = [null_resource.build_lambda_functions]

  environment {
    variables = {
      CANDIDATES_TABLE_NAME = var.candidates_table_name
    }
  }
}

# Export Results Lambda
resource "aws_lambda_function" "export_results" {
  filename            = local.export_results_zip
  function_name       = "${var.project_name}-export-results-${var.environment}"
  role                = var.execution_role_arn
  handler             = "index.lambda_handler"
  runtime             = "python3.11"
  timeout             = var.lambda_timeout
  memory_size         = var.lambda_memory
  source_code_hash    = filebase64sha256(local.export_results_zip)
  depends_on          = [null_resource.build_lambda_functions]

  environment {
    variables = {
      VOTES_TABLE_NAME      = var.votes_table_name
      CANDIDATES_TABLE_NAME = var.candidates_table_name
    }
  }
}

# Bulk Upload Voters Lambda
resource "aws_lambda_function" "bulk_upload_voters" {
  filename            = local.bulk_upload_voters_zip
  function_name       = "${var.project_name}-bulk-upload-voters-${var.environment}"
  role                = var.execution_role_arn
  handler             = "index.lambda_handler"
  runtime             = "python3.11"
  timeout             = var.lambda_timeout
  memory_size         = var.lambda_memory
  source_code_hash    = filebase64sha256(local.bulk_upload_voters_zip)
  depends_on          = [null_resource.build_lambda_functions]

  environment {
    variables = {
      VOTERS_TABLE_NAME = var.voters_table_name
    }
  }
}

# Admin Login Lambda
resource "aws_lambda_function" "admin_login" {
  filename            = local.admin_login_zip
  function_name       = "${var.project_name}-admin-login-${var.environment}"
  role                = var.execution_role_arn
  handler             = "index.lambda_handler"
  runtime             = "python3.11"
  timeout             = var.lambda_timeout
  memory_size         = var.lambda_memory
  source_code_hash    = filebase64sha256(local.admin_login_zip)
  depends_on          = [null_resource.build_lambda_functions]

  environment {
    variables = {
      ADMIN_USERNAME                = "admin"
      ADMIN_PASSWORD_HASH           = ""  # Set via terraform.tfvars
      JWT_SECRET                    = "rwa-voting-secret-key"
      ADMIN_TOKEN_EXPIRY_HOURS      = "24"
    }
  }
}

# Admin Stats Lambda
resource "aws_lambda_function" "admin_stats" {
  filename            = local.admin_stats_zip
  function_name       = "${var.project_name}-admin-stats-${var.environment}"
  role                = var.execution_role_arn
  handler             = "index.lambda_handler"
  runtime             = "python3.11"
  timeout             = var.lambda_timeout
  memory_size         = var.lambda_memory
  source_code_hash    = filebase64sha256(local.admin_stats_zip)
  depends_on          = [null_resource.build_lambda_functions]

  environment {
    variables = {
      ELECTIONS_TABLE_NAME  = var.elections_table_name
      CANDIDATES_TABLE_NAME = var.candidates_table_name
      VOTERS_TABLE_NAME     = var.voters_table_name
      VOTES_TABLE_NAME      = var.votes_table_name
    }
  }
}

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

output "get_posts_function_arn" {
  value = aws_lambda_function.get_posts.arn
}

output "get_posts_function_name" {
  value = aws_lambda_function.get_posts.function_name
}

output "export_results_function_arn" {
  value = aws_lambda_function.export_results.arn
}

output "export_results_function_name" {
  value = aws_lambda_function.export_results.function_name
}

output "bulk_upload_voters_function_arn" {
  value = aws_lambda_function.bulk_upload_voters.arn
}

output "bulk_upload_voters_function_name" {
  value = aws_lambda_function.bulk_upload_voters.function_name
}

output "admin_login_function_arn" {
  value = aws_lambda_function.admin_login.arn
}

output "admin_login_function_name" {
  value = aws_lambda_function.admin_login.function_name
}

output "admin_stats_function_arn" {
  value = aws_lambda_function.admin_stats.arn
}

output "admin_stats_function_name" {
  value = aws_lambda_function.admin_stats.function_name
}

# Get Elections Lambda
resource "aws_lambda_function" "get_elections" {
  filename            = local.get_elections_zip
  function_name       = "${var.project_name}-get-elections-${var.environment}"
  role                = var.execution_role_arn
  handler             = "index.lambda_handler"
  runtime             = "python3.11"
  timeout             = var.lambda_timeout
  memory_size         = var.lambda_memory
  source_code_hash    = filebase64sha256(local.get_elections_zip)
  depends_on          = [null_resource.build_lambda_functions]

  environment {
    variables = {
      ELECTIONS_TABLE_NAME = var.elections_table_name
    }
  }
}

output "get_elections_function_arn" {
  value = aws_lambda_function.get_elections.arn
}

output "get_elections_function_name" {
  value = aws_lambda_function.get_elections.function_name
}

# Get Candidates Lambda
resource "aws_lambda_function" "get_candidates" {
  filename            = local.get_candidates_zip
  function_name       = "${var.project_name}-get-candidates-${var.environment}"
  role                = var.execution_role_arn
  handler             = "index.lambda_handler"
  runtime             = "python3.11"
  timeout             = var.lambda_timeout
  memory_size         = var.lambda_memory
  source_code_hash    = filebase64sha256(local.get_candidates_zip)
  depends_on          = [null_resource.build_lambda_functions]

  environment {
    variables = {
      CANDIDATES_TABLE_NAME = var.candidates_table_name
    }
  }
}

output "get_candidates_function_arn" {
  value = aws_lambda_function.get_candidates.arn
}

output "get_candidates_function_name" {
  value = aws_lambda_function.get_candidates.function_name
}
