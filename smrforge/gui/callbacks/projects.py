"""
Project management callbacks.
"""

try:
    from dash import Input, Output, State, html
    from dash.exceptions import PreventUpdate
    import dash_bootstrap_components as dbc
    _DASH_AVAILABLE = True
except ImportError:
    _DASH_AVAILABLE = False

from smrforge.utils.logging import get_logger

logger = get_logger(__name__)


def register_project_callbacks(app):
    """Register project callbacks."""
    if not _DASH_AVAILABLE:
        return
    
    @app.callback(
        Output('project-store', 'data'),
        Output('project-feedback', 'children'),
        Output('reactor-spec-store', 'data', allow_duplicate=True),
        Output('analysis-results-store', 'data', allow_duplicate=True),
        Input('nav-save-project', 'n_clicks'),
        Input('nav-open-project', 'n_clicks'),
        State('reactor-spec-store', 'data'),
        State('analysis-results-store', 'data'),
        prevent_initial_call=True
    )
    def handle_project(n_save, n_open, reactor_spec, results):
        """Handle both save and open project actions."""
        from dash import callback_context as ctx
        if not ctx.triggered:
            raise PreventUpdate
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        logger.info(f"Project action triggered: {button_id}")
        
        if button_id == 'nav-save-project':
            return _save_project(reactor_spec, results)
        elif button_id == 'nav-open-project':
            return _open_project()
        else:
            raise PreventUpdate
    
    def _save_project(reactor_spec, results):
        """Save project."""
        logger.info("Saving project")
        
        if not reactor_spec or (isinstance(reactor_spec, dict) and len(reactor_spec) == 0):
            feedback = dbc.Alert("No reactor specification to save. Create or load a reactor first.", color="warning", className="small")
            return (
                {'name': None, 'path': None, 'status': 'error', 'message': 'No reactor specification to save'}, 
                feedback,
                {},  # reactor-spec-store (no change)
                {}   # analysis-results-store (no change)
            )
        
        try:
            import json
            from datetime import datetime
            from pathlib import Path
            
            # Create project data
            project_data = {
                'reactor_spec': reactor_spec,
                'results': results or {},
                'created': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            # Save to default location
            project_path = Path('./smrforge_project.json')
            with open(project_path, 'w') as f:
                json.dump(project_data, f, indent=2, default=str)
            
            logger.info(f"Project saved to {project_path}")
            
            feedback = dbc.Alert([
                html.Strong("✓ Project Saved"),
                html.P(f"Saved to: {project_path.absolute()}")
            ], color="success", className="small")
            
            return (
                {
                    'name': project_path.name,
                    'path': str(project_path.absolute()),
                    'status': 'success',
                    'message': f'Project saved to {project_path.absolute()}'
                }, 
                feedback,
                {},  # reactor-spec-store (no change)
                {}   # analysis-results-store (no change)
            )
        except Exception as e:
            logger.error(f"Error saving project: {e}", exc_info=True)
            feedback = dbc.Alert(f"✗ Error saving project: {str(e)}", color="danger", className="small")
            return (
                {
                    'name': None,
                    'path': None,
                    'status': 'error',
                    'message': f'Error saving project: {str(e)}'
                }, 
                feedback,
                {},  # reactor-spec-store (no change)
                {}   # analysis-results-store (no change)
            )
    
    def _open_project():
        """Open project."""
        logger.info("Opening project")
        
        try:
            import json
            from pathlib import Path
            
            # Try to load the default project file
            project_path = Path('./smrforge_project.json')
            
            if not project_path.exists():
                feedback = dbc.Alert([
                    html.Strong("Project file not found"),
                    html.P(f"Looking for: {project_path.absolute()}"),
                    html.P("Save a project first, or use CLI to load projects.")
                ], color="warning", className="small")
                return (
                    {
                        'name': None,
                        'path': None,
                        'status': 'error',
                        'message': 'Project file not found'
                    }, 
                    feedback,
                    {},  # reactor-spec-store (no change)
                    {}   # analysis-results-store (no change)
                )
            
            # Load project data
            with open(project_path, 'r') as f:
                project_data = json.load(f)
            
            reactor_spec = project_data.get('reactor_spec', {})
            results = project_data.get('results', {})
            
            if not reactor_spec or len(reactor_spec) == 0:
                feedback = dbc.Alert("Project file is empty or invalid.", color="warning", className="small")
                return (
                    {
                        'name': None,
                        'path': None,
                        'status': 'error',
                        'message': 'Project file is empty or invalid'
                    }, 
                    feedback,
                    {},  # reactor-spec-store (no change)
                    {}   # analysis-results-store (no change)
                )
            
            logger.info(f"Project loaded: {project_path}")
            
            feedback = dbc.Alert([
                html.Strong("✓ Project Loaded"),
                html.P(f"Loaded: {project_path.name}"),
                html.P("Reactor specification and results have been loaded.")
            ], color="success", className="small")
            
            # Return the loaded data to update the stores
            return (
                {
                    'name': project_path.name,
                    'path': str(project_path.absolute()),
                    'status': 'success',
                    'message': f'Project loaded from {project_path.absolute()}'
                }, 
                feedback,
                reactor_spec,  # Update reactor-spec-store
                results        # Update analysis-results-store
            )
        
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing project file: {e}", exc_info=True)
            feedback = dbc.Alert(f"✗ Error parsing project file: {str(e)}", color="danger", className="small")
            return (
                {
                    'name': None,
                    'path': None,
                    'status': 'error',
                    'message': f'Error parsing project file: {str(e)}'
                }, 
                feedback,
                {},  # reactor-spec-store (no change)
                {}   # analysis-results-store (no change)
            )
        except Exception as e:
            logger.error(f"Error opening project: {e}", exc_info=True)
            feedback = dbc.Alert(f"✗ Error opening project: {str(e)}", color="danger", className="small")
            return (
                {
                    'name': None,
                    'path': None,
                    'status': 'error',
                    'message': f'Error opening project: {str(e)}'
                }, 
                feedback,
                {},  # reactor-spec-store (no change)
                {}   # analysis-results-store (no change)
            )
