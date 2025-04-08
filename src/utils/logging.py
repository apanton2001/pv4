"""
Prometheus Trading Bot - Logging Utilities

Enhanced structured logging with JSON formatting for better analysis
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Default log format for regular logging
DEFAULT_LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

class PrometheusLogger:
    """
    Centralized logging class that manages both traditional and structured logging
    """
    
    def __init__(
        self,
        log_file: Optional[Union[str, Path]] = None,
        console: bool = True,
        log_level: int = logging.INFO,
        structured_enabled: bool = True
    ):
        """
        Initialize the logger
        
        Args:
            log_file: Path to the log file
            console: Whether to log to console
            log_level: Log level (default: INFO)
            structured_enabled: Whether to enable structured logging
        """
        self.logger = logging.getLogger("prometheus")
        self.logger.setLevel(log_level)
        self.structured_enabled = structured_enabled
        
        # Clear any existing handlers
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        # Add file handler if log_file is provided
        if log_file:
            if isinstance(log_file, str):
                log_file = Path(log_file)
                
            # Create directory if it doesn't exist
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, mode='a')
            file_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
            self.logger.addHandler(file_handler)
            
        # Add console handler if requested
        if console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
            self.logger.addHandler(console_handler)
    
    def log(self, msg: str, level: int = logging.INFO):
        """Log a message using traditional logging"""
        self.logger.log(level, msg)
    
    def structured_log(self, event_type: str, data: Dict[str, Any], level: int = logging.INFO):
        """
        Log structured data with event type for better analysis
        
        Args:
            event_type: Type of event (e.g., "order_submitted", "error", etc.)
            data: Dictionary of data to log
            level: Log level
        """
        if not self.structured_enabled:
            return
            
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        
        self.logger.log(level, json.dumps(log_entry))
    
    # Convenience methods for different log levels
    def debug(self, msg: str):
        self.log(msg, logging.DEBUG)
        
    def info(self, msg: str):
        self.log(msg, logging.INFO)
        
    def warning(self, msg: str):
        self.log(msg, logging.WARNING)
        
    def error(self, msg: str):
        self.log(msg, logging.ERROR)
        
    def critical(self, msg: str):
        self.log(msg, logging.CRITICAL)
    
    # Structured logging convenience methods
    def debug_event(self, event_type: str, data: Dict[str, Any]):
        self.structured_log(event_type, data, logging.DEBUG)
        
    def info_event(self, event_type: str, data: Dict[str, Any]):
        self.structured_log(event_type, data, logging.INFO)
        
    def warning_event(self, event_type: str, data: Dict[str, Any]):
        self.structured_log(event_type, data, logging.WARNING)
        
    def error_event(self, event_type: str, data: Dict[str, Any]):
        self.structured_log(event_type, data, logging.ERROR)
        
    def critical_event(self, event_type: str, data: Dict[str, Any]):
        self.structured_log(event_type, data, logging.CRITICAL)

# Global logger instance
_default_logger = None

def setup_logging(
    log_file: Optional[Union[str, Path]] = 'logs/prometheus.log',
    console: bool = True,
    log_level: int = logging.INFO,
    structured_enabled: bool = True
) -> PrometheusLogger:
    """
    Setup global logging configuration and return logger
    
    Args:
        log_file: Path to the log file
        console: Whether to log to console 
        log_level: Log level
        structured_enabled: Whether to enable structured logging
    
    Returns:
        PrometheusLogger instance
    """
    global _default_logger
    _default_logger = PrometheusLogger(
        log_file=log_file,
        console=console,
        log_level=log_level,
        structured_enabled=structured_enabled
    )
    return _default_logger

def get_logger() -> PrometheusLogger:
    """
    Get the global logger instance
    
    Returns:
        PrometheusLogger instance
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logging()
    return _default_logger

# Convenience functions for direct access without getting logger instance
def log(msg: str, level: int = logging.INFO):
    get_logger().log(msg, level)

def structured_log(event_type: str, data: Dict[str, Any], level: int = logging.INFO):
    get_logger().structured_log(event_type, data, level)

def debug(msg: str):
    get_logger().debug(msg)
    
def info(msg: str):
    get_logger().info(msg)
    
def warning(msg: str):
    get_logger().warning(msg)
    
def error(msg: str):
    get_logger().error(msg)
    
def critical(msg: str):
    get_logger().critical(msg)

def debug_event(event_type: str, data: Dict[str, Any]):
    get_logger().debug_event(event_type, data)
    
def info_event(event_type: str, data: Dict[str, Any]):
    get_logger().info_event(event_type, data)
    
def warning_event(event_type: str, data: Dict[str, Any]):
    get_logger().warning_event(event_type, data)
    
def error_event(event_type: str, data: Dict[str, Any]):
    get_logger().error_event(event_type, data)
    
def critical_event(event_type: str, data: Dict[str, Any]):
    get_logger().critical_event(event_type, data) 