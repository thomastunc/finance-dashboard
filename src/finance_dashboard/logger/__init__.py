import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


class Logger:
    """Base logger class that creates daily log files in the logs directory."""

    def __init__(self, log_file_name=None, log_level=None):
        # Parse log level from environment or use default
        if log_level is None:
            log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
            log_level = getattr(logging, log_level_str, logging.INFO)

        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Generate log file path with date if not provided
        if log_file_name is None:
            today = datetime.now().strftime("%Y-%m-%d")
            log_file_name = f"finance_dashboard_{today}.log"

        log_file_path = logs_dir / log_file_name

        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(log_level)

        # Create a timed rotating file handler for daily log files
        file_handler = TimedRotatingFileHandler(
            log_file_path,
            when="midnight",
            interval=1,
            backupCount=30,  # Keep 30 days of logs
            encoding="utf-8",
        )
        file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(log_level)

        self.log.addHandler(file_handler)

    def get_logger(self, name):
        """Get a child logger with the specified name."""
        return self.log.getChild(name)
