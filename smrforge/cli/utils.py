"""
SMRForge CLI utilities.

Shared helpers for print styling, JSON conversion, heat source parsing, etc.
"""

import ast
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np

try:
    import yaml

    _YAML_AVAILABLE = True
except ImportError:  # pragma: no cover
    _YAML_AVAILABLE = False  # pragma: no cover
    yaml = None  # type: ignore

# Rich library for better UX (progress bars, colored output, tables)
try:
    from rich import print as rprint
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
    )
    from rich.table import Table

    _RICH_AVAILABLE = True
except ImportError:  # pragma: no cover
    _RICH_AVAILABLE = False  # pragma: no cover
    # Fallback to basic print
    rprint = print  # pragma: no cover

console = Console() if _RICH_AVAILABLE else None

# Re-export for command modules that need them
__all__ = [
    "_GLYPH_ERROR",
    "_GLYPH_INFO",
    "_GLYPH_SUCCESS",
    "_GLYPH_WARNING",
    "_RICH_AVAILABLE",
    "_YAML_AVAILABLE",
    "_parse_heat_source_safe",
    "_print_error",
    "_print_info",
    "_print_success",
    "_print_warning",
    "_save_workflow_plot",
    "_supports_unicode",
    "_to_jsonable",
    "console",
    "rprint",
    "yaml",
    "Panel",
    "Table",
]


def _parse_heat_source_safe(heat_source_str: str):
    """
    Parse heat_source config safely (no eval of arbitrary code).
    Supports: constant (e.g. 1e6), or lambda t: <constant>.
    """
    s = heat_source_str.strip()
    # Constant: "1e6", "0.0" -> lambda t: 1e6
    try:
        val = ast.literal_eval(s)
        if isinstance(val, (int, float)):
            return lambda t: float(val)
    except (ValueError, SyntaxError):
        pass
    # lambda t: <literal>
    m = re.match(r"lambda\s+t\s*:\s*(.+)", s, re.DOTALL)
    if m:
        try:
            val = ast.literal_eval(m.group(1).strip())
            if isinstance(val, (int, float)):
                return lambda t: float(val)
        except (ValueError, SyntaxError):
            pass
    raise ValueError(
        f"Unsafe or unsupported heat_source: {heat_source_str!r}. "
        "Use a constant (e.g. 1e6) or lambda t: <constant>."
    )


def _supports_unicode(text: str) -> bool:
    """Best-effort check whether the active output encoding supports `text`."""
    stream = None
    if _RICH_AVAILABLE and console is not None:
        stream = getattr(console, "file", None)
    if stream is None:
        stream = sys.stdout  # pragma: no cover
    encoding = getattr(stream, "encoding", None) or "utf-8"
    try:
        text.encode(encoding)
        return True
    except Exception:  # pragma: no cover
        return False  # pragma: no cover


_GLYPH_SUCCESS = "✓" if _supports_unicode("✓") else "OK"
_GLYPH_ERROR = "✗" if _supports_unicode("✗") else "X"
_GLYPH_INFO = "ℹ" if _supports_unicode("ℹ") else "i"
_GLYPH_WARNING = "⚠" if _supports_unicode("⚠") else "!"


def _to_jsonable(obj: Any) -> Any:
    """Convert common non-JSON types (e.g., numpy arrays) into JSON-safe values."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, set):
        return [_to_jsonable(v) for v in sorted(obj, key=str)]
    return obj


def _save_workflow_plot(fig: Any, path: Path) -> None:
    """Save workflow plot (Plotly figure or matplotlib (fig, ax)) to path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(fig, tuple) and len(fig) == 2:
        fig, ax = fig
        fmt = path.suffix.lower().lstrip(".")
        fig.savefig(str(path), format=fmt or "png", dpi=150, bbox_inches="tight")
    elif hasattr(fig, "write_html"):
        if path.suffix.lower() == ".html":
            fig.write_html(str(path))
        else:
            try:
                fig.write_image(str(path))
            except Exception:
                fig.write_html(str(path.with_suffix(".html")))
    else:
        raise ValueError("Unsupported figure type for save")


def _print_success(message: str):
    """Print success message with styling if rich is available."""
    if _RICH_AVAILABLE:
        try:
            console.print(f"[bold green]{_GLYPH_SUCCESS}[/bold green] {message}")
        except UnicodeEncodeError:  # pragma: no cover
            print(f"{_GLYPH_SUCCESS} {message}")  # pragma: no cover
    else:  # pragma: no cover
        print(f"{_GLYPH_SUCCESS} {message}")


def _print_error(message: str):
    """Print error message with styling if rich is available."""
    if _RICH_AVAILABLE:
        try:
            console.print(f"[bold red]{_GLYPH_ERROR}[/bold red] {message}")
        except UnicodeEncodeError:  # pragma: no cover
            print(f"{_GLYPH_ERROR} {message}")  # pragma: no cover
    else:  # pragma: no cover
        print(f"{_GLYPH_ERROR} {message}")


def _print_info(message: str):
    """Print info message with styling if rich is available."""
    if _RICH_AVAILABLE:
        try:
            console.print(f"[blue]{_GLYPH_INFO}[/blue] {message}")
        except UnicodeEncodeError:  # pragma: no cover
            print(f"{_GLYPH_INFO} {message}")  # pragma: no cover
    else:  # pragma: no cover
        print(f"{_GLYPH_INFO} {message}")


def _print_warning(message: str):
    """Print warning message with styling if rich is available."""
    if _RICH_AVAILABLE:
        try:
            console.print(f"[bold yellow]{_GLYPH_WARNING}[/bold yellow] {message}")
        except UnicodeEncodeError:  # pragma: no cover
            print(f"{_GLYPH_WARNING} {message}")  # pragma: no cover
    else:  # pragma: no cover
        print(f"{_GLYPH_WARNING} {message}")
