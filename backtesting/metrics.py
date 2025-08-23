"""
Performance metrics calculation for backtesting results.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """Calculate various performance metrics for backtesting results."""
    
    def __init__(self, risk_free_rate: float = 0.06):
        """
        Initialize PerformanceMetrics.
        
        Args:
            risk_free_rate: Annual risk-free rate (default: 6%)
        """
        self.risk_free_rate = risk_free_rate
    
    def calculate_returns(self, equity_curve: pd.Series) -> Dict[str, float]:
        """
        Calculate return metrics.
        
        Args:
            equity_curve: Series with portfolio values over time
            
        Returns:
            Dictionary with return metrics
        """
        if equity_curve.empty:
            return {}
        
        # Calculate daily returns
        daily_returns = equity_curve.pct_change().dropna()
        
        # Total return
        total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
        
        # Annualized return
        days = (equity_curve.index[-1] - equity_curve.index[0]).days
        years = days / 365.25
        annualized_return = ((1 + total_return) ** (1 / years)) - 1 if years > 0 else 0
        
        # Average daily return
        avg_daily_return = daily_returns.mean()
        
        # Volatility (annualized)
        daily_volatility = daily_returns.std()
        annualized_volatility = daily_volatility * np.sqrt(252)
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'avg_daily_return': avg_daily_return,
            'daily_volatility': daily_volatility,
            'annualized_volatility': annualized_volatility
        }
    
    def calculate_drawdown(self, equity_curve: pd.Series) -> Dict[str, Any]:
        """
        Calculate drawdown metrics.
        
        Args:
            equity_curve: Series with portfolio values over time
            
        Returns:
            Dictionary with drawdown metrics
        """
        if equity_curve.empty:
            return {}
        
        # Calculate running maximum
        running_max = equity_curve.expanding().max()
        
        # Calculate drawdown
        drawdown = (equity_curve - running_max) / running_max
        
        # Maximum drawdown
        max_drawdown = drawdown.min()
        
        # Current drawdown
        current_drawdown = drawdown.iloc[-1]
        
        # Drawdown duration
        underwater = drawdown < 0
        underwater_periods = underwater.sum()
        total_periods = len(drawdown)
        underwater_ratio = underwater_periods / total_periods if total_periods > 0 else 0
        
        # Find longest drawdown period
        longest_drawdown = 0
        current_underwater = 0
        
        for is_underwater in underwater:
            if is_underwater:
                current_underwater += 1
                longest_drawdown = max(longest_drawdown, current_underwater)
            else:
                current_underwater = 0
        
        return {
            'max_drawdown': max_drawdown,
            'current_drawdown': current_drawdown,
            'underwater_periods': underwater_periods,
            'underwater_ratio': underwater_ratio,
            'longest_drawdown_periods': longest_drawdown,
            'drawdown_series': drawdown
        }
    
    def calculate_risk_metrics(self, equity_curve: pd.Series) -> Dict[str, float]:
        """
        Calculate risk-adjusted performance metrics.
        
        Args:
            equity_curve: Series with portfolio values over time
            
        Returns:
            Dictionary with risk metrics
        """
        if equity_curve.empty:
            return {}
        
        # Calculate daily returns
        daily_returns = equity_curve.pct_change().dropna()
        
        if daily_returns.empty:
            return {}
        
        # Sharpe Ratio
        excess_returns = daily_returns - (self.risk_free_rate / 252)  # Daily risk-free rate
        sharpe_ratio = excess_returns.mean() / daily_returns.std() * np.sqrt(252) if daily_returns.std() > 0 else 0
        
        # Sortino Ratio (using downside deviation)
        downside_returns = daily_returns[daily_returns < 0]
        downside_deviation = downside_returns.std() if len(downside_returns) > 0 else 0
        sortino_ratio = excess_returns.mean() / downside_deviation * np.sqrt(252) if downside_deviation > 0 else 0
        
        # Calmar Ratio
        total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
        days = (equity_curve.index[-1] - equity_curve.index[0]).days
        years = days / 365.25
        annualized_return = ((1 + total_return) ** (1 / years)) - 1 if years > 0 else 0
        
        # Calculate max drawdown for Calmar ratio
        running_max = equity_curve.expanding().max()
        drawdown = (equity_curve - running_max) / running_max
        max_drawdown = abs(drawdown.min())
        
        calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0
        
        # Value at Risk (95% confidence)
        var_95 = np.percentile(daily_returns, 5)
        
        # Conditional Value at Risk (Expected Shortfall)
        cvar_95 = daily_returns[daily_returns <= var_95].mean()
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'var_95': var_95,
            'cvar_95': cvar_95,
            'downside_deviation': downside_deviation
        }
    
    def calculate_trade_metrics(self, trades: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate trade-specific metrics.
        
        Args:
            trades: DataFrame with trade information
            
        Returns:
            Dictionary with trade metrics
        """
        if trades.empty:
            return {}
        
        # Basic trade counts
        total_trades = len(trades)
        winning_trades = len(trades[trades['pnl'] > 0])
        losing_trades = len(trades[trades['pnl'] < 0])
        breakeven_trades = len(trades[trades['pnl'] == 0])
        
        # Win rate
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Profit factor
        gross_profit = trades[trades['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(trades[trades['pnl'] < 0]['pnl'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Average trade metrics
        avg_trade_pnl = trades['pnl'].mean()
        avg_winning_trade = trades[trades['pnl'] > 0]['pnl'].mean()
        avg_losing_trade = trades[trades['pnl'] < 0]['pnl'].mean()
        
        # Largest win/loss
        largest_win = trades['pnl'].max()
        largest_loss = trades['pnl'].min()
        
        # Trade duration metrics
        if 'duration' in trades.columns:
            avg_trade_duration = trades['duration'].mean()
            longest_trade = trades['duration'].max()
            shortest_trade = trades['duration'].min()
        else:
            avg_trade_duration = longest_trade = shortest_trade = None
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'breakeven_trades': breakeven_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_trade_pnl': avg_trade_pnl,
            'avg_winning_trade': avg_winning_trade,
            'avg_losing_trade': avg_losing_trade,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'avg_trade_duration': avg_trade_duration,
            'longest_trade': longest_trade,
            'shortest_trade': shortest_trade
        }
    
    def calculate_all_metrics(self, equity_curve: pd.Series, trades: pd.DataFrame = None) -> Dict[str, Any]:
        """
        Calculate all performance metrics.
        
        Args:
            equity_curve: Series with portfolio values over time
            trades: DataFrame with trade information (optional)
            
        Returns:
            Dictionary with all performance metrics
        """
        metrics = {}
        
        # Return metrics
        metrics.update(self.calculate_returns(equity_curve))
        
        # Drawdown metrics
        metrics.update(self.calculate_drawdown(equity_curve))
        
        # Risk metrics
        metrics.update(self.calculate_risk_metrics(equity_curve))
        
        # Trade metrics (if available)
        if trades is not None and not trades.empty:
            metrics.update(self.calculate_trade_metrics(trades))
        
        return metrics
    
    def generate_report(self, metrics: Dict[str, Any]) -> str:
        """
        Generate a formatted performance report.
        
        Args:
            metrics: Dictionary with performance metrics
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        report.append("BACKTESTING PERFORMANCE REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Returns Section
        report.append("RETURNS:")
        report.append("-" * 20)
        if 'total_return' in metrics:
            report.append(f"Total Return: {metrics['total_return']:.2%}")
        if 'annualized_return' in metrics:
            report.append(f"Annualized Return: {metrics['annualized_return']:.2%}")
        if 'avg_daily_return' in metrics:
            report.append(f"Average Daily Return: {metrics['avg_daily_return']:.4%}")
        report.append("")
        
        # Risk Section
        report.append("RISK METRICS:")
        report.append("-" * 20)
        if 'annualized_volatility' in metrics:
            report.append(f"Annualized Volatility: {metrics['annualized_volatility']:.2%}")
        if 'max_drawdown' in metrics:
            report.append(f"Maximum Drawdown: {metrics['max_drawdown']:.2%}")
        if 'sharpe_ratio' in metrics:
            report.append(f"Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
        if 'sortino_ratio' in metrics:
            report.append(f"Sortino Ratio: {metrics['sortino_ratio']:.3f}")
        if 'calmar_ratio' in metrics:
            report.append(f"Calmar Ratio: {metrics['calmar_ratio']:.3f}")
        report.append("")
        
        # Trade Section
        if 'total_trades' in metrics:
            report.append("TRADE METRICS:")
            report.append("-" * 20)
            report.append(f"Total Trades: {metrics['total_trades']}")
            report.append(f"Winning Trades: {metrics['winning_trades']}")
            report.append(f"Losing Trades: {metrics['losing_trades']}")
            report.append(f"Win Rate: {metrics['win_rate']:.2%}")
            report.append(f"Profit Factor: {metrics['profit_factor']:.3f}")
            if metrics['avg_trade_pnl'] is not None:
                report.append(f"Average Trade P&L: {metrics['avg_trade_pnl']:.2f}")
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)

# Global metrics calculator instance
metrics_calculator = PerformanceMetrics()
