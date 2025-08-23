"""
Unified data fetching module using yfinance for reliable stock market data.
"""
import logging
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
import pandas as pd
import yfinance as yf
import time
import requests
from config.settings import API_CONFIG, DEFAULT_STOCKS

logger = logging.getLogger(__name__)

class UnifiedDataFetcher:
    """Unified data fetcher using yfinance with robust error handling."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.max_retries = API_CONFIG.get('max_retries', 3)
        self.retry_delay = API_CONFIG.get('retry_delay', 5)  # seconds
    
    def fetch_stock_data(self, symbol: str, start_date: date, end_date: date) -> Optional[pd.DataFrame]:
        """
        Fetch stock data for the given symbol and date range.
        
        Args:
            symbol: Stock symbol (with or without exchange suffix)
            start_date: Start date for data
            end_date: End date for data
            
        Returns:
            DataFrame with stock data or None if failed
        """
        # Try different symbol formats for maximum compatibility
        symbol_variants = [
            f"{symbol}.NS",  # NSE format
            f"{symbol}.BO",  # BSE format
            symbol,          # Plain symbol
            f"{symbol}.NSE", # Alternative NSE format
        ]
        
        last_error = None
        
        for attempt in range(self.max_retries):
            for symbol_variant in symbol_variants:
                try:
                    logger.info(f"Attempt {attempt + 1}: Fetching data for {symbol_variant} from {start_date} to {end_date}")
                    
                    ticker = yf.Ticker(symbol_variant)
                    data = ticker.history(
                        start=start_date,
                        end=end_date + timedelta(days=1),  # Include end date
                        timeout=API_CONFIG.get('yahoo_timeout', 30)
                    )
                    
                    if not data.empty:
                        # Clean and standardize column names
                        data = data.rename(columns={
                            'Open': 'open',
                            'High': 'high',
                            'Low': 'low',
                            'Close': 'close',
                            'Volume': 'volume',
                            'Dividends': 'dividends',
                            'Stock Splits': 'splits'
                        })
                        
                        # Add symbol and date index as a column
                        data['symbol'] = symbol
                        data.index.name = 'date'
                        data = data.reset_index()
                        
                        logger.info(f"Successfully fetched {len(data)} records for {symbol}")
                        return data
                        
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"Failed to fetch {symbol_variant}: {last_error}")
                    time.sleep(self.retry_delay)
        
        logger.error(f"Failed to fetch data for {symbol} after {self.max_retries} attempts: {last_error}")
        return None
    
    def fetch_multiple_stocks(self, symbols: List[str], start_date: date, end_date: date) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple stock symbols.
        
        Args:
            symbols: List of stock symbols
            start_date: Start date for data
            end_date: End date for data
            
        Returns:
            Dictionary mapping symbols to their DataFrames
        """
        results = {}
        
        for symbol in symbols:
            data = self.fetch_stock_data(symbol, start_date, end_date)
            if data is not None:
                results[symbol] = data
            time.sleep(1)  # Be nice to the API
            
        return results
        
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get basic stock information.
        
        Args:
            symbol: Stock symbol (with or without exchange suffix)
            
        Returns:
            Dictionary containing stock information
        """
        try:
            # Try different symbol formats for maximum compatibility
            symbol_variants = [
                f"{symbol}.NS",  # NSE format
                f"{symbol}.BO",  # BSE format
                symbol,          # Plain symbol
                f"{symbol}.NSE", # Alternative NSE format
            ]
            
            for symbol_variant in symbol_variants:
                try:
                    ticker = yf.Ticker(symbol_variant)
                    info = ticker.info
                    
                    # Only proceed if we got valid info
                    if info and len(info) > 1:  # yfinance returns a dict with at least some data
                        return {
                            'symbol': symbol,
                            'company_name': info.get('longName', info.get('shortName', '')),
                            'sector': info.get('sector', ''),
                            'industry': info.get('industry', ''),
                            'market_cap': info.get('marketCap', 0),
                            'currency': info.get('currency', 'INR')
                        }
                except Exception as e:
                    logger.debug(f"Failed to get info for {symbol_variant}: {e}")
                    continue
                    
            logger.warning(f"Could not fetch stock info for {symbol} using any symbol variant")
            return {
                'symbol': symbol,
                'company_name': '',
                'sector': '',
                'industry': '',
                'market_cap': 0,
                'currency': 'INR'
            }
            
        except Exception as e:
            logger.error(f"Error getting stock info for {symbol}: {e}")
            return {
                'symbol': symbol,
                'company_name': '',
                'sector': '',
                'industry': '',
                'market_cap': 0,
                'currency': 'INR'
            }

# Global fetcher instance
unified_fetcher = UnifiedDataFetcher()

def get_fetcher() -> UnifiedDataFetcher:
    """Get the global unified fetcher instance."""
    return unified_fetcher
