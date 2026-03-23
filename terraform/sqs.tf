resource "aws_sqs_queue" "transactions_dlq" {
  name                      = "${var.project_name}-transactions-dlq"
  message_retention_seconds = 1209600 # 14 days
}

resource "aws_sqs_queue" "transactions" {
  name                       = "${var.project_name}-transactions"
  visibility_timeout_seconds = 60
  message_retention_seconds  = 86400 # 1 day
  receive_wait_time_seconds  = 5

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.transactions_dlq.arn
    maxReceiveCount     = 3
  })
}
