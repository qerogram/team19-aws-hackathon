# ARM64 지원을 위한 Python 베이스 이미지 사용
FROM --platform=linux/arm64 python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 환경 변수 설정 (런타임에 오버라이드 가능)
ENV PORT=5000
ENV DEBUG=false

# DB 환경 변수 (기본값 설정 - ECS에서 오버라이드 가능)
ENV DB_HOST=superset-hackathon-postgres.cm1822i8mf8x.us-east-1.rds.amazonaws.com
ENV DB_PORT=5432
ENV DB_NAME=superset
ENV DB_USER=supersetuser
ENV DB_PASSWORD=SupersetHackathon2024!

# AWS 환경 변수 (ECS IAM Role 사용시 불필요하지만, 로컬 테스트용)
ENV AWS_REGION=us-east-1

# 포트 노출
EXPOSE 5000

# 애플리케이션 실행
CMD ["python", "app.py"]