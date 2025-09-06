from langchain.tools import tool

@tool
def get_database_schema(table_name: str = "") -> str:
    """Get business context and domain knowledge about table schemas.
    
    Provides detailed semantic information including:
    - Column meanings and business purposes
    - Possible values and their meanings (e.g., city names, age groups)
    - Business rules and relationships between tables
    - Usage guidelines for different event types
    
    Best for: Understanding what the data MEANS from a business perspective.
    Use together with explore_table_structure for complete understanding.
    
    Args:
        table_name: Specific table name or empty for all tables
    
    Returns:
        Detailed business schema with column descriptions and domain values
    """
    
    table_schemas = {
        "ecommerce_users": """
ecommerce_users (사용자 마스터)
- user_id: SERIAL PRIMARY KEY (사용자 고유 ID)
- email: VARCHAR(255) UNIQUE NOT NULL (이메일 주소)
- created_at: TIMESTAMP NOT NULL (가입 일시)
- city: VARCHAR(50) (거주 도시: 서울, 부산, 대구, 인천, 광주, 대전)
- age_group: VARCHAR(20) (연령대: 20-29, 30-39, 40-49, 50+)
        """,
        "ecommerce_products": """
ecommerce_products (상품 마스터)
- product_id: SERIAL PRIMARY KEY (상품 고유 ID)
- name: VARCHAR(255) NOT NULL (상품명)
- category: VARCHAR(50) NOT NULL (카테고리: 패션, 뷰티, 식품, 가전, 생활용품)
- price: DECIMAL(10,2) NOT NULL (상품 가격)
- created_at: TIMESTAMP DEFAULT NOW() (상품 등록 일시)
        """,
        "ecommerce_events": """
ecommerce_events (모든 이벤트 통합)
- event_id: SERIAL PRIMARY KEY (이벤트 고유 ID)
- user_id: INTEGER REFERENCES ecommerce_users(user_id) (사용자 ID - ecommerce_users 테이블과 연결)
- event_type: VARCHAR(20) NOT NULL (이벤트 타입: 'session', 'view', 'order')
- product_id: INTEGER REFERENCES ecommerce_products(product_id) (상품 ID - ecommerce_products 테이블과 연결, view/order 시 사용)
- quantity: INTEGER (주문 수량, order 이벤트 시만 사용)
- amount: DECIMAL(10,2) (주문 금액, order 이벤트 시만 사용)
- device_type: VARCHAR(20) (디바이스: mobile/desktop/tablet, session 이벤트 시만 사용)
- created_at: TIMESTAMP NOT NULL (이벤트 발생 일시)

Event Types:
- session: 세션 시작 (device_type 필수)
- view: 상품 조회 (product_id 필수)
- order: 주문 (product_id, quantity, amount 필수)
        """
    }
    
    # 특정 테이블 요청 시
    if table_name and table_name.strip():
        table_name_lower = table_name.lower().strip()
        for key, schema in table_schemas.items():
            if key.lower() == table_name_lower:
                return schema
        return f"Table '{table_name}' not found. Available tables: ecommerce_users, ecommerce_products, ecommerce_events"
    
    # 전체 스키마 반환
    all_schema = "E-Commerce Database Schema:\n\n"
    all_schema += "테이블 관계:\n"
    all_schema += "- ecommerce_events.user_id → ecommerce_users.user_id (FK 관계)\n"
    all_schema += "- ecommerce_events.product_id → ecommerce_products.product_id (FK 관계)\n\n"
    
    for table, schema in table_schemas.items():
        all_schema += schema + "\n"
    
    return all_schema

@tool
def list_available_tables() -> str:
    """List predefined tables with their business domain descriptions.
    
    Returns a quick reference of available data domains in the e-commerce system.
    Use explore_table_structure to see actual tables in the live database.
    """
    return "Available tables: ecommerce_users, ecommerce_products, ecommerce_events"