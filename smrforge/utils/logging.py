"""
Logging configuration and utilities for SMRForge.

This module provides structured logging throughout the SMRForge package.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Create the main logger for SMRForge
_logger: Optional[logging.Logger] = None


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger for SMRForge.

    Args:
        name: Logger name. If None, returns the root SMRForge logger.
              Use 'smrforge.module' for module-specific loggers.

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger('smrforge.neutronics')
        >>> logger.info("Starting solver iteration")
    """
    if name is None:
        name = "smrforge"

    return logging.getLogger(name)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None,
    date_format: str = "%Y-%m-%d %H:%M:%S",
) -> None:
    """
    Configure logging for SMRForge.

    This function should be called once at the start of an application
    to configure logging behavior. If not called, logging defaults to
    WARNING level with console output.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If None, only console logging.
        format_string: Custom log format string. If None, uses default format.
        date_format: Format string for timestamps

    Example:
        >>> from smrforge.utils.logging import setup_logging
        >>> setup_logging(level="DEBUG", log_file=Path("smrforge.log"))
    """
    global _logger

    # Convert level string to logging constant
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Default format
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create formatter
    formatter = logging.Formatter(fmt=format_string, datefmt=date_format)

    # Get root logger
    root_logger = logging.getLogger("smrforge")
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file is not None:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Prevent propagation to root logger
    root_logger.propagate = False

    _logger = root_logger

    # Log the configuration
    root_logger.info(f"Logging configured: level={level}, file={log_file}")


def log_solver_iteration(
    iteration: int,
    k_eff: float,
    residual: float,
    logger: Optional[logging.Logger] = None,
) -> None:
    """
    Log solver iteration information.

    Args:
        iteration: Iteration number
        k_eff: Current k-effective estimate
        residual: Current residual
        logger: Logger instance. If None, uses default logger.

    Example:
        >>> log_solver_iteration(10, 1.001234, 1e-6)
    """
    if logger is None:
        logger = get_logger("smrforge.neutronics")

    logger.debug(
        f"Iteration {iteration:4d}: k_eff = {k_eff:.8f}, " f"residual = {residual:.2e}"
    )


def log_convergence(
    k_eff: float,
    iterations: int,
    residual: float,
    logger: Optional[logging.Logger] = None,
) -> None:
    """
    Log solver convergence information.

    Args:
        k_eff: Final k-effective
        iterations: Number of iterations
        residual: Final residual
        logger: Logger instance. If None, uses default logger.

    Example:
        >>> log_convergence(1.001234, 25, 5e-8)
    """
    if logger is None:
        logger = get_logger("smrforge.neutronics")

    logger.info(
        f"Solver converged: k_eff = {k_eff:.8f}, "
        f"iterations = {iterations}, residual = {residual:.2e}"
    )


def log_nuclear_data_fetch(
    nuclide: str,
    reaction: str,
    temperature: float,
    backend: str,
    logger: Optional[logging.Logger] = None,
) -> None:
    """
    Log nuclear data fetching operations.

    Args:
        nuclide: Nuclide name (e.g., "U235")
        reaction: Reaction type (e.g., "total", "fission")
        temperature: Temperature in Kelvin
        backend: Backend used (e.g., "sandy", "endf_parser")
        logger: Logger instance. If None, uses default logger.

    Example:
        >>> log_nuclear_data_fetch("U235", "fission", 1200.0, "sandy")
    """
    if logger is None:
        logger = get_logger("smrforge.core")

    logger.info(
        f"Fetching nuclear data: {nuclide}/{reaction} at {temperature}K "
        f"(backend: {backend})"
    )


def log_cache_operation(
    operation: str, key: str, logger: Optional[logging.Logger] = None
) -> None:
    """
    Log cache operations (hit, miss, write).

    Args:
        operation: Operation type ("hit", "miss", "write")
        key: Cache key
        logger: Logger instance. If None, uses default logger.

    Example:
        >>> log_cache_operation("hit", "endfb8.0/U235/total/1200.0K")
    """
    if logger is None:
        logger = get_logger("smrforge.core")

    logger.debug(f"Cache {operation}: {key}")


# Initialize with default settings on import
# Users can override by calling setup_logging()
setup_logging(level="WARNING")  # Default to WARNING to avoid noise
