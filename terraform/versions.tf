terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  # Never hard-code credentials - use the AWS CLI profile or environment
  # variables (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY) instead.
  default_tags {
    tags = {
      Project   = "clinicflow"
      ManagedBy = "terraform"
    }
  }
}
