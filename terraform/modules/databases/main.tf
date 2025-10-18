# RDS PostgreSQL
resource "aws_db_subnet_group" "postgres" {
  name       = "${var.project_name}-postgres-subnet-${var.environment}"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "${var.project_name}-postgres-subnet-group-${var.environment}"
  }
}

resource "aws_db_instance" "postgres" {
  identifier     = "${var.project_name}-postgres-${var.environment}"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.postgres_instance_class

  allocated_storage     = var.postgres_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true
  max_allocated_storage = var.postgres_max_allocated_storage

  db_name  = "valyrion"
  username = "valyrion_admin"
  password = var.postgres_password

  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  vpc_security_group_ids = [var.database_security_group_id]

  multi_az               = var.enable_multi_az
  publicly_accessible    = false
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  skip_final_snapshot       = var.environment == "dev" ? true : false
  final_snapshot_identifier = var.environment == "dev" ? null : "${var.project_name}-postgres-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  tags = {
    Name = "${var.project_name}-postgres-${var.environment}"
  }
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "redis" {
  name       = "${var.project_name}-redis-subnet-${var.environment}"
  subnet_ids = var.private_subnet_ids
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.project_name}-redis-${var.environment}"
  engine               = "redis"
  engine_version       = "7.0"
  node_type            = var.redis_node_type
  num_cache_nodes      = 1
  parameter_group_name = aws_elasticache_parameter_group.redis.name
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [var.database_security_group_id]
  port                 = 6379

  snapshot_retention_limit = var.environment == "prod" ? 7 : 1
  snapshot_window          = "03:00-05:00"

  tags = {
    Name = "${var.project_name}-redis-${var.environment}"
  }
}

resource "aws_elasticache_parameter_group" "redis" {
  name   = "${var.project_name}-redis-params-${var.environment}"
  family = "redis7"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }
}

# OpenSearch (Elasticsearch)
resource "aws_opensearch_domain" "main" {
  domain_name    = "${var.project_name}-search-${var.environment}"
  engine_version = "OpenSearch_2.9"

  cluster_config {
    instance_type  = var.opensearch_instance_type
    instance_count = var.opensearch_instance_count
    zone_awareness_enabled = var.opensearch_instance_count > 1

    dynamic "zone_awareness_config" {
      for_each = var.opensearch_instance_count > 1 ? [1] : []
      content {
        availability_zone_count = min(var.opensearch_instance_count, 3)
      }
    }
  }

  ebs_options {
    ebs_enabled = true
    volume_size = var.opensearch_ebs_volume_size
    volume_type = "gp3"
  }

  vpc_options {
    subnet_ids         = slice(var.private_subnet_ids, 0, min(var.opensearch_instance_count, length(var.private_subnet_ids)))
    security_group_ids = [var.database_security_group_id]
  }

  encrypt_at_rest {
    enabled = true
  }

  node_to_node_encryption {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  advanced_security_options {
    enabled                        = true
    internal_user_database_enabled = true
    master_user_options {
      master_user_name     = "admin"
      master_user_password = var.opensearch_master_password
    }
  }

  access_policies = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        AWS = "*"
      }
      Action   = "es:*"
      Resource = "arn:aws:es:${var.aws_region}:${data.aws_caller_identity.current.account_id}:domain/${var.project_name}-search-${var.environment}/*"
    }]
  })

  tags = {
    Name = "${var.project_name}-opensearch-${var.environment}"
  }
}

# S3 Bucket for document storage
resource "aws_s3_bucket" "documents" {
  bucket = "${var.project_name}-documents-${var.environment}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "${var.project_name}-documents-${var.environment}"
  }
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    id     = "archive-old-documents"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }
}

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket = aws_s3_bucket.documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Data source
data "aws_caller_identity" "current" {}
