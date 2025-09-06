#!/bin/bash
# User Data Script for EC2 Instance
# Deploys full Superset stack using Docker Compose from ECR

set -e

# Variables
ECR_REGISTRY="${ECR_REGISTRY}"
REGION="us-east-1"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a /var/log/user-data.log
}

log "🚀 Starting EC2 initialization for Superset stack..."

# Update system
log "📦 Updating system packages..."
yum update -y

# Install Docker
log "🐳 Installing Docker..."
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose (ARM64)
log "🐳 Installing Docker Compose for ARM64..."
curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-linux-aarch64" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Install AWS CLI v2 (ARM64)
log "☁️ Installing AWS CLI v2 for ARM64..."
curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install
rm -rf aws awscliv2.zip

# Install other dependencies
log "📚 Installing Git and other dependencies..."
yum install -y git python3 python3-pip

# Configure AWS CLI to use instance profile
log "🔑 Configuring AWS CLI..."
mkdir -p /home/ec2-user/.aws
cat > /home/ec2-user/.aws/config << EOF
[default]
region = us-east-1
output = json
EOF
chown -R ec2-user:ec2-user /home/ec2-user/.aws

# ECR Login
log "🔐 Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Clone the repository (or copy docker-compose files)
log "📥 Setting up Superset directory..."
mkdir -p /opt/superset
cd /opt/superset

# Create superset_config.py
cat > superset_config.py << 'EOF'
import os

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    SQLALCHEMY_DATABASE_URI = DATABASE_URL

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_REDIS_HOST": REDIS_HOST,
    "CACHE_REDIS_PORT": REDIS_PORT,
    "CACHE_DEFAULT_TIMEOUT": 300,
}

DATA_CACHE_CONFIG = CACHE_CONFIG

class CeleryConfig:
    broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
    result_backend = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

CELERY_CONFIG = CeleryConfig
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY")
EOF

# Create docker-compose.yml for production with ECR images and RDS
cat > docker-compose.yml << 'EOF'
version: "3.8"
services:
  redis:
    image: redis:7
    container_name: superset_cache
    restart: unless-stopped
    volumes:
      - redis-data:/data

  superset:
    image: 381491983173.dkr.ecr.us-east-1.amazonaws.com/superset-superset:latest
    container_name: superset_app
    restart: unless-stopped
    user: "root"
    ports:
      - "8088:8088"
    environment:
      FLASK_ENV: production
      SUPERSET_ENV: production
      REDIS_HOST: redis
      REDIS_PORT: 6379
      DATABASE_URL: "postgresql://supersetuser:SupersetHackathon2024!@superset-hackathon-postgres.cm1822i8mf8x.us-east-1.rds.amazonaws.com:5432/superset"
      SUPERSET_SECRET_KEY: "hackathon-superset-secret-key-2024-change-in-production"
    depends_on:
      - redis
    volumes:
      - superset-data:/app/superset_home
      - ./superset_config.py:/app/pythonpath/superset_config.py

  superset-init:
    image: 381491983173.dkr.ecr.us-east-1.amazonaws.com/superset-superset-init:latest
    container_name: superset_init
    environment:
      FLASK_ENV: production
      SUPERSET_ENV: production
      REDIS_HOST: redis
      REDIS_PORT: 6379
      DATABASE_URL: "postgresql://supersetuser:SupersetHackathon2024!@superset-hackathon-postgres.cm1822i8mf8x.us-east-1.rds.amazonaws.com:5432/superset"
      SUPERSET_SECRET_KEY: "hackathon-superset-secret-key-2024-change-in-production"
    depends_on:
      - redis
    volumes:
      - superset-data:/app/superset_home

  superset-worker:
    image: 381491983173.dkr.ecr.us-east-1.amazonaws.com/superset-superset-worker:latest
    container_name: superset_worker
    restart: unless-stopped
    user: "root"
    environment:
      FLASK_ENV: production
      SUPERSET_ENV: production
      REDIS_HOST: redis
      REDIS_PORT: 6379
      DATABASE_URL: "postgresql://supersetuser:SupersetHackathon2024!@superset-hackathon-postgres.cm1822i8mf8x.us-east-1.rds.amazonaws.com:5432/superset"
      SUPERSET_SECRET_KEY: "hackathon-superset-secret-key-2024-change-in-production"
    depends_on:
      - redis
    volumes:
      - superset-data:/app/superset_home

  superset-worker-beat:
    image: 381491983173.dkr.ecr.us-east-1.amazonaws.com/superset-superset-worker-beat:latest
    container_name: superset_worker_beat
    restart: unless-stopped
    user: "root"
    environment:
      FLASK_ENV: production
      SUPERSET_ENV: production
      REDIS_HOST: redis
      REDIS_PORT: 6379
      DATABASE_URL: "postgresql://supersetuser:SupersetHackathon2024!@superset-hackathon-postgres.cm1822i8mf8x.us-east-1.rds.amazonaws.com:5432/superset"
      SUPERSET_SECRET_KEY: "hackathon-superset-secret-key-2024-change-in-production"
    depends_on:
      - redis
    volumes:
      - superset-data:/app/superset_home

  langchain-api:
    image: 381491983173.dkr.ecr.us-east-1.amazonaws.com/langchain-api:latest
    container_name: langchain_api
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      PORT: 5000
      DEBUG: "false"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  redis-data:
  superset-data:
