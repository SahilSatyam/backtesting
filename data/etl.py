"""
ETL (Extract, Transform, Load) pipeline for stock data.
"""
import logging
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from data.fetcher import data_fetcher
from data.alternative_fetcher import alternative_data_fetcher
from database.operations import (
    get_or_create_stock, insert_daily_prices, get_price_dataframe,
    get_stock_count, get_price_count, get_last_price_date
)
from config.settings import DEFAULT_STOCKS, DEFAULT_START_DATE, DEFAULT_END_DATE

logger = logging.getLogger(__name__)

class ETLPipeline:
    """ETL pipeline for stock data processing."""
    
    def __init__(self):
        self.fetcher = data_fetcher
    
    def extract_stock_data(self, symbol: str, start_date: date, end_date: date) -> Optional[pd.DataFrame]:
        """Extract stock data from external sources."""
        logger.info(f"Extracting data for {symbol} from {start_date} to {end_date}")
        
        # Try main fetcher first
        data = self.fetcher.fetch_stock_data(symbol, start_date, end_date)
        
        if data is None or data.empty:
            logger.warning(f"Main fetcher failed for {symbol}, trying alternative fetcher...")
            # Try alternative fetcher
            data = alternative_data_fetcher.fetch_stock_data(symbol, start_date, end_date)
        
        if data is None or data.empty:
            logger.error(f"No data extracted for {symbol} from any source")
            return None
        
        # Validate data quality
        if not self.fetcher.validate_data(data):
            logger.error(f"Data validation failed for {symbol}")
            return None
        
        logger.info(f"Successfully extracted {len(data)} records for {symbol}")
        return data
    
    def transform_stock_data(self, data: pd.DataFrame, symbol: str) -> List[Dict[str, Any]]:
        """Transform raw data into database format."""
        logger.info(f"Transforming data for {symbol}")
        
        if data is None or data.empty:
            return []
        
        # Clean and transform data
        transformed_data = []
        
        for _, row in data.iterrows():
            # Handle missing values
            price_data = {
                'date': row['date'],
                'open': float(row['open']) if pd.notna(row['open']) else None,
                'high': float(row['high']) if pd.notna(row['high']) else None,
                'low': float(row['low']) if pd.notna(row['low']) else None,
                'close': float(row['close']) if pd.notna(row['close']) else None,
                'volume': int(row['volume']) if pd.notna(row['volume']) else None
            }
            
            # Additional data quality checks
            if price_data['close'] is not None and price_data['close'] <= 0:
                logger.warning(f"Skipping invalid close price for {symbol} on {price_data['date']}")
                continue
            
            if price_data['volume'] is not None and price_data['volume'] < 0:
                logger.warning(f"Skipping invalid volume for {symbol} on {price_data['date']}")
                continue
            
            transformed_data.append(price_data)
        
        logger.info(f"Transformed {len(transformed_data)} records for {symbol}")
        return transformed_data
    
    def load_stock_data(self, symbol: str, price_data: List[Dict[str, Any]]) -> bool:
        """Load stock data into database."""
        if not price_data:
            logger.warning(f"No data to load for {symbol}")
            return False
        
        try:
            # Get or create stock record
            stock_info = self.fetcher.get_stock_info(symbol)
            stock = get_or_create_stock(
                symbol=symbol,
                company_name=stock_info.get('company_name'),
                sector=stock_info.get('sector')
            )
            
            if stock is None:
                logger.error(f"Failed to create stock record for {symbol}")
                return False
            
            # Insert price data
            success = insert_daily_prices(stock.id, price_data)
            
            if success:
                logger.info(f"Successfully loaded {len(price_data)} records for {symbol}")
            else:
                logger.error(f"Failed to load data for {symbol}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error loading data for {symbol}: {e}")
            return False
    
    def process_single_stock(self, symbol: str, start_date: date = None, end_date: date = None, 
                           incremental: bool = True) -> bool:
        """
        Process a single stock through the ETL pipeline.
        
        Args:
            symbol: Stock symbol
            start_date: Start date for data fetching (if None, will use incremental logic)
            end_date: End date for data fetching (if None, will use today's date)
            incremental: Whether to use incremental fetching (only fetch new data)
        """
        try:
            logger.info(f"Processing ETL for {symbol}")
            
            # Determine fetch dates
            if end_date is None:
                end_date = datetime.now().date()
            
            if start_date is None and incremental:
                # Get the last date we have data for this symbol
                last_date = get_last_price_date(symbol)
                if last_date:
                    # Start from the next day after the last date we have
                    start_date = last_date + timedelta(days=1)
                    logger.info(f"Incremental fetch for {symbol}: fetching from {start_date} to {end_date}")
                else:
                    # No existing data, use default start date
                    start_date = datetime.strptime(DEFAULT_START_DATE, '%Y-%m-%d').date()
                    logger.info(f"Initial fetch for {symbol}: fetching from {start_date} to {end_date}")
            elif start_date is None:
                # Non-incremental mode, use default start date
                start_date = datetime.strptime(DEFAULT_START_DATE, '%Y-%m-%d').date()
            
            # Check if we need to fetch any data
            if start_date > end_date:
                logger.info(f"No new data to fetch for {symbol} (last date: {last_date}, today: {end_date})")
                return True
            
            # Extract data
            raw_data = self.extract_stock_data(symbol, start_date, end_date)
            if raw_data is None or raw_data.empty:
                logger.info(f"No new data available for {symbol} from {start_date} to {end_date}")
                return True  # Consider this a success as there's no new data
            
            # Transform data
            transformed_data = self.transform_stock_data(raw_data, symbol)
            if not transformed_data:
                logger.error(f"Failed to transform data for {symbol}")
                return False
            
            # Load data
            success = self.load_stock_data(symbol, transformed_data)
            if success:
                logger.info(f"Successfully processed ETL for {symbol} ({len(transformed_data)} new records)")
            else:
                logger.error(f"Failed to load data for {symbol}")
            
            return success
            
        except Exception as e:
            logger.error(f"ETL processing failed for {symbol}: {e}")
            return False
    
    def process_multiple_stocks(self, symbols: List[str], start_date: date = None, end_date: date = None, 
                              incremental: bool = True) -> Dict[str, bool]:
        """
        Process multiple stocks through the ETL pipeline.
        
        Args:
            symbols: List of stock symbols
            start_date: Start date for data fetching (if None, will use incremental logic)
            end_date: End date for data fetching (if None, will use today's date)
            incremental: Whether to use incremental fetching (only fetch new data)
        """
        logger.info(f"Processing ETL for {len(symbols)} stocks (incremental: {incremental})")
        
        results = {}
        
        for symbol in symbols:
            logger.info(f"Processing {symbol} ({symbols.index(symbol) + 1}/{len(symbols)})")
            
            success = self.process_single_stock(symbol, start_date, end_date, incremental)
            results[symbol] = success
            
            # Add delay between stocks to avoid rate limiting
            import time
            time.sleep(2)
        
        # Summary
        successful = sum(results.values())
        failed = len(results) - successful
        
        logger.info(f"ETL Summary: {successful} successful, {failed} failed")
        
        return results
    
    def update_existing_data(self, symbol: str, days_back: int = 30) -> bool:
        """Update existing stock data with recent data."""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        logger.info(f"Updating data for {symbol} from {start_date} to {end_date}")
        
        return self.process_single_stock(symbol, start_date, end_date)
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of data in database."""
        try:
            stock_count = get_stock_count()
            price_count = get_price_count()
            
            return {
                'total_stocks': stock_count,
                'total_price_records': price_count,
                'average_records_per_stock': price_count / stock_count if stock_count > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting data summary: {e}")
            return {}

# Global ETL pipeline instance
etl_pipeline = ETLPipeline()

def run_etl(symbols: List[str] = None, start_date: str = None, end_date: str = None, 
           incremental: bool = True):
    """
    Run the ETL pipeline for specified stocks and date range.
    
    Args:
        symbols: List of stock symbols (if None, uses DEFAULT_STOCKS)
        start_date: Start date in YYYY-MM-DD format (if None, uses incremental logic)
        end_date: End date in YYYY-MM-DD format (if None, uses today's date)
        incremental: Whether to use incremental fetching (only fetch new data)
    """
    if symbols is None:
        symbols = DEFAULT_STOCKS
    
    # Convert string dates to date objects if provided
    start_dt = None
    end_dt = None
    
    if start_date:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    if end_date:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    logger.info(f"Starting ETL pipeline for {len(symbols)} stocks")
    if incremental:
        logger.info("Mode: Incremental (only fetching new data)")
    else:
        logger.info(f"Mode: Full fetch (date range: {start_dt} to {end_dt})")
    
    results = etl_pipeline.process_multiple_stocks(symbols, start_dt, end_dt, incremental)
    
    # Print summary
    print("\nETL Results Summary:")
    print("=" * 50)
    for symbol, success in results.items():
        status = "✓" if success else "✗"
        print(f"{status} {symbol}")
    
    successful_count = sum(results.values())
    print(f"\nTotal: {successful_count}/{len(symbols)} successful")
    
    return results

def update_recent_data(symbols: List[str] = None, days_back: int = 30):
    """Update recent data for specified stocks."""
    if symbols is None:
        symbols = DEFAULT_STOCKS
    
    logger.info(f"Updating recent data for {len(symbols)} stocks")
    
    results = {}
    for symbol in symbols:
        success = etl_pipeline.update_existing_data(symbol, days_back)
        results[symbol] = success
    
    return results

def run_daily_update(symbols: List[str] = None):
    """
    Run daily ETL update - fetches only the latest data since last fetch.
    This is the recommended function for regular daily updates.
    """
    if symbols is None:
        symbols = DEFAULT_STOCKS
    
    logger.info(f"Running daily ETL update for {len(symbols)} stocks")
    
    # Use incremental mode to only fetch new data
    return run_etl(symbols=symbols, incremental=True)

def get_etl_status(symbols: List[str] = None) -> Dict[str, Any]:
    """
    Get the status of ETL data for specified symbols.
    Shows the latest date for each symbol and whether updates are needed.
    """
    if symbols is None:
        symbols = DEFAULT_STOCKS
    
    status = {}
    today = datetime.now().date()
    
    for symbol in symbols:
        last_date = get_last_price_date(symbol)
        if last_date:
            days_since_update = (today - last_date).days
            needs_update = days_since_update > 0
            status[symbol] = {
                'last_date': last_date,
                'days_since_update': days_since_update,
                'needs_update': needs_update
            }
        else:
            status[symbol] = {
                'last_date': None,
                'days_since_update': None,
                'needs_update': True
            }
    
    return status
