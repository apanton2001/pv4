"""
Prometheus Trading Bot - Data Utilities

Enhanced market data fetching with multiple feed sources and fallback mechanisms
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd

from src.utils import logging as log
from src.utils.api import AlpacaClient

class MarketDataFetcher:
    """
    Enhanced market data fetcher with multiple data sources and fallback mechanisms
    """
    
    def __init__(self, client: AlpacaClient):
        """
        Initialize the market data fetcher
        
        Args:
            client: AlpacaClient instance
        """
        self.client = client
        self.data_stats = {
            "attempts": 0,
            "successes": 0,
            "feed_successes": {"sip": 0, "default": 0, "iex": 0},
            "timeframe_successes": {},
            "last_successful_fetch": None
        }
    
    def get_bars(
        self,
        symbol: str,
        lookback_bars: int = 100,
        timeframe: str = '1H',
        min_required_bars: Optional[int] = None
    ) -> Optional[pd.DataFrame]:
        """
        Get historical price bars with enhanced fallback mechanisms
        
        This method tries multiple data feeds and implements pagination
        and timeframe fallbacks if necessary
        
        Args:
            symbol: Stock symbol
            lookback_bars: Number of bars to fetch
            timeframe: Bar timeframe (e.g. 1D, 1H, 15Min)
            min_required_bars: Minimum number of bars required (defaults to lookback_bars)
            
        Returns:
            DataFrame with historical bars or None if all attempts failed
        """
        self.data_stats["attempts"] += 1
        min_required_bars = min_required_bars or lookback_bars
        
        # Parameter setup
        params = {'limit': min(1000, lookback_bars), 'timeframe': timeframe}
        
        # Try multiple feed sources in priority order
        feeds_to_try = ['sip', None, 'iex']  # None = Alpaca's default feed
        
        for feed in feeds_to_try:
            try:
                feed_name = feed or 'default'
                
                if feed:
                    params['feed'] = feed
                elif 'feed' in params:
                    del params['feed']
                
                log.debug(f"Fetching {lookback_bars} {timeframe} bars for {symbol} using feed: {feed_name}")
                
                fetch_start = datetime.now()
                
                # Initial data fetch
                bars_df = self.client.get_bars(symbol, **params)
                
                # If we didn't get enough bars and need pagination
                if bars_df is not None and not bars_df.empty and len(bars_df) < lookback_bars:
                    log.info(f"Initial fetch returned only {len(bars_df)} bars, attempting pagination...")
                    
                    log.info_event("pagination_attempt", {
                        "symbol": symbol,
                        "initial_bars": len(bars_df),
                        "timeframe": timeframe,
                        "feed": feed_name
                    })
                    
                    # Get oldest timestamp from current data to use as end parameter
                    oldest_ts = bars_df.index.min()
                    
                    # Try pagination to get more historical data
                    pagination_params = params.copy()
                    pagination_params['end'] = oldest_ts
                    more_bars_df = self.client.get_bars(symbol, **pagination_params)
                    
                    # Combine dataframes if we got more data
                    if more_bars_df is not None and not more_bars_df.empty:
                        bars_df = pd.concat([more_bars_df, bars_df])
                        bars_df = bars_df[~bars_df.index.duplicated(keep='first')]  # Remove duplicates
                        log.info(f"Pagination successful, now have {len(bars_df)} bars")
                        
                        log.info_event("pagination_success", {
                            "symbol": symbol,
                            "additional_bars": len(more_bars_df),
                            "total_bars": len(bars_df),
                            "timeframe": timeframe,
                            "feed": feed_name
                        })
                
                # If we got data, process it
                if bars_df is not None and not bars_df.empty:
                    # Standardize index
                    bars_df = self._standardize_dataframe(bars_df, symbol)
                    
                    if bars_df is None:
                        continue  # Try next feed if standardization failed
                    
                    # Check if we have enough data
                    if len(bars_df) >= min_required_bars:
                        fetch_time = (datetime.now() - fetch_start).total_seconds()
                        log.info(f"Fetched {len(bars_df)} {timeframe} bars for {symbol} using feed: {feed_name}")
                        
                        # Update stats
                        self.data_stats["successes"] += 1
                        self.data_stats["feed_successes"][feed_name] = self.data_stats["feed_successes"].get(feed_name, 0) + 1
                        self.data_stats["timeframe_successes"][timeframe] = self.data_stats["timeframe_successes"].get(timeframe, 0) + 1
                        self.data_stats["last_successful_fetch"] = datetime.now().isoformat()
                        
                        log.info_event("data_fetch_success", {
                            "symbol": symbol,
                            "bar_count": len(bars_df),
                            "timeframe": timeframe,
                            "feed": feed_name,
                            "fetch_time_seconds": fetch_time,
                            "date_range": {
                                "start": bars_df.index.min().isoformat(),
                                "end": bars_df.index.max().isoformat()
                            }
                        })
                        
                        return bars_df
                    else:
                        log.warning(f"Feed {feed_name} returned only {len(bars_df)} bars (need {min_required_bars}), trying next feed...")
                        
                        log.warning_event("insufficient_data", {
                            "symbol": symbol,
                            "bar_count": len(bars_df),
                            "needed_bars": min_required_bars,
                            "timeframe": timeframe,
                            "feed": feed_name
                        })
            except Exception as e:
                log.error(f"Error fetching {timeframe} bars for {symbol} using feed {feed or 'default'}: {str(e)}")
                log.error_event("data_fetch_error", {
                    "symbol": symbol,
                    "feed": feed or 'default',
                    "timeframe": timeframe,
                    "error": str(e)
                })
        
        # Fallback to different timeframe if all feeds failed
        return self._try_timeframe_fallbacks(symbol, lookback_bars, timeframe, min_required_bars)
    
    def _standardize_dataframe(self, df: pd.DataFrame, symbol: str) -> Optional[pd.DataFrame]:
        """
        Standardize DataFrame indices, columns, and types
        
        Args:
            df: DataFrame to standardize
            symbol: Symbol for error messages
            
        Returns:
            Standardized DataFrame or None if failed
        """
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        
        try:
            # Standardize index
            if isinstance(df.index, pd.DatetimeIndex):
                if df.index.tz is None:
                    df.index = df.index.tz_localize('UTC')
                else:
                    df.index = df.index.tz_convert('UTC')
            else:
                df = df.reset_index()
                ts_col = 'timestamp' if 'timestamp' in df.columns else ('index' if 'index' in df.columns else None)
                if ts_col:
                    df.rename(columns={ts_col: 'timestamp'}, inplace=True)
                    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
                    df = df.set_index('timestamp')
                else:
                    log.error(f"Cannot find timestamp column for {symbol}")
                    return None
            
            df = df.sort_index()
            
            # Check required columns
            if not all(col in df.columns for col in required_cols):
                log.error(f"Missing required columns for {symbol}")
                return None
            
            # Select and convert required columns
            return df[required_cols].astype(float)
        except Exception as e:
            log.error(f"Error standardizing DataFrame for {symbol}: {e}")
            return None
    
    def _try_timeframe_fallbacks(
        self,
        symbol: str,
        lookback_bars: int,
        timeframe: str,
        min_required_bars: int
    ) -> Optional[pd.DataFrame]:
        """
        Try fallback timeframes when the primary timeframe fails
        
        Args:
            symbol: Stock symbol
            lookback_bars: Number of bars to fetch
            timeframe: Original timeframe that failed
            min_required_bars: Minimum number of bars required
            
        Returns:
            DataFrame with historical bars or None if all fallbacks failed
        """
        # Define fallback paths
        fallbacks = {
            '1Min': ['2Min', '5Min', '15Min', '1H', '1D'],
            '2Min': ['5Min', '15Min', '1H', '1D'],
            '5Min': ['15Min', '1H', '1D'],
            '15Min': ['30Min', '1H', '1D'],
            '30Min': ['1H', '1D'],
            '1H': ['1D'],
            '1D': []  # No fallback for daily
        }
        
        # Get fallback options for the current timeframe
        fallback_options = fallbacks.get(timeframe, [])
        
        if not fallback_options:
            # For daily timeframe, try with fewer bars as last resort
            if timeframe == '1D' and lookback_bars > 100:
                reduced_lookback = min(100, min_required_bars)
                log.warning(f"Could not get enough daily bars, reducing request size to {reduced_lookback}...")
                
                log.warning_event("request_size_reduction", {
                    "symbol": symbol,
                    "from_size": lookback_bars,
                    "to_size": reduced_lookback
                })
                
                return self.get_bars(
                    symbol, 
                    lookback_bars=reduced_lookback, 
                    timeframe=timeframe, 
                    min_required_bars=min_required_bars
                )
        else:
            # Try the next timeframe in the fallback sequence
            next_timeframe = fallback_options[0]
            log.warning(f"Could not get enough {timeframe} bars, falling back to {next_timeframe}...")
            
            log.warning_event("timeframe_fallback", {
                "symbol": symbol,
                "from_timeframe": timeframe,
                "to_timeframe": next_timeframe
            })
            
            return self.get_bars(
                symbol, 
                lookback_bars=lookback_bars, 
                timeframe=next_timeframe,
                min_required_bars=min_required_bars
            )
        
        # If we get here, all fallbacks failed
        log.error(f"Failed to fetch sufficient data for {symbol} across all feeds and fallbacks")
        log.error_event("data_fetch_complete_failure", {
            "symbol": symbol,
            "attempts": self.data_stats["attempts"],
            "success_rate": self.data_stats["successes"] / self.data_stats["attempts"] if self.data_stats["attempts"] > 0 else 0
        })
        
        return None
    
    def test_data_feeds(
        self, 
        symbol: str,
        timeframes: Optional[List[str]] = None,
        lookback_bars: int = 100
    ) -> Dict:
        """
        Test different data feeds and timeframes to find the most reliable combination
        
        Args:
            symbol: Stock symbol to test
            timeframes: List of timeframes to test (defaults to ['1D', '1H', '15Min'])
            lookback_bars: Number of bars to request
            
        Returns:
            Dictionary with test results
        """
        log.info(f"=== Data Feed Diagnostic Test for {symbol} ===")
        log.info_event("diagnostic_test_start", {"symbol": symbol})
        
        timeframes = timeframes or ['1D', '1H', '15Min']
        feeds = ['sip', None, 'iex']
        
        results = {
            "feed_results": {},
            "timeframe_results": {},
            "best_combination": None,
            "highest_bar_count": 0
        }
        
        for tf in timeframes:
            if tf not in results["timeframe_results"]:
                results["timeframe_results"][tf] = {"success": False, "max_bars": 0}
                
            for feed in feeds:
                feed_name = feed or "default"
                if feed_name not in results["feed_results"]:
                    results["feed_results"][feed_name] = {"success": False, "max_bars": 0}
                
                try:
                    params = {'limit': lookback_bars, 'timeframe': tf}
                    if feed:
                        params['feed'] = feed
                    
                    log.info(f"Testing {tf} bars with feed: {feed_name}")
                    bars_df = self.client.get_bars(symbol, **params)
                    
                    if bars_df is not None and not bars_df.empty:
                        bar_count = len(bars_df)
                        log.info(f"SUCCESS: Got {bar_count} {tf} bars using {feed_name} feed")
                        
                        # Update results tracking
                        results["feed_results"][feed_name]["success"] = True
                        results["feed_results"][feed_name]["max_bars"] = max(
                            results["feed_results"][feed_name]["max_bars"], 
                            bar_count
                        )
                        
                        results["timeframe_results"][tf]["success"] = True
                        results["timeframe_results"][tf]["max_bars"] = max(
                            results["timeframe_results"][tf]["max_bars"], 
                            bar_count
                        )
                        
                        # Check if this is the best combination so far
                        if bar_count > results["highest_bar_count"]:
                            results["highest_bar_count"] = bar_count
                            results["best_combination"] = {"feed": feed_name, "timeframe": tf}
                    else:
                        log.error(f"❌ No data returned for {tf} with {feed_name} feed")
                except Exception as e:
                    log.error(f"❌ Error testing {tf} with {feed_name} feed: {str(e)}")
        
        # Test the enhanced get_bars method
        log.info("Testing enhanced get_bars method:")
        bars = self.get_bars(symbol, lookback_bars=lookback_bars)
        if bars is not None and not bars.empty:
            log.info(f"✅ Enhanced method returned {len(bars)} bars")
            log.info(f"Date range: {bars.index.min()} to {bars.index.max()}")
            
            results["enhanced_method"] = {
                "success": True,
                "bar_count": len(bars),
                "date_range": {
                    "start": bars.index.min().isoformat(),
                    "end": bars.index.max().isoformat()
                }
            }
        else:
            log.error("❌ Enhanced method failed to return data")
            results["enhanced_method"] = {"success": False}
        
        # Log summary of best options
        if results["best_combination"]:
            best_feed = results["best_combination"]["feed"]
            best_tf = results["best_combination"]["timeframe"]
            best_count = results["highest_bar_count"]
            
            log.info(f"RECOMMENDATION: Use {best_feed} feed with {best_tf} timeframe ({best_count} bars)")
        else:
            log.critical("No successful data fetch combinations found!")
        
        log.info_event("diagnostic_test_results", results)
        log.info("=== End of Diagnostic Test ===")
        
        return results 