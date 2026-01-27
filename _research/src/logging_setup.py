"""
Logging configuration for the Strategic Orchestrator.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Optional


# Create module logger
logger = logging.getLogger("strategic_orchestrator")

# Default format for console and file
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
LOG_FORMAT_DEBUG = "%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    verbose: bool = False,
    quiet: bool = False
) -> logging.Logger:
    """
    Configure logging for the orchestrator.

    Args:
        level: Base logging level (default INFO)
        log_file: Optional path to log file
        verbose: If True, set DEBUG level with detailed format
        quiet: If True, set WARNING level (overrides verbose)

    Returns:
        Configured logger instance
    """
    # Determine effective level
    if quiet:
        effective_level = logging.WARNING
    elif verbose:
        effective_level = logging.DEBUG
    else:
        effective_level = level

    # Choose format based on verbosity
    log_format = LOG_FORMAT_DEBUG if verbose else LOG_FORMAT

    # Configure root logger for this module
    logger.setLevel(effective_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(effective_level)
    console_handler.setFormatter(logging.Formatter(log_format, LOG_DATE_FORMAT))
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Always capture everything to file
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT_DEBUG, LOG_DATE_FORMAT))
        logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")

    return logger


# Initialize with default settings (can be reconfigured via setup_logging)
setup_logging()


class LogTimer:
    """Context manager for timing operations with logging."""

    def __init__(self, operation: str, level: int = logging.DEBUG):
        self.operation = operation
        self.level = level
        self.start_time = None
        self.elapsed = None

    def __enter__(self):
        self.start_time = time.time()
        logger.log(self.level, f"Starting: {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.time() - self.start_time
        if exc_type:
            logger.warning(f"Failed: {self.operation} ({self.elapsed:.2f}s) - {exc_val}")
        else:
            logger.log(self.level, f"Completed: {self.operation} ({self.elapsed:.2f}s)")
        return False
