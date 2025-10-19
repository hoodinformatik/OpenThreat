"""
Centralized logging configuration for OpenThreat.

This module provides consistent logging across all backend services.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
) -> None:
    """
    Configure logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        format_string: Optional custom format string
    """
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )

    # Create formatter
    formatter = logging.Formatter(format_string)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Silence noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Production-ready logging configuration
class LogConfig:
    """Logging configuration for production."""

    LEVEL = "INFO"
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Sensitive data patterns to filter
    SENSITIVE_PATTERNS = [
        r"password",
        r"api[_-]?key",
        r"secret",
        r"token",
        r"auth",
    ]

    @staticmethod
    def filter_sensitive_data(message: str) -> str:
        """
        Filter sensitive data from log messages.

        Args:
            message: Log message

        Returns:
            Filtered message
        """
        import re

        for pattern in LogConfig.SENSITIVE_PATTERNS:
            message = re.sub(
                f"{pattern}[\"']?\\s*[:=]\\s*[\"']?([^\\s\"']+)",
                f"{pattern}=***REDACTED***",
                message,
                flags=re.IGNORECASE,
            )

        return message


class SensitiveDataFilter(logging.Filter):
    """Filter to remove sensitive data from logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record to remove sensitive data.

        Args:
            record: Log record

        Returns:
            True to keep the record
        """
        record.msg = LogConfig.filter_sensitive_data(str(record.msg))
        return True
