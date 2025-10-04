"""Centralized exception handling for the Finance Dashboard application."""

import logging
import traceback
from datetime import datetime
from typing import Any


class FinanceDashboardError(Exception):
    """Base exception for Finance Dashboard."""

    pass


class ConfigurationError(FinanceDashboardError):
    """Raised when configuration is invalid or missing."""

    pass


class DataSourceError(FinanceDashboardError):
    """Raised when data source operations fail."""

    pass


class ExceptionHandler:
    """Centralized exception handling utility."""

    @staticmethod
    def log_exception(
        logger: logging.Logger,
        exception: Exception,
        context: str = "",
        additional_info: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Log exception with detailed information and return error details.

        Args:
            logger: Logger instance to use
            exception: The exception that occurred
            context: Context string describing where the error occurred
            additional_info: Additional information to include in the log

        Returns:
            Dictionary containing error details

        """
        error_details = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "error_type": type(exception).__name__,
            "error_message": str(exception),
            "traceback": traceback.format_exc(),
        }

        if additional_info:
            error_details.update(additional_info)

        logger.error(f"Exception in {context}: {error_details}")
        return error_details

    @staticmethod
    def handle_repository_error(
        logger: logging.Logger,
        exception: Exception,
        source: str,
        operation: str,
        reraise: bool = False,
    ) -> None:
        """Handle repository-level errors with consistent logging.

        Args:
            logger: Logger instance
            exception: The exception that occurred
            source: Name of the data source (e.g., 'Bunq', 'DeGiro')
            operation: Operation being performed
            reraise: Whether to re-raise the exception

        """
        context = f"{source} {operation}"
        ExceptionHandler.log_exception(logger, exception, context, {"source": source, "operation": operation})

        if reraise:
            raise DataSourceError(f"{context} failed: {exception!s}") from exception

    @staticmethod
    def safe_execute(func, logger: logging.Logger, context: str, default_return=None):
        """Safely execute a function with exception handling.

        Args:
            func: Function to execute
            logger: Logger instance
            context: Context description
            default_return: Value to return if function fails

        Returns:
            Function result or default_return if exception occurs

        """
        try:
            return func()
        except Exception as e:
            ExceptionHandler.log_exception(logger, e, context)
            return default_return
