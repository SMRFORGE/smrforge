"""
Utility functions and helpers

This module provides utility functions for SMRForge, including:
- Logo access functions
- Logging configuration and utilities

See FEATURE_STATUS.md for current status.
"""

from smrforge.utils.logging import (
    get_logger,
    log_cache_operation,
    log_convergence,
    log_nuclear_data_fetch,
    log_solver_iteration,
    setup_logging,
)
from smrforge.utils.logo import get_logo_data, get_logo_path

__all__ = [
    "get_logo_path",
    "get_logo_data",
    "get_logger",
    "setup_logging",
    "log_solver_iteration",
    "log_convergence",
    "log_nuclear_data_fetch",
    "log_cache_operation",
]

# Parallel batch processing (optional import)
try:
    from smrforge.utils.parallel_batch import batch_process, batch_solve_keff
    __all__.extend(["batch_process", "batch_solve_keff"])
except ImportError:
    pass