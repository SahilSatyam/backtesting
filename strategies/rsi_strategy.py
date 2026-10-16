"""
RSI Mean Reversion Strategy Implementation.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from strategies.base_strategy import BaseStrategy
import logging

logger = logging.getLogger(__name__)

class RSIMeanReversion(BaseStrategy):
    """
    RSI Mean Reversion Strategy.
    
    This strategy buys when the RSI crosses back up through the oversold
    level (momentum recovering from an oversold condition) and sells when
    the RSI crosses back down through the overbought level.
    
    RSI uses Wilder's smoothing (exponential moving average with alpha = 1/period),
    which is the standard definition and gives more weight to recent changes
    than a simple average of gains/losses.
    """
    
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        """
        Initialize RSI Mean Reversion Strategy.
        
        Args:
            period: Lookback period for RSI calculation
            oversold: RSI level below which the asset is considered oversold
            overbought: RSI level above which the asset is considered overbought
        """
        super().__init__(name="RSI Mean Reversion")
        
        if not 0 < oversold < overbought < 100:
            raise ValueError("Require 0 < oversold < overbought < 100")
        if period < 2:
            raise ValueError("period must be at least 2")
        
        self.parameters = {
            'period': period,
            'oversold': oversold,
            'overbought': overbought
        }
        
        logger.info(f"Initialized {self.name} with parameters: {self.parameters}")
    
    def calculate_rsi(self, close: pd.Series) -> pd.Series:
        """
        Calculate RSI using Wilder's smoothing.
        
        Args:
            close: Series of closing prices
            
        Returns:
            Series with RSI values (0-100)
        """
        period = self.parameters['period']
        
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)
        
        # Wilder's smoothing == EMA with alpha = 1/period
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        
        # When there are no losses RSI is 100 by definition; flat prices are neutral
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.where(~((avg_gain == 0) & (avg_loss == 0)), 50.0)
        rsi = rsi.where(~((avg_gain == 0) & (avg_loss > 0)), 100.0)
        
        return rsi
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate the RSI indicator for the strategy.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with additional indicator columns
        """
        if not self.validate_data(data):
            return data
        
        df = data.copy()
        df['rsi'] = self.calculate_rsi(df['close'])
        
        logger.info(f"Calculated RSI indicators for {len(df)} data points")
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on RSI level crossings.
        
        Buy when RSI crosses up through the oversold level,
        sell when RSI crosses down through the overbought level.
        
        Args:
            data: DataFrame with OHLCV data indexed by date
            
        Returns:
            DataFrame with signals (1 for buy, -1 for sell, 0 for hold)
        """
        if not self.validate_data(data):
            return pd.DataFrame()
        
        # Calculate indicators
        df = self.calculate_indicators(data)
        
        oversold = self.parameters['oversold']
        overbought = self.parameters['overbought']
        
        rsi = df['rsi']
        prev_rsi = rsi.shift(1)
        
        # Initialize signals
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Buy: RSI crosses up through the oversold level
        buy_signals = (prev_rsi <= oversold) & (rsi > oversold)
        signals.loc[buy_signals, 'signal'] = 1
        
        # Sell: RSI crosses down through the overbought level
        sell_signals = (prev_rsi >= overbought) & (rsi < overbought)
        signals.loc[sell_signals, 'signal'] = -1
        
        # Add additional columns for analysis
        signals['rsi'] = df['rsi']
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
        """Get detailed summary of the strategy signals."""
        if self.signals.empty:
            return {}
        
        summary = self.get_signals_summary()
        summary['avg_rsi'] = self.signals['rsi'].mean()
        
        buy_signals = self.signals[self.signals['signal'] == 1]
        sell_signals = self.signals[self.signals['signal'] == -1]
        
        if not buy_signals.empty:
            summary['avg_buy_rsi'] = buy_signals['rsi'].mean()
            summary['avg_buy_price'] = buy_signals['close'].mean()
        
        if not sell_signals.empty:
            summary['avg_sell_rsi'] = sell_signals['rsi'].mean()
            summary['avg_sell_price'] = sell_signals['close'].mean()
        
        return summary
