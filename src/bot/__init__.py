"""
Prometheus Trading Bot - Bot Package

Core trading bot functionality and strategy interfaces
"""

from src.bot.strategy import Strategy, MAStrategy
from src.bot.trader import TradingBot, run_bot, main

__all__ = ["Strategy", "MAStrategy", "TradingBot", "run_bot", "main"]
