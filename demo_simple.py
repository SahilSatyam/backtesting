#!/usr/bin/env python3
"""
Simple demo script that uses mock data to test the backtesting system.
This bypasses external API issues and focuses on testing the core functionality.
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import setup_logging, create_directories, format_currency
from database.operations import init_database, get_or_create_stock, insert_daily_prices
from strategies.moving_average_crossover import MovingAverageCrossover
from backtesting.engine import backtest_engine
from visualization.charts import plot_equity_curve, plot_strategy_signals

def create_mock_data(symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
    """Create mock stock data for testing."""
    print(f"Creating mock data for {symbol}...")
    
    # Generate date range
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    date_range = [d.date() for d in date_range if d.weekday() < 5]  # Only weekdays
    
    # Create mock price data with some realistic patterns
    np.random.seed(42)  # For reproducible results
    
    # Start with a base price
    base_price = 1000.0
    
    # Generate price movements
    returns = np.random.normal(0.001, 0.02, len(date_range))  # Daily returns
    prices = [base_price]
    
    for ret in returns[1:]:
        new_price = prices[-1] * (1 + ret)
        prices.append(max(new_price, 1.0))  # Ensure price doesn't go below 1
    
    # Create OHLCV data
    data = []
    for i, (dt, close_price) in enumerate(zip(date_range, prices)):
        # Generate OHLC from close price
        volatility = 0.02
        open_price = close_price * (1 + np.random.normal(0, volatility/2))
        high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, volatility/4)))
        low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, volatility/4)))
        volume = int(np.random.uniform(1000000, 10000000))
        
        data.append({
            'date': dt,
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume
        })
    
    return pd.DataFrame(data)

def load_mock_data_to_db(symbol: str, data: pd.DataFrame) -> bool:
    """Load mock data into the database."""
    try:
        # Create stock record
        stock = get_or_create_stock(
            symbol=symbol,
            company_name=f"Mock {symbol} Company",
            sector="Technology"
        )
        
        if stock is None:
            print(f"Failed to create stock record for {symbol}")
            return False
        
        # Get the stock ID (not the object) to avoid session binding issues
        stock_id = stock.id if hasattr(stock, 'id') else None
        
        if stock_id is None:
            print(f"Failed to get stock ID for {symbol}")
            return False
        
        # Convert DataFrame to list of dictionaries
        price_data = data.to_dict('records')
        
        # Insert price data using the stock ID
        success = insert_daily_prices(stock_id, price_data)
        
        if success:
            print(f"✓ Successfully loaded {len(price_data)} records for {symbol}")
            return True
        else:
            print(f"✗ Failed to load data for {symbol}")
            return False
            
    except Exception as e:
        print(f"Error loading mock data for {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_demo():
    """Run the simple demo with mock data."""
    print("Indian Stock Market Backtesting System - Simple Demo")
    print("=" * 60)
    
    # Setup
    setup_logging(log_level="INFO")
    create_directories()
    
    try:
        # 1. Initialize database
        print("1. Initializing database...")
        init_database()
        print("✓ Database initialized successfully")
        
        # 2. Create and load mock data
        print("\n2. Creating mock data...")
        symbol = "DEMO"
        start_date = date(2022, 1, 1)
        end_date = date(2023, 12, 31)
        
        mock_data = create_mock_data(symbol, start_date, end_date)
        
        if load_mock_data_to_db(symbol, mock_data):
            print("✓ Mock data loaded successfully")
        else:
            print("✗ Failed to load mock data")
            return
        
        # 3. Create strategy
        print("\n3. Creating Moving Average Crossover strategy...")
        strategy = MovingAverageCrossover(short_window=10, long_window=30)
        
        # 4. Run backtest with mock data directly
        print("\n4. Running backtest...")
        
        # Convert mock data to the format expected by the backtest engine
        mock_data_indexed = mock_data.set_index('date')
        
        results = backtest_engine.run_backtest(
            symbol=symbol,
            strategy=strategy,
            start_date="2022-01-01",
            end_date="2023-12-31",
            initial_capital=100000,
            data=mock_data_indexed  # Pass the data directly to avoid database issues
        )
        
        if results:
            # 5. Display results
            print("\n5. Backtest Results:")
            print("-" * 40)
            print(f"Symbol: {results['symbol']}")
            print(f"Strategy: {results['strategy']}")
            print(f"Initial Capital: {format_currency(results['initial_capital'])}")
            print(f"Final Capital: {format_currency(results['final_capital'])}")
            print(f"Total P&L: {format_currency(results['final_capital'] - results['initial_capital'])}")
            
            # Performance metrics
            metrics = results['metrics']
            if metrics:
                print(f"\nPerformance Metrics:")
                print(f"Total Return: {metrics.get('total_return', 0):.2%}")
                print(f"Annualized Return: {metrics.get('annualized_return', 0):.2%}")
                print(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}")
                print(f"Maximum Drawdown: {metrics.get('max_drawdown', 0):.2%}")
                
                if 'total_trades' in metrics:
                    print(f"Total Trades: {metrics['total_trades']}")
                    print(f"Win Rate: {metrics['win_rate']:.2%}")
            
            # 6. Generate charts
            print("\n6. Generating charts...")
            try:
                # Create charts directory
                os.makedirs('charts', exist_ok=True)
                
                # Plot equity curve
                plot_equity_curve(
                    results['equity_curve'],
                    title=f"Equity Curve - {symbol} (Mock Data)",
                    save_path=f"charts/equity_curve_{symbol}_mock.png",
                    show=False
                )
                
                # Plot strategy signals
                plot_strategy_signals(
                    results['data'],
                    results['signals'],
                    strategy_name=f"{results['strategy']} - {symbol} (Mock Data)",
                    save_path=f"charts/signals_{symbol}_mock.png",
                    show=False
                )
                
                print("✓ Charts generated successfully!")
                
            except Exception as e:
                print(f"Warning: Could not generate charts: {e}")
            
            print("\n" + "=" * 60)
            print("✓ Demo completed successfully!")
            print("This demonstrates the core backtesting functionality.")
            print("For real data, ensure your database connection is working.")
            print("=" * 60)
            
        else:
            print("✗ Backtest failed - no results generated")
            
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_demo()
