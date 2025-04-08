"""
Trading Bot - Core trading engine for Prometheus

This module implements the main trading loop and execution logic
"""

import argparse
import asyncio
import logging
import signal
import sys
import time
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd

from src.api.alpaca import AlpacaClient
from src.bot.strategy import Strategy
from src.data.provider import DataProvider
from src.utils.logging import setup_logging

logger = logging.getLogger(__name__)

class TradingBot:
    """
    TradingBot is the core trading engine that manages the trading lifecycle
    including data fetching, strategy execution, and order management.
    """
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        symbols: List[str],
        strategies: List[Strategy],
        paper: bool = True,
        max_positions: int = 5,
        risk_per_trade: float = 0.02,
        time_frame: str = "1Min",
        market_hours_only: bool = True,
        cooldown_period: int = 20,
    ):
        """
        Initialize the trading bot with the specified parameters
        
        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            symbols: List of ticker symbols to trade
            strategies: List of strategy instances to apply
            paper: Whether to use paper trading
            max_positions: Maximum number of positions to hold at once
            risk_per_trade: Maximum risk per trade as percentage of portfolio
            time_frame: Timeframe for candlestick data
            market_hours_only: Whether to trade only during market hours
            cooldown_period: Period to wait between trading cycles (seconds)
        """
        setup_logging()
        self.symbols = symbols
        self.strategies = strategies
        self.max_positions = max_positions
        self.risk_per_trade = risk_per_trade
        self.time_frame = time_frame
        self.market_hours_only = market_hours_only
        self.cooldown_period = cooldown_period
        
        # Initialize the API client
        self.client = AlpacaClient(api_key, api_secret, paper)
        
        # Initialize data provider
        self.data_provider = DataProvider(self.client)
        
        # Trading state
        self.positions = {}
        self.account_info = {}
        self.is_running = False
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._handle_exit)
        signal.signal(signal.SIGTERM, self._handle_exit)
        
        logger.info(f"TradingBot initialized with {len(symbols)} symbols and {len(strategies)} strategies")
    
    async def run(self):
        """
        Main trading loop that coordinates trading activities
        and checks market status
        """
        self.is_running = True
        
        logger.info("Starting trading bot")
        
        try:
            # Initial updates
            await self._update_account_info()
            await self._update_positions()
            
            while self.is_running:
                # Check if market is open
                if self.market_hours_only:
                    is_open = await self._check_market_status()
                    if not is_open:
                        logger.info("Market is closed, waiting for 5 minutes")
                        await asyncio.sleep(300)  # Sleep for 5 minutes
                        continue
                
                # Run a complete trading cycle
                await self._trading_cycle()
                
                # Wait for cooldown period
                logger.debug(f"Waiting for {self.cooldown_period} seconds until next cycle")
                await asyncio.sleep(self.cooldown_period)
        
        except Exception as e:
            logger.error(f"Error in main trading loop: {e}", exc_info=True)
        
        finally:
            await self._cleanup()
    
    async def _trading_cycle(self):
        """
        Execute a complete trading cycle for all strategies and symbols
        """
        logger.debug("Starting trading cycle")
        
        # Update account and positions
        await self._update_account_info()
        await self._update_positions()
        
        # Calculate how many new positions we can take
        current_positions = len(self.positions)
        available_slots = max(0, self.max_positions - current_positions)
        
        if available_slots == 0:
            logger.info(f"Maximum positions reached ({self.max_positions}), skipping analysis")
            return
        
        logger.info(f"Current positions: {current_positions}, available slots: {available_slots}")
        
        # Process each symbol
        for symbol in self.symbols:
            # Skip symbols we already have positions in
            if symbol in self.positions:
                continue
            
            # Get market data for this symbol
            data = await self._fetch_data_for_symbol(symbol)
            if data is None or data.empty:
                logger.warning(f"No data available for {symbol}, skipping")
                continue
            
            # Apply each strategy
            for strategy in self.strategies:
                try:
                    # Generate signals based on data
                    signal = await strategy.analyze(symbol, data)
                    
                    # Execute signal if not None
                    if signal is not None:
                        order_id = await self._execute_signal(symbol, signal)
                        if order_id:
                            available_slots -= 1
                            if available_slots <= 0:
                                logger.info("Reached maximum positions, stopping cycle")
                                return
                
                except Exception as e:
                    logger.error(f"Error applying strategy {strategy.__class__.__name__} to {symbol}: {e}", exc_info=True)
        
        logger.debug("Trading cycle completed")
    
    async def _fetch_data_for_symbol(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Fetch market data for a specified symbol
        
        Args:
            symbol: The ticker symbol to fetch data for
            
        Returns:
            DataFrame containing market data or None if unavailable
        """
        try:
            # Fetch bars data
            data = await self.data_provider.get_bars(
                symbols=[symbol],
                timeframe=self.time_frame,
                limit=100  # Last 100 bars
            )
            
            if not data or symbol not in data:
                logger.warning(f"No data returned for {symbol}")
                return None
            
            return data[symbol]
        
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}", exc_info=True)
            return None
    
    async def _execute_signal(self, symbol: str, signal: Dict) -> Optional[str]:
        """
        Execute a trading signal based on the analysis from strategies
        
        Args:
            symbol: The ticker symbol to trade
            signal: The signal dictionary containing action and metadata
            
        Returns:
            Order ID if successful, None otherwise
        """
        action = signal.get("action")
        if action not in ["buy", "sell", "exit"]:
            logger.warning(f"Unknown action {action} for {symbol}, ignoring")
            return None
        
        try:
            if action == "buy":
                # Calculate position size based on risk
                risk_amount = float(self.account_info.get("equity", 0)) * self.risk_per_trade
                price = signal.get("price")
                stop_loss = signal.get("stop_loss")
                
                if not price or not stop_loss:
                    logger.warning(f"Missing price or stop_loss for {symbol} buy signal")
                    return None
                
                risk_per_share = abs(price - stop_loss)
                if risk_per_share <= 0:
                    logger.warning(f"Invalid risk per share for {symbol}: {risk_per_share}")
                    return None
                
                qty = int(risk_amount / risk_per_share)
                if qty <= 0:
                    logger.warning(f"Calculated quantity for {symbol} is zero or negative: {qty}")
                    return None
                
                # Place the order
                logger.info(f"Placing buy order for {qty} shares of {symbol} at market")
                order = await self.client.create_order(
                    symbol=symbol,
                    qty=qty,
                    side="buy",
                    type="market"
                )
                
                # If we have a stop loss, set it
                if stop_loss and order:
                    await self.client.create_order(
                        symbol=symbol,
                        qty=qty,
                        side="sell",
                        type="stop",
                        stop_price=stop_loss,
                        time_in_force="gtc"
                    )
                
                return order.get("id") if order else None
            
            elif action == "sell" or action == "exit":
                # Close position
                logger.info(f"Closing position for {symbol}")
                order = await self.client.close_position(symbol)
                return order.get("id") if order else None
        
        except Exception as e:
            logger.error(f"Error executing {action} signal for {symbol}: {e}", exc_info=True)
            return None
    
    async def _update_positions(self):
        """Update the current positions from Alpaca"""
        try:
            positions = await self.client.list_positions()
            self.positions = {p["symbol"]: p for p in positions}
            logger.info(f"Updated positions: {len(self.positions)} active positions")
        except Exception as e:
            logger.error(f"Error updating positions: {e}", exc_info=True)
    
    async def _update_account_info(self):
        """Update the account information from Alpaca"""
        try:
            account = await self.client.get_account()
            self.account_info = account
            logger.info(f"Updated account info: Equity=${account.get('equity', 'N/A')}")
        except Exception as e:
            logger.error(f"Error updating account info: {e}", exc_info=True)
    
    async def _check_market_status(self) -> bool:
        """
        Check if the market is currently open
        
        Returns:
            True if market is open, False otherwise
        """
        try:
            clock = await self.client.get_clock()
            is_open = clock.get("is_open", False)
            
            if is_open:
                logger.info("Market is open")
            else:
                next_open = clock.get("next_open")
                next_close = clock.get("next_close")
                logger.info(f"Market is closed. Next open: {next_open}, Next close: {next_close}")
            
            return is_open
        
        except Exception as e:
            logger.error(f"Error checking market status: {e}", exc_info=True)
            return False
    
    def _handle_exit(self, signum, frame):
        """Handle exit signals gracefully"""
        logger.info(f"Received signal {signum}, initiating shutdown")
        self.is_running = False
    
    async def _cleanup(self):
        """Clean up resources before exiting"""
        logger.info("Cleaning up resources")
        # Close data provider connections
        try:
            if hasattr(self.data_provider, 'close'):
                await self.data_provider.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)
        logger.info("Trading bot shutdown complete")


async def run_bot(args):
    """
    Run the trading bot with the given arguments
    
    Args:
        args: Command line arguments
    """
    from src.bot.strategy import MAStrategy
    
    # Create strategy instances
    strategies = [MAStrategy(short_window=20, long_window=50)]
    
    # Create and run the trading bot
    bot = TradingBot(
        api_key=args.api_key,
        api_secret=args.api_secret,
        symbols=args.symbols,
        strategies=strategies,
        paper=args.paper,
        max_positions=args.max_positions,
        risk_per_trade=args.risk_per_trade,
        time_frame=args.timeframe,
        market_hours_only=args.market_hours_only,
        cooldown_period=args.cooldown
    )
    
    await bot.run()


def main():
    """Entry point for the trading bot"""
    parser = argparse.ArgumentParser(description="Prometheus Trading Bot")
    
    parser.add_argument("--api-key", required=True, help="Alpaca API key")
    parser.add_argument("--api-secret", required=True, help="Alpaca API secret")
    parser.add_argument("--symbols", required=True, nargs="+", help="Symbols to trade")
    parser.add_argument("--paper", action="store_true", default=True, help="Use paper trading")
    parser.add_argument("--max-positions", type=int, default=5, help="Maximum positions to hold")
    parser.add_argument("--risk-per-trade", type=float, default=0.02, help="Risk per trade as fraction of portfolio")
    parser.add_argument("--timeframe", default="1Min", help="Timeframe for candlestick data")
    parser.add_argument("--market-hours-only", action="store_true", default=True, help="Trade only during market hours")
    parser.add_argument("--cooldown", type=int, default=20, help="Cooldown period between cycles (seconds)")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_bot(args))
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down")
    except Exception as e:
        logger.error(f"Error running bot: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main() 