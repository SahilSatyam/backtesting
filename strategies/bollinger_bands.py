"""
Bollinger Bands Mean Reversion Strategy Implementation.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from strategies.base_strategy import BaseStrategy
import logging

logger = logging.getLogger(__name__)

class BollingerBands(BaseStrategy):
    """
    Bollinger Bands Mean Reversion Strategy.
    
    This strategy buys when the close crosses up through the lower band
    (price recovering from an oversold extreme) and sells when the close
    crosses down through the upper band (price fading from an overbought
    extreme).
    
    Bands are computed as a middle band (simple moving average) plus and
    minus a multiple of the rolling standard deviation.
    """
    
    def __init__(self, window: int = 20, num_std: float = 2.0):
        """
        Initialize Bollinger Bands Strategy.
        
        Args:
            window: Lookback period for the middle band and deviation
            num_std: Number of standard deviations for the upper/lower bands
        """
        super().__init__(name="Bollinger Bands")
        
        if window < 2:
            raise ValueError("window must be at least 2")
        if num_std <= 0:
            raise ValueError("num_std must be positive")
        
        self.parameters = {
            'window': window,
            'num_std': num_std
        }
        
        logger.info(f"Initialized {self.name} with parameters: {self.parameters}")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Bollinger Bands for the strategy.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with additional indicator columns
        """
        if not self.validate_data(data):
            return data
        
        df = data.copy()
        
        window = self.parameters['window']
        num_std = self.parameters['num_std']
        
        middle = df['close'].rolling(window=window).mean()
        std = df['close'].rolling(window=window).std()
        
        df['bb_middle'] = middle
        df['bb_upper'] = middle + num_std * std
        df['bb_lower'] = middle - num_std * std
        
        # %B: position of the close within the bands (0 at lower, 1 at upper)
        band_width = df['bb_upper'] - df['bb_lower']
        df['bb_percent_b'] = (df['close'] - df['bb_lower']) / band_width.replace(0, np.nan)
        
        logger.info(f"Calculated Bollinger Band indicators for {len(df)} data points")
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on Bollinger Band crossings.
        
        Buy when the close crosses up through the lower band,
        sell when the close crosses down through the upper band.
        
        Args:
            data: DataFrame with OHLCV data indexed by date
            
        Returns:
            DataFrame with signals (1 for buy, -1 for sell, 0 for hold)
        """
        if not self.validate_data(data):
            return pd.DataFrame()
        
        # Calculate indicators
        df = self.calculate_indicators(data)
        
        close = df['close']
        prev_close = close.shift(1)
        
        # Initialize signals
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Buy: close crosses up through the lower band
        buy_signals = (prev_close < df['bb_lower'].shift(1)) & (close >= df['bb_lower'])
        signals.loc[buy_signals, 'signal'] = 1
        
        # Sell: close crosses down through the upper band
        sell_signals = (prev_close > df['bb_upper'].shift(1)) & (close <= df['bb_upper'])
        signals.loc[sell_signals, 'signal'] = -1
        
        # Add additional columns for analysis
        signals['bb_upper'] = df['bb_upper']
        signals['bb_middle'] = df['bb_middle']
        signals['bb_lower'] = df['bb_lower']
        signals['bb_percent_b'] = df['bb_percent_b']
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
        summary['avg_percent_b'] = self.signals['bb_percent_b'].mean()
        summary['avg_band_width'] = (self.signals['bb_upper'] - self.signals['bb_lower']).mean()
        
        buy_signals = self.signals[self.signals['signal'] == 1]
        sell_signals = self.signals[self.signals['signal'] == -1]
        
        if not buy_signals.empty:
            summary['avg_buy_percent_b'] = buy_signals['bb_percent_b'].mean()
            summary['avg_buy_price'] = buy_signals['close'].mean()
        
        if not sell_signals.empty:
            summary['avg_sell_percent_b'] = sell_signals['bb_percent_b'].mean()
            summary['avg_sell_price'] = sell_signals['close'].mean()
        
        return summary
