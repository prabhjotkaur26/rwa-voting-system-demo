variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "rwa-voting"
}

variable "sns_topic_name" {
  description = "SNS topic name for SMS OTP"
  type        = string
  default     = "voting-otp-topic"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory" {
  description = "Lambda function memory in MB"
  type        = number
  default     = 256
}

variable "api_throttling_burst_limit" {
  description = "API Gateway burst limit for throttling"
  type        = number
  default     = 5000
}

variable "api_throttling_rate_limit" {
  description = "API Gateway rate limit for throttling"
  type        = number
  default     = 2000
}

variable "otp_expiry_minutes" {
  description = "OTP expiry time in minutes"
  type        = number
  default     = 5
}

variable "dynamodb_read_capacity" {
  description = "DynamoDB read capacity units (on-demand recommended for free tier)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "dynamodb_write_capacity" {
  description = "DynamoDB write capacity units (on-demand recommended for free tier)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "enable_cors" {
  description = "Enable CORS for API Gateway"
  type        = bool
  default     = true
}

variable "allowed_origins" {
  description = "Allowed origins for CORS"
  type        = list(string)
  default     = ["*"]
}

variable "tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}
