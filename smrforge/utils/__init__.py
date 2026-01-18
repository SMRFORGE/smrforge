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

# Optimization utilities (optional import)
try:
    from smrforge.utils.optimization_utils import (
        ensure_contiguous,
        vectorized_cross_section_lookup,
        vectorized_normalize,
        batch_vectorized_operations,
        zero_copy_slice,
        smart_array_copy,
    )
    __all__.extend([
        "ensure_contiguous",
        "vectorized_cross_section_lookup",
        "vectorized_normalize",
        "batch_vectorized_operations",
        "zero_copy_slice",
        "smart_array_copy",
    ])
except ImportError:
    pass

# Memory management utilities (Phase 3 optimization)
try:
    from smrforge.utils.memory_mapped import (
        MemoryMappedArray,
        create_memory_mapped_cross_sections,
        load_memory_mapped_cross_sections,
    )
    from smrforge.utils.memory_pool import (
        ParticleMemoryPool,
        MemoryPoolManager,
    )
    __all__.extend([
        "MemoryMappedArray",
        "create_memory_mapped_cross_sections",
        "load_memory_mapped_cross_sections",
        "ParticleMemoryPool",
        "MemoryPoolManager",
    ])
except ImportError:
    pass