"""
Prometheus Trading Bot - Data Provider

Handles data fetching, caching, and preprocessing for trading strategies
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import pandas as pd
import numpy as np

from src.api.alpaca import AlpacaClient

class DataProvider:
    """
    Provider for market data used by trading strategies
    
    Handles fetching, caching, and preprocessing data from various sources
    """
    
    def __init__(self, client: AlpacaClient):
        """
        Initialize the data provider
        
        Args:
            client: API client for data fetching
        """
        self.client = client
        
        # Cache settings
        self.cache = {}  # Symbol -> DataFrame cache
        self.cache_timestamps = {}  # Symbol -> last update time
        self.cache_duration = timedelta(minutes=5)  # How long to keep cached data
        
        # Statistics tracking
        self.stats = {
            "requests": 0,
            "cache_hits": 0,
            "failed_requests": 0,
            "last_request_time": None
        }
    
    async def get_bars(
        self,
        symbols: List[str],
        timeframe: str = "1Min",
        limit: int = 100,
        start: Optional[str] = None,
        end: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Get historical bar data for symbols
        
        Args:
            symbols: List of symbols to get data for
            timeframe: Bar timeframe (1Min, 5Min, 15Min, 1H, 1D)
            limit: Maximum number of bars to retrieve
            start: Start time in ISO format
            end: End time in ISO format
            use_cache: Whether to use cached data if available
            
        Returns:
            Dictionary mapping symbols to DataFrames with bar data
        """
        self.stats["requests"] += 1
        self.stats["last_request_time"] = datetime.now()
        
        # Check cache first if enabled
        if use_cache:
            cache_key = f"{','.join(sorted(symbols))}_{timeframe}_{limit}"
            
            if cache_key in self.cache and self._is_cache_valid(cache_key):
                self.stats["cache_hits"] += 1
                return self.cache[cache_key]
        
        # Fetch data from API
        try:
            data = await self.client.get_bars(
                symbols=symbols,
                timeframe=timeframe,
                limit=limit,
                start=start,
                end=end
            )
            
            # Process data through cleaning pipeline for each symbol
            for symbol in data:
                if symbol in data and not data[symbol].empty:
                    data[symbol] = self._clean_and_prepare_data(data[symbol])
            
            # Cache the result if valid
            if use_cache and data:
                self.cache[cache_key] = data
                self.cache_timestamps[cache_key] = datetime.now()
            
            return data
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            print(f"Error fetching bars: {e}")
            return {}
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if cached data is still valid
        
        Args:
            cache_key: Cache key to check
            
        Returns:
            True if cache is valid, False otherwise
        """
        if cache_key not in self.cache_timestamps:
            return False
            
        age = datetime.now() - self.cache_timestamps[cache_key]
        return age < self.cache_duration
    
    def _clean_and_prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and prepare data for analysis
        
        Args:
            df: DataFrame with raw data
            
        Returns:
            DataFrame with cleaned and prepared data
        """
        if df.empty:
            return df
            
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Ensure required columns exist
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                print(f"Warning: Missing column {col} in DataFrame")
                return pd.DataFrame()  # Return empty DataFrame if missing columns
        
        # Remove rows with NaN values in required columns
        df = df.dropna(subset=required_cols)
        
        # Remove duplicate indices
        df = df[~df.index.duplicated(keep='first')]
        
        # Sort by timestamp
        df = df.sort_index()
        
        # Convert to float (in case they're objects)
        for col in ['open', 'high', 'low', 'close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert volume to int
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0).astype(np.int64)
        
        return df
    
    async def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Get the latest price for a symbol
        
        Args:
            symbol: Symbol to get price for
            
        Returns:
            Latest price or None if not available
        """
        try:
            # Get the latest 1-minute bar
            bars = await self.get_bars(
                symbols=[symbol],
                timeframe="1Min",
                limit=1
            )
            
            if symbol in bars and not bars[symbol].empty:
                return float(bars[symbol]['close'].iloc[-1])
                
            return None
            
        except Exception as e:
            print(f"Error getting latest price for {symbol}: {e}")
            return None
    
    async def get_daily_bars(
        self, 
        symbols: List[str], 
        lookback_days: int = 30
    ) -> Dict[str, pd.DataFrame]:
        """
        Get daily bars for a list of symbols
        
        Args:
            symbols: List of symbols to get data for
            lookback_days: Number of days to look back
            
        Returns:
            Dictionary mapping symbols to DataFrames with daily bar data
        """
        end = datetime.now()
        start = end - timedelta(days=lookback_days)
        
        return await self.get_bars(
            symbols=symbols,
            timeframe="1D",
            start=start.isoformat(),
            end=end.isoformat()
        )
    
    async def get_multi_timeframe_data(
        self,
        symbol: str,
        timeframes: List[str] = ["1Min", "5Min", "1H", "1D"],
        limit: int = 100
    ) -> Dict[str, pd.DataFrame]:
        """
        Get data for multiple timeframes for a single symbol
        
        Args:
            symbol: Symbol to get data for
            timeframes: List of timeframes to get data for
            limit: Number of bars to get for each timeframe
            
        Returns:
            Dictionary mapping timeframes to DataFrames
        """
        result = {}
        
        # Fetch data for each timeframe
        for tf in timeframes:
            data = await self.get_bars(
                symbols=[symbol],
                timeframe=tf,
                limit=limit
            )
            
            if symbol in data:
                result[tf] = data[symbol]
        
        return result
    
    def get_cache_stats(self) -> Dict:
        """
        Get statistics about the cache
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "cache_size": len(self.cache),
            "cache_hits": self.stats["cache_hits"],
            "requests": self.stats["requests"],
            "hit_ratio": self.stats["cache_hits"] / max(1, self.stats["requests"]),
            "failed_requests": self.stats["failed_requests"],
            "last_request_time": self.stats["last_request_time"].isoformat() if self.stats["last_request_time"] else None
        }
    
    async def clear_cache(self):
        """Clear the data cache"""
        self.cache.clear()
        self.cache_timestamps.clear()
        print("Cache cleared")
        
    async def close(self):
        """Close any open connections"""
        # No connections to close currently
        self.clear_cache()
        print("Data provider closed") 