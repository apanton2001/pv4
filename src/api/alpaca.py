"""
Prometheus Trading Bot - Alpaca API Client

Handles communication with Alpaca Markets API for trading and market data
"""

import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Union

import alpaca_trade_api as tradeapi
import pandas as pd
from dotenv import load_dotenv

# Load environment variables if present
load_dotenv()

class AlpacaClient:
    """
    Client for interacting with the Alpaca Markets API
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        api_secret: Optional[str] = None, 
        paper: bool = True,
        base_url: Optional[str] = None
    ):
        """
        Initialize the Alpaca API client
        
        Args:
            api_key: Alpaca API key (falls back to ALPACA_API_KEY env var)
            api_secret: Alpaca API secret (falls back to ALPACA_API_SECRET env var)
            paper: Whether to use paper trading
            base_url: Override the API base URL
        """
        # Use provided credentials or get from environment
        self.api_key = api_key or os.getenv('ALPACA_API_KEY')
        self.api_secret = api_secret or os.getenv('ALPACA_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            raise ValueError("API key and secret must be provided or set as environment variables")
            
        # Set base URL based on paper trading flag
        if not base_url:
            if paper:
                base_url = "https://paper-api.alpaca.markets"
            else:
                base_url = "https://api.alpaca.markets"
                
        self.base_url = base_url
        self.data_url = "https://data.alpaca.markets"
        
        # Initialize API client
        self.api = tradeapi.REST(
            key_id=self.api_key,
            secret_key=self.api_secret,
            base_url=self.base_url,
            api_version='v2'
        )
        
        # Track API rate limits
        self.last_request_time = 0
        self.min_request_interval = 0.2  # 200ms minimum between requests
    
    async def _rate_limit(self):
        """Apply rate limiting to API requests"""
        now = time.time()
        elapsed = now - self.last_request_time
        
        if elapsed < self.min_request_interval:
            await time.sleep(self.min_request_interval - elapsed)
            
        self.last_request_time = time.time()
    
    async def get_account(self) -> Dict:
        """
        Get account information
        
        Returns:
            Dictionary with account details
        """
        await self._rate_limit()
        
        try:
            account = self.api.get_account()
            return {
                "id": account.id,
                "status": account.status,
                "equity": float(account.equity),
                "cash": float(account.cash),
                "buying_power": float(account.buying_power),
                "long_market_value": float(account.long_market_value),
                "short_market_value": float(account.short_market_value),
                "initial_margin": float(account.initial_margin),
                "last_equity": float(account.last_equity),
                "last_maintenance_margin": float(account.last_maintenance_margin),
                "multiplier": account.multiplier,
                "currency": account.currency
            }
        except Exception as e:
            print(f"Error getting account: {e}")
            return {}
    
    async def get_clock(self) -> Dict:
        """
        Get market clock
        
        Returns:
            Dictionary with clock details
        """
        await self._rate_limit()
        
        try:
            clock = self.api.get_clock()
            return {
                "timestamp": clock.timestamp.isoformat(),
                "is_open": clock.is_open,
                "next_open": clock.next_open.isoformat() if clock.next_open else None,
                "next_close": clock.next_close.isoformat() if clock.next_close else None
            }
        except Exception as e:
            print(f"Error getting clock: {e}")
            return {
                "is_open": False
            }
    
    async def list_positions(self) -> List[Dict]:
        """
        Get all open positions
        
        Returns:
            List of position dictionaries
        """
        await self._rate_limit()
        
        try:
            positions = self.api.list_positions()
            return [{
                "symbol": p.symbol,
                "qty": int(p.qty),
                "side": "long" if int(p.qty) > 0 else "short",
                "avg_entry_price": float(p.avg_entry_price),
                "market_value": float(p.market_value),
                "cost_basis": float(p.cost_basis),
                "unrealized_pl": float(p.unrealized_pl),
                "unrealized_plpc": float(p.unrealized_plpc),
                "current_price": float(p.current_price),
                "lastday_price": float(p.lastday_price),
                "change_today": float(p.change_today)
            } for p in positions]
        except Exception as e:
            print(f"Error listing positions: {e}")
            return []
    
    async def get_bars(
        self,
        symbols: List[str],
        timeframe: str = "1Min",
        limit: int = 100,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        Get historical bar data for multiple symbols
        
        Args:
            symbols: List of symbols to get data for
            timeframe: Bar timeframe (1Min, 5Min, 15Min, 1H, 1D)
            limit: Maximum number of bars to retrieve
            start: Start time in ISO format
            end: End time in ISO format
            
        Returns:
            Dictionary of DataFrames keyed by symbol
        """
        await self._rate_limit()
        
        try:
            # Build request parameters
            params = {
                "timeframe": timeframe,
                "limit": limit
            }
            
            if start:
                params["start"] = start
            
            if end:
                params["end"] = end
            
            # Make API request
            bars = self.api.get_bars(symbols, **params)
            
            # Process the results
            result = {}
            for symbol in symbols:
                # Filter bars for this symbol
                symbol_bars = [b for b in bars if b.symbol == symbol]
                
                if not symbol_bars:
                    continue
                
                # Convert to DataFrame
                df = pd.DataFrame([{
                    "timestamp": b.t,
                    "open": float(b.o),
                    "high": float(b.h),
                    "low": float(b.l),
                    "close": float(b.c),
                    "volume": int(b.v)
                } for b in symbol_bars])
                
                # Set timestamp as index
                if not df.empty:
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                    df = df.set_index("timestamp")
                    result[symbol] = df
            
            return result
        
        except Exception as e:
            print(f"Error getting bars: {e}")
            return {}
    
    async def create_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        type: str = "market",
        time_in_force: str = "day",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        client_order_id: Optional[str] = None,
        extended_hours: bool = False,
    ) -> Dict:
        """
        Create a new order
        
        Args:
            symbol: Symbol to trade
            qty: Order quantity
            side: Order side (buy or sell)
            type: Order type (market, limit, stop, stop_limit)
            time_in_force: Time in force (day, gtc, opg, cls, ioc, fok)
            limit_price: Limit price for limit and stop-limit orders
            stop_price: Stop price for stop and stop-limit orders
            client_order_id: Client-specified order ID
            extended_hours: Whether to allow trading during extended hours
            
        Returns:
            Dictionary with order details
        """
        await self._rate_limit()
        
        try:
            # Build parameters
            params = {
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "type": type,
                "time_in_force": time_in_force,
                "extended_hours": extended_hours
            }
            
            if limit_price and (type == "limit" or type == "stop_limit"):
                params["limit_price"] = limit_price
                
            if stop_price and (type == "stop" or type == "stop_limit"):
                params["stop_price"] = stop_price
                
            if client_order_id:
                params["client_order_id"] = client_order_id
            
            # Submit order
            order = self.api.submit_order(**params)
            
            # Convert to dictionary
            return {
                "id": order.id,
                "client_order_id": order.client_order_id,
                "symbol": order.symbol,
                "side": order.side,
                "type": order.type,
                "status": order.status,
                "filled_qty": float(order.filled_qty) if order.filled_qty else 0,
                "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else None,
                "limit_price": float(order.limit_price) if order.limit_price else None,
                "stop_price": float(order.stop_price) if order.stop_price else None,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "updated_at": order.updated_at.isoformat() if order.updated_at else None
            }
        
        except Exception as e:
            print(f"Error creating order: {e}")
            return {}
    
    async def get_orders(self, status: str = "open") -> List[Dict]:
        """
        Get orders
        
        Args:
            status: Order status (open, closed, all)
            
        Returns:
            List of order dictionaries
        """
        await self._rate_limit()
        
        try:
            orders = self.api.list_orders(status=status)
            
            return [{
                "id": o.id,
                "client_order_id": o.client_order_id,
                "symbol": o.symbol,
                "side": o.side,
                "type": o.type,
                "status": o.status,
                "filled_qty": float(o.filled_qty) if o.filled_qty else 0,
                "filled_avg_price": float(o.filled_avg_price) if o.filled_avg_price else None,
                "limit_price": float(o.limit_price) if o.limit_price else None,
                "stop_price": float(o.stop_price) if o.stop_price else None,
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "updated_at": o.updated_at.isoformat() if o.updated_at else None
            } for o in orders]
        
        except Exception as e:
            print(f"Error getting orders: {e}")
            return []
    
    async def close_position(self, symbol: str) -> Dict:
        """
        Close a position for a symbol
        
        Args:
            symbol: Symbol to close position for
            
        Returns:
            Dictionary with order details
        """
        await self._rate_limit()
        
        try:
            order = self.api.close_position(symbol)
            
            return {
                "id": order.id,
                "client_order_id": order.client_order_id,
                "symbol": order.symbol,
                "side": order.side,
                "type": order.type,
                "status": order.status,
                "filled_qty": float(order.filled_qty) if order.filled_qty else 0,
                "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else None,
                "created_at": order.created_at.isoformat() if order.created_at else None
            }
        
        except Exception as e:
            print(f"Error closing position: {e}")
            return {} 