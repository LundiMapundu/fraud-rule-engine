output "alb_dns_name" {
  description = "ALB DNS name (API endpoint)"
  value       = aws_lb.app.dns_name
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = aws_elasticache_cluster.main.cache_nodes[0].address
}

output "sqs_queue_url" {
  description = "SQS transaction queue URL"
  value       = aws_sqs_queue.transactions.url
}

output "sqs_dlq_url" {
  description = "SQS dead-letter queue URL"
  value       = aws_sqs_queue.transactions_dlq.url
}

output "sns_topic_arn" {
  description = "SNS fraud alerts topic ARN"
  value       = aws_sns_topic.fraud_alerts.arn
}

output "s3_bucket_name" {
  description = "S3 audit bucket name"
  value       = aws_s3_bucket.audit.id
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.app.repository_url
}

output "database_url" {
  description = "Full database connection string"
  value       = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.main.endpoint}/${var.db_name}"
  sensitive   = true
}
