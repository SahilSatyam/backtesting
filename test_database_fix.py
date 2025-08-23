#!/usr/bin/env python3
"""
Test script to verify database session binding fixes.
"""
import sys
import os
from datetime import date
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import setup_logging
from database.operations import init_database, get_or_create_stock, insert_daily_prices, get_price_dataframe

def test_database_operations():
    """Test database operations to ensure session binding issues are fixed."""
    print("Testing Database Operations")
    print("=" * 50)
    
    # Setup logging
    setup_logging(log_level="INFO")
    
    try:
        # 1. Initialize database
        print("1. Initializing database...")
        init_database()
        print("✓ Database initialized successfully")
        
        # 2. Test stock creation
        print("\n2. Testing stock creation...")
        stock = get_or_create_stock(
            symbol="TEST",
            company_name="Test Company",
            sector="Technology"
        )
        
        if stock and hasattr(stock, 'id'):
            print(f"✓ Stock created successfully: {stock.symbol} (ID: {stock.id})")
        else:
            print("✗ Stock creation failed")
            return
        
        # 3. Test price data insertion
        print("\n3. Testing price data insertion...")
        test_data = [
            {
                'date': date(2023, 1, 1),
                'open': 100.0,
                'high': 105.0,
                'low': 98.0,
                'close': 102.0,
                'volume': 1000000
            },
            {
                'date': date(2023, 1, 2),
                'open': 102.0,
                'high': 108.0,
                'low': 101.0,
                'close': 106.0,
                'volume': 1200000
            }
        ]
        
        success = insert_daily_prices(stock.id, test_data)
        if success:
            print("✓ Price data inserted successfully")
        else:
            print("✗ Price data insertion failed")
            return
        
        # 4. Test price data retrieval
        print("\n4. Testing price data retrieval...")
        df = get_price_dataframe("TEST", date(2023, 1, 1), date(2023, 1, 2))
        
        if not df.empty:
            print(f"✓ Price data retrieved successfully: {len(df)} records")
            print(f"  Date range: {df.index.min()} to {df.index.max()}")
            print(f"  Price range: ₹{df['close'].min():.2f} to ₹{df['close'].max():.2f}")
        else:
            print("✗ Price data retrieval failed")
            return
        
        print("\n" + "=" * 50)
        print("✓ All database operations completed successfully!")
        print("Session binding issues have been resolved.")
        print("=" * 50)
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database_operations()
