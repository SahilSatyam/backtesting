"""
Data fetching module for stock market data from various sources.
"""
import logging
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import time
import requests
from nsepy import get_history
import yfinance as yf
from config.settings import API_CONFIG, DEFAULT_STOCKS

logger = logging.getLogger(__name__)

class DataFetcher:
    """Fetches stock data from various sources."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_nse_data(self, symbol: str, start_date: date, end_date: date) -> Optional[pd.DataFrame]:
        """Fetch data from NSE using NSEpy."""
        try:
            logger.info(f"Fetching NSE data for {symbol} from {start_date} to {end_date}")
            
            # Add .NS suffix for NSE stocks
            nse_symbol = f"{symbol}.NS" if not symbol.endswith('.NS') else symbol
            
            # Handle NSEpy's known bug with FrameLocalsProxy
            data = None
            try:
                # First try with .NS suffix
                data = get_history(
                    symbol=nse_symbol,
                    start=start_date,
                    end=end_date
                )
            except Exception as nse_error:
                error_msg = str(nse_error)
                if "FrameLocalsProxy" in error_msg:
                    logger.warning(f"NSEpy FrameLocalsProxy error for {symbol}, trying without .NS suffix")
                    try:
                        # Try without .NS suffix
                        data = get_history(
                            symbol=symbol,
                            start=start_date,
                            end=end_date
                        )
                    except Exception as fallback_error:
                        logger.error(f"NSEpy fallback also failed for {symbol}: {fallback_error}")
                        return None
                else:
                    logger.warning(f"NSEpy failed for {symbol}, trying without .NS suffix: {nse_error}")
                    try:
                        # Try without .NS suffix
                        data = get_history(
                            symbol=symbol,
                            start=start_date,
                            end=end_date
                        )
                    except Exception as fallback_error:
                        logger.error(f"NSEpy fallback also failed for {symbol}: {fallback_error}")
                        return None
            
            if data.empty:
                logger.warning(f"No NSE data found for {symbol}")
                return None
            
            # Clean and standardize column names
            data = data.reset_index()
            data.columns = [col.lower() for col in data.columns]
            
            # Rename columns to match our schema
            column_mapping = {
                'date': 'date',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            }
            
            data = data.rename(columns=column_mapping)
            data = data[list(column_mapping.values())]
            
            # Convert date to date type
            data['date'] = pd.to_datetime(data['date']).dt.date
            
            logger.info(f"Successfully fetched {len(data)} records for {symbol} from NSE")
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch NSE data for {symbol}: {e}")
            return None
    
    def fetch_yahoo_data(self, symbol: str, start_date: date, end_date: date) -> Optional[pd.DataFrame]:
        """Fetch data from Yahoo Finance."""
        try:
            logger.info(f"Fetching Yahoo Finance data for {symbol} from {start_date} to {end_date}")
            
            # Add .NS suffix for NSE stocks if not present
            yahoo_symbol = f"{symbol}.NS" if not symbol.endswith('.NS') else symbol
            
            ticker = yf.Ticker(yahoo_symbol)
            data = ticker.history(
                start=start_date,
                end=end_date,
                timeout=API_CONFIG['yahoo_timeout']
            )
            
            if data.empty:
                logger.warning(f"No Yahoo Finance data found for {symbol}")
                return None
            
            # Clean and standardize data
            data = data.reset_index()
            data.columns = [col.lower() for col in data.columns]
            
            # Rename columns to match our schema
            column_mapping = {
                'date': 'date',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            }
            
            data = data.rename(columns=column_mapping)
            data = data[list(column_mapping.values())]
            
            # Convert date to date type
            data['date'] = pd.to_datetime(data['date']).dt.date
            
            logger.info(f"Successfully fetched {len(data)} records for {symbol} from Yahoo Finance")
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch Yahoo Finance data for {symbol}: {e}")
            return None
    
    def fetch_stock_data(self, symbol: str, start_date: date, end_date: date, 
                        sources: List[str] = None) -> Optional[pd.DataFrame]:
        """Fetch stock data from multiple sources with fallback."""
        if sources is None:
            sources = ['nsepy', 'yahoo_finance']
        
        for source in sources:
            try:
                if source == 'nsepy':
                    data = self.fetch_nse_data(symbol, start_date, end_date)
                elif source == 'yahoo_finance':
                    data = self.fetch_yahoo_data(symbol, start_date, end_date)
                else:
                    logger.warning(f"Unknown data source: {source}")
                    continue
                
                if data is not None and not data.empty:
                    return data
                
                # Add delay between requests to avoid rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error fetching data from {source} for {symbol}: {e}")
                continue
        
        logger.error(f"Failed to fetch data for {symbol} from all sources")
        return None
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """Get basic stock information."""
        try:
            # Try Yahoo Finance for stock info
            yahoo_symbol = f"{symbol}.NS" if not symbol.endswith('.NS') else symbol
            ticker = yf.Ticker(yahoo_symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'company_name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', 0),
                'currency': info.get('currency', 'INR')
            }
            
        except Exception as e:
            logger.error(f"Failed to get stock info for {symbol}: {e}")
            return {
                'symbol': symbol,
                'company_name': '',
                'sector': '',
                'industry': '',
                'market_cap': 0,
                'currency': 'INR'
            }
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate fetched data quality."""
        if data is None or data.empty:
            return False
        
        # Check for required columns
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        if not all(col in data.columns for col in required_columns):
            logger.error("Missing required columns in data")
            return False
        
        # Check for null values in critical columns
        critical_columns = ['date', 'close']
        for col in critical_columns:
            if data[col].isnull().any():
                logger.warning(f"Found null values in {col} column")
        
        # Check for reasonable price values
        if (data['close'] <= 0).any():
            logger.error("Found invalid close prices (<= 0)")
            return False
        
        # Check for reasonable volume values
        if (data['volume'] < 0).any():
            logger.error("Found invalid volume values (< 0)")
            return False
        
        # Check date range
        if len(data) > 0:
            date_range = (data['date'].max() - data['date'].min()).days
            if date_range < 1:
                logger.warning("Data spans less than 1 day")
        
        return True

# Global fetcher instance
data_fetcher = DataFetcher()
