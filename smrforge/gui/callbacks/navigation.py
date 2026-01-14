"""
Navigation callbacks for sidebar.
"""

try:
    from dash import Input, Output, State, html
    from dash.exceptions import PreventUpdate
    from dash import callback_context
    _DASH_AVAILABLE = True
except ImportError:
    _DASH_AVAILABLE = False
    callback_context = None

from smrforge.utils.logging import get_logger

logger = get_logger(__name__)

from smrforge.gui.components import (
    create_reactor_builder,
    create_analysis_panel,
    create_results_viewer,
    create_data_manager,
)


def register_navigation_callbacks(app):
    """Register navigation callbacks."""
    if not _DASH_AVAILABLE:
        return
    
    @app.callback(
        Output('main-content', 'children'),
        Input('nav-reactor-builder', 'n_clicks'),
        Input('nav-analysis', 'n_clicks'),
        Input('nav-results', 'n_clicks'),
        Input('nav-data-manager', 'n_clicks'),
        prevent_initial_call=False
    )
    def update_main_content(n1, n2, n3, n4):
        """Update main content based on navigation clicks."""
        from dash import callback_context as ctx
        if not ctx.triggered:
            logger.debug("Initial load: showing reactor builder")
            return create_reactor_builder()
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        logger.info(f"Navigation: switching to {button_id}")
        
        if button_id == 'nav-reactor-builder':
            return create_reactor_builder()
        elif button_id == 'nav-analysis':
            return create_analysis_panel()
        elif button_id == 'nav-results':
            return create_results_viewer()
        elif button_id == 'nav-data-manager':
            return create_data_manager()
        
        return create_reactor_builder()
