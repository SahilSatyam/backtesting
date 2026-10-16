"""
Moving Average Crossover Strategy Implementation.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from strategies.base_strategy import BaseStrategy
import logging

logger = logging.getLogger(__name__)

class MovingAverageCrossover(BaseStrategy):
    """
    Moving Average Crossover Strategy.
    
    This strategy generates buy signals when the short-term moving average
    crosses above the long-term moving average, and sell signals when it
    crosses below.
    
    Supports simple (SMA) and exponential (EMA) moving averages. EMA reacts
    faster to recent prices, reducing crossover lag at the cost of more
    whipsaws in choppy markets.
    """
    
    def __init__(self, short_window: int = 20, long_window: int = 50,
                 ma_type: str = 'sma'):
        """
        Initialize Moving Average Crossover Strategy.
        
        Args:
            short_window: Period for short-term moving average
            long_window: Period for long-term moving average
            ma_type: Type of moving average, 'sma' or 'ema'
        """
        super().__init__(name="Moving Average Crossover")
        
        ma_type = ma_type.lower()
        if ma_type not in ('sma', 'ema'):
            raise ValueError(f"Unsupported ma_type '{ma_type}'. Use 'sma' or 'ema'.")
        if short_window >= long_window:
            raise ValueError("short_window must be smaller than long_window")
        
        self.parameters = {
            'short_window': short_window,
            'long_window': long_window,
            'ma_type': ma_type
        }
        
        logger.info(f"Initialized {self.name} with parameters: {self.parameters}")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate moving averages for the strategy.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with additional indicator columns
        """
        if not self.validate_data(data):
            return data
        
        df = data.copy()
        
        # Calculate moving averages
        short_window = self.parameters['short_window']
        long_window = self.parameters['long_window']
        ma_type = self.parameters.get('ma_type', 'sma')
        
        if ma_type == 'ema':
            df[f'ma_{short_window}'] = df['close'].ewm(span=short_window, adjust=False).mean()
            df[f'ma_{long_window}'] = df['close'].ewm(span=long_window, adjust=False).mean()
        else:
            df[f'ma_{short_window}'] = df['close'].rolling(window=short_window).mean()
            df[f'ma_{long_window}'] = df['close'].rolling(window=long_window).mean()
        
        # Calculate crossover signals
        df['ma_cross'] = np.where(
            df[f'ma_{short_window}'] > df[f'ma_{long_window}'], 1, 0
        )
        
        # Calculate crossover points
        df['ma_cross_change'] = df['ma_cross'].diff()
        
        logger.info(f"Calculated indicators for {len(df)} data points")
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on moving average crossovers.
        
        Args:
            data: DataFrame with OHLCV data indexed by date
            
        Returns:
            DataFrame with signals (1 for buy, -1 for sell, 0 for hold)
        """
        if not self.validate_data(data):
            return pd.DataFrame()
        
        # Calculate indicators
        df = self.calculate_indicators(data)
        
        # Initialize signals
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Generate buy signals (short MA crosses above long MA)
        buy_signals = (df['ma_cross_change'] == 1)
        signals.loc[buy_signals, 'signal'] = 1
        
        # Generate sell signals (short MA crosses below long MA)
        sell_signals = (df['ma_cross_change'] == -1)
        signals.loc[sell_signals, 'signal'] = -1
        
        # Add additional columns for analysis
        signals['short_ma'] = df[f"ma_{self.parameters['short_window']}"]
        signals['long_ma'] = df[f"ma_{self.parameters['long_window']}"]
        signals['close'] = df['close']
        signals['volume'] = df['volume']
        
        # Store signals for later use
        self.signals = signals
        
        # Log signal summary
        buy_count = (signals['signal'] == 1).sum()
        sell_count = (signals['signal'] == -1).sum()
        
        logger.info(f"Generated {buy_count} buy signals and {sell_count} sell signals")
        
        return signals
    
    def get_strategy_summary(self) -> Dict[str, Any]:
        """Get detailed summary of the strategy performance."""
        if self.signals.empty:
            return {}
        
        summary = self.get_signals_summary()
        
        # Add strategy-specific metrics
        if not self.signals.empty:
            # Calculate average price at buy/sell points
            buy_signals = self.signals[self.signals['signal'] == 1]
            sell_signals = self.signals[self.signals['signal'] == -1]
            
            if not buy_signals.empty:
                summary['avg_buy_price'] = buy_signals['close'].mean()
                summary['buy_price_std'] = buy_signals['close'].std()
            
            if not sell_signals.empty:
                summary['avg_sell_price'] = sell_signals['close'].mean()
                summary['sell_price_std'] = sell_signals['close'].std()
            
            # Calculate moving average statistics
            summary['avg_short_ma'] = self.signals['short_ma'].mean()
            summary['avg_long_ma'] = self.signals['long_ma'].mean()
            summary['ma_spread'] = summary['avg_short_ma'] - summary['avg_long_ma']
        
        return summary
    
    def plot_strategy(self, data: pd.DataFrame, signals: pd.DataFrame = None):
        """
        Plot the strategy with moving averages and signals.
        
        Args:
            data: DataFrame with OHLCV data
            signals: DataFrame with signals (optional)
        """
        try:
            import matplotlib.pyplot as plt
            
            if signals is None:
                signals = self.signals
            
            if signals.empty:
                logger.warning("No signals to plot")
                return
            
            # Calculate indicators for plotting
            df = self.calculate_indicators(data)
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
            
            # Plot price and moving averages
            ax1.plot(data.index, data['close'], label='Close Price', alpha=0.7, linewidth=1)
            ax1.plot(df.index, df[f"ma_{self.parameters['short_window']}"], 
                    label=f'{self.parameters["short_window"]}-day MA', alpha=0.8, linewidth=2)
            ax1.plot(df.index, df[f"ma_{self.parameters['long_window']}"], 
                    label=f'{self.parameters["long_window"]}-day MA', alpha=0.8, linewidth=2)
            
            # Plot buy signals
            buy_signals = signals[signals['signal'] == 1]
            if not buy_signals.empty:
                ax1.scatter(buy_signals.index, buy_signals['close'], 
                           color='green', marker='^', s=100, label='Buy Signal', zorder=5)
            
            # Plot sell signals
            sell_signals = signals[signals['signal'] == -1]
            if not sell_signals.empty:
                ax1.scatter(sell_signals.index, sell_signals['close'], 
                           color='red', marker='v', s=100, label='Sell Signal', zorder=5)
            
            ax1.set_title(f'{self.name} Strategy - Price and Moving Averages')
            ax1.set_ylabel('Price')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Plot volume
            ax2.bar(data.index, data['volume'], alpha=0.7, color='blue')
            ax2.set_title('Volume')
            ax2.set_ylabel('Volume')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.show()
            
        except ImportError:
            logger.error("Matplotlib not available for plotting")
        except Exception as e:
            logger.error(f"Error plotting strategy: {e}")
    
    def optimize_parameters(self, data: pd.DataFrame, 
                          short_range: tuple = (5, 50, 5),
                          long_range: tuple = (20, 200, 10),
                          metric: str = 'sharpe_ratio') -> Dict[str, Any]:
        """
        Optimize strategy parameters using grid search over real backtest
        performance (commission and slippage included).
        
        Args:
            data: DataFrame with OHLCV data
            short_range: (start, end, step) for short window optimization
            long_range: (start, end, step) for long window optimization
            metric: Backtest metric to maximize ('sharpe_ratio', 'total_return',
                    'calmar_ratio', 'sortino_ratio')
            
        Returns:
            Dictionary with optimal parameters and performance metrics:
            {
                'best_parameters': {...} or None,
                'best_metric': value of the optimized metric for best_parameters,
                'all_results': [ {'short_window', 'long_window', 'sharpe_ratio',
                                  'total_return', 'max_drawdown', 'final_capital'}, ... ]
            }
        """
        # Imported lazily to avoid a circular import at module load time
        from backtesting.engine import BacktestEngine
        
        logger.info(f"Starting parameter optimization (objective: {metric})...")
        
        engine = BacktestEngine()
        best_params = None
        best_value = -np.inf
        
        short_windows = range(short_range[0], short_range[1], short_range[2])
        long_windows = range(long_range[0], long_range[1], long_range[2])
        
        results = []
        
        for short_window in short_windows:
            for long_window in long_windows:
                if short_window >= long_window:
                    continue
                
                # Create strategy with new parameters
                strategy = MovingAverageCrossover(short_window, long_window,
                                                  ma_type=self.parameters.get('ma_type', 'sma'))
                backtest = engine.run_backtest('OPTIMIZATION', strategy, data=data)
                
                if not backtest:
                    continue
                
                metrics = backtest['metrics']
                value = metrics.get(metric)
                
                if value is None or not np.isfinite(value):
                    continue
                
                results.append({
                    'short_window': short_window,
                    'long_window': long_window,
                    metric: value,
                    'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                    'total_return': metrics.get('total_return', 0),
                    'max_drawdown': metrics.get('max_drawdown', 0),
                    'final_capital': backtest['final_capital']
                })
                
                if value > best_value:
                    best_value = value
                    best_params = {'short_window': short_window, 'long_window': long_window,
                                   'ma_type': self.parameters.get('ma_type', 'sma')}
        
        logger.info(f"Optimization complete. Best parameters: {best_params} "
                    f"({metric}: {best_value:.4f})")
        
        return {
            'best_parameters': best_params,
            'best_metric': best_value if np.isfinite(best_value) else None,
            'all_results': results
        }
