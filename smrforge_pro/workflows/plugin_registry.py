"""
Plugin and hook registry - Pro implementation.

Provides real register_surrogate, get_surrogate, list_surrogates, unregister_surrogate.
Hooks (register_hook, run_hooks) remain in Community - use smrforge.workflows.plugin_registry.
"""

from typing import Any, Dict, Optional

# Pro: real surrogate registry
_SURROGATE_REGISTRY: Dict[str, Any] = {}


def register_surrogate(name: str, factory_or_model: Any) -> None:
    """
    Register a surrogate by name.

    Args:
        name: Unique identifier for the surrogate
        factory_or_model: Callable that returns a model with predict(), or model instance
    """
    _SURROGATE_REGISTRY[name] = factory_or_model


def register_surrogate_from_path(
    name: str,
    path: Any,
    param_names: Optional[list] = None,
    **kwargs: Any,
) -> None:
    """
    Convenience: load surrogate from path and register.

    Args:
        name: Registry name
        path: Path to .onnx, .pt, .pth, .pkl, .pickle
        param_names: Ordered parameter names for spec->features
        **kwargs: Passed to load_surrogate_from_path
    """
    from smrforge_pro.ai.surrogates import load_surrogate_from_path

    model = load_surrogate_from_path(path, param_names=param_names, **kwargs)
    register_surrogate(name, model)


def get_surrogate(name: str) -> Optional[Any]:
    """Get registered surrogate by name. Returns callable/model or None."""
    return _SURROGATE_REGISTRY.get(name)


def list_surrogates() -> list:
    """List names of registered surrogates."""
    return list(_SURROGATE_REGISTRY.keys())


def unregister_surrogate(name: str) -> bool:
    """Remove surrogate from registry. Returns True if it existed."""
    if name in _SURROGATE_REGISTRY:
        del _SURROGATE_REGISTRY[name]
        return True
    return False


__all__ = [
    "register_surrogate",
    "register_surrogate_from_path",
    "get_surrogate",
    "list_surrogates",
    "unregister_surrogate",
]
