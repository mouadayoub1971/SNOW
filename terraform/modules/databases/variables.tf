variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs"
  type        = list(string)
}

variable "database_security_group_id" {
  description = "Security group ID for databases"
  type        = string
}

variable "enable_multi_az" {
  description = "Enable Multi-AZ for RDS"
  type        = bool
  default     = false
}

# PostgreSQL
variable "postgres_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.large"
}

variable "postgres_allocated_storage" {
  description = "Allocated storage for PostgreSQL (GB)"
  type        = number
  default     = 100
}

variable "postgres_max_allocated_storage" {
  description = "Maximum allocated storage for PostgreSQL (GB)"
  type        = number
  default     = 500
}

variable "postgres_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
}

# Redis
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.r6g.large"
}

# OpenSearch
variable "opensearch_instance_type" {
  description = "OpenSearch instance type"
  type        = string
  default     = "r6g.large.search"
}

variable "opensearch_instance_count" {
  description = "Number of OpenSearch instances"
  type        = number
  default     = 2
}

variable "opensearch_ebs_volume_size" {
  description = "EBS volume size for OpenSearch (GB)"
  type        = number
  default     = 100
}

variable "opensearch_master_password" {
  description = "OpenSearch master user password"
  type        = string
  sensitive   = true
}
