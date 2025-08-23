"""
Database configuration and connection settings.
"""
from config.settings import DB_CONFIG
import logging

logger = logging.getLogger(__name__)

# SQLAlchemy database URL with better error handling
def build_database_url():
    """Build database URL with proper error handling."""
    try:
        # Ensure all required fields are present
        required_fields = ['user', 'password', 'host', 'port', 'database']
        for field in required_fields:
            if field not in DB_CONFIG:
                raise ValueError(f"Missing required database configuration field: {field}")
        
        # Clean and validate values
        user = str(DB_CONFIG['user']).strip()
        password = str(DB_CONFIG['password']).strip()
        host = str(DB_CONFIG['host']).strip()
        port = int(DB_CONFIG['port'])
        database = str(DB_CONFIG['database']).strip()
        
        # Validate port number
        if port <= 0 or port > 65535:
            raise ValueError(f"Invalid port number: {port}")
        
        # Build URL
        if password:
            url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        else:
            url = f"postgresql://{user}@{host}:{port}/{database}"
        
        logger.info(f"Database URL constructed successfully for host: {host}, port: {port}")
        return url
        
    except Exception as e:
        logger.error(f"Error building database URL: {e}")
        logger.error(f"DB_CONFIG: {DB_CONFIG}")
        raise

# Build the database URL
DATABASE_URL = build_database_url()

# Database engine configuration
ENGINE_CONFIG = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_pre_ping': True,
    'pool_recycle': 3600,
    'echo': False,  # Set to True for SQL query logging
}

# Table creation SQL
CREATE_TABLES_SQL = {
    'stocks': """
        CREATE TABLE IF NOT EXISTS stocks (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) UNIQUE NOT NULL,
            company_name VARCHAR(200),
            sector VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """,
    
    'daily_prices': """
        CREATE TABLE IF NOT EXISTS daily_prices (
            id SERIAL PRIMARY KEY,
            stock_id INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
            date DATE NOT NULL,
            open DECIMAL(10, 2),
            high DECIMAL(10, 2),
            low DECIMAL(10, 2),
            close DECIMAL(10, 2),
            volume BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(stock_id, date)
        );
    """
}

# Index creation SQL
CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_daily_prices_stock_date ON daily_prices(stock_id, date);",
    "CREATE INDEX IF NOT EXISTS idx_daily_prices_date ON daily_prices(date);",
    "CREATE INDEX IF NOT EXISTS idx_stocks_symbol ON stocks(symbol);",
]

# Database initialization SQL
INIT_DB_SQL = """
    -- Create database if not exists (run as superuser)
    SELECT 'CREATE DATABASE stock_backtesting'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'stock_backtesting');
"""
