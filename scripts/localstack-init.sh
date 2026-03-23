#!/bin/bash
set -euo pipefail

REGION=af-south-1
ENDPOINT=http://localhost:4566

echo "Creating SQS dead-letter queue..."
awslocal sqs create-queue \
    --queue-name fraud-engine-transactions-dlq \
    --region "$REGION"

echo "Creating SQS transaction queue with DLQ..."
awslocal sqs create-queue \
    --queue-name fraud-engine-transactions \
    --region "$REGION" \
    --attributes '{
        "RedrivePolicy": "{\"deadLetterTargetArn\":\"arn:aws:sqs:af-south-1:000000000000:fraud-engine-transactions-dlq\",\"maxReceiveCount\":\"3\"}",
        "VisibilityTimeout": "60"
    }'

echo "Creating SNS fraud-alerts topic..."
awslocal sns create-topic \
    --name fraud-alerts \
    --region "$REGION"

echo "Creating S3 audit bucket..."
awslocal s3 mb s3://fraud-engine-audit --region "$REGION"

echo "LocalStack resources initialized successfully."
