#!/usr/bin/env python3
"""
Test script to verify the fixes for NSEpy FrameLocalsProxy error.
"""
import sys
import os
from datetime import date
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import setup_logging
from data.fetcher import data_fetcher
from data.alternative_fetcher import alternative_data_fetcher

def test_data_fetchers():
    """Test both data fetchers to ensure they work properly."""
    print("Testing Data Fetchers")
    print("=" * 50)
    
    # Setup logging
    setup_logging(log_level="INFO")
    
    # Test parameters
    symbol = "RELIANCE"
    start_date = date(2023, 1, 1)
    end_date = date(2023, 12, 31)
    
    print(f"Testing symbol: {symbol}")
    print(f"Date range: {start_date} to {end_date}")
    print()
    
    # Test 1: Main fetcher (with NSEpy fix)
    print("1. Testing main fetcher (with NSEpy fix)...")
    try:
        data = data_fetcher.fetch_stock_data(symbol, start_date, end_date)
        if data is not None and not data.empty:
            print(f"✓ Main fetcher SUCCESS: {len(data)} records")
            print(f"  Date range: {data['date'].min()} to {data['date'].max()}")
            print(f"  Price range: ₹{data['close'].min():.2f} to ₹{data['close'].max():.2f}")
        else:
            print("✗ Main fetcher FAILED: No data returned")
    except Exception as e:
        print(f"✗ Main fetcher ERROR: {e}")
    
    print()
    
    # Test 2: Alternative fetcher
    print("2. Testing alternative fetcher...")
    try:
        data = alternative_data_fetcher.fetch_stock_data(symbol, start_date, end_date)
        if data is not None and not data.empty:
            print(f"✓ Alternative fetcher SUCCESS: {len(data)} records")
            print(f"  Date range: {data['date'].min()} to {data['date'].max()}")
            print(f"  Price range: ₹{data['close'].min():.2f} to ₹{data['close'].max():.2f}")
        else:
            print("✗ Alternative fetcher FAILED: No data returned")
    except Exception as e:
        print(f"✗ Alternative fetcher ERROR: {e}")
    
    print()
    
    # Test 3: Test with a different symbol
    print("3. Testing with TCS symbol...")
    try:
        data = alternative_data_fetcher.fetch_stock_data("TCS", start_date, end_date)
        if data is not None and not data.empty:
            print(f"✓ TCS fetch SUCCESS: {len(data)} records")
        else:
            print("✗ TCS fetch FAILED: No data returned")
    except Exception as e:
        print(f"✗ TCS fetch ERROR: {e}")
    
    print()
    print("=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_data_fetchers()
