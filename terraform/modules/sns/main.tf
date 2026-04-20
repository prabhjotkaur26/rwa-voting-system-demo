variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "topic_name" {
  type = string
}

resource "aws_sns_topic" "voting_otp" {
  name              = "${var.project_name}-${var.topic_name}-${var.environment}"
  display_name      = "RWA Voting OTP"
  fifo_topic        = false
  content_based_deduplication = false

  lifecycle {
    ignore_changes = [tags, tags_all]
  }
}

output "sns_topic_arn" {
  value = aws_sns_topic.voting_otp.arn
}

output "sns_topic_name" {
  value = aws_sns_topic.voting_otp.name
}
