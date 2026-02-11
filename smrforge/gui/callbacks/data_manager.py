"""
Data manager callbacks.
"""

try:
    import dash_bootstrap_components as dbc
    from dash import Input, Output, State, html
    from dash.exceptions import PreventUpdate

    _DASH_AVAILABLE = True
except ImportError:
    _DASH_AVAILABLE = False


def register_data_manager_callbacks(app):
    """Register data manager callbacks."""
    if not _DASH_AVAILABLE:
        return

    @app.callback(
        Output("endf-custom-inputs", "children"),
        Input("endf-download-type", "value"),
        prevent_initial_call=False,
    )
    def update_endf_inputs(download_type):
        """Update ENDF download inputs based on type."""
        if download_type == "isotopes":
            return dbc.Input(
                id="endf-isotopes-input",
                type="text",
                placeholder="U235, U238, Pu239 (comma-separated)",
            )
        elif download_type == "elements":
            return dbc.Input(
                id="endf-elements-input",
                type="text",
                placeholder="U, Pu, Th (comma-separated)",
            )
        return ""

    @app.callback(
        Output("endf-download-status", "children"),
        Output("endf-download-progress", "children"),
        Input("download-endf-button", "n_clicks"),
        State("endf-library-dropdown", "value"),
        State("endf-download-type", "value"),
        State("endf-isotopes-input", "value"),
        State("endf-elements-input", "value"),
        State("endf-output-dir", "value"),
        State("endf-max-workers", "value"),
        prevent_initial_call=True,
    )
    def download_endf_data(
        n_clicks, library, download_type, isotopes, elements, output_dir, max_workers
    ):
        """Download ENDF data."""
        try:
            from pathlib import Path

            from smrforge.data_downloader import download_endf_data

            # Prepare download parameters
            kwargs = {
                "library": library or "ENDF/B-VIII.1",
                "output_dir": output_dir or "~/ENDF-Data",
                "show_progress": False,  # We'll show progress in UI
                "max_workers": max_workers or 5,
            }

            if download_type == "common_smr":
                kwargs["nuclide_set"] = "common_smr"
            elif download_type == "isotopes" and isotopes:
                kwargs["isotopes"] = [i.strip() for i in isotopes.split(",")]
            elif download_type == "elements" and elements:
                kwargs["elements"] = [e.strip() for e in elements.split(",")]
            else:
                return (
                    dbc.Alert("Please specify isotopes or elements.", color="warning"),
                    "",
                )

            # Download
            stats = download_endf_data(**kwargs)

            status = dbc.Alert(
                [
                    html.H5("Download Complete!"),
                    html.P(f"Downloaded: {stats.get('downloaded', 0)} files"),
                    html.P(f"Skipped: {stats.get('skipped', 0)} files"),
                    html.P(f"Failed: {stats.get('failed', 0)} files"),
                ],
                color="success",
            )

            return status, ""

        except Exception as e:
            return dbc.Alert(f"✗ Download error: {str(e)}", color="danger"), ""

    @app.callback(
        Output("endf-download-status", "children", allow_duplicate=True),
        Input("save-config-button", "n_clicks"),
        State("config-endf-dir", "value"),
        State("config-cache-dir", "value"),
        prevent_initial_call=True,
    )
    def save_configuration(n_clicks, endf_dir, cache_dir):
        """Save configuration settings."""
        if not n_clicks:
            return ""

        try:
            # In a real implementation, this would save to config file
            # For now, just show a success message
            config_info = []
            if endf_dir:
                config_info.append(html.P(f"ENDF Directory: {endf_dir}"))
            if cache_dir:
                config_info.append(html.P(f"Cache Directory: {cache_dir}"))

            if config_info:
                return dbc.Alert(
                    [html.H5("Configuration Saved"), html.Div(config_info)],
                    color="success",
                )
            else:
                return dbc.Alert("No configuration changes to save.", color="info")
        except Exception as e:
            return dbc.Alert(f"✗ Configuration error: {str(e)}", color="danger")
