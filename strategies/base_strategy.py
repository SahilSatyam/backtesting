"""
Base strategy class for all trading strategies.
"""
import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import date
import logging

logger = logging.getLogger(__name__)

class BaseStrategy(ABC):
    """Abstract base class for all trading strategies."""
    
    def __init__(self, name: str = "Base Strategy"):
        self.name = name
        self.parameters = {}
        self.signals = pd.DataFrame()
        self.positions = pd.DataFrame()
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals from price data.
        
        Args:
            data: DataFrame with OHLCV data indexed by date
            
        Returns:
            DataFrame with signals (1 for buy, -1 for sell, 0 for hold)
        """
        pass
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for the strategy.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with additional indicator columns
        """
        return data.copy()
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate input data for the strategy.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            True if data is valid, False otherwise
        """
        if data is None or data.empty:
            logger.error("Data is None or empty")
            return False
        
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return False
        
        # Check for null values in critical columns
        if data['close'].isnull().any():
            logger.warning("Found null values in close prices")
        
        # Check for reasonable price values
        if (data['close'] <= 0).any():
            logger.error("Found invalid close prices (<= 0)")
            return False
        
        return True
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters."""
        return self.parameters.copy()
    
    def set_parameters(self, parameters: Dict[str, Any]):
        """Set strategy parameters."""
        self.parameters.update(parameters)
        logger.info(f"Updated parameters for {self.name}: {parameters}")
    
    def get_signals_summary(self) -> Dict[str, Any]:
        """Get summary of generated signals."""
        if self.signals.empty:
            return {}
        
        buy_signals = (self.signals['signal'] == 1).sum()
        sell_signals = (self.signals['signal'] == -1).sum()
        hold_signals = (self.signals['signal'] == 0).sum()
        
        return {
            'total_signals': len(self.signals),
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'hold_signals': hold_signals,
            'signal_ratio': buy_signals / max(sell_signals, 1)
        }
    
    def plot_signals(self, data: pd.DataFrame, signals: pd.DataFrame = None):
        """
        Plot price data with trading signals.
        
        Args:
            data: DataFrame with OHLCV data
            signals: DataFrame with signals (optional, uses self.signals if None)
        """
        try:
            import matplotlib.pyplot as plt
            
            if signals is None:
                signals = self.signals
            
            if signals.empty:
                logger.warning("No signals to plot")
                return
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
            
            # Plot price data
            ax1.plot(data.index, data['close'], label='Close Price', alpha=0.7)
            
            # Plot buy signals
            buy_signals = signals[signals['signal'] == 1]
            if not buy_signals.empty:
                ax1.scatter(buy_signals.index, data.loc[buy_signals.index, 'close'], 
                           color='green', marker='^', s=100, label='Buy Signal')
            
            # Plot sell signals
            sell_signals = signals[signals['signal'] == -1]
            if not sell_signals.empty:
                ax1.scatter(sell_signals.index, data.loc[sell_signals.index, 'close'], 
                           color='red', marker='v', s=100, label='Sell Signal')
            
            ax1.set_title(f'{self.name} - Price and Signals')
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
            logger.error(f"Error plotting signals: {e}")
    
    def __str__(self):
        return f"{self.name} (Parameters: {self.parameters})"
    
    def __repr__(self):
        return self.__str__()
