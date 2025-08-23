"""
Visualization module for backtesting results and charts.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

def plot_equity_curve(equity_curve: pd.Series, title: str = "Equity Curve", 
                     save_path: str = None, show: bool = True):
    """
    Plot the equity curve.
    
    Args:
        equity_curve: Series with portfolio values over time
        title: Chart title
        save_path: Path to save the chart (optional)
        show: Whether to display the chart
    """
    try:
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(15, 8))
        plt.plot(equity_curve.index, equity_curve.values, linewidth=2, color='blue')
        plt.title(title, fontsize=16, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Portfolio Value (₹)', fontsize=12)
        plt.grid(True, alpha=0.3)
        
        # Add start and end values
        start_value = equity_curve.iloc[0]
        end_value = equity_curve.iloc[-1]
        plt.annotate(f'Start: ₹{start_value:,.0f}', 
                    xy=(equity_curve.index[0], start_value),
                    xytext=(10, 10), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
        plt.annotate(f'End: ₹{end_value:,.0f}', 
                    xy=(equity_curve.index[-1], end_value),
                    xytext=(10, 10), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='green', alpha=0.7))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Chart saved to {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close()
            
    except ImportError:
        logger.error("Matplotlib not available for plotting")
    except Exception as e:
        logger.error(f"Error plotting equity curve: {e}")

def plot_drawdown(drawdown_series: pd.Series, title: str = "Drawdown Analysis",
                 save_path: str = None, show: bool = True):
    """
    Plot the drawdown series.
    
    Args:
        drawdown_series: Series with drawdown values over time
        title: Chart title
        save_path: Path to save the chart (optional)
        show: Whether to display the chart
    """
    try:
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(15, 8))
        plt.fill_between(drawdown_series.index, drawdown_series.values, 0, 
                        alpha=0.3, color='red', label='Drawdown')
        plt.plot(drawdown_series.index, drawdown_series.values, color='red', linewidth=1)
        plt.title(title, fontsize=16, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Drawdown (%)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Add max drawdown annotation
        max_dd = drawdown_series.min()
        max_dd_date = drawdown_series.idxmin()
        plt.annotate(f'Max DD: {max_dd:.2%}', 
                    xy=(max_dd_date, max_dd),
                    xytext=(10, -10), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.7))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Chart saved to {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close()
            
    except ImportError:
        logger.error("Matplotlib not available for plotting")
    except Exception as e:
        logger.error(f"Error plotting drawdown: {e}")

def plot_trades(data: pd.DataFrame, trades: pd.DataFrame, title: str = "Trades Analysis",
               save_path: str = None, show: bool = True):
    """
    Plot price data with trade entry and exit points.
    
    Args:
        data: DataFrame with OHLCV data
        trades: DataFrame with trade information
        title: Chart title
        save_path: Path to save the chart (optional)
        show: Whether to display the chart
    """
    try:
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(15, 10))
        
        # Plot price data
        plt.plot(data.index, data['close'], label='Close Price', alpha=0.7, linewidth=1)
        
        if not trades.empty:
            # Plot buy points
            buy_trades = trades[trades['pnl'] != 0]  # Filter out potential errors
            if not buy_trades.empty:
                plt.scatter(buy_trades['entry_date'], buy_trades['entry_price'], 
                           color='green', marker='^', s=100, label='Buy', zorder=5)
                plt.scatter(buy_trades['exit_date'], buy_trades['exit_price'], 
                           color='red', marker='v', s=100, label='Sell', zorder=5)
        
        plt.title(title, fontsize=16, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Price (₹)', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Chart saved to {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close()
            
    except ImportError:
        logger.error("Matplotlib not available for plotting")
    except Exception as e:
        logger.error(f"Error plotting trades: {e}")

def plot_monthly_returns(equity_curve: pd.Series, title: str = "Monthly Returns",
                        save_path: str = None, show: bool = True):
    """
    Plot monthly returns heatmap.
    
    Args:
        equity_curve: Series with portfolio values over time
        title: Chart title
        save_path: Path to save the chart (optional)
        show: Whether to display the chart
    """
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        # Calculate monthly returns
        monthly_returns = equity_curve.resample('M').last().pct_change().dropna()
        
        # Create year-month matrix
        monthly_returns.index = pd.to_datetime(monthly_returns.index)
        monthly_returns_df = monthly_returns.to_frame('returns')
        monthly_returns_df['year'] = monthly_returns_df.index.year
        monthly_returns_df['month'] = monthly_returns_df.index.month
        
        # Pivot for heatmap
        returns_matrix = monthly_returns_df.pivot(index='year', columns='month', values='returns')
        
        # Create heatmap
        plt.figure(figsize=(12, 8))
        sns.heatmap(returns_matrix, annot=True, fmt='.2%', cmap='RdYlGn', 
                   center=0, cbar_kws={'label': 'Monthly Return'})
        plt.title(title, fontsize=16, fontweight='bold')
        plt.xlabel('Month', fontsize=12)
        plt.ylabel('Year', fontsize=12)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Chart saved to {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close()
            
    except ImportError:
        logger.error("Matplotlib/Seaborn not available for plotting")
    except Exception as e:
        logger.error(f"Error plotting monthly returns: {e}")

def plot_performance_comparison(results: Dict[str, Any], benchmark: pd.Series = None,
                              title: str = "Performance Comparison",
                              save_path: str = None, show: bool = True):
    """
    Plot performance comparison with benchmark.
    
    Args:
        results: Dictionary with backtest results
        benchmark: Series with benchmark values (optional)
        title: Chart title
        save_path: Path to save the chart (optional)
        show: Whether to display the chart
    """
    try:
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(15, 8))
        
        # Plot strategy equity curve
        equity_curve = results['equity_curve']
        normalized_strategy = equity_curve / equity_curve.iloc[0]
        plt.plot(normalized_strategy.index, normalized_strategy.values, 
                label='Strategy', linewidth=2, color='blue')
        
        # Plot benchmark if provided
        if benchmark is not None:
            normalized_benchmark = benchmark / benchmark.iloc[0]
            plt.plot(normalized_benchmark.index, normalized_benchmark.values, 
                    label='Benchmark', linewidth=2, color='red', alpha=0.7)
        
        plt.title(title, fontsize=16, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Normalized Value', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Chart saved to {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close()
            
    except ImportError:
        logger.error("Matplotlib not available for plotting")
    except Exception as e:
        logger.error(f"Error plotting performance comparison: {e}")

def create_interactive_chart(results: Dict[str, Any], title: str = "Interactive Backtest Results"):
    """
    Create an interactive chart using Plotly.
    
    Args:
        results: Dictionary with backtest results
        title: Chart title
        
    Returns:
        Plotly figure object
    """
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=('Portfolio Value', 'Drawdown', 'Trades'),
            vertical_spacing=0.1,
            row_heights=[0.5, 0.25, 0.25]
        )
        
        # Portfolio value
        equity_curve = results['equity_curve']
        fig.add_trace(
            go.Scatter(x=equity_curve.index, y=equity_curve.values,
                      mode='lines', name='Portfolio Value',
                      line=dict(color='blue', width=2)),
            row=1, col=1
        )
        
        # Drawdown
        if 'drawdown_series' in results.get('metrics', {}):
            drawdown = results['metrics']['drawdown_series']
            fig.add_trace(
                go.Scatter(x=drawdown.index, y=drawdown.values,
                          mode='lines', name='Drawdown',
                          fill='tonexty', line=dict(color='red')),
                row=2, col=1
            )
        
        # Trades
        trades = results.get('trades', pd.DataFrame())
        if not trades.empty:
            # Buy points
            fig.add_trace(
                go.Scatter(x=trades['entry_date'], y=trades['entry_price'],
                          mode='markers', name='Buy',
                          marker=dict(color='green', size=8, symbol='triangle-up')),
                row=3, col=1
            )
            
            # Sell points
            fig.add_trace(
                go.Scatter(x=trades['exit_date'], y=trades['exit_price'],
                          mode='markers', name='Sell',
                          marker=dict(color='red', size=8, symbol='triangle-down')),
                row=3, col=1
            )
        
        # Update layout
        fig.update_layout(
            title=title,
            height=800,
            showlegend=True,
            hovermode='x unified'
        )
        
        return fig
        
    except ImportError:
        logger.error("Plotly not available for interactive plotting")
        return None
    except Exception as e:
        logger.error(f"Error creating interactive chart: {e}")
        return None

def plot_strategy_signals(data: pd.DataFrame, signals: pd.DataFrame, 
                         strategy_name: str = "Strategy Signals",
                         save_path: str = None, show: bool = True):
    """
    Plot price data with strategy signals.
    
    Args:
        data: DataFrame with OHLCV data
        signals: DataFrame with trading signals
        strategy_name: Name of the strategy
        save_path: Path to save the chart (optional)
        show: Whether to display the chart
    """
    try:
        import matplotlib.pyplot as plt
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
        
        # Plot price and signals
        ax1.plot(data.index, data['close'], label='Close Price', alpha=0.7, linewidth=1)
        
        if not signals.empty:
            # Buy signals
            buy_signals = signals[signals['signal'] == 1]
            if not buy_signals.empty:
                ax1.scatter(buy_signals.index, buy_signals['close'], 
                           color='green', marker='^', s=100, label='Buy Signal', zorder=5)
            
            # Sell signals
            sell_signals = signals[signals['signal'] == -1]
            if not sell_signals.empty:
                ax1.scatter(sell_signals.index, sell_signals['close'], 
                           color='red', marker='v', s=100, label='Sell Signal', zorder=5)
        
        ax1.set_title(f'{strategy_name} - Price and Signals', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price (₹)', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot volume
        ax2.bar(data.index, data['volume'], alpha=0.7, color='blue')
        ax2.set_title('Volume', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Volume', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Chart saved to {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close()
            
    except ImportError:
        logger.error("Matplotlib not available for plotting")
    except Exception as e:
        logger.error(f"Error plotting strategy signals: {e}")
