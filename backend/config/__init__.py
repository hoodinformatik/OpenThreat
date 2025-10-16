"""Configuration module for OpenThreat backend."""

from .logging_config import setup_logging, get_logger, LogConfig

__all__ = ["setup_logging", "get_logger", "LogConfig"]