EOF

# Set ECR_REGISTRY in environment
echo "ECR_REGISTRY=$ECR_REGISTRY" > .env

sudo aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 381491983173.dkr.ecr.us-east-1.amazonaws.com

# Pull all images
log "🐳 Pulling Docker images from ECR..."
sudo docker-compose pull

# Start the stack
log "🚀 Starting Superset stack..."
sudo docker-compose up -d

# Wait for initialization
log "⏳ Waiting for services to initialize..."
sleep 60

# Health checks
log "🏥 Performing health checks..."
if curl -f http://localhost:8088/health > /dev/null 2>&1; then
    log "✅ Superset is healthy"
else
    log "⚠️  Superset health check failed - may still be initializing"
fi

if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    log "✅ LangChain API is healthy"
else
    log "❌ LangChain API health check failed"
fi

# Display container status
log "📊 Container status:"
sudo docker-compose ps | tee -a /var/log/user-data.log


# ========================================
# RDS 초기 데이터 생성
# ========================================
echo "Initializing RDS with sample data..."

# Install Python packages for data generation
pip3 install psycopg2-binary faker

# Create data generation script
cat > /tmp/init_rds_data.py << 'PYTHON_EOF'
#import psycopg2
from psycopg2.extras import execute_batch
import random
from datetime import datetime, timedelta
from faker import Faker

# ========================
# Configuration
# ========================

DB_CONFIG = {
    'host': 'superset-hackathon-postgres.cm1822i8mf8x.us-east-1.rds.amazonaws.com',
    'database': 'superset',
    'user': 'supersetuser',
    'password': 'SupersetHackathon2024!',
    'port': 5432
}

CONFIG = {
    'days': 30,
    'total_users': 2000,
    'total_products': 200,
    'daily_dau_range': (400, 600)
}

CITIES = ['서울', '부산', '대구', '인천', '광주', '대전']
AGE_GROUPS = ['20-29', '30-39', '40-49', '50+']
CATEGORIES = ['패션', '뷰티', '식품', '가전', '생활용품']
DEVICE_TYPES = ['mobile', 'desktop', 'tablet']
EVENT_TYPES = ['session', 'order', 'view']

# ========================
# Database Setup
# ========================

