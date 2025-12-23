"""
Utility functions and helpers

This module provides utility functions for SMRForge, including:
- Logo access functions
- Logging configuration and utilities

See FEATURE_STATUS.md for current status.
"""

from smrforge.utils.logo import get_logo_path, get_logo_data
from smrforge.utils.logging import (
    get_logger,
    setup_logging,
    log_solver_iteration,
    log_convergence,
    log_nuclear_data_fetch,
    log_cache_operation,
)

__all__ = [
    'get_logo_path',
    'get_logo_data',
    'get_logger',
    'setup_logging',
    'log_solver_iteration',
    'log_convergence',
    'log_nuclear_data_fetch',
    'log_cache_operation',
]
