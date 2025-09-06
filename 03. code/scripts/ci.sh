#!/bin/bash

# ARM64 아키텍처로 Docker 이미지 빌드 스크립트

echo "ARM64 아키텍처로 Docker 이미지를 빌드합니다..."

# Docker buildx 설정 (멀티 플랫폼 빌드 지원)
docker buildx create --use --name arm-builder 2>/dev/null || true

# ARM64 이미지 빌드
docker buildx build \
  --platform linux/arm64 \
  --tag data-agent:arm64 \
  --load \
  ..

docker tag data-agent:latest 381491983173.dkr.ecr.us-east-1.amazonaws.com/langchain-api:latest

docker push 381491983173.dkr.ecr.us-east-1.amazonaws.com/langchain-api:latest 

echo "빌드 완료! 이미지 이름: data-agent:arm64"
echo ""
echo "실행 방법:"
echo "docker run -p 5000:5000 --env-file .env data-agent:arm64"
echo ""
echo "또는 docker-compose 사용:"
echo "docker-compose up"