def create_tables(conn):
    """테이블 생성"""
    cursor = conn.cursor()
    
    drop_sql = """
        DROP TABLE IF EXISTS events CASCADE;
        DROP TABLE IF EXISTS products CASCADE;
        DROP TABLE IF EXISTS users CASCADE;
    """
    
    create_sql = """
    CREATE TABLE ecommerce_users (
        user_id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        created_at TIMESTAMP NOT NULL,
        city VARCHAR(50),
        age_group VARCHAR(20)
    );
    
    CREATE TABLE ecommerce_products (
        product_id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        category VARCHAR(50) NOT NULL,
        price DECIMAL(10, 2) NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    CREATE TABLE ecommerce_events (
        event_id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES ecommerce_users(user_id),
        event_type VARCHAR(20) NOT NULL,
        product_id INTEGER REFERENCES ecommerce_products(product_id),
        quantity INTEGER,
        amount DECIMAL(10, 2),
        device_type VARCHAR(20),
        created_at TIMESTAMP NOT NULL
    );
    
    CREATE INDEX idx_events_user_id ON ecommerce_events(user_id);
    CREATE INDEX idx_events_type ON ecommerce_events(event_type);
    CREATE INDEX idx_events_date ON ecommerce_events(created_at);
    """
    
    cursor.execute(drop_sql)
    cursor.execute(create_sql)
    conn.commit()
    print("✅ 테이블 생성 완료 (users, products, events)")

# ========================
# Data Generation
# ========================

