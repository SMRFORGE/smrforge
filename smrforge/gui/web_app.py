"""
SMRForge Web Dashboard

Main Dash application for SMRForge GUI.
Provides web-based interface while maintaining full CLI compatibility.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

try:
    import dash
    from dash import dcc, html, Input, Output, State
    import dash_bootstrap_components as dbc
    from dash.exceptions import PreventUpdate
    import plotly.graph_objects as go
    import plotly.express as px
    import numpy as np
    _DASH_AVAILABLE = True
except ImportError as e:
    _DASH_AVAILABLE = False
    dcc = None
    html = None
    dbc = None
    go = None
    px = None
    dash = None

from smrforge.utils.logging import get_logger

logger = get_logger(__name__)

if _DASH_AVAILABLE:
    # Initialize Dash app with Bootstrap theme (default: light)
    # Themes will be switched dynamically via clientside callback using Bootswatch CDN
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],  # Default light theme
        title="SMRForge Dashboard",
        suppress_callback_exceptions=True,
    )
    app.config.suppress_callback_exceptions = True
else:
    app = None


def create_app() -> Optional["dash.Dash"]:
    """
    Create and configure the SMRForge Dash application.
    
    Returns:
        Dash application instance, or None if Dash is not available.
    
    Example:
        >>> from smrforge.gui import create_app
        >>> app = create_app()
        >>> app.run_server(debug=True)
    """
    if not _DASH_AVAILABLE:
        logger.error(
            "Dash is not available. Install with: pip install dash dash-bootstrap-components"
        )
        return None
    
    # Import components
    from smrforge.gui.components import (
        create_sidebar,
        create_reactor_builder,
        create_analysis_panel,
        create_results_viewer,
        create_data_manager,
    )
    
    # Main layout
    app.layout = dbc.Container([
        dcc.Store(id='reactor-spec-store', data={}),
        dcc.Store(id='analysis-results-store', data={}),
        dcc.Store(id='project-store', data={'name': None, 'path': None, 'status': None, 'message': None}),
        dcc.Store(id='theme-store', data={'theme': 'light'}),  # Theme preference
        dcc.Interval(id='progress-interval', interval=1000, disabled=True),
        
        # Header
        dbc.Row([
            dbc.Col([
                html.H1("SMRForge Dashboard", className="text-center mb-4"),
                html.P(
                    "Small Modular Reactor Design and Analysis Toolkit",
                    className="text-center text-muted mb-4"
                ),
            ])
        ]),
        
        # Main content area
        dbc.Row([
            # Sidebar
            dbc.Col([
                create_sidebar()
            ], width=3, className="border-end"),
            
            # Main content
            dbc.Col([
                html.Div(id='main-content', children=create_reactor_builder())
            ], width=9),
        ]),
        
        # Footer
        dbc.Row([
            dbc.Col([
                html.Hr(),
                html.P(
                    [
                        "SMRForge Dashboard - ",
                        html.A("Documentation", href="https://github.com/cmwhalen/smrforge", target="_blank"),
                        " | ",
                        html.A("CLI Available", href="#", id="cli-info-link"),
                    ],
                    className="text-center text-muted small"
                ),
            ])
        ], className="mt-4"),
    ], fluid=True, className="p-4")
    
    # Register callbacks
    _register_callbacks()
    
    return app


def _register_callbacks():
    """Register all Dash callbacks."""
    from smrforge.gui.callbacks import (
        register_navigation_callbacks,
        register_reactor_builder_callbacks,
        register_analysis_callbacks,
        register_results_callbacks,
        register_data_manager_callbacks,
        register_project_callbacks,
    )
    from smrforge.gui.callbacks.theme import register_theme_callbacks
    
    register_navigation_callbacks(app)
    register_reactor_builder_callbacks(app)
    register_analysis_callbacks(app)
    register_results_callbacks(app)
    register_data_manager_callbacks(app)
    register_project_callbacks(app)
    register_theme_callbacks(app)


def run_server(
    host: str = "127.0.0.1",
    port: int = 8050,
    debug: bool = False,
    **kwargs
) -> None:
    """
    Run the SMRForge dashboard server.
    
    Args:
        host: Host address (default: 127.0.0.1)
        port: Port number (default: 8050)
        debug: Enable debug mode (default: False)
        **kwargs: Additional arguments passed to app.run_server()
    
    Example:
        >>> from smrforge.gui import run_server
        >>> run_server(port=8050, debug=True)
    """
    if not _DASH_AVAILABLE:
        raise ImportError(
            "Dash is not available. Install with: pip install dash dash-bootstrap-components"
        )
    
    app_instance = create_app()
    if app_instance is None:
        raise RuntimeError("Failed to create Dash application")
    
    logger.info(f"Starting SMRForge Dashboard on http://{host}:{port}")
    logger.info("Press Ctrl+C to stop the server")
    
    # Dash 3.x uses app.run() instead of app.run_server()
    # Check if run() method exists (Dash 3.x+), otherwise use run_server() (Dash 2.x)
    if hasattr(app_instance, 'run'):
        app_instance.run(host=host, port=port, debug=debug, **kwargs)
    else:
        # Fallback for older Dash versions
        app_instance.run_server(host=host, port=port, debug=debug, **kwargs)


if __name__ == "__main__":
    run_server(debug=True)
