#!/bin/bash

echo "🗑️  Cleaning up all ECR repositories..."

# ECR 리포지토리 목록
REPOS=(
  "superset-superset"
  "superset-superset-worker"
  "superset-superset-node"
  "superset-superset-init"
  "langchain-api"
  "superset-superset-websocket"
  "superset-superset-worker-beat"
  "superset-nginx"
)

for repo in "${REPOS[@]}"; do
  echo "Deleting ECR repository: $repo"
  aws ecr delete-repository --repository-name "$repo" --force --profile hackathon --region us-east-1 2>/dev/null || echo "Repository $repo not found or already deleted"
done

echo "✅ ECR cleanup completed!"
