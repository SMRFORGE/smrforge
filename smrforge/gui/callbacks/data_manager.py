"""
Data manager callbacks.
"""

try:
    from dash import Input, Output, State
    from dash.exceptions import PreventUpdate
    import dash_bootstrap_components as dbc
    _DASH_AVAILABLE = True
except ImportError:
    _DASH_AVAILABLE = False


def register_data_manager_callbacks(app):
    """Register data manager callbacks."""
    if not _DASH_AVAILABLE:
        return
    
    @app.callback(
        Output('endf-custom-inputs', 'children'),
        Input('endf-download-type', 'value'),
        prevent_initial_call=False
    )
    def update_endf_inputs(download_type):
        """Update ENDF download inputs based on type."""
        if download_type == 'isotopes':
            return dbc.Input(
                id="endf-isotopes-input",
                type="text",
                placeholder="U235, U238, Pu239 (comma-separated)",
            )
        elif download_type == 'elements':
            return dbc.Input(
                id="endf-elements-input",
                type="text",
                placeholder="U, Pu, Th (comma-separated)",
            )
        return ""
    
    @app.callback(
        Output('endf-download-status', 'children'),
        Output('endf-download-progress', 'children'),
        Input('download-endf-button', 'n_clicks'),
        State('endf-library-dropdown', 'value'),
        State('endf-download-type', 'value'),
        State('endf-isotopes-input', 'value'),
        State('endf-elements-input', 'value'),
        State('endf-output-dir', 'value'),
        State('endf-max-workers', 'value'),
        prevent_initial_call=True
    )
    def download_endf_data(n_clicks, library, download_type, isotopes, elements, output_dir, max_workers):
        """Download ENDF data."""
        try:
            from smrforge.data_downloader import download_endf_data
            from pathlib import Path
            
            # Prepare download parameters
            kwargs = {
                'library': library or 'ENDF/B-VIII.1',
                'output_dir': output_dir or '~/ENDF-Data',
                'show_progress': False,  # We'll show progress in UI
                'max_workers': max_workers or 5,
            }
            
            if download_type == 'common_smr':
                kwargs['nuclide_set'] = 'common_smr'
            elif download_type == 'isotopes' and isotopes:
                kwargs['isotopes'] = [i.strip() for i in isotopes.split(',')]
            elif download_type == 'elements' and elements:
                kwargs['elements'] = [e.strip() for e in elements.split(',')]
            else:
                return dbc.Alert("Please specify isotopes or elements.", color="warning"), ""
            
            # Download
            stats = download_endf_data(**kwargs)
            
            status = dbc.Alert([
                html.H5("Download Complete!"),
                html.P(f"Downloaded: {stats.get('downloaded', 0)} files"),
                html.P(f"Skipped: {stats.get('skipped', 0)} files"),
                html.P(f"Failed: {stats.get('failed', 0)} files"),
            ], color="success")
            
            return status, ""
        
        except Exception as e:
            return dbc.Alert(f"✗ Download error: {str(e)}", color="danger"), ""
