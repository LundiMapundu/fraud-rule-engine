#!/bin/bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-af-south-1}"
ECR_REPO="${ECR_REPO:-fraud-rule-engine}"
ECS_CLUSTER="${ECS_CLUSTER:-fraud-engine-cluster}"
ECS_SERVICE="${ECS_SERVICE:-fraud-engine-service}"

echo "=== Fraud Rule Engine Deployment ==="

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"

echo "1. Authenticating with ECR..."
aws ecr get-login-password --region "$AWS_REGION" | \
    docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "2. Building Docker image..."
docker build -t "$ECR_REPO" .

echo "3. Tagging and pushing to ECR..."
docker tag "$ECR_REPO:latest" "$ECR_URI:latest"
docker push "$ECR_URI:latest"

echo "4. Updating ECS service..."
aws ecs update-service \
    --cluster "$ECS_CLUSTER" \
    --service "$ECS_SERVICE" \
    --force-new-deployment \
    --region "$AWS_REGION" \
    --no-cli-pager

echo "5. Waiting for deployment to stabilize..."
aws ecs wait services-stable \
    --cluster "$ECS_CLUSTER" \
    --services "$ECS_SERVICE" \
    --region "$AWS_REGION"

echo "=== Deployment complete ==="
