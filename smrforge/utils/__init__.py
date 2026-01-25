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


# Keep `smrforge.utils` on the parent package consistent with `sys.modules`.
# Some test suites delete/reload modules and then call `importlib.reload(smrforge.utils)`,
# which requires that `smrforge.utils` refers to the exact module object stored in
# `sys.modules["smrforge.utils"]`.
import sys as _sys  # noqa: E402

_parent_pkg = _sys.modules.get("smrforge")

# Also ensure our own entry is present and canonical. Some test suites delete
# `sys.modules["smrforge.utils"]` without clearing the attribute on `smrforge`,
# which can cause `importlib.reload(smrforge.utils)` to fail if it holds a stale
# module object.
_sys.modules["smrforge.utils"] = _sys.modules[__name__]

# Avoid leaving a potentially stale cached attribute on the parent package.
# Access should go through `smrforge.__getattr__("utils")`, which always returns
# the canonical module from `sys.modules`.
if _parent_pkg is not None:
    try:
        delattr(_parent_pkg, "utils")
    except Exception:
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