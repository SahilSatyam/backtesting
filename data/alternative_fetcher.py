"""
Alternative data fetching module that bypasses NSEpy issues.
"""
import logging
import pandas as pd
import requests
import time
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any
import yfinance as yf
from config.settings import API_CONFIG

logger = logging.getLogger(__name__)

class AlternativeDataFetcher:
    """Alternative data fetcher that doesn't rely on NSEpy."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def fetch_yahoo_data(self, symbol: str, start_date: date, end_date: date) -> Optional[pd.DataFrame]:
        """Fetch data from Yahoo Finance with better error handling."""
        try:
            logger.info(f"Fetching Yahoo Finance data for {symbol} from {start_date} to {end_date}")
            
            # Try different symbol formats for Indian stocks
            symbol_variants = [
                f"{symbol}.NS",  # NSE format
                f"{symbol}.BO",  # BSE format
                symbol,          # Plain symbol
                f"{symbol}.NSE", # Alternative NSE format
            ]
            
            for symbol_variant in symbol_variants:
                try:
                    logger.info(f"Trying Yahoo Finance with symbol: {symbol_variant}")
                    ticker = yf.Ticker(symbol_variant)
                    
                    # Get data with timeout
                    data = ticker.history(
                        start=start_date,
                        end=end_date,
                        timeout=API_CONFIG.get('yahoo_timeout', 30)
                    )
                    
                    if not data.empty:
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
                        
                        logger.info(f"Successfully fetched {len(data)} records for {symbol} using {symbol_variant}")
                        return data
                    
                except Exception as e:
                    logger.warning(f"Yahoo Finance failed for {symbol_variant}: {e}")
                    continue
            
            logger.error(f"Failed to fetch data for {symbol} from Yahoo Finance with all symbol variants")
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch Yahoo Finance data for {symbol}: {e}")
            return None
    
    def fetch_nse_website_data(self, symbol: str, start_date: date, end_date: date) -> Optional[pd.DataFrame]:
        """Fetch data from NSE website directly (fallback method)."""
        try:
            logger.info(f"Fetching NSE website data for {symbol} from {start_date} to {end_date}")
            
            # NSE website URL format
            url = f"https://www.nseindia.com/api/historical/cm/equity?symbol={symbol}"
            
            # Add headers to mimic browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.nseindia.com/',
                'DNT': '1',
            }
            
            response = self.session.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # Process the JSON data into DataFrame format
                # This would need to be implemented based on NSE's actual API response format
                logger.info(f"Successfully fetched data from NSE website for {symbol}")
                return self._process_nse_json_data(data, start_date, end_date)
            else:
                logger.warning(f"NSE website returned status {response.status_code} for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to fetch NSE website data for {symbol}: {e}")
            return None
    
    def _process_nse_json_data(self, data: Dict, start_date: date, end_date: date) -> Optional[pd.DataFrame]:
        """Process NSE JSON data into DataFrame format."""
        try:
            # This is a placeholder - actual implementation would depend on NSE's API format
            # For now, return None to indicate this method needs implementation
            logger.warning("NSE JSON processing not yet implemented")
            return None
        except Exception as e:
            logger.error(f"Failed to process NSE JSON data: {e}")
            return None
    
    def fetch_stock_data(self, symbol: str, start_date: date, end_date: date) -> Optional[pd.DataFrame]:
        """Fetch stock data using alternative methods."""
        # Try Yahoo Finance first (most reliable)
        data = self.fetch_yahoo_data(symbol, start_date, end_date)
        if data is not None and not data.empty:
            return data
        
        # Try NSE website as fallback
        data = self.fetch_nse_website_data(symbol, start_date, end_date)
        if data is not None and not data.empty:
            return data
        
        logger.error(f"Failed to fetch data for {symbol} from all alternative sources")
        return None
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """Get basic stock information from Yahoo Finance."""
        try:
            # Try different symbol formats
            symbol_variants = [f"{symbol}.NS", f"{symbol}.BO", symbol]
            
            for symbol_variant in symbol_variants:
                try:
                    ticker = yf.Ticker(symbol_variant)
                    info = ticker.info
                    
                    if info and 'longName' in info:
                        return {
                            'symbol': symbol,
                            'company_name': info.get('longName', ''),
                            'sector': info.get('sector', ''),
                            'industry': info.get('industry', ''),
                            'market_cap': info.get('marketCap', 0),
                            'currency': info.get('currency', 'INR')
                        }
                        
                except Exception as e:
                    logger.warning(f"Failed to get info for {symbol_variant}: {e}")
                    continue
            
            # Return default info if all attempts fail
            return {
                'symbol': symbol,
                'company_name': '',
                'sector': '',
                'industry': '',
                'market_cap': 0,
                'currency': 'INR'
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

# Global alternative fetcher instance
alternative_data_fetcher = AlternativeDataFetcher()
