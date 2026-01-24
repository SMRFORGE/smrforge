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

# Expose units submodule as `smrforge.utils.units` for compatibility with tests/code
from . import units as units  # noqa: F401

__all__ = [
    "get_logo_path",
    "get_logo_data",
    "get_logger",
    "setup_logging",
    "log_solver_iteration",
    "log_convergence",
    "log_nuclear_data_fetch",
    "log_cache_operation",
    "units",
]

# Expose optional submodules as attributes so tests can patch them reliably,
# even when optional dependencies are missing.
parallel_batch = None
optimization_utils = None
memory_mapped = None
memory_pool = None

# Parallel batch processing (optional import)
try:
    from . import parallel_batch as parallel_batch  # noqa: F401
    from smrforge.utils.parallel_batch import batch_process, batch_solve_keff
    __all__.extend(["parallel_batch", "batch_process", "batch_solve_keff"])
except ImportError:
    pass

# Optimization utilities (optional import)
try:
    from . import optimization_utils as optimization_utils  # noqa: F401
    from smrforge.utils.optimization_utils import (
        ensure_contiguous,
        vectorized_cross_section_lookup,
        vectorized_normalize,
        batch_vectorized_operations,
        zero_copy_slice,
        smart_array_copy,
    )
    __all__.extend([
        "optimization_utils",
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
    from . import memory_mapped as memory_mapped  # noqa: F401
    from . import memory_pool as memory_pool  # noqa: F401
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
        "memory_mapped",
        "memory_pool",
        "MemoryMappedArray",
        "create_memory_mapped_cross_sections",
        "load_memory_mapped_cross_sections",
        "ParticleMemoryPool",
        "MemoryPoolManager",
    ])
except ImportError:
    pass