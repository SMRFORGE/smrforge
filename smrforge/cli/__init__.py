"""
SMRForge CLI

Command-line interface for SMRForge, including dashboard launcher.
All features remain available via Python API and CLI.
"""

from .main import main
from .utils import (
    _GLYPH_ERROR,
    _GLYPH_INFO,
    _GLYPH_SUCCESS,
    _GLYPH_WARNING,
    _RICH_AVAILABLE,
    _YAML_AVAILABLE,
    _print_error,
    _print_info,
    _print_success,
    _print_warning,
    _save_workflow_plot,
    _supports_unicode,
    _to_jsonable,
    console,
    rprint,
)

# Re-export handlers and helpers for tests and external use
from .commands.data import data_validate
from .commands.reactor import _reactor_analyze_batch, reactor_create
from .commands.serve import serve_dashboard
from .commands.workflow import _write_design_study_html

__all__ = [
    "main",
    "_GLYPH_ERROR",
    "_GLYPH_INFO",
    "_GLYPH_SUCCESS",
    "_GLYPH_WARNING",
    "_RICH_AVAILABLE",
    "_YAML_AVAILABLE",
    "_print_error",
    "_print_info",
    "_print_success",
    "_print_warning",
    "_reactor_analyze_batch",
    "_save_workflow_plot",
    "_supports_unicode",
    "_to_jsonable",
    "_write_design_study_html",
    "console",
    "rprint",
    "data_validate",
    "reactor_create",
    "serve_dashboard",
]
