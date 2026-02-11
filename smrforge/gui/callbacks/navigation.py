"""
Navigation callbacks for sidebar.
"""

try:
    from dash import Input, Output, State, callback_context, html
    from dash.exceptions import PreventUpdate

    _DASH_AVAILABLE = True
except ImportError:
    _DASH_AVAILABLE = False
    callback_context = None

from smrforge.utils.logging import get_logger

logger = get_logger(__name__)

from smrforge.gui.components import (
    create_analysis_panel,
    create_data_manager,
    create_feature_lab,
    create_geometry_designer,
    create_reactor_builder,
    create_results_viewer,
)


def register_navigation_callbacks(app):
    """Register navigation callbacks."""
    if not _DASH_AVAILABLE:
        return

    @app.callback(
        Output("main-content", "children"),
        Input("nav-reactor-builder", "n_clicks"),
        Input("nav-geometry-designer", "n_clicks"),
        Input("nav-analysis", "n_clicks"),
        Input("nav-results", "n_clicks"),
        Input("nav-data-manager", "n_clicks"),
        Input("nav-feature-lab", "n_clicks"),
        prevent_initial_call=False,
    )
    def update_main_content(n1, n2, n3, n4, n5, n6):
        """Update main content based on navigation clicks."""
        from dash import callback_context as ctx

        if not ctx.triggered:
            logger.debug("Initial load: showing reactor builder")
            return create_reactor_builder()

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        logger.info(f"Navigation: switching to {button_id}")

        if button_id == "nav-reactor-builder":
            return create_reactor_builder()
        elif button_id == "nav-geometry-designer":
            return create_geometry_designer()
        elif button_id == "nav-analysis":
            return create_analysis_panel()
        elif button_id == "nav-results":
            return create_results_viewer()
        elif button_id == "nav-data-manager":
            return create_data_manager()
        elif button_id == "nav-feature-lab":
            return create_feature_lab()

        return create_reactor_builder()
