terraform {
  backend "s3" {
    bucket         = "rwa-voting-system-terraform-state-1776157684"
    key            = "terraform.tfstate"
    region         = "ap-south-1"
    encrypt        = true
    dynamodb_table = "rwa-voting-terraform-locks"
  }
}
