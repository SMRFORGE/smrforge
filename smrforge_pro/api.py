"""
Pro API stability helpers: deprecated, deprecation_message, check_api_stability for CI.
"""

import functools
import inspect
import warnings
from typing import Any, Callable, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def deprecated(
    message: str = "",
    since: str = "",
    remove_in: str = "",
) -> Callable[[F], F]:
    """
    Mark a function or method as deprecated.

    Args:
        message: Custom deprecation message
        since: Version when deprecated (e.g. "0.2.0")
        remove_in: Version when it will be removed (e.g. "0.4.0")

    Returns:
        Decorated function that warns on use.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            msg = deprecation_message(func.__qualname__, message=message, since=since, remove_in=remove_in)
            warnings.warn(msg, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


def deprecation_message(
    name: str,
    message: str = "",
    since: str = "",
    remove_in: str = "",
) -> str:
    """
    Build a deprecation message for API stability documentation.

    Args:
        name: Function/class name
        message: Custom text
        since: Version when deprecated
        remove_in: Version when removal planned

    Returns:
        Formatted deprecation string.
    """
    parts = [f"{name} is deprecated"]
    if since:
        parts.append(f"(since {since})")
    if remove_in:
        parts.append(f"and will be removed in {remove_in}")
    base = " ".join(parts) + "."
    if message:
        base += " " + message
    return base


def check_api_stability(
    module_name: str,
    public_symbols: Optional[list[str]] = None,
    deprecated_symbols: Optional[dict[str, str]] = None,
) -> tuple[int, list[str]]:
    """
    Check API stability: no new removals of public symbols without deprecation.

    For CI: fails if deprecated symbols are still in use without proper notice,
    or if public API changed unexpectedly.

    Args:
        module_name: Module to check (e.g. "smrforge_pro.api")
        public_symbols: Expected public __all__ (optional; derived from module if None)
        deprecated_symbols: Dict of symbol -> deprecation message (optional)

    Returns:
        (exit_code, list of issue messages). 0 = pass, 1 = fail.
    """
    issues: list[str] = []
    try:
        import importlib

        mod = importlib.import_module(module_name)
    except ImportError as e:
        return 1, [f"Cannot import {module_name}: {e}"]

    all_members = getattr(mod, "__all__", None)
    if public_symbols is not None and all_members is not None:
        missing = set(public_symbols) - set(all_members)
        extra = set(all_members) - set(public_symbols)
        if missing:
            issues.append(f"Public symbols missing from __all__: {missing}")
        if extra and public_symbols:
            issues.append(f"Unexpected symbols in __all__: {extra}")

    if deprecated_symbols:
        for sym, msg in deprecated_symbols.items():
            if hasattr(mod, sym):
                obj = getattr(mod, sym)
                if not (
                    (callable(obj) and getattr(obj, "__doc__", "").find("deprecated") >= 0)
                    or "deprecated" in (getattr(obj, "__doc__", "") or "").lower()
                ):
                    issues.append(f"{sym}: {msg}")

    return (1 if issues else 0, issues)
