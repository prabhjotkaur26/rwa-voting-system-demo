variable "project_name" { type = string }
variable "environment" { type = string }
variable "lambda_timeout" { type = number }
variable "lambda_memory" { type = number }
variable "execution_role_arn" { type = string }

variable "votes_table_name" { type = string }
variable "otp_table_name" { type = string }
variable "candidates_table_name" { type = string }
variable "elections_table_name" { type = string }
variable "voters_table_name" { type = string }

variable "sns_topic_arn" { type = string }

variable "otp_expiry_minutes" { type = number }
variable "aws_region" { type = string }
