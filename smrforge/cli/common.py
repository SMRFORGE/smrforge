"""
SMRForge CLI common utilities.

Shared imports, constants, and helper functions for the CLI package.
"""

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np

try:
    import yaml

    _YAML_AVAILABLE = True
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore
    _YAML_AVAILABLE = False  # pragma: no cover

# Rich library for better UX (progress bars, colored output, tables)
try:
    from rich import print as rprint
    from rich.console import Console
    from rich.panel import Panel  # noqa: F401
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
    rprint = print  # pragma: no cover
    Console = None  # type: ignore
    Panel = None  # type: ignore
    Table = None  # type: ignore

console = Console() if _RICH_AVAILABLE else None


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


def _load_json_or_yaml(path: Path) -> Any:
    """
    Load JSON or YAML file from path. Detects format by suffix.
    Raises if YAML requested but PyYAML not available.
    """
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        if not _YAML_AVAILABLE:
            raise ImportError("PyYAML required for YAML files. Install: pip install pyyaml")
        return yaml.safe_load(raw)
    return json.loads(raw)


def load_reactor_from_path(path_or_preset: str | Path):
    """
    Load reactor from file path (JSON/YAML) or preset name.
    Returns create_reactor(**data) for files, create_reactor(name=...) for presets.
    """
    from smrforge.convenience import create_reactor

    p = Path(path_or_preset) if isinstance(path_or_preset, str) and (
        path_or_preset.endswith(".json") or path_or_preset.endswith(".yaml") or path_or_preset.endswith(".yml")
    ) else path_or_preset
    if isinstance(p, Path) and p.exists():
        data = _load_json_or_yaml(p)
        return create_reactor(**data)
    return create_reactor(name=str(path_or_preset))


def _load_reactor_from_args(args: Any):
    """Load reactor from args.reactor (file path or preset name)."""
    r = getattr(args, "reactor", None)
    if not r:
        _exit_error("--reactor FILE or preset name required")
    return load_reactor_from_path(r)


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


def _exit_error(message: str) -> None:
    """
    Print error message and exit with code 1.
    Use for CLI validation failures (missing args, file not found, etc.).
    Never returns.
    """
    _print_error(message)
    sys.exit(1)


def _require_path(args: Any, attr: str, error_msg: str) -> Path:
    """
    Get path from args.attr; exit with error if missing or not existing.

    Args:
        args: Parsed args object (or Mock)
        attr: Attribute name (e.g. "reactor", "results")
        error_msg: Message to show when path is invalid

    Returns:
        Path instance (never returns if invalid)
    """
    val = getattr(args, attr, None)
    if not val:
        _exit_error(error_msg)
    p = Path(val)
    if not p.exists():
        _exit_error(error_msg)
    return p


def _exit_pro_required(feature_name: str, extra: str = "") -> None:
    """
    Print standard Pro-required message and exit with code 1.
    Use in except ImportError when smrforge_pro is missing.

    Args:
        feature_name: Human-readable feature name (e.g. "Surrogate workflow")
        extra: Optional additional text (e.g. "Alternative: Use 'smrforge workflow sweep'")
    """
    msg = f"{feature_name} requires SMRForge Pro.\nUpgrade: https://smrforge.io or pip install smrforge-pro"
    if extra:
        msg = f"{feature_name} requires SMRForge Pro.\n{extra}\nUpgrade: https://smrforge.io or pip install smrforge-pro"
    _print_error(msg)
    sys.exit(1)
