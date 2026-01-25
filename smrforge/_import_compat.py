"""
Import/reload compatibility helpers.

These utilities centralize a few patterns used in tests that aggressively
delete/overwrite `sys.modules[...]` entries and reload packages.

They are intentionally lightweight (std-lib only) to avoid circular imports.
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Optional


def canonical_import(qualified_name: str) -> ModuleType:
    """
    Return the canonical module object for `qualified_name`.

    If `sys.modules[qualified_name]` exists, return it. Otherwise, import it.
    """
    mod = sys.modules.get(qualified_name)
    if mod is None:
        mod = importlib.import_module(qualified_name)
    return mod


def ensure_sys_modules_alias(qualified_name: str, module: ModuleType) -> None:
    """Force `sys.modules[qualified_name]` to point at `module`."""
    sys.modules[qualified_name] = module


def bind_parent_attr_from_modules(
    parent_qualified: str,
    attr: str,
    module_qualified: Optional[str] = None,
) -> None:
    """
    Ensure `sys.modules[parent_qualified].<attr>` points at the canonical module.

    Useful when other tests reload the parent package and then patch via:
    `patch.object(parent.<attr>, ...)`.
    """
    parent = sys.modules.get(parent_qualified)
    if parent is None:
        return

    module_qualified = module_qualified or f"{parent_qualified}.{attr}"
    mod = sys.modules.get(module_qualified)
    if mod is None:
        return

    try:
        setattr(parent, attr, mod)
    except Exception:
        # Best-effort only; never fail import for this.
        return


def delete_attr_if_present(parent_qualified: str, attr: str) -> None:
    """Best-effort `delattr(sys.modules[parent_qualified], attr)`."""
    parent = sys.modules.get(parent_qualified)
    if parent is None:
        return
    try:
        delattr(parent, attr)
    except Exception:
        return


def delete_global(globals_dict: dict, name: str) -> None:
    """Best-effort `del globals()[name]`."""
    if name in globals_dict:
        try:
            del globals_dict[name]
        except Exception:
            return

