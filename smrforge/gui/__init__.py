"""
SMRForge GUI Module

Provides web-based dashboard interface using Dash while maintaining full CLI compatibility.
"""

try:
    from smrforge.gui.web_app import create_app, run_server
    _GUI_AVAILABLE = True
except ImportError:
    _GUI_AVAILABLE = False

__all__ = []

if _GUI_AVAILABLE:
    __all__.extend([
        "create_app",
        "run_server",
    ])
