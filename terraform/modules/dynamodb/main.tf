variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "read_capacity" {
  type        = string
  description = "DynamoDB read capacity (PAY_PER_REQUEST or number for provisioned)"
  default     = "PAY_PER_REQUEST"
}

variable "write_capacity" {
  type        = string
  description = "DynamoDB write capacity (PAY_PER_REQUEST or number for provisioned)"
  default     = "PAY_PER_REQUEST"
}

variable "otp_expiry_minutes" {
  type        = number
  description = "OTP expiry time in minutes"
  default     = 5
}

# Votes Table - PK: electionId#postId, SK: mobileNumber
resource "aws_dynamodb_table" "votes" {
  name           = "${var.project_name}-votes-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "electionId#postId"
  range_key      = "mobileNumber"

  attribute {
    name = "electionId#postId"
    type = "S"
  }

  attribute {
    name = "mobileNumber"
    type = "S"
  }

  attribute {
    name = "electionId"
    type = "S"
  }

  # GSI for querying by electionId only
  global_secondary_index {
    name            = "electionId-index"
    hash_key        = "electionId"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  lifecycle {
    ignore_changes = [tags, tags_all]
  }
}

# OTP Table - PK: mobileNumber with TTL
resource "aws_dynamodb_table" "otp" {
  name           = "${var.project_name}-otp-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "mobileNumber"

  attribute {
    name = "mobileNumber"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  lifecycle {
    ignore_changes = [tags, tags_all]
  }
}

# Candidates Table - PK: electionId#postId, SK: candidateId
resource "aws_dynamodb_table" "candidates" {
  name           = "${var.project_name}-candidates-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "electionId#postId"
  range_key      = "candidateId"

  attribute {
    name = "electionId#postId"
    type = "S"
  }

  attribute {
    name = "candidateId"
    type = "S"
  }

  lifecycle {
    ignore_changes = [tags, tags_all]
  }
}

# Elections Table - PK: electionId
resource "aws_dynamodb_table" "elections" {
  name           = "${var.project_name}-elections-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "electionId"

  attribute {
    name = "electionId"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  lifecycle {
    ignore_changes = [tags, tags_all]
  }
}

# Voters Table - PK: mobileNumber
# Stores voter registration data: flat/house number, name, mobile
resource "aws_dynamodb_table" "voters" {
  name           = "${var.project_name}-voters-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "mobileNumber"

  attribute {
    name = "mobileNumber"
    type = "S"
  }

  attribute {
    name = "flatNumber"
    type = "S"
  }

  # GSI for searching by flat/house number
  global_secondary_index {
    name            = "flatNumber-index"
    hash_key        = "flatNumber"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  lifecycle {
    ignore_changes = [tags_all]
  }
}

output "votes_table_name" {
  value = aws_dynamodb_table.votes.name
}

output "votes_table_arn" {
  value = aws_dynamodb_table.votes.arn
}

output "otp_table_name" {
  value = aws_dynamodb_table.otp.name
}

output "otp_table_arn" {
  value = aws_dynamodb_table.otp.arn
}

output "candidates_table_name" {
  value = aws_dynamodb_table.candidates.name
}

output "candidates_table_arn" {
  value = aws_dynamodb_table.candidates.arn
}

output "elections_table_name" {
  value = aws_dynamodb_table.elections.name
}

output "elections_table_arn" {
  value = aws_dynamodb_table.elections.arn
}

output "voters_table_name" {
  value = aws_dynamodb_table.voters.name
}

output "voters_table_arn" {
  value = aws_dynamodb_table.voters.arn
}
