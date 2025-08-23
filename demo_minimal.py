#!/usr/bin/env python3
"""
Minimal demo script that tests the backtesting system without database.
This bypasses all database issues and focuses on testing the core functionality.
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
from strategies.moving_average_crossover import MovingAverageCrossover
from backtesting.engine import BacktestEngine
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

def run_minimal_demo():
    """Run the minimal demo without database."""
    print("Indian Stock Market Backtesting System - Minimal Demo (No Database)")
    print("=" * 70)
    
    # Setup
    setup_logging(log_level="INFO")
    create_directories()
    
    try:
        # 1. Create mock data
        print("1. Creating mock data...")
        symbol = "DEMO"
        start_date = date(2022, 1, 1)
        end_date = date(2023, 12, 31)
        
        mock_data = create_mock_data(symbol, start_date, end_date)
        print(f"✓ Created {len(mock_data)} records of mock data")
        
        # 2. Create strategy
        print("\n2. Creating Moving Average Crossover strategy...")
        strategy = MovingAverageCrossover(short_window=10, long_window=30)
        
        # 3. Run backtest with mock data directly
        print("\n3. Running backtest with mock data...")
        
        # Create a simple backtest engine that works with DataFrame directly
        engine = BacktestEngine()
        
        # Convert mock data to the format expected by the backtest engine
        # Set the index to date for the backtest engine
        mock_data_indexed = mock_data.set_index('date')
        
        # Run the backtest
        results = engine.run_backtest(
            symbol=symbol,
            strategy=strategy,
            start_date="2022-01-01",
            end_date="2023-12-31",
            initial_capital=100000,
            data=mock_data_indexed  # Pass the data directly
        )
        
        if results:
            # 4. Display results
            print("\n4. Backtest Results:")
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
            
            # 5. Generate charts
            print("\n5. Generating charts...")
            try:
                # Create charts directory
                os.makedirs('charts', exist_ok=True)
                
                # Plot equity curve
                plot_equity_curve(
                    results['equity_curve'],
                    title=f"Equity Curve - {symbol} (Mock Data)",
                    save_path=f"charts/equity_curve_{symbol}_minimal.png",
                    show=False
                )
                
                # Plot strategy signals
                plot_strategy_signals(
                    results['data'],
                    results['signals'],
                    strategy_name=f"{results['strategy']} - {symbol} (Mock Data)",
                    save_path=f"charts/signals_{symbol}_minimal.png",
                    show=False
                )
                
                print("✓ Charts generated successfully!")
                
            except Exception as e:
                print(f"Warning: Could not generate charts: {e}")
            
            print("\n" + "=" * 70)
            print("✓ Minimal demo completed successfully!")
            print("This demonstrates the core backtesting functionality without database dependencies.")
            print("=" * 70)
            
        else:
            print("✗ Backtest failed - no results generated")
            
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_minimal_demo()
