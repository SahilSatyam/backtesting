#!/usr/bin/env python3
"""
ETL Manager - Comprehensive tool for managing stock data ETL process.
Provides incremental updates, status checking, and automated scheduling.
"""
import sys
import os
import argparse
from datetime import datetime, date, timedelta
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import setup_logging
from data.etl import run_etl, run_daily_update, get_etl_status, update_recent_data
from database.operations import get_stock_count, get_price_count, get_last_price_date
from config.settings import DEFAULT_STOCKS

def print_etl_status(symbols=None):
    """Print the current ETL status for all symbols."""
    if symbols is None:
        symbols = DEFAULT_STOCKS
    
    print("ETL Status Report")
    print("=" * 60)
    
    status = get_etl_status(symbols)
    today = datetime.now().date()
    
    print(f"Report Date: {today}")
    print(f"Total Symbols: {len(symbols)}")
    print()
    
    # Summary
    needs_update = sum(1 for s in status.values() if s['needs_update'])
    up_to_date = len(status) - needs_update
    
    print(f"Summary:")
    print(f"  ✓ Up to date: {up_to_date}")
    print(f"  ⚠ Needs update: {needs_update}")
    print()
    
    # Detailed status
    print("Detailed Status:")
    print("-" * 60)
    print(f"{'Symbol':<12} {'Last Date':<12} {'Days Ago':<10} {'Status':<10}")
    print("-" * 60)
    
    for symbol, info in status.items():
        if info['last_date']:
            last_date = info['last_date']
            days_ago = info['days_since_update']
            status_icon = "✓" if not info['needs_update'] else "⚠"
            print(f"{symbol:<12} {last_date:<12} {days_ago:<10} {status_icon:<10}")
        else:
            print(f"{symbol:<12} {'No Data':<12} {'N/A':<10} ⚠")
    
    print("-" * 60)

def run_incremental_update(symbols=None, verbose=True):
    """Run incremental ETL update and show results."""
    if symbols is None:
        symbols = DEFAULT_STOCKS
    
    if verbose:
        print("Running Incremental ETL Update")
        print("=" * 40)
        print(f"Symbols: {', '.join(symbols)}")
        print(f"Mode: Incremental (only new data)")
        print()
    
    results = run_daily_update(symbols)
    
    if verbose:
        print("\nUpdate Results:")
        print("-" * 40)
        for symbol, success in results.items():
            status = "✓ Success" if success else "✗ Failed"
            print(f"{symbol:<12} {status}")
        
        successful = sum(results.values())
        print(f"\nSummary: {successful}/{len(symbols)} successful")
    
    return results

def run_full_update(symbols=None, start_date=None, end_date=None, verbose=True):
    """Run full ETL update for specified date range."""
    if symbols is None:
        symbols = DEFAULT_STOCKS
    
    if verbose:
        print("Running Full ETL Update")
        print("=" * 40)
        print(f"Symbols: {', '.join(symbols)}")
        if start_date:
            print(f"Start Date: {start_date}")
        if end_date:
            print(f"End Date: {end_date}")
        print(f"Mode: Full fetch (all data)")
        print()
    
    results = run_etl(symbols=symbols, start_date=start_date, end_date=end_date, incremental=False)
    
    if verbose:
        print("\nUpdate Results:")
        print("-" * 40)
        for symbol, success in results.items():
            status = "✓ Success" if success else "✗ Failed"
            print(f"{symbol:<12} {status}")
        
        successful = sum(results.values())
        print(f"\nSummary: {successful}/{len(symbols)} successful")
    
    return results

def show_database_stats():
    """Show database statistics."""
    print("Database Statistics")
    print("=" * 40)
    
    try:
        stock_count = get_stock_count()
        price_count = get_price_count()
        
        print(f"Total Stocks: {stock_count}")
        print(f"Total Price Records: {price_count:,}")
        if stock_count > 0:
            avg_records = price_count / stock_count
            print(f"Average Records per Stock: {avg_records:.1f}")
        
        print()
        
        # Show latest dates for each symbol
        print("Latest Data by Symbol:")
        print("-" * 40)
        for symbol in DEFAULT_STOCKS:
            last_date = get_last_price_date(symbol)
            if last_date:
                print(f"{symbol:<12} {last_date}")
            else:
                print(f"{symbol:<12} No data")
                
    except Exception as e:
        print(f"Error getting database stats: {e}")

def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(description='ETL Manager for Stock Data')
    parser.add_argument('action', choices=['status', 'update', 'full-update', 'stats'], 
                       help='Action to perform')
    parser.add_argument('--symbols', nargs='+', help='Stock symbols to process')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD) for full update')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD) for full update')
    parser.add_argument('--quiet', action='store_true', help='Suppress verbose output')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(log_level="INFO")
    
    symbols = args.symbols if args.symbols else None
    
    if args.action == 'status':
        print_etl_status(symbols)
    
    elif args.action == 'update':
        run_incremental_update(symbols, verbose=not args.quiet)
    
    elif args.action == 'full-update':
        run_full_update(symbols, args.start_date, args.end_date, verbose=not args.quiet)
    
    elif args.action == 'stats':
        show_database_stats()

if __name__ == "__main__":
    main()
