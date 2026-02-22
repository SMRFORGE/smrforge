"""
Plugin and hook registry for SMRForge extensibility.

Enables AI/ML surrogates, external solvers, and post-processors to plug in
without modifying core code. Supports NQA-1 path and AI future-proofing.

Usage:
    >>> from smrforge.workflows.plugin_registry import register_surrogate, get_surrogate
    >>> register_surrogate("my_ml_model", my_factory)
    >>> surrogate = get_surrogate("my_ml_model")(X, y)
"""

from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from ..utils.logging import get_logger

logger = get_logger("smrforge.workflows.plugin_registry")

T = TypeVar("T")

# --- Surrogate registry ---
# Maps name -> factory(X, y, **kwargs) or path loader
_SURROGATE_REGISTRY: Dict[str, Any] = {}

# --- Hook registry ---
# Maps hook_name -> list of callables(上下文) to run before/after key operations
_HOOK_REGISTRY: Dict[str, list] = {}


def register_surrogate(
    name: str,
    factory: Union[Callable[..., Any], str, Path],
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Register a surrogate model factory or path (BYOS).

    Args:
        name: Unique identifier (e.g., "rbf", "linear", "my_onnx_model").
        factory: Callable(X, y, **kwargs) returning object with .predict(X_new),
                 or Path/str to .onnx, .pt, .pkl file for lazy loading.
        metadata: Optional metadata (validity_envelope, etc.) for audit.

    Example:
        >>> register_surrogate("gp", my_gp_factory)
        >>> register_surrogate("my_model", Path("keff_predictor.onnx"))
    """
    if name in _SURROGATE_REGISTRY:
        logger.warning("Overwriting existing surrogate '%s' in registry", name)

    if isinstance(factory, (str, Path)):
        path = Path(factory)
        if not path.exists():
            raise FileNotFoundError(f"Surrogate model file not found: {path}")

        def _path_factory(X, y, param_names=None, output_name="output", **kwargs):
            from ..ai.surrogate import load_surrogate_from_path

            pnames = param_names or [f"x{i}" for i in range(X.shape[1])]
            return load_surrogate_from_path(
                path, param_names=pnames, output_name=output_name
            )

        _SURROGATE_REGISTRY[name] = (_path_factory, metadata)
    else:
        _SURROGATE_REGISTRY[name] = (factory, metadata)


def get_surrogate(name: str) -> Optional[Callable[..., Any]]:
    """Get a surrogate factory by name. Returns None if not registered."""
    entry = _SURROGATE_REGISTRY.get(name)
    if entry is None:
        return None
    factory, _ = entry if isinstance(entry, tuple) else (entry, None)
    return factory


def list_surrogates() -> list:
    """Return list of registered surrogate names."""
    return list(_SURROGATE_REGISTRY.keys())


def unregister_surrogate(name: str) -> bool:
    """Remove surrogate from registry. Returns True if it existed."""
    if name in _SURROGATE_REGISTRY:
        del _SURROGATE_REGISTRY[name]
        return True
    return False


def get_surrogate_metadata(name: str) -> Optional[Dict[str, Any]]:
    """Get metadata for a registered surrogate. Returns None if not registered."""
    entry = _SURROGATE_REGISTRY.get(name)
    if entry is None:
        return None
    _, meta = entry if isinstance(entry, tuple) else (None, None)
    return meta


# --- Hooks ---


def register_hook(hook_name: str, callback: Callable[..., None], append: bool = True) -> None:
    """
    Register a hook callback for a named event.

    Args:
        hook_name: Event name (e.g., "before_solve", "after_keff", "after_burnup").
        callback: Callable that will receive context dict and optional kwargs.
        append: If True, append to list; if False, replace.

    Example:
        >>> def log_before_solve(ctx):
        ...     logger.info("Starting solve", extra=ctx)
        >>> register_hook("before_solve", log_before_solve)
    """
    if hook_name not in _HOOK_REGISTRY or not append:
        _HOOK_REGISTRY[hook_name] = []
    if append:
        _HOOK_REGISTRY[hook_name].append(callback)


def run_hooks(hook_name: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> None:
    """Run all callbacks registered for hook_name. Swallows exceptions (logs only)."""
    ctx = dict(context) if context else {}
    ctx.update(kwargs)
    for cb in _HOOK_REGISTRY.get(hook_name, []):
        try:
            cb(ctx)
        except Exception as e:  # Hook failures must not break core flow
            logger.debug(f"Hook {hook_name} callback failed: {e}")


def clear_hooks(hook_name: Optional[str] = None) -> None:
    """Clear hooks. If hook_name is None, clears all."""
    if hook_name is None:
        _HOOK_REGISTRY.clear()
    elif hook_name in _HOOK_REGISTRY:
        del _HOOK_REGISTRY[hook_name]
