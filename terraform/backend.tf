terraform {
  backend "s3" {
    bucket         = "rwa-voting-system-terraform-state"
    key            = "terraform.tfstate"
    region         = "ap-south-1"
    encrypt        = true
    dynamodb_table = "rwa-voting-terraform-locks"
  }
}
