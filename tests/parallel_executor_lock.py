"""
Global lock for limiting concurrent ThreadPoolExecutor/ProcessPoolExecutor creation.

This prevents resource contention when many tests run together.
On Windows, we limit to 1 concurrent executor to avoid thread limits.
"""
import threading
import sys

# Limit to 1 concurrent executor on Windows (more restrictive to avoid hangs)
# On other platforms, allow 2 concurrent executors
_max_concurrent = 1 if sys.platform == 'win32' else 2
_executor_semaphore = threading.Semaphore(_max_concurrent)


def get_executor_lock():
    """Get the global executor semaphore for limiting concurrent executors."""
    return _executor_semaphore
