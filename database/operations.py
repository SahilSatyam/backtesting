"""
Database operations for creating tables, inserting data, and querying.
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from database.connection import db_manager
from database.models import Base, Stock, DailyPrice
from config.database import CREATE_TABLES_SQL, CREATE_INDEXES_SQL

logger = logging.getLogger(__name__)

def init_database():
    """Initialize database tables and indexes."""
    try:
        # Create tables
        Base.metadata.create_all(bind=db_manager.engine)
        logger.info("Database tables created successfully")
        
        # Create indexes
        with db_manager.get_session() as session:
            for index_sql in CREATE_INDEXES_SQL:
                session.execute(text(index_sql))
            session.commit()
        logger.info("Database indexes created successfully")
        
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def create_stock(symbol: str, company_name: str = None, sector: str = None) -> Optional[Stock]:
    """Create a new stock record."""
    try:
        with db_manager.get_session() as session:
            stock = Stock(
                symbol=symbol.upper(),
                company_name=company_name,
                sector=sector
            )
            session.add(stock)
            session.commit()
            session.refresh(stock)
            logger.info(f"Created stock: {symbol}")
            return stock
    except IntegrityError:
        logger.warning(f"Stock {symbol} already exists")
        return get_stock_by_symbol(symbol)
    except SQLAlchemyError as e:
        logger.error(f"Failed to create stock {symbol}: {e}")
        return None

def get_stock_by_symbol(symbol: str) -> Optional[Stock]:
    """Get stock by symbol."""
    try:
        with db_manager.get_session() as session:
            stock = session.query(Stock).filter(Stock.symbol == symbol.upper()).first()
            return stock
    except SQLAlchemyError as e:
        logger.error(f"Failed to get stock {symbol}: {e}")
        return None

def get_or_create_stock(symbol: str, company_name: str = None, sector: str = None) -> Stock:
    """Get existing stock or create new one."""
    try:
        with db_manager.get_session() as session:
            # Try to get existing stock
            stock = session.query(Stock).filter(Stock.symbol == symbol.upper()).first()
            
            if stock is None:
                # Create new stock
                stock = Stock(
                    symbol=symbol.upper(),
                    company_name=company_name,
                    sector=sector
                )
                session.add(stock)
                session.commit()
                session.refresh(stock)
                logger.info(f"Created new stock: {symbol}")
            else:
                logger.info(f"Found existing stock: {symbol}")
            
            # Return a fresh copy of the stock object to avoid session binding issues
            stock_id = stock.id
            stock_symbol = stock.symbol
            stock_company_name = stock.company_name
            stock_sector = stock.sector
            
            # Create a new Stock object that's not bound to any session
            detached_stock = Stock(
                id=stock_id,
                symbol=stock_symbol,
                company_name=stock_company_name,
                sector=stock_sector
            )
            
            return detached_stock
            
    except IntegrityError:
        logger.warning(f"Stock {symbol} already exists")
        # Try to get it again
        return get_stock_by_symbol(symbol)
    except SQLAlchemyError as e:
        logger.error(f"Failed to get or create stock {symbol}: {e}")
        return None

def insert_daily_prices(stock_id: int, prices_data: List[Dict[str, Any]]) -> bool:
    """Insert daily price data for a stock."""
    try:
        with db_manager.get_session() as session:
            for price_data in prices_data:
                daily_price = DailyPrice(
                    stock_id=stock_id,
                    date=price_data['date'],
                    open=price_data.get('open'),
                    high=price_data.get('high'),
                    low=price_data.get('low'),
                    close=price_data.get('close'),
                    volume=price_data.get('volume')
                )
                session.add(daily_price)
            session.commit()
            logger.info(f"Inserted {len(prices_data)} price records for stock_id {stock_id}")
            return True
    except IntegrityError as e:
        logger.warning(f"Some price records already exist for stock_id {stock_id}: {e}")
        return True  # Consider this a success as data exists
    except SQLAlchemyError as e:
        logger.error(f"Failed to insert price data for stock_id {stock_id}: {e}")
        return False

def get_daily_prices(symbol: str, start_date: date = None, end_date: date = None) -> List[DailyPrice]:
    """Get daily prices for a stock within date range."""
    try:
        with db_manager.get_session() as session:
            query = session.query(DailyPrice).join(Stock).filter(Stock.symbol == symbol.upper())
            
            if start_date:
                query = query.filter(DailyPrice.date >= start_date)
            if end_date:
                query = query.filter(DailyPrice.date <= end_date)
            
            prices = query.order_by(DailyPrice.date).all()
            logger.info(f"Retrieved {len(prices)} price records for {symbol}")
            return prices
    except SQLAlchemyError as e:
        logger.error(f"Failed to get price data for {symbol}: {e}")
        return []

def get_price_dataframe(symbol: str, start_date: date = None, end_date: date = None):
    """Get price data as pandas DataFrame."""
    import pandas as pd
    
    try:
        with db_manager.get_session() as session:
            # Query the data directly in the session
            query = session.query(DailyPrice).join(Stock).filter(Stock.symbol == symbol.upper())
            
            if start_date:
                query = query.filter(DailyPrice.date >= start_date)
            if end_date:
                query = query.filter(DailyPrice.date <= end_date)
            
            # Execute query and fetch all results
            prices = query.order_by(DailyPrice.date).all()
            
            if not prices:
                logger.warning(f"No price data found for {symbol}")
                return pd.DataFrame()
            
            # Convert to list of dictionaries while still in session
            data = []
            for price in prices:
                data.append({
                    'date': price.date,
                    'open': float(price.open) if price.open else None,
                    'high': float(price.high) if price.high else None,
                    'low': float(price.low) if price.low else None,
                    'close': float(price.close) if price.close else None,
                    'volume': price.volume
                })
            
            logger.info(f"Retrieved {len(data)} price records for {symbol}")
            
            # Create DataFrame from the data
            df = pd.DataFrame(data)
            if not df.empty:
                df.set_index('date', inplace=True)
                df.sort_index(inplace=True)
            
            return df
            
    except SQLAlchemyError as e:
        logger.error(f"Failed to get price data for {symbol}: {e}")
        return pd.DataFrame()

def get_all_stocks() -> List[Stock]:
    """Get all stocks from database."""
    try:
        with db_manager.get_session() as session:
            stocks = session.query(Stock).all()
            return stocks
    except SQLAlchemyError as e:
        logger.error(f"Failed to get stocks: {e}")
        return []

def get_stock_count() -> int:
    """Get total number of stocks."""
    try:
        with db_manager.get_session() as session:
            count = session.query(Stock).count()
            return count
    except SQLAlchemyError as e:
        logger.error(f"Failed to get stock count: {e}")
        return 0

def get_price_count(symbol: str = None) -> int:
    """Get total number of price records."""
    try:
        with db_manager.get_session() as session:
            query = session.query(DailyPrice)
            if symbol:
                query = query.join(Stock).filter(Stock.symbol == symbol.upper())
            count = query.count()
            return count
    except SQLAlchemyError as e:
        logger.error(f"Failed to get price count: {e}")
        return 0

def get_last_price_date(symbol: str) -> Optional[date]:
    """Get the latest date for which price data exists for a stock."""
    try:
        with db_manager.get_session() as session:
            latest_price = session.query(DailyPrice).join(Stock).filter(
                Stock.symbol == symbol.upper()
            ).order_by(DailyPrice.date.desc()).first()
            
            if latest_price:
                logger.info(f"Latest price date for {symbol}: {latest_price.date}")
                return latest_price.date
            else:
                logger.info(f"No price data found for {symbol}")
                return None
                
    except SQLAlchemyError as e:
        logger.error(f"Failed to get latest price date for {symbol}: {e}")
        return None

def cleanup_old_data(days_to_keep: int = 365):
    """Clean up old price data."""
    try:
        cutoff_date = datetime.now().date() - timedelta(days=days_to_keep)
        with db_manager.get_session() as session:
            deleted = session.query(DailyPrice).filter(DailyPrice.date < cutoff_date).delete()
            session.commit()
            logger.info(f"Cleaned up {deleted} old price records")
            return deleted
    except SQLAlchemyError as e:
        logger.error(f"Failed to cleanup old data: {e}")
        return 0
