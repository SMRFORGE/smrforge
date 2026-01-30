"""
Data Manager Component

Interface for managing ENDF nuclear data downloads and configuration.
"""

try:
    import dash_bootstrap_components as dbc
    from dash import html, dcc
    _DASH_AVAILABLE = True
except ImportError:
    _DASH_AVAILABLE = False
    dbc = None  # type: ignore[assignment]
    html = None  # type: ignore[assignment]
    dcc = None  # type: ignore[assignment]


def create_data_manager():
    """
    Create the data manager component.
    
    Returns:
        Dash component for data management interface.
    """
    if not _DASH_AVAILABLE:
        return "Dash not available"
    
    return dbc.Container([
        html.H2("Data Manager", className="mb-4"),
        
        # ENDF Data Download
        dbc.Card([
            dbc.CardHeader("ENDF Nuclear Data Download"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Library Version"),
                        dcc.Dropdown(
                            id="endf-library-dropdown",
                            options=[
                                {"label": "ENDF/B-VIII.1", "value": "ENDF/B-VIII.1"},
                                {"label": "ENDF/B-VIII.0", "value": "ENDF/B-VIII.0"},
                                {"label": "JEFF-3.3", "value": "JEFF-3.3"},
                                {"label": "JENDL-5.0", "value": "JENDL-5.0"},
                            ],
                            value="ENDF/B-VIII.1",
                        ),
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Download Type"),
                        dcc.Dropdown(
                            id="endf-download-type",
                            options=[
                                {"label": "Common SMR Nuclides", "value": "common_smr"},
                                {"label": "Specific Isotopes", "value": "isotopes"},
                                {"label": "By Element", "value": "elements"},
                            ],
                            value="common_smr",
                        ),
                    ], width=6),
                ], className="mb-3"),
                
                html.Div(id="endf-custom-inputs", className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Output Directory"),
                        dbc.Input(
                            id="endf-output-dir",
                            type="text",
                            placeholder="~/ENDF-Data",
                            value="~/ENDF-Data",
                        ),
                    ], width=8),
                    dbc.Col([
                        dbc.Label("Max Workers (parallel downloads)"),
                        dbc.Input(
                            id="endf-max-workers",
                            type="number",
                            value=5,
                            min=1,
                            max=20,
                        ),
                    ], width=4),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            "Download ENDF Data",
                            id="download-endf-button",
                            color="primary",
                            size="lg",
                        ),
                    ])
                ]),
                
                # Progress
                html.Div(id="endf-download-progress", className="mt-3"),
                
                # Status
                html.Div(id="endf-download-status", className="mt-3"),
            ])
        ], className="mb-4"),
        
        # Configuration
        dbc.Card([
            dbc.CardHeader("Configuration"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("ENDF Directory"),
                        dbc.Input(
                            id="config-endf-dir",
                            type="text",
                            placeholder="~/ENDF-Data",
                        ),
                        dbc.FormText("Set SMRFORGE_ENDF_DIR environment variable or configure here"),
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Cache Directory"),
                        dbc.Input(
                            id="config-cache-dir",
                            type="text",
                            placeholder="~/.smrforge/cache",
                        ),
                    ], width=6),
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            "Save Configuration",
                            id="save-config-button",
                            color="primary",
                            className="mt-3",
                        ),
                    ])
                ]),
            ])
        ]),
        
        # CLI reminder
        dbc.Alert(
            "💡 Data downloads can also be done via CLI: "
            "from smrforge.data_downloader import download_endf_data",
            color="info",
            className="mt-3"
        ),
    ], fluid=True)
