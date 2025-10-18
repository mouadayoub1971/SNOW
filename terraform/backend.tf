terraform {
  backend "s3" {
    bucket         = "valyrion-terraform-state"
    key            = "valyrion/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "valyrion-terraform-locks"
  }

  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Valyrion"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
