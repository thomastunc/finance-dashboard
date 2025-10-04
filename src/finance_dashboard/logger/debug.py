"""
Logging configuration helper for debugging Bunq integration issues.
This module provides utilities to configure detailed logging for troubleshooting.
"""

import logging
import sys
from pathlib import Path

class DebugLogger:
    """Enhanced logger configuration for debugging financial integrations"""
    
    def __init__(self, log_file: str = "finance_debug.log", console_level: str = "INFO", file_level: str = "DEBUG"):
        self.log_file = log_file
        self.console_level = getattr(logging, console_level.upper())
        self.file_level = getattr(logging, file_level.upper())
        self.setup_logging()
    
    def setup_logging(self):
        """Configure detailed logging with both console and file output"""
        # Create formatter with more detail
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        console_formatter = logging.Formatter(
            '%(levelname)s - %(name)s - %(message)s'
        )
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        root_logger.handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.console_level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler(self.log_file, mode='w')
        file_handler.setLevel(self.file_level)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # Set specific loggers to DEBUG for our modules
        debug_modules = [
            'finance_dashboard.model.bank.bunq',
            'finance_dashboard.repository.bank.bunq_repository',
            'finance_dashboard.repository',
            '__main__'
        ]
        
        for module in debug_modules:
            logger = logging.getLogger(module)
            logger.setLevel(logging.DEBUG)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for the given name"""
        return logging.getLogger(name)
    
    @staticmethod
    def log_exception_details(logger: logging.Logger, exception: Exception, context: str = ""):
        """Log detailed exception information"""
        import traceback
        
        error_details = {
            'context': context,
            'error_type': type(exception).__name__,
            'error_message': str(exception),
            'traceback': traceback.format_exc()
        }
        
        logger.error(f"Exception details: {error_details}")
    
    @staticmethod
    def log_function_entry(logger: logging.Logger, function_name: str, **kwargs):
        """Log function entry with parameters"""
        params = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
        logger.debug(f"Entering {function_name}({params})")
    
    @staticmethod
    def log_function_exit(logger: logging.Logger, function_name: str, result=None):
        """Log function exit with result"""
        if result is not None:
            logger.debug(f"Exiting {function_name} with result: {result}")
        else:
            logger.debug(f"Exiting {function_name}")

# Example usage:
# debug_logger = DebugLogger()
# logger = debug_logger.get_logger(__name__)
# logger.info("This is a test message")
