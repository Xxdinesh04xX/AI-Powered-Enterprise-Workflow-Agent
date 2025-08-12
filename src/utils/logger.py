"""
Logging configuration and utilities for the workflow agent.

This module sets up structured logging with proper formatting,
rotation, and different log levels for various components.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from loguru import logger
from src.core.config import config

class LoggerSetup:
    """Setup and configure logging for the application."""
    
    def __init__(self):
        self.logger = logger
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure loguru logger with appropriate settings."""
        # Remove default handler
        self.logger.remove()
        
        # Console handler with colored output
        self.logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            level="INFO",
            colorize=True
        )
        
        # File handler with rotation
        log_file = Path("logs/workflow_agent.log")
        log_file.parent.mkdir(exist_ok=True)
        
        self.logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="DEBUG",
            rotation="1 day",
            retention="30 days",
            compression="zip"
        )
        
        # Error file handler
        error_log_file = Path("logs/errors.log")
        self.logger.add(
            error_log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="ERROR",
            rotation="1 week",
            retention="12 weeks"
        )
    
    def get_logger(self, name: Optional[str] = None):
        """Get a logger instance with optional name binding."""
        if name:
            return self.logger.bind(name=name)
        return self.logger

# Global logger setup
logger_setup = LoggerSetup()
app_logger = logger_setup.get_logger("workflow_agent")

def get_logger(name: str):
    """Get a named logger instance."""
    return logger_setup.get_logger(name)
