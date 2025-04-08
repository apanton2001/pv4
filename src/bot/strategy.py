"""
Prometheus Trading Bot - Strategy Interface

Base class and interfaces for implementing trading strategies
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

from src.utils import logging as log


class Strategy(ABC):
    """
    Abstract base class for trading strategies
    
    All strategies must inherit from this class and implement the required methods
    """
    
    def __init__(self, name: str):
        """
        Initialize a strategy
        
        Args:
            name: Strategy name for identification
        """
        self.name = name
        log.info(f"Initializing strategy: {self.name}")
    
    @abstractmethod
    async def analyze(self, symbol: str, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze market data and generate a trading signal
        
        Args:
            symbol: Symbol being analyzed
            data: DataFrame with market data (OHLCV)
            
        Returns:
            Trading signal dictionary with action and metadata
        """
        pass
    
    @abstractmethod
    def get_required_data(self) -> Dict[str, Any]:
        """
        Get the data requirements for this strategy
        
        Returns:
            Dictionary with data requirements (timeframe, lookback_bars, etc.)
        """
        pass
    
    async def log_analysis(self, symbol: str, data: pd.DataFrame, signal: Dict[str, Any]):
        """
        Log the analysis results
        
        Args:
            symbol: Symbol being analyzed
            data: DataFrame with market data
            signal: Trading signal dictionary
        """
        action = signal.get("action", "UNKNOWN")
        log.info(f"Strategy {self.name} generated signal: {action} for {symbol}")
        
        metrics = signal.get("metrics", {})
        metrics["latest_close"] = float(data['close'].iloc[-1])
        
        log.info_event("strategy_analysis", {
            "strategy": self.name,
            "symbol": symbol,
            "action": action,
            "metrics": metrics
        })
    
    def __str__(self) -> str:
        return f"Strategy({self.name})"
    
    def __repr__(self) -> str:
        return self.__str__()


class MAStrategy(Strategy):
    """
    Moving Average Crossover strategy
    
    Generates BUY signals when short MA crosses above long MA
    Generates SELL signals when short MA crosses below long MA
    """
    
    def __init__(
        self, 
        short_window: int = 10, 
        long_window: int = 30,
        name: str = "MA_Crossover"
    ):
        """
        Initialize MA Crossover strategy
        
        Args:
            short_window: Short moving average window
            long_window: Long moving average window
            name: Strategy name
        """
        super().__init__(name)
        self.short_window = short_window
        self.long_window = long_window
        log.info(f"MA Crossover strategy initialized with windows: {short_window}/{long_window}")
    
    def get_required_data(self) -> Dict[str, Any]:
        """
        Get data requirements for MA strategy
        
        Returns:
            Dictionary with timeframe and lookback_bars
        """
        # Need at least long_window + 1 bars for signals
        # Add buffer for safety
        lookback_bars = self.long_window + 10
        
        return {
            "timeframe": "1H",  # Default timeframe
            "lookback_bars": lookback_bars,
            "min_required_bars": self.long_window + 1
        }
    
    def calculate_moving_averages(self, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Calculate moving averages on price data
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added MA columns or None if not enough data
        """
        if data is None or len(data) < self.long_window:
            log.warning(f"Insufficient data ({len(data) if data is not None else 0}) for MA calculation")
            return None
            
        try:
            df = data.copy()
            df['MA_short'] = df['close'].rolling(window=self.short_window).mean()
            df['MA_long'] = df['close'].rolling(window=self.long_window).mean()
            return df
        except Exception as e:
            log.error(f"Error calculating moving averages: {e}")
            return None
    
    async def analyze(self, symbol: str, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze price data with MA crossover strategy
        
        Args:
            symbol: Symbol being analyzed
            data: DataFrame with OHLCV data
            
        Returns:
            Trading signal dictionary with action and metadata
        """
        # Default to no signal if anything fails
        null_signal = {"action": None}
        
        # Calculate moving averages
        df_with_ma = self.calculate_moving_averages(data)
        
        if df_with_ma is None or len(df_with_ma) < 2:
            log.debug(f"Insufficient data for MA analysis on {symbol}")
            return null_signal
            
        try:
            # Get current and previous MA values
            current_short_ma = df_with_ma['MA_short'].iloc[-1]
            current_long_ma = df_with_ma['MA_long'].iloc[-1]
            prev_short_ma = df_with_ma['MA_short'].iloc[-2]
            prev_long_ma = df_with_ma['MA_long'].iloc[-2]
            
            # Check for NaN values
            if (pd.isna(current_short_ma) or pd.isna(current_long_ma) or 
                pd.isna(prev_short_ma) or pd.isna(prev_long_ma)):
                log.debug(f"NaN values in MA calculation for {symbol}")
                return null_signal
                
            # Build metrics
            metrics = {
                "latest_close": float(df_with_ma['close'].iloc[-1]),
                "current_short_ma": float(current_short_ma),
                "current_long_ma": float(current_long_ma),
                "prev_short_ma": float(prev_short_ma),
                "prev_long_ma": float(prev_long_ma)
            }
            
            # Get the current price for signal generation
            current_price = float(df_with_ma['close'].iloc[-1])
            
            # Determine signal based on crossovers
            signal = {}
            
            if prev_short_ma <= prev_long_ma and current_short_ma > current_long_ma:
                # Golden Cross - Buy Signal
                signal = {
                    "action": "buy",
                    "price": current_price,
                    "stop_loss": current_price * 0.95,  # 5% stop loss
                    "reason": "Golden Cross (Short MA crossed above Long MA)",
                    "metrics": metrics
                }
            elif prev_short_ma >= prev_long_ma and current_short_ma < current_long_ma:
                # Death Cross - Sell Signal
                signal = {
                    "action": "sell",
                    "price": current_price,
                    "reason": "Death Cross (Short MA crossed below Long MA)",
                    "metrics": metrics
                }
            else:
                # No crossover - No signal
                signal = {
                    "action": None,
                    "metrics": metrics,
                    "reason": "No crossover detected"
                }
                
            # Log analysis results if we have an actionable signal
            if signal["action"]:
                await self.log_analysis(symbol, data, signal)
            
            return signal
            
        except Exception as e:
            log.error(f"Error in MA crossover analysis for {symbol}: {e}")
            return null_signal 