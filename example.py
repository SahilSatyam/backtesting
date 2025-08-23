"""
Simple example script to demonstrate the backtesting system.
"""
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.operations import init_database
from data.etl import run_etl
from strategies.moving_average_crossover import MovingAverageCrossover
from backtesting.engine import backtest_engine
from utils.helpers import setup_logging, create_directories

def main():
    """Run a simple example backtest."""
    
    # Setup
    setup_logging(log_level="INFO")
    create_directories()
    
    print("Indian Stock Market Backtesting System - Example")
    print("=" * 50)
    
    try:
        # 1. Initialize database
        print("1. Initializing database...")
        init_database()
        
        # 2. Fetch data for RELIANCE
        print("2. Fetching data for RELIANCE...")
        etl_results = run_etl(
            symbols=["RELIANCE"],
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        
        if not etl_results.get("RELIANCE", False):
            print("Failed to fetch data for RELIANCE")
            return
        
        # 3. Create strategy
        print("3. Creating Moving Average Crossover strategy...")
        strategy = MovingAverageCrossover(short_window=20, long_window=50)
        
        # 4. Run backtest
        print("4. Running backtest...")
        results = backtest_engine.run_backtest(
            symbol="RELIANCE",
            strategy=strategy,
            start_date="2023-01-01",
            end_date="2023-12-31",
            initial_capital=100000
        )
        
        if results:
            # 5. Display results
            print("\n5. Results:")
            print("-" * 30)
            print(f"Symbol: {results['symbol']}")
            print(f"Strategy: {results['strategy']}")
            print(f"Initial Capital: ₹{results['initial_capital']:,.2f}")
            print(f"Final Capital: ₹{results['final_capital']:,.2f}")
            print(f"Total P&L: ₹{results['final_capital'] - results['initial_capital']:,.2f}")
            
            # Performance metrics
            metrics = results['metrics']
            if metrics:
                print(f"Total Return: {metrics.get('total_return', 0):.2%}")
                print(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}")
                print(f"Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
                
                if 'total_trades' in metrics:
                    print(f"Total Trades: {metrics['total_trades']}")
                    print(f"Win Rate: {metrics['win_rate']:.2%}")
            
            print("\nExample completed successfully!")
            
        else:
            print("Backtest failed - no results generated")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
