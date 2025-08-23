"""
Main script for the Indian Stock Market Backtesting System.

This script demonstrates the complete functionality of the backtesting system
including data fetching, database operations, strategy implementation, and
performance analysis.
"""
import sys
import os
import logging
from datetime import datetime, date
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import project modules
from utils.helpers import setup_logging, create_directories, save_results, format_currency
from database.operations import init_database, get_stock_count, get_price_count
from data.etl import run_etl, update_recent_data
from strategies.moving_average_crossover import MovingAverageCrossover
from backtesting.engine import backtest_engine
from visualization.charts import (
    plot_equity_curve, plot_drawdown, plot_trades, 
    plot_strategy_signals, create_interactive_chart
)
from config.settings import DEFAULT_STOCKS, DEFAULT_START_DATE, DEFAULT_END_DATE

def main():
    """Main function to run the backtesting system."""
    
    # Setup logging
    setup_logging(log_level="INFO", log_file="logs/backtesting.log")
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Indian Stock Market Backtesting System")
    
    # Create necessary directories
    create_directories()
    
    try:
        # Step 1: Initialize Database
        logger.info("Step 1: Initializing database...")
        init_database()
        logger.info("Database initialized successfully")
        
        # Step 2: Check existing data
        stock_count = get_stock_count()
        price_count = get_price_count()
        logger.info(f"Current database status: {stock_count} stocks, {price_count} price records")
        
        # Step 3: Fetch data if needed
        if stock_count == 0:
            logger.info("Step 2: Fetching stock data...")
            print("\nFetching stock data from NSE/BSE...")
            etl_results = run_etl(
                symbols=DEFAULT_STOCKS[:5],  # Start with 5 stocks for demo
                start_date="2022-01-01",
                end_date="2023-12-31"
            )
            logger.info(f"ETL completed: {sum(etl_results.values())} successful")
        else:
            logger.info("Data already exists in database")
        
        # Step 4: Run backtesting
        logger.info("Step 3: Running backtesting...")
        
        # Create strategy
        strategy = MovingAverageCrossover(short_window=20, long_window=50)
        
        # Run backtest for a single stock
        symbol = "RELIANCE"
        print(f"\nRunning backtest for {symbol}...")
        
        results = backtest_engine.run_backtest(
            symbol=symbol,
            strategy=strategy,
            start_date="2022-01-01",
            end_date="2023-12-31",
            initial_capital=100000
        )
        
        if results:
            # Step 5: Display results
            logger.info("Step 4: Displaying results...")
            display_results(results)
            
            # Step 6: Generate visualizations
            logger.info("Step 5: Generating visualizations...")
            generate_charts(results)
            
            # Step 7: Save results
            logger.info("Step 6: Saving results...")
            save_results(results)
            
        else:
            logger.error("Backtest failed - no results generated")
        
        # Step 7: Run multiple backtests (commented out as it's not implemented yet)
        # logger.info("Step 7: Running multiple backtests...")
        # run_multiple_backtests()
        
        logger.info("Backtesting system completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True)
        print(f"An error occurred: {e}")

def display_results(results: Dict[str, Any]):
    """Display backtest results in a formatted way."""
    print("\n" + "="*80)
    print("BACKTESTING RESULTS")
    print("="*80)
    
    # Basic information
    print(f"Symbol: {results['symbol']}")
    print(f"Strategy: {results['strategy']}")
    print(f"Parameters: {results['strategy_params']}")
    print(f"Period: {results['start_date']} to {results['end_date']}")
    print(f"Initial Capital: {format_currency(results['initial_capital'])}")
    print(f"Final Capital: {format_currency(results['final_capital'])}")
    
    # Performance metrics
    metrics = results['metrics']
    if metrics:
        print(f"\nPERFORMANCE METRICS:")
        print("-" * 40)
        print(f"Total Return: {metrics.get('total_return', 0):.2%}")
        print(f"Annualized Return: {metrics.get('annualized_return', 0):.2%}")
        print(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}")
        print(f"Maximum Drawdown: {metrics.get('max_drawdown', 0):.2%}")
        print(f"Volatility: {metrics.get('annualized_volatility', 0):.2%}")
        
        # Trade metrics
        if 'total_trades' in metrics:
            print(f"\nTRADE METRICS:")
            print("-" * 40)
            print(f"Total Trades: {metrics['total_trades']}")
            print(f"Winning Trades: {metrics['winning_trades']}")
            print(f"Losing Trades: {metrics['losing_trades']}")
            print(f"Win Rate: {metrics['win_rate']:.2%}")
            print(f"Profit Factor: {metrics['profit_factor']:.3f}")
    
    # Signal summary
    signals = results['signals']
    if not signals.empty:
        buy_signals = (signals['signal'] == 1).sum()
        sell_signals = (signals['signal'] == -1).sum()
        print(f"\nSIGNAL SUMMARY:")
        print("-" * 40)
        print(f"Buy Signals: {buy_signals}")
        print(f"Sell Signals: {sell_signals}")
        print(f"Total Signals: {len(signals)}")
    
    print("="*80)

def generate_charts(results: Dict[str, Any]):
    """Generate and save charts for the backtest results."""
    # Initialize logger
    logger = logging.getLogger(__name__)
    
    try:
        # Create charts directory with error handling
        charts_dir = 'charts'
        try:
            os.makedirs(charts_dir, exist_ok=True)
            if not os.path.isdir(charts_dir):
                raise NotADirectoryError(f"Failed to create directory: {os.path.abspath(charts_dir)}")
            logger.info(f"Using charts directory: {os.path.abspath(charts_dir)}")
        except Exception as e:
            logger.error(f"Error creating charts directory: {e}")
            print(f"Error: Could not create charts directory. Please check permissions or create it manually: {os.path.abspath(charts_dir)}")
            return
        
        # Generate equity curve chart
        print("Generating equity curve chart...")
        try:
            save_path = os.path.join(charts_dir, f"equity_curve_{results['symbol']}.png")
            plot_equity_curve(
                results['equity_curve'],
                title=f"Equity Curve - {results['symbol']}",
                save_path=save_path,
                show=False
            )
            logger.info(f"Saved equity curve to: {os.path.abspath(save_path)}")
        except Exception as e:
            logger.error(f"Error generating equity curve: {e}")
            print(f"Warning: Could not generate equity curve: {e}")
        
        # Generate drawdown chart
        if 'drawdown_series' in results['metrics']:
            print("Generating drawdown chart...")
            try:
                save_path = os.path.join(charts_dir, f"drawdown_{results['symbol']}.png")
                plot_drawdown(
                    results['metrics']['drawdown_series'],
                    title=f"Drawdown Analysis - {results['symbol']}",
                    save_path=save_path,
                    show=False
                )
                logger.info(f"Saved drawdown chart to: {os.path.abspath(save_path)}")
            except Exception as e:
                logger.error(f"Error generating drawdown chart: {e}")
                print(f"Warning: Could not generate drawdown chart: {e}")
        
        # Generate trades chart
        if not results['trades'].empty:
            print("Generating trades chart...")
            try:
                save_path = os.path.join(charts_dir, f"trades_{results['symbol']}.png")
                plot_trades(
                    results['data'],
                    results['trades'],
                    title=f"Trades Analysis - {results['symbol']}",
                    save_path=save_path,
                    show=False
                )
                logger.info(f"Saved trades chart to: {os.path.abspath(save_path)}")
            except Exception as e:
                logger.error(f"Error generating trades chart: {e}")
                print(f"Warning: Could not generate trades chart: {e}")
        
        # Generate strategy signals chart
        print("Generating strategy signals chart...")
        try:
            save_path = os.path.join(charts_dir, f"signals_{results['symbol']}.png")
            plot_strategy_signals(
                results['data'],
                results['signals'],
                strategy_name=f"{results['strategy']} - {results['symbol']}",
                save_path=save_path,
                show=False
            )
            logger.info(f"Saved signals chart to: {os.path.abspath(save_path)}")
        except Exception as e:
            logger.error(f"Error generating signals chart: {e}")
            print(f"Warning: Could not generate signals chart: {e}")
        
        # Create interactive chart
        print("Generating interactive chart...")
        try:
            save_path = os.path.join(charts_dir, f"interactive_{results['symbol']}.html")
            fig = create_interactive_chart(
                results,
                title=f"Interactive Backtest Results - {results['symbol']}"
            )
            if fig:
                fig.write_html(save_path)
                logger.info(f"Saved interactive chart to: {os.path.abspath(save_path)}")
        except Exception as e:
            logger.error(f"Error generating interactive chart: {e}")
            print(f"Warning: Could not generate interactive chart: {e}")
        
        print("All charts generation completed! Check the logs for any warnings.")
        
    except Exception as e:
        error_msg = f"Error generating charts: {e}"
        print(error_msg)
        logger.error(error_msg, exc_info=True)
        test_symbols = ["RELIANCE", "TCS", "INFY"]
        
        print(f"\nRunning backtests for multiple symbols: {test_symbols}")
        
        # Run multiple backtests
        all_results = backtest_engine.run_multiple_backtests(
            symbols=test_symbols,
            strategy=strategy,
            start_date="2022-01-01",
            end_date="2023-12-31"
        )
        
        # Display aggregate results
        aggregate = all_results['aggregate_results']
        if aggregate:
            print(f"\nAGGREGATE RESULTS:")
            print("-" * 40)
            print(f"Total Symbols: {aggregate['total_symbols']}")
            print(f"Total Initial Capital: {format_currency(aggregate['total_initial_capital'])}")
            print(f"Total Final Capital: {format_currency(aggregate['total_final_capital'])}")
            print(f"Total P&L: {format_currency(aggregate['total_pnl'])}")
            print(f"Total Return: {aggregate['total_return']:.2%}")
            print(f"Average Return: {aggregate['avg_return']:.2%}")
            print(f"Average Sharpe Ratio: {aggregate['avg_sharpe_ratio']:.3f}")
            print(f"Average Max Drawdown: {aggregate['avg_max_drawdown']:.2%}")
        
        # Display individual results
        individual = all_results['individual_results']
        print(f"\nINDIVIDUAL RESULTS:")
        print("-" * 40)
        for symbol, result in individual.items():
            if result:
                total_return = result['metrics'].get('total_return', 0)
                sharpe = result['metrics'].get('sharpe_ratio', 0)
                print(f"{symbol}: Return={total_return:.2%}, Sharpe={sharpe:.3f}")
            else:
                print(f"{symbol}: Failed")
        
    except Exception as e:
        logger.error(f"Error running multiple backtests: {e}")

def demo_mode():
    """Run a quick demo of the system."""
    print("INDIAN STOCK MARKET BACKTESTING SYSTEM - DEMO MODE")
    print("=" * 60)
    
    try:
        # Initialize database
        print("1. Initializing database...")
        init_database()
        
        # Fetch data for one stock
        print("2. Fetching sample data...")
        etl_results = run_etl(
            symbols=["RELIANCE"],
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        
        if etl_results.get("RELIANCE", False):
            # Run quick backtest
            print("3. Running quick backtest...")
            strategy = MovingAverageCrossover(short_window=10, long_window=30)
            
            results = backtest_engine.run_backtest(
                symbol="RELIANCE",
                strategy=strategy,
                start_date="2023-01-01",
                end_date="2023-12-31",
                initial_capital=100000
            )
            
            if results:
                print("4. Demo completed successfully!")
                print(f"Final Capital: {format_currency(results['final_capital'])}")
                print(f"Total Return: {results['metrics'].get('total_return', 0):.2%}")
            else:
                print("Demo failed - no results generated")
        else:
            print("Demo failed - could not fetch data")
            
    except Exception as e:
        print(f"Demo failed with error: {e}")

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo_mode()
    else:
        main()
