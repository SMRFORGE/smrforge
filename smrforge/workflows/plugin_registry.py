"""
Plugin and hook registry for SMRForge extensibility.

Hooks enable external solvers and post-processors to plug in without modifying core code.
Surrogate registry is Pro tier only; use SMRForge Pro for AI/surrogate features.

Usage:
    >>> from smrforge.workflows.plugin_registry import register_hook, run_hooks
    >>> register_hook("before_solve", my_callback)
    >>> run_hooks("before_solve", context={"reactor_spec": spec})
"""

from typing import Any, Callable, Dict, Optional, TypeVar

from ..utils.logging import get_logger

logger = get_logger("smrforge.workflows.plugin_registry")

T = TypeVar("T")

_MSG = (
    "Surrogate registry requires SMRForge Pro. "
    "Upgrade at https://smrforge.io or install smrforge-pro."
)

try:
    from smrforge_pro.workflows.plugin_registry import (
        get_surrogate as _get_surrogate,
        list_surrogates as _list_surrogates,
        register_surrogate as _register_surrogate,
        unregister_surrogate as _unregister_surrogate,
    )
    _PRO_AVAILABLE = True
except ImportError:
    _get_surrogate = None  # type: ignore
    _list_surrogates = None  # type: ignore
    _register_surrogate = None  # type: ignore
    _unregister_surrogate = None  # type: ignore
    _PRO_AVAILABLE = False


def register_surrogate(name: str, factory: Callable[..., Any]) -> None:
    """Pro tier only."""
    if _PRO_AVAILABLE:
        _register_surrogate(name, factory)
        return
    raise ImportError(_MSG)


def get_surrogate(name: str) -> Optional[Callable[..., Any]]:
    """Pro tier only."""
    if _PRO_AVAILABLE:
        return _get_surrogate(name)
    raise ImportError(_MSG)


def list_surrogates() -> list:
    """Pro tier only."""
    if _PRO_AVAILABLE:
        return _list_surrogates()
    raise ImportError(_MSG)


def unregister_surrogate(name: str) -> bool:
    """Pro tier only."""
    if _PRO_AVAILABLE:
        return _unregister_surrogate(name)
    raise ImportError(_MSG)


# --- Hook registry ---
# Maps hook_name -> list of callables(上下文) to run before/after key operations
_HOOK_REGISTRY: Dict[str, list] = {}


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
