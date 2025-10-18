output "postgres_endpoint" {
  description = "PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "postgres_address" {
  description = "PostgreSQL address"
  value       = aws_db_instance.postgres.address
}

output "postgres_port" {
  description = "PostgreSQL port"
  value       = aws_db_instance.postgres.port
}

output "postgres_database_name" {
  description = "PostgreSQL database name"
  value       = aws_db_instance.postgres.db_name
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "redis_port" {
  description = "Redis port"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].port
}

output "opensearch_endpoint" {
  description = "OpenSearch endpoint"
  value       = aws_opensearch_domain.main.endpoint
}

output "opensearch_domain_name" {
  description = "OpenSearch domain name"
  value       = aws_opensearch_domain.main.domain_name
}

output "s3_bucket_name" {
  description = "S3 bucket name for documents"
  value       = aws_s3_bucket.documents.id
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.documents.arn
}
