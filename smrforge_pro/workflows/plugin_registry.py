"""
Pro surrogate plugin registry.
"""

from typing import Any, Callable, Dict, Optional

_SURROGATE_REGISTRY: Dict[str, Callable[..., Any]] = {}


def register_surrogate(name: str, factory: Callable[..., Any]) -> None:
    """Register a surrogate factory (BYOS)."""
    _SURROGATE_REGISTRY[name] = factory


def get_surrogate(name: str) -> Optional[Callable[..., Any]]:
    """Get surrogate factory by name."""
    return _SURROGATE_REGISTRY.get(name)


def list_surrogates() -> list:
    """List names of registered surrogates."""
    return list(_SURROGATE_REGISTRY.keys())


def unregister_surrogate(name: str) -> bool:
    """Unregister a surrogate. Returns True if was present."""
    if name in _SURROGATE_REGISTRY:
        del _SURROGATE_REGISTRY[name]
        return True
    return False
