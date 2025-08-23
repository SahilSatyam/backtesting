"""
Configuration settings for the backtesting system.
"""
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def validate_db_config():
    """Validate database configuration and provide helpful error messages."""
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'stock_backtesting'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
    }
    
    # Validate port number
    try:
        port = int(config['port'])
        if port <= 0 or port > 65535:
            raise ValueError(f"Invalid port number: {port}")
        config['port'] = port
    except ValueError as e:
        logger.error(f"Invalid port number in configuration: {config['port']}")
        logger.error("Please set DB_PORT to a valid number between 1 and 65535")
        raise
    
    # Validate other fields
    if not config['host'].strip():
        logger.error("DB_HOST is empty or invalid")
        raise ValueError("DB_HOST cannot be empty")
    
    if not config['database'].strip():
        logger.error("DB_NAME is empty or invalid")
        raise ValueError("DB_NAME cannot be empty")
    
    if not config['user'].strip():
        logger.error("DB_USER is empty or invalid")
        raise ValueError("DB_USER cannot be empty")
    
    logger.info(f"Database configuration validated: host={config['host']}, port={config['port']}, database={config['database']}, user={config['user']}")
    return config

# Database Configuration
try:
    DB_CONFIG = validate_db_config()
except Exception as e:
    logger.error("Database configuration validation failed!")
    logger.error("Please create a .env file with the following variables:")
    logger.error("DB_HOST=localhost")
    logger.error("DB_PORT=5432")
    logger.error("DB_NAME=stock_backtesting")
    logger.error("DB_USER=postgres")
    logger.error("DB_PASSWORD=your_password")
    logger.error(f"Error: {e}")
    # Use safe defaults for now
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'stock_backtesting',
        'user': 'postgres',
        'password': '',
    }

# API Configuration
API_CONFIG = {
    'nsepy_timeout': int(os.getenv('NSEPY_TIMEOUT', 30)),
    'yahoo_timeout': int(os.getenv('YAHOO_TIMEOUT', 30)),
}

# Default Settings
DEFAULT_START_DATE = os.getenv('DEFAULT_START_DATE', '2023-01-01')
# Default end date to yesterday (last working day)
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
DEFAULT_END_DATE = os.getenv('DEFAULT_END_DATE', yesterday)
DEFAULT_SHORT_WINDOW = int(os.getenv('DEFAULT_SHORT_WINDOW', 20))
DEFAULT_LONG_WINDOW = int(os.getenv('DEFAULT_LONG_WINDOW', 50))

# NIFTY 50 Stocks (as of August 2025)
DEFAULT_STOCKS = [
    # Major Sectors Representation
    'RELIANCE',    # Oil & Gas
    'TCS',         # IT
    'HDFCBANK',    # Banking
    'ICICIBANK',   # Banking
    'INFY',        # IT
    'HINDUNILVR',  # FMCG
    'ITC',         # FMCG
    'SBIN',        # Banking
    'BHARTIARTL',  # Telecom
    'KOTAKBANK',   # Banking
    'AXISBANK',    # Banking
    'ASIANPAINT',  # Consumer Goods
    'MARUTI',      # Automobile
    'HCLTECH',     # IT
    'SUNPHARMA',   # Pharma
    'TITAN',       # Consumer Goods
    'LT',          # Construction
    'BAJFINANCE',  # Financial Services
    'NTPC',        # Power
    'ONGC',        # Oil & Gas
    'NESTLEIND',   # FMCG
    'ULTRACEMCO',  # Cement
    'TATAMOTORS',  # Automobile
    'BAJAJFINSV',  # Financial Services
    'ADANIPORTS',  # Infrastructure
    'HDFCLIFE',    # Insurance
    'SBILIFE',     # Insurance
    'POWERGRID',   # Power
    'M&M',         # Automobile
    'TATASTEEL',   # Metals
    'GRASIM',      # Diversified
    'DIVISLAB',    # Pharma
    'JSWSTEEL',    # Metals
    'TATACONSUM',  # FMCG
    'BAJAJ-AUTO',  # Automobile
    'HINDALCO',    # Metals
    'CIPLA',       # Pharma
    'UPL',         # Chemicals
    'TECHM',       # IT
    'HDFCAMC',     # Financial Services
    'BRITANNIA',   # FMCG
    'EICHERMOT',   # Automobile
    'DRREDDY',     # Pharma
    'SHREECEM',    # Cement
    'COALINDIA',   # Mining
    'INDUSINDBK',  # Banking
    'HEROMOTOCO',  # Automobile
    'BPCL',        # Oil & Gas
    'ADANIENT',    # Diversified
    'WIPRO'        # IT
]

# Logging Configuration
LOG_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'file': os.getenv('LOG_FILE', 'backtesting.log'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}

# Backtesting Configuration
BACKTEST_CONFIG = {
    'initial_capital': 1000000,  # 1 million initial capital
    'commission': 0.001,  # 0.1% commission
    'slippage': 0.0005,   # 0.05% slippage
    'risk_free_rate': 0.06,  # 6% risk-free rate for Sharpe ratio
}

# Data Source Priority
DATA_SOURCES = ['nsepy', 'yahoo_finance']

# File paths
DATA_DIR = 'data_files'
RESULTS_DIR = 'results'
CHARTS_DIR = 'charts'
