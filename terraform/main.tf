terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Using local backend for dev environment
  # For production, configure S3 backend with DynamoDB locking
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "fraud-rule-engine"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
