variable "project_name" { type = string }
variable "environment" { type = string }

# REQUIRED lambdas
variable "send_otp_function_arn" { type = string }
variable "send_otp_function_name" { type = string }

variable "verify_otp_function_arn" { type = string }
variable "verify_otp_function_name" { type = string }

variable "cast_vote_function_arn" { type = string }
variable "cast_vote_function_name" { type = string }

variable "get_results_function_arn" { type = string }
variable "get_results_function_name" { type = string }

variable "create_election_function_arn" { type = string }
variable "create_election_function_name" { type = string }

variable "add_candidates_function_arn" { type = string }
variable "add_candidates_function_name" { type = string }

# OPTIONAL (IMPORTANT FIX)
variable "get_posts_function_arn" {
  type    = string
  default = null
}

variable "get_posts_function_name" {
  type    = string
  default = null
}

variable "export_results_function_arn" {
  type    = string
  default = null
}

variable "export_results_function_name" {
  type    = string
  default = null
}

variable "bulk_upload_voters_function_arn" {
  type    = string
  default = null
}

variable "bulk_upload_voters_function_name" {
  type    = string
  default = null
}

variable "admin_login_function_arn" {
  type    = string
  default = null
}

variable "admin_login_function_name" {
  type    = string
  default = null
}

variable "admin_stats_function_arn" {
  type    = string
  default = null
}

variable "admin_stats_function_name" {
  type    = string
  default = null
}

variable "get_elections_function_arn" {
  type    = string
  default = null
}

variable "get_elections_function_name" {
  type    = string
  default = null
}

variable "get_candidates_function_arn" {
  type    = string
  default = null
}

variable "get_candidates_function_name" {
  type    = string
  default = null
}

# API SETTINGS (default de diye)
variable "enable_cors" {
  type    = bool
  default = true
}

variable "allowed_origins" {
  type    = list(string)
  default = ["*"]
}

variable "throttling_burst_limit" {
  type    = number
  default = 100
}

variable "throttling_rate_limit" {
  type    = number
  default = 50
}
