"""
Exception handling utilities for safety-critical and physics code.

Use in except blocks to avoid swallowing system-level exceptions
(KeyboardInterrupt, SystemExit, MemoryError) that should propagate.
"""

from typing import Tuple, Type


# Exceptions that should NOT be caught and handled in physics code;
# they must propagate to the caller (or interpreter).
_RERAISE_TYPES: Tuple[Type[BaseException], ...] = (
    KeyboardInterrupt,
    SystemExit,
    MemoryError,
)


def reraise_if_system(exception: BaseException) -> None:
    """
    Re-raise if the exception is a system-level exception that must not be swallowed.

    Call this at the start of an except block in physics/safety-critical code
    to ensure KeyboardInterrupt, SystemExit, MemoryError, etc. propagate.

    Args:
        exception: The caught exception.

    Example:
        >>> try:
        ...     result = expensive_physics_calc()
        ... except Exception as e:
        ...     reraise_if_system(e)
        ...     logger.warning("Physics fallback: %s", e)
        ...     result = default_value
    """
    if isinstance(exception, _RERAISE_TYPES):
        raise


def is_system_exception(exception: BaseException) -> bool:
    """Return True if the exception should not be caught in physics code."""
    return isinstance(exception, _RERAISE_TYPES)
