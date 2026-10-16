"""
Main backtesting engine for running trading strategies.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
import logging
from strategies.base_strategy import BaseStrategy
from backtesting.metrics import metrics_calculator
from config.settings import BACKTEST_CONFIG

logger = logging.getLogger(__name__)

class BacktestEngine:
    """Main backtesting engine for running trading strategies."""
    
    def __init__(self, initial_capital: float = None, commission: float = None, 
                 slippage: float = None):
        """
        Initialize BacktestEngine.
        
        Args:
            initial_capital: Starting capital
            commission: Commission rate per trade
            slippage: Slippage rate per trade
        """
        self.initial_capital = initial_capital or BACKTEST_CONFIG['initial_capital']
        self.commission = commission or BACKTEST_CONFIG['commission']
        self.slippage = slippage or BACKTEST_CONFIG['slippage']
        
        logger.info(f"Initialized BacktestEngine with capital: {self.initial_capital}")
    
    def run_backtest(self, symbol: str, strategy: BaseStrategy, 
                    start_date: str = None, end_date: str = None,
                    initial_capital: float = None, data: pd.DataFrame = None,
                    stop_loss_pct: float = None, take_profit_pct: float = None) -> Dict[str, Any]:
        """
        Run a backtest for a given symbol and strategy.
        
        Args:
            symbol: Stock symbol
            strategy: Trading strategy instance
            start_date: Start date for backtest (YYYY-MM-DD)
            end_date: End date for backtest (YYYY-MM-DD)
            initial_capital: Starting capital (overrides default)
            data: Optional DataFrame with price data (if not provided, will fetch from database)
            stop_loss_pct: Optional stop-loss as a fraction (e.g. 0.05 exits 5% below entry)
            take_profit_pct: Optional take-profit as a fraction (e.g. 0.10 exits 10% above entry)
            
        Returns:
            Dictionary with backtest results
        """
        logger.info(f"Starting backtest for {symbol} with {strategy.name}")
        
        # Get price data
        if data is not None:
            # Use provided data
            logger.info(f"Using provided data for {symbol}")
        else:
            # Fetch data from database
            data = self._get_data(symbol, start_date, end_date)
            
        if data.empty:
            logger.error(f"No data available for {symbol}")
            return {}
        
        # Generate signals
        signals = strategy.generate_signals(data)
        if signals.empty:
            logger.error(f"No signals generated for {symbol}")
            return {}
        
        # Run simulation
        results = self._run_simulation(data, signals, initial_capital,
                                       stop_loss_pct=stop_loss_pct,
                                       take_profit_pct=take_profit_pct)
        
        # Calculate performance metrics
        metrics = self._calculate_performance(results)
        
        # Prepare final results
        backtest_results = {
            'symbol': symbol,
            'strategy': strategy.name,
            'strategy_params': strategy.get_parameters(),
            'start_date': data.index[0],
            'end_date': data.index[-1],
            'initial_capital': results['initial_capital'],
            'final_capital': results['final_capital'],
            'stop_loss_pct': stop_loss_pct,
            'take_profit_pct': take_profit_pct,
            'equity_curve': results['equity_curve'],
            'trades': results['trades'],
            'signals': signals,
            'metrics': metrics,
            'data': data
        }
        
        logger.info(f"Backtest completed for {symbol}")
        return backtest_results
    
    def _get_data(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Get price data for the symbol."""
        try:
            # Imported lazily so backtests on provided data don't require a database
            from database.operations import get_price_dataframe
            
            # Convert string dates to date objects
            start_dt = None
            end_dt = None
            
            if start_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            if end_date:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            data = get_price_dataframe(symbol, start_dt, end_dt)
            
            if data.empty:
                logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()
            
            logger.info(f"Retrieved {len(data)} data points for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error getting data for {symbol}: {e}")
            return pd.DataFrame()
    
    def _run_simulation(self, data: pd.DataFrame, signals: pd.DataFrame, 
                       initial_capital: float = None,
                       stop_loss_pct: float = None,
                       take_profit_pct: float = None) -> Dict[str, Any]:
        """
        Run the trading simulation.
        
        Args:
            data: Price data
            signals: Trading signals
            initial_capital: Starting capital
            stop_loss_pct: Optional stop-loss as a fraction below entry price
            take_profit_pct: Optional take-profit as a fraction above entry price
            
        Returns:
            Dictionary with simulation results
        """
        capital = initial_capital or self.initial_capital
        current_capital = capital
        position = 0
        entry_price = 0
        entry_date = None
        
        # Fee-adjusted price used for fills
        buy_fill_price = lambda p: p * (1 + self.commission + self.slippage)
        sell_fill_price = lambda p: p * (1 - self.commission - self.slippage)
        
        # Initialize tracking variables
        equity_curve = []
        trades = []
        
        for date, row in data.iterrows():
            signal = signals.loc[date, 'signal'] if date in signals.index else 0
            price = row['close']
            open_price = row['open'] if 'open' in data.columns else price
            
            exit_price = None
            exit_reason = None
            
            # Check risk-management exits first (they take priority over signals)
            if position > 0:
                low = row['low'] if 'low' in data.columns else price
                high = row['high'] if 'high' in data.columns else price
                
                if stop_loss_pct is not None:
                    stop_price = entry_price * (1 - stop_loss_pct)
                    if low <= stop_price:
                        # If price gapped below the stop, fill at the (worse) open price
                        exit_price = min(stop_price, open_price)
                        exit_reason = 'stop_loss'
                
                if exit_price is None and take_profit_pct is not None:
                    target_price = entry_price * (1 + take_profit_pct)
                    if high >= target_price:
                        # If price gapped above the target, fill at the (better) open price
                        exit_price = max(target_price, open_price)
                        exit_reason = 'take_profit'
            
            # Handle signal-driven exit
            if exit_price is None and signal == -1 and position > 0:
                exit_price = price
                exit_reason = 'signal'
            
            # Execute exit
            if exit_price is not None and position > 0:
                proceeds = position * sell_fill_price(exit_price)
                current_capital += proceeds
                
                # Calculate trade P&L
                trade_pnl = proceeds - (position * buy_fill_price(entry_price))
                
                # Record trade
                trade_duration = (date - entry_date).days if entry_date else 0
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': date,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'shares': position,
                    'pnl': trade_pnl,
                    'duration': trade_duration,
                    'exit_reason': exit_reason
                })
                
                logger.debug(f"SELL ({exit_reason}): {date} - {position} shares at {exit_price:.2f}, P&L: {trade_pnl:.2f}")
                
                position = 0
                entry_price = 0
                entry_date = None
            
            # Handle buy signal (position sizing accounts for commission and slippage,
            # so the cost can never exceed available capital)
            if signal == 1 and position == 0:
                shares = int(current_capital / buy_fill_price(price))
                if shares > 0:
                    cost = shares * buy_fill_price(price)
                    position = shares
                    entry_price = price
                    entry_date = date
                    current_capital -= cost
                    
                    logger.debug(f"BUY: {date} - {shares} shares at {price:.2f}")
            
            # Calculate current portfolio value
            portfolio_value = current_capital + (position * price)
            equity_curve.append({
                'date': date,
                'capital': current_capital,
                'position_value': position * price,
                'portfolio_value': portfolio_value,
                'position': position
            })
        
        # Close any remaining position at the end
        if position > 0:
            final_price = data.iloc[-1]['close']
            proceeds = position * sell_fill_price(final_price)
            current_capital += proceeds
            
            trade_pnl = proceeds - (position * buy_fill_price(entry_price))
            trade_duration = (data.index[-1] - entry_date).days if entry_date else 0
            
            trades.append({
                'entry_date': entry_date,
                'exit_date': data.index[-1],
                'entry_price': entry_price,
                'exit_price': final_price,
                'shares': position,
                'pnl': trade_pnl,
                'duration': trade_duration,
                'exit_reason': 'end_of_data'
            })
        
        # Convert to DataFrames
        equity_df = pd.DataFrame(equity_curve)
        equity_df.set_index('date', inplace=True)
        
        trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
        
        return {
            'initial_capital': capital,
            'final_capital': current_capital,
            'equity_curve': equity_df['portfolio_value'],
            'trades': trades_df,
            'equity_data': equity_df
        }
    
    def _calculate_performance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics for the backtest results."""
        equity_curve = results['equity_curve']
        trades = results['trades']
        
        # Calculate all metrics
        metrics = metrics_calculator.calculate_all_metrics(equity_curve, trades)
        
        # Add basic metrics
        metrics['initial_capital'] = results['initial_capital']
        metrics['final_capital'] = results['final_capital']
        metrics['total_pnl'] = results['final_capital'] - results['initial_capital']
        
        return metrics
    
    def run_multiple_backtests(self, symbols: List[str], strategy: BaseStrategy,
                              start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        Run backtests for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            strategy: Trading strategy instance
            start_date: Start date for backtests
            end_date: End date for backtests
            
        Returns:
            Dictionary with results for all symbols
        """
        logger.info(f"Running backtests for {len(symbols)} symbols")
        
        results = {}
        
        for symbol in symbols:
            logger.info(f"Running backtest for {symbol} ({symbols.index(symbol) + 1}/{len(symbols)})")
            
            try:
                result = self.run_backtest(symbol, strategy, start_date, end_date)
                results[symbol] = result
            except Exception as e:
                logger.error(f"Error running backtest for {symbol}: {e}")
                results[symbol] = {}
        
        # Calculate aggregate metrics
        aggregate_results = self._calculate_aggregate_metrics(results)
        
        return {
            'individual_results': results,
            'aggregate_results': aggregate_results
        }
    
    def _calculate_aggregate_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate aggregate metrics across all symbols."""
        successful_results = {k: v for k, v in results.items() if v}
        
        if not successful_results:
            return {}
        
        # Aggregate metrics
        total_initial_capital = sum(r['initial_capital'] for r in successful_results.values())
        total_final_capital = sum(r['final_capital'] for r in successful_results.values())
        total_pnl = total_final_capital - total_initial_capital
        
        # Average metrics
        avg_return = np.mean([r['metrics'].get('total_return', 0) for r in successful_results.values()])
        avg_sharpe = np.mean([r['metrics'].get('sharpe_ratio', 0) for r in successful_results.values()])
        avg_max_drawdown = np.mean([r['metrics'].get('max_drawdown', 0) for r in successful_results.values()])
        
        return {
            'total_symbols': len(successful_results),
            'total_initial_capital': total_initial_capital,
            'total_final_capital': total_final_capital,
            'total_pnl': total_pnl,
            'total_return': (total_final_capital / total_initial_capital - 1) if total_initial_capital > 0 else 0,
            'avg_return': avg_return,
            'avg_sharpe_ratio': avg_sharpe,
            'avg_max_drawdown': avg_max_drawdown
        }
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive backtest report."""
        if not results:
            return "No backtest results available."
        
        report = []
        report.append("=" * 80)
        report.append("BACKTESTING REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Basic information
        report.append(f"Symbol: {results.get('symbol', 'N/A')}")
        report.append(f"Strategy: {results.get('strategy', 'N/A')}")
        report.append(f"Parameters: {results.get('strategy_params', {})}")
        report.append(f"Period: {results.get('start_date', 'N/A')} to {results.get('end_date', 'N/A')}")
        report.append(f"Initial Capital: ₹{results.get('initial_capital', 0):,.2f}")
        report.append(f"Final Capital: ₹{results.get('final_capital', 0):,.2f}")
        report.append("")
        
        # Performance metrics
        metrics = results.get('metrics', {})
        if metrics:
            report.append(metrics_calculator.generate_report(metrics))
        
        # Trade summary
        trades = results.get('trades', pd.DataFrame())
        if not trades.empty:
            report.append(f"Total Trades: {len(trades)}")
            if 'pnl' in trades.columns:
                winning_trades = len(trades[trades['pnl'] > 0])
                losing_trades = len(trades[trades['pnl'] < 0])
                report.append(f"Winning Trades: {winning_trades}")
                report.append(f"Losing Trades: {losing_trades}")
                report.append(f"Win Rate: {winning_trades/len(trades)*100:.1f}%")
        
        return "\n".join(report)

# Global backtest engine instance
backtest_engine = BacktestEngine()
