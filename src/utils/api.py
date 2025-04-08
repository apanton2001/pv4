"""
Prometheus Trading Bot - API Utilities

Handles Alpaca API connections with retry mechanism and error handling
"""

import os
import time
from typing import Any, Callable, Dict, Optional, TypeVar, Union

import alpaca_trade_api as tradeapi
from dotenv import load_dotenv

from src.utils import logging as log

# Type variable for generic function return
T = TypeVar('T')

# Default retry settings
MAX_RETRIES = 3  # Max retries for API calls
RETRY_DELAY_BASE = 2  # Base for exponential backoff (2^retry_count seconds)

class AlpacaClient:
    """
    Wrapper around the Alpaca API client with enhanced error handling and retry logic
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        max_retries: int = MAX_RETRIES,
        retry_delay_base: int = RETRY_DELAY_BASE
    ):
        """
        Initialize the Alpaca API client
        
        Args:
            api_key: Alpaca API key (defaults to ALPACA_KEY environment variable if None)
            api_secret: Alpaca API secret (defaults to ALPACA_SECRET environment variable if None)
            base_url: Alpaca API base URL (defaults to paper trading URL if None)
            max_retries: Maximum number of retries for API calls
            retry_delay_base: Base for exponential backoff
        """
        # Load environment variables if not already loaded
        load_dotenv()
        
        # Use provided credentials or get from environment
        self.api_key = api_key or os.getenv('ALPACA_KEY')
        self.api_secret = api_secret or os.getenv('ALPACA_SECRET')
        self.base_url = base_url or 'https://paper-api.alpaca.markets'
        
        if not self.api_key or not self.api_secret:
            raise ValueError("API key and secret must be provided or set as environment variables")
        
        self.max_retries = max_retries
        self.retry_delay_base = retry_delay_base
        
        # Initialize API client
        self.api = tradeapi.REST(
            key_id=self.api_key, 
            secret_key=self.api_secret, 
            base_url=self.base_url
        )
        
        log.info(f"Alpaca API client initialized with base URL: {self.base_url}")
    
    def retry_api_call(self, func: Callable[[], T], max_retries: Optional[int] = None) -> Optional[T]:
        """
        Retry an API call with exponential backoff
        
        Args:
            func: Function to call
            max_retries: Maximum number of retries (defaults to self.max_retries)
            
        Returns:
            Result of the function call or None if all retries failed
        """
        max_retries = max_retries or self.max_retries
        
        for retry_count in range(max_retries):
            try:
                return func()
            except Exception as e:
                log.warning(f"API call failed (attempt {retry_count+1}/{max_retries}): {e}")
                
                if retry_count == max_retries - 1:
                    log.error(f"API call failed after {max_retries} retries")
                    log.error_event("api_call_failed", {
                        "error": str(e),
                        "retries": max_retries
                    })
                    return None
                
                # Exponential backoff
                wait_time = self.retry_delay_base ** retry_count
                log.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        return None
    
    def verify_connection(self) -> bool:
        """
        Verify the connection to Alpaca API by checking account
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            account = self.retry_api_call(lambda: self.api.get_account())
            if account:
                log.info(f"Alpaca connection verified. Account status: {account.status}")
                log.info_event("connection_success", {
                    "account_status": account.status,
                    "buying_power": float(account.buying_power)
                })
                return True
            else:
                log.error("Failed to verify Alpaca connection")
                return False
        except Exception as e:
            log.error(f"Error verifying Alpaca connection: {e}")
            log.error_event("connection_failure", {"error": str(e)})
            return False
    
    def get_bars(
        self,
        symbol: str,
        timeframe: str = '1H',
        limit: int = 100,
        feed: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Get historical price bars with retry logic
        
        Args:
            symbol: Stock symbol
            timeframe: Bar timeframe (e.g. 1D, 1H, 15Min)
            limit: Maximum number of bars to retrieve
            feed: Data feed to use (None=default, 'sip', 'iex')
            **kwargs: Additional arguments to pass to get_bars
            
        Returns:
            DataFrame with bars or None if failed
        """
        params = {'limit': limit, 'timeframe': timeframe, **kwargs}
        if feed:
            params['feed'] = feed
            
        log.debug(f"Getting {limit} {timeframe} bars for {symbol} using feed: {feed or 'default'}")
        
        result = self.retry_api_call(lambda: self.api.get_bars(symbol, **params).df)
        
        if result is not None and not result.empty:
            log.info(f"Got {len(result)} {timeframe} bars for {symbol}")
            return result
        else:
            log.warning(f"No bars returned for {symbol}")
            return None
    
    def submit_order(
        self,
        symbol: str,
        qty: Union[int, float],
        side: str,
        order_type: str = 'market',
        time_in_force: str = 'day',
        **kwargs
    ) -> Optional[Any]:
        """
        Submit an order with retry logic
        
        Args:
            symbol: Stock symbol
            qty: Order quantity
            side: Order side ('buy' or 'sell')
            order_type: Order type ('market', 'limit', etc.)
            time_in_force: Time in force ('day', 'gtc', etc.)
            **kwargs: Additional arguments to pass to submit_order
            
        Returns:
            Order object or None if failed
        """
        if side not in ['buy', 'sell']:
            log.error(f"Invalid order side: {side}")
            return None
            
        if qty <= 0:
            log.warning(f"Invalid order quantity: {qty}")
            return None
            
        log.info(f"Submitting {side} order for {qty} shares of {symbol}")
        log.info_event("order_attempt", {
            "symbol": symbol,
            "quantity": qty,
            "side": side,
            "type": order_type,
            "time_in_force": time_in_force,
        })
        
        order = self.retry_api_call(lambda: self.api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=order_type,
            time_in_force=time_in_force,
            **kwargs
        ))
        
        if order:
            log.info(f"Order submitted: ID={order.id}, Symbol={symbol}, Qty={qty}, Side={side}")
            log.info_event("order_submitted", {
                "order_id": order.id,
                "symbol": symbol,
                "quantity": qty,
                "side": side,
                "status": order.status
            })
        else:
            log.error(f"Failed to submit {side} order for {symbol}")
            log.error_event("order_submission_failed", {
                "symbol": symbol,
                "quantity": qty,
                "side": side
            })
            
        return order
    
    def get_position(self, symbol: str) -> Optional[Any]:
        """
        Get position for a symbol with retry logic
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Position object or None if no position or failed
        """
        try:
            position = self.retry_api_call(lambda: self.api.get_position(symbol))
            if position:
                log.info(f"Found position: {position.qty} shares of {symbol}")
                return position
        except tradeapi.rest.APIError as e:
            if e.status_code == 404:  # No position found
                log.info(f"No position found for {symbol}")
                return None
            else:
                log.error(f"Error getting position for {symbol}: {e}")
                log.error_event("position_error", {
                    "symbol": symbol,
                    "error": str(e),
                    "status_code": e.status_code
                })
        except Exception as e:
            log.error(f"Error getting position for {symbol}: {e}")
            log.error_event("position_error", {
                "symbol": symbol,
                "error": str(e)
            })
            
        return None
    
    def get_account(self) -> Optional[Any]:
        """
        Get account information with retry logic
        
        Returns:
            Account object or None if failed
        """
        return self.retry_api_call(lambda: self.api.get_account())

# Convenience function to create a client
def create_client(
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    base_url: Optional[str] = None,
    max_retries: int = MAX_RETRIES,
    verify: bool = True
) -> Optional[AlpacaClient]:
    """
    Create and verify an Alpaca API client
    
    Args:
        api_key: Alpaca API key
        api_secret: Alpaca API secret
        base_url: Alpaca API base URL
        max_retries: Maximum number of retries for API calls
        verify: Whether to verify the connection
        
    Returns:
        AlpacaClient instance or None if verification failed and verify=True
    """
    try:
        client = AlpacaClient(
            api_key=api_key,
            api_secret=api_secret,
            base_url=base_url,
            max_retries=max_retries
        )
        
        if verify and not client.verify_connection():
            log.error("Failed to verify Alpaca connection")
            return None
            
        return client
    except Exception as e:
        log.error(f"Error creating Alpaca client: {e}")
        log.error_event("client_creation_failed", {"error": str(e)})
        return None 