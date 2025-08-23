"""
Utility helper functions for the backtesting system.
"""
import os
import logging
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

def setup_logging(log_level: str = "INFO", log_file: str = "backtesting.log"):
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Log file path
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger.info(f"Logging configured with level: {log_level}")

def create_directories():
    """Create necessary directories for the project."""
    directories = ['data_files', 'results', 'charts', 'logs']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")

def save_results(results: Dict[str, Any], filename: str = None):
    """
    Save backtest results to file.
    
    Args:
        results: Dictionary with backtest results
        filename: Output filename (optional)
    """
    def json_serial(obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif isinstance(obj, (pd.DataFrame, pd.Series)):
            return obj.to_dict()
        elif isinstance(obj, dict):
            # Convert all keys to strings and recursively process values
            return {str(k) if not isinstance(k, (str, int, float, bool)) and k is not None else k: json_serial(v) 
                   for k, v in obj.items()}
        elif isinstance(obj, (list, tuple, set)):
            return [json_serial(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return json_serial(obj.__dict__)
        return str(obj)  # fallback to string representation

    results_dir = 'results'
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backtest_results_{timestamp}.json"
    
    # Ensure the filename is within the results directory
    if not filename.startswith(results_dir + os.sep):
        filename = os.path.join(results_dir, filename)
    
    # Create results directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    try:
        # Convert all data to serializable format
        serializable_results = json_serial(results)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Results saved to {os.path.abspath(filename)}")
        return True
    except Exception as e:
        logger.error(f"Error saving results: {e}")

def load_results(filename: str) -> Dict[str, Any]:
    """
    Load backtest results from file.
    
    Args:
        filename: Input filename
        
    Returns:
        Dictionary with backtest results
    """
    try:
        with open(filename, 'r') as f:
            results = json.load(f)
        
        # Convert back to DataFrames where needed
        for key in ['equity_curve', 'data', 'signals', 'trades']:
            if key in results and isinstance(results[key], dict):
                if key == 'equity_curve':
                    results[key] = pd.Series(results[key])
                else:
                    results[key] = pd.DataFrame(results[key])
        
        logger.info(f"Results loaded from {filename}")
        return results
    except Exception as e:
        logger.error(f"Error loading results: {e}")
        return {}

def format_currency(amount: float) -> str:
    """
    Format amount as Indian currency.
    
    Args:
        amount: Amount to format
        
    Returns:
        Formatted currency string
    """
    if amount >= 1e7:  # 1 crore
        return f"₹{amount/1e7:.2f} Cr"
    elif amount >= 1e5:  # 1 lakh
        return f"₹{amount/1e5:.2f} L"
    elif amount >= 1e3:  # 1 thousand
        return f"₹{amount/1e3:.2f} K"
    else:
        return f"₹{amount:.2f}"

def format_percentage(value: float) -> str:
    """
    Format value as percentage.
    
    Args:
        value: Value to format (as decimal)
        
    Returns:
        Formatted percentage string
    """
    return f"{value:.2%}"

def calculate_date_range(start_date: str = None, end_date: str = None, 
                        days_back: int = 365) -> tuple:
    """
    Calculate date range for backtesting.
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        days_back: Days to go back from end_date if start_date not provided
        
    Returns:
        Tuple of (start_date, end_date) as date objects
    """
    if end_date is None:
        end_date = datetime.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if start_date is None:
        start_date = end_date - timedelta(days=days_back)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    return start_date, end_date

def validate_symbol(symbol: str) -> bool:
    """
    Validate stock symbol format.
    
    Args:
        symbol: Stock symbol to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not symbol or not isinstance(symbol, str):
        return False
    
    # Basic validation: alphanumeric and common characters
    import re
    pattern = r'^[A-Z0-9._-]+$'
    return bool(re.match(pattern, symbol.upper()))

def get_market_cap_category(market_cap: float) -> str:
    """
    Get market cap category.
    
    Args:
        market_cap: Market capitalization in INR
        
    Returns:
        Market cap category string
    """
    if market_cap >= 20000e7:  # 20,000 Cr
        return "Large Cap"
    elif market_cap >= 5000e7:  # 5,000 Cr
        return "Mid Cap"
    else:
        return "Small Cap"

def calculate_volatility(prices: pd.Series, window: int = 252) -> pd.Series:
    """
    Calculate rolling volatility.
    
    Args:
        prices: Price series
        window: Rolling window size
        
    Returns:
        Rolling volatility series
    """
    returns = prices.pct_change().dropna()
    volatility = returns.rolling(window=window).std() * (252 ** 0.5)
    return volatility

def calculate_beta(stock_returns: pd.Series, market_returns: pd.Series) -> float:
    """
    Calculate beta of stock relative to market.
    
    Args:
        stock_returns: Stock return series
        market_returns: Market return series
        
    Returns:
        Beta value
    """
    # Align the series
    aligned_data = pd.concat([stock_returns, market_returns], axis=1).dropna()
    if len(aligned_data) < 2:
        return 1.0
    
    stock_ret = aligned_data.iloc[:, 0]
    market_ret = aligned_data.iloc[:, 1]
    
    # Calculate beta
    covariance = stock_ret.cov(market_ret)
    market_variance = market_ret.var()
    
    beta = covariance / market_variance if market_variance != 0 else 1.0
    return beta

def calculate_correlation_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate correlation matrix for returns.
    
    Args:
        returns_df: DataFrame with return series
        
    Returns:
        Correlation matrix
    """
    return returns_df.corr()

def generate_summary_statistics(data: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate summary statistics for price data.
    
    Args:
        data: DataFrame with OHLCV data
        
    Returns:
        Dictionary with summary statistics
    """
    if data.empty:
        return {}
    
    stats = {}
    
    # Price statistics
    if 'close' in data.columns:
        stats['price_stats'] = {
            'mean': data['close'].mean(),
            'std': data['close'].std(),
            'min': data['close'].min(),
            'max': data['close'].max(),
            'median': data['close'].median()
        }
    
    # Volume statistics
    if 'volume' in data.columns:
        stats['volume_stats'] = {
            'mean': data['volume'].mean(),
            'std': data['volume'].std(),
            'min': data['volume'].min(),
            'max': data['volume'].max(),
            'median': data['volume'].median()
        }
    
    # Return statistics
    if 'close' in data.columns:
        returns = data['close'].pct_change().dropna()
        stats['return_stats'] = {
            'mean': returns.mean(),
            'std': returns.std(),
            'skewness': returns.skew(),
            'kurtosis': returns.kurtosis(),
            'min': returns.min(),
            'max': returns.max()
        }
    
    # Date range
    stats['date_range'] = {
        'start_date': data.index[0],
        'end_date': data.index[-1],
        'total_days': len(data)
    }
    
    return stats

def print_summary_table(data: pd.DataFrame, title: str = "Data Summary"):
    """
    Print a formatted summary table.
    
    Args:
        data: DataFrame to summarize
        title: Table title
    """
    print(f"\n{title}")
    print("=" * 50)
    print(f"Shape: {data.shape}")
    print(f"Date Range: {data.index[0]} to {data.index[-1]}")
    print(f"Total Days: {len(data)}")
    
    if 'close' in data.columns:
        print(f"Price Range: ₹{data['close'].min():.2f} - ₹{data['close'].max():.2f}")
        print(f"Average Price: ₹{data['close'].mean():.2f}")
    
    if 'volume' in data.columns:
        print(f"Average Volume: {data['volume'].mean():,.0f}")
    
    print("=" * 50)
