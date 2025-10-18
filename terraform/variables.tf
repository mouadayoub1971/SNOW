variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "valyrion"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "openai_api_key" {
  description = "OpenAI API key (stored in Secrets Manager)"
  type        = string
  sensitive   = true
}

variable "finnhub_api_key" {
  description = "Finnhub API key (stored in Secrets Manager)"
  type        = string
  sensitive   = true
}

variable "api_instance_count" {
  description = "Number of API server instances"
  type        = number
  default     = 2
}

variable "worker_instance_count" {
  description = "Number of worker instances"
  type        = number
  default     = 2
}

variable "enable_multi_az" {
  description = "Enable Multi-AZ for databases"
  type        = bool
  default     = false
}