def generate_users(conn, total_users, start_date, end_date):
    """사용자 생성"""
    cursor = conn.cursor()
    faker = Faker('ko_KR')
    
    users = []
    days = (end_date - start_date).days
    user_count = 0
    
    for day in range(days + 1):
        current_date = start_date + timedelta(days=day)
        daily_signups = random.randint(50, 100)
        
        for _ in range(daily_signups):
            signup_time = current_date + timedelta(
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            email = f"user{user_count}_{faker.user_name()}@example.com"
            user_count += 1
            
            users.append((
                email,
                signup_time,
                random.choice(CITIES),
                random.choice(AGE_GROUPS)
            ))
    
    execute_batch(cursor, """
        INSERT INTO ecommerce_users (email, created_at, city, age_group)
        VALUES (%s, %s, %s, %s)
    """, users)
    
    conn.commit()
    print(f"✅ {len(users)}명 사용자 생성 완료")

def generate_products(conn, total_products):
    """상품 생성"""
    cursor = conn.cursor()
    faker = Faker('ko_KR')
    
    products = []
    for _ in range(total_products):
        products.append((
            faker.catch_phrase(),
            random.choice(CATEGORIES),
            round(random.uniform(5000, 200000), -3)
        ))
    
    execute_batch(cursor, """
        INSERT INTO ecommerce_products (name, category, price)
        VALUES (%s, %s, %s)
    """, products)
    
    conn.commit()
    print(f"✅ {total_products}개 상품 생성 완료")

def generate_daily_events(conn, date, dau_range):
    """일별 이벤트 생성"""
    cursor = conn.cursor()
    
    # 활성 사용자 선택
    cursor.execute("""
        SELECT user_id FROM ecommerce_users 
        WHERE created_at <= %s 
        ORDER BY RANDOM() 
        LIMIT %s
    """, (date, random.randint(*dau_range)))
    
    active_users = [row[0] for row in cursor.fetchall()]
    
    # 상품 목록
    cursor.execute("SELECT product_id, price FROM ecommerce_products")
    products = cursor.fetchall()
    
    events = []
    
    for user_id in active_users:
        # 세션 이벤트 (1-3개)
        num_sessions = random.randint(1, 3)
        
        for _ in range(num_sessions):
            session_time = date + timedelta(
                hours=random.randint(9, 22),
                minutes=random.randint(0, 59)
            )
            
            # 세션 이벤트
            events.append((
                user_id,
                'session',
                None,  # product_id
                None,  # quantity
                None,  # amount
                random.choice(DEVICE_TYPES),
                session_time
            ))
            
            # 상품 조회 이벤트 (세션당 3-10개)
            num_views = random.randint(3, 10)
            viewed_products = random.sample(products, min(num_views, len(products)))
            
            for product_id, price in viewed_products:
                view_time = session_time + timedelta(seconds=random.randint(10, 300))
                
                events.append((
                    user_id,
                    'view',
                    product_id,
                    None,  # quantity
                    None,  # amount
                    None,  # device_type
                    view_time
                ))
                
                # 5% 확률로 주문 이벤트
                if random.random() < 0.05:
                    quantity = random.randint(1, 3)
                    total_amount = price * quantity
                    order_time = view_time + timedelta(minutes=random.randint(1, 30))
                    
                    events.append((
                        user_id,
                        'order',
                        product_id,
                        quantity,
                        total_amount,
                        None,  # device_type
                        order_time
                    ))
    
    # 이벤트 삽입
    if events:
        execute_batch(cursor, """
            INSERT INTO ecommerce_events (user_id, event_type, product_id, quantity, amount, device_type, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, events)
    
    conn.commit()
    return len(active_users), len([e for e in events if e[1] == 'order'])

# ========================
# Validation & Analysis
# ========================

def validate_data(conn):
    """데이터 검증"""
    cursor = conn.cursor()
    
    validations = [
        ("총 사용자 수", "SELECT COUNT(*) FROM ecommerce_users"),
        ("총 상품 수", "SELECT COUNT(*) FROM ecommerce_products"),
        ("총 이벤트 수", "SELECT COUNT(*) FROM ecommerce_events"),
        ("세션 이벤트", "SELECT COUNT(*) FROM ecommerce_events WHERE event_type = 'session'"),
        ("조회 이벤트", "SELECT COUNT(*) FROM ecommerce_events WHERE event_type = 'view'"),
        ("주문 이벤트", "SELECT COUNT(*) FROM ecommerce_events WHERE event_type = 'order'"),
        ("평균 DAU", """
            SELECT ROUND(AVG(dau), 0) FROM (
                SELECT DATE(created_at) as date, COUNT(DISTINCT user_id) as dau
                FROM ecommerce_events WHERE event_type = 'session'
                GROUP BY DATE(created_at)
            ) daily_stats
        """),
        ("총 매출", """
            SELECT COALESCE(SUM(amount), 0) 
            FROM ecommerce_events 
            WHERE event_type = 'order'
        """),
        ("주문 전환율 (%)", """
            SELECT ROUND(
                COUNT(DISTINCT CASE WHEN event_type = 'order' THEN user_id END) * 100.0 / 
                COUNT(DISTINCT CASE WHEN event_type = 'session' THEN user_id END), 2
            ) FROM events
        """),
        ("데이터 무결성", """
            SELECT COUNT(*) FROM ecommerce_events e
            LEFT JOIN ecommerce_users u ON e.user_id = u.user_id
            WHERE u.user_id IS NULL
        """)
    ]
    
    print("\n📊 데이터 검증 결과:")
    for name, query in validations:
        cursor.execute(query)
        result = cursor.fetchone()[0]
        if name == "데이터 무결성":
            status = "✅" if result == 0 else "❌"
            print(f"  {status} {name}: {result} (0이어야 정상)")
        else:
            print(f"  ✅ {name}: {result:,}")

def export_sample_queries(conn):
    """샘플 쿼리 실행 및 결과 출력"""
    cursor = conn.cursor()
    
    sample_queries = [
        ("최근 7일 일별 DAU", """
            SELECT DATE(created_at) as date, COUNT(DISTINCT user_id) as dau
            FROM ecommerce_events 
            WHERE event_type = 'session' 
            AND created_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """),
        ("카테고리별 매출 TOP 5", """
            SELECT p.category, 
                   COUNT(*) as orders, 
                   SUM(e.amount) as revenue
            FROM ecommerce_events e
            JOIN ecommerce_products p ON e.product_id = p.product_id
            WHERE e.event_type = 'order'
            GROUP BY p.category
            ORDER BY revenue DESC
            LIMIT 5
        """),
        ("디바이스별 세션 현황", """
            SELECT device_type, 
                   COUNT(*) as sessions,
                   COUNT(DISTINCT user_id) as unique_users
            FROM ecommerce_events
            WHERE event_type = 'session'
            GROUP BY device_type
            ORDER BY sessions DESC
        """),
        ("베스트셀러 상품 TOP 5", """
            SELECT p.name, p.category,
                   COUNT(*) as orders,
                   SUM(e.amount) as revenue
            FROM ecommerce_events e
            JOIN products p ON e.product_id = p.product_id
            WHERE e.event_type = 'order'
            GROUP BY p.product_id, p.name, p.category
            ORDER BY orders DESC
            LIMIT 5
        """)
    ]
    
    print("\n🔍 샘플 쿼리 결과:")
    for name, query in sample_queries:
        print(f"\n{name}:")
        cursor.execute(query)
        results = cursor.fetchall()
        for row in results[:5]:
            print(f"  {row}")

# ========================
# Main Execution
# ========================

def main():
    """메인 실행 함수"""
    print("🚀 Ultra Simple E-Commerce Mock 데이터 생성 시작")
    start_time = datetime.now()
    
    try:
        # DB 연결
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ 데이터베이스 연결 성공")
        
        # 1. 테이블 생성
        create_tables(conn)
        
        # 2. 마스터 데이터 생성
        print("\n📦 마스터 데이터 생성 중...")
        generate_products(conn, CONFIG['total_products'])
        
        # 3. 사용자 생성
        print("\n👥 사용자 데이터 생성 중...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=CONFIG['days'])
        generate_users(conn, CONFIG['total_users'], start_date, end_date)
        
        # 4. 일별 이벤트 데이터 생성
        print("\n📈 일별 이벤트 데이터 생성 중...")
        current_date = start_date
        total_dau = 0
        total_orders = 0
        
        while current_date <= end_date:
            print(f"  - {current_date.strftime('%Y-%m-%d')} 처리 중...")
            
            # 주말은 활동 감소
            dau_range = CONFIG['daily_dau_range']
            if current_date.weekday() >= 5:
                dau_range = (int(dau_range[0] * 0.7), int(dau_range[1] * 0.7))
            
            dau, orders = generate_daily_events(conn, current_date, dau_range)
            total_dau += dau
            total_orders += orders
            
            current_date += timedelta(days=1)
        
        # 5. 검증 및 샘플 쿼리
        validate_data(conn)
        export_sample_queries(conn)
        
        # 6. 완료
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n✅ 데이터 생성 완료! (소요시간: {elapsed:.1f}초)")
        print(f"📊 요약: 평균 DAU {total_dau//CONFIG['days']:,}명, 총 주문 {total_orders:,}건")
        
    except psycopg2.Error as e:
        print(f"❌ 데이터베이스 에러: {e}")
        return False
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
PYTHON_EOF

# Run the initialization script
python3 /tmp/init_rds_data.py

# Start Docker Compose
echo "Starting Superset services..."
docker-compose up -d

# Wait for Superset to be ready
sleep 30

# Initialize Superset
echo "Initializing Superset..."
sudo docker-compose exec -T superset superset db upgrade
sudo docker-compose exec -T superset superset init

# Create admin user
sudo docker-compose exec -T superset superset fab create-admin \
  --username admin \
  --firstname Admin \
  --lastname Admin \
  --email admin@example.com \
  --password admin || echo "Admin user might already exist"

# Set permissions
chown -R ec2-user:ec2-user /opt/superset

log "🎉 EC2 initialization completed!"
log "📍 Services available at:"
log "   - Superset: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
log "   - Superset Admin: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8088"
log "   - LangChain API: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):5000"
log ""
log "📝 To check logs: docker-compose logs -f [service-name]"
log "📝 To restart services: cd /opt/superset && docker-compose restart"
