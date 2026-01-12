"""
Project management callbacks.
"""

try:
    from dash import Input, Output, State
    from dash.exceptions import PreventUpdate
    import dash_bootstrap_components as dbc
    _DASH_AVAILABLE = True
except ImportError:
    _DASH_AVAILABLE = False


def register_project_callbacks(app):
    """Register project callbacks."""
    if not _DASH_AVAILABLE:
        return
    
    @app.callback(
        Output('project-store', 'data'),
        Input('nav-save-project', 'n_clicks'),
        State('reactor-spec-store', 'data'),
        State('analysis-results-store', 'data'),
        prevent_initial_call=True
    )
    def save_project(n_clicks, reactor_spec, results):
        """Save project."""
        if not reactor_spec:
            return {'name': None, 'path': None}
        
        # In a real implementation, this would open a file dialog
        # For now, just return a placeholder
        return {'name': 'project.json', 'path': './project.json'}
