"""
Convenience modules for simplified APIs.

Provides high-level convenience functions for common operations,
wrapping more complex APIs for easier adoption.
"""

# Transient convenience functions (optional - requires safety module)
try:
    from smrforge.convenience.transients import (
        quick_transient,
        reactivity_insertion,
        decay_heat_removal,
    )

    _TRANSIENT_CONVENIENCE_AVAILABLE = True
except ImportError:
    _TRANSIENT_CONVENIENCE_AVAILABLE = False

__all__ = []

if _TRANSIENT_CONVENIENCE_AVAILABLE:
    __all__.extend(
        [
            "quick_transient",
            "reactivity_insertion",
            "decay_heat_removal",
        ]
    )
