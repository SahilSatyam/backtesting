"""
Data package for fetching and processing stock market data.

This package provides a unified interface for fetching stock market data using yfinance.
"""

from .unified_fetcher import UnifiedDataFetcher, get_fetcher, unified_fetcher

# For backward compatibility
DataFetcher = UnifiedDataFetcher
data_fetcher = unified_fetcher
AlternativeDataFetcher = UnifiedDataFetcher
alternative_data_fetcher = unified_fetcher

__all__ = [
    'UnifiedDataFetcher',
    'get_fetcher',
    'unified_fetcher',
    # For backward compatibility
    'DataFetcher',
    'data_fetcher',
    'AlternativeDataFetcher',
    'alternative_data_fetcher'
]
