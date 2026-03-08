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
        Output("nav-reactor-builder", "active"),
        Output("nav-geometry-designer", "active"),
        Output("nav-analysis", "active"),
        Output("nav-results", "active"),
        Output("nav-data-manager", "active"),
        Output("nav-feature-lab", "active"),
        Input("nav-reactor-builder", "n_clicks"),
        Input("nav-geometry-designer", "n_clicks"),
        Input("nav-analysis", "n_clicks"),
        Input("nav-results", "n_clicks"),
        Input("nav-data-manager", "n_clicks"),
        Input("nav-feature-lab", "n_clicks"),
        prevent_initial_call=False,
    )
    def update_main_content(n1, n2, n3, n4, n5, n6):
        """Update main content and sidebar active state based on navigation clicks."""
        from dash import callback_context as ctx

        def _active(active_id):
            content_map = {
                "nav-reactor-builder": create_reactor_builder,
                "nav-geometry-designer": create_geometry_designer,
                "nav-analysis": create_analysis_panel,
                "nav-results": create_results_viewer,
                "nav-data-manager": create_data_manager,
                "nav-feature-lab": create_feature_lab,
            }
            content = content_map.get(active_id, create_reactor_builder)()
            flags = [
                active_id == "nav-reactor-builder",
                active_id == "nav-geometry-designer",
                active_id == "nav-analysis",
                active_id == "nav-results",
                active_id == "nav-data-manager",
                active_id == "nav-feature-lab",
            ]
            return content, *flags

        if not ctx.triggered:
            logger.debug("Initial load: showing reactor builder")
            return _active("nav-reactor-builder")

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        logger.info(f"Navigation: switching to {button_id}")
        return _active(button_id)
