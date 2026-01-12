"""
Reactor Builder Component

Form-based interface for creating reactor specifications.
"""

try:
    import dash_bootstrap_components as dbc
    from dash import html, dcc
    _DASH_AVAILABLE = True
except ImportError:
    _DASH_AVAILABLE = False


def create_reactor_builder():
    """
    Create the reactor builder component.
    
    Returns:
        Dash component for reactor building interface.
    """
    if not _DASH_AVAILABLE:
        return html.Div("Dash not available")
    
    try:
        import smrforge as smr
        presets = smr.list_presets()
    except:
        presets = []
    
    return dbc.Container([
        html.H2("Reactor Builder", className="mb-4"),
        
        # Preset selection
        dbc.Card([
            dbc.CardHeader("Preset Designs"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Select Preset Design"),
                        dcc.Dropdown(
                            id="preset-dropdown",
                            options=[{"label": p, "value": p} for p in presets],
                            placeholder="Select a preset or create custom...",
                            clearable=True,
                        ),
                    ], width=6),
                    dbc.Col([
                        dbc.Button(
                            "Load Preset",
                            id="load-preset-button",
                            color="primary",
                            className="mt-4"
                        ),
                    ], width=6),
                ]),
            ])
        ], className="mb-4"),
        
        # Custom reactor parameters
        dbc.Card([
            dbc.CardHeader("Reactor Parameters"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Reactor Name"),
                        dbc.Input(
                            id="reactor-name-input",
                            type="text",
                            placeholder="My Reactor",
                            value="Custom-Reactor"
                        ),
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Reactor Type"),
                        dcc.Dropdown(
                            id="reactor-type-dropdown",
                            options=[
                                {"label": "Prismatic HTGR", "value": "prismatic"},
                                {"label": "Pebble Bed HTGR", "value": "pebble_bed"},
                                {"label": "PWR SMR", "value": "pwr_smr"},
                                {"label": "BWR SMR", "value": "bwr_smr"},
                            ],
                            value="prismatic",
                        ),
                    ], width=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Thermal Power (MW)"),
                        dbc.Input(
                            id="power-input",
                            type="number",
                            value=10.0,
                            min=0.1,
                            step=0.1,
                        ),
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Core Height (cm)"),
                        dbc.Input(
                            id="core-height-input",
                            type="number",
                            value=200.0,
                            min=10.0,
                            step=10.0,
                        ),
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Core Diameter (cm)"),
                        dbc.Input(
                            id="core-diameter-input",
                            type="number",
                            value=100.0,
                            min=10.0,
                            step=10.0,
                        ),
                    ], width=4),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Fuel Enrichment"),
                        dbc.Input(
                            id="enrichment-input",
                            type="number",
                            value=0.195,
                            min=0.0,
                            max=1.0,
                            step=0.001,
                        ),
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Inlet Temperature (K)"),
                        dbc.Input(
                            id="inlet-temp-input",
                            type="number",
                            value=823.15,
                            min=273.15,
                            step=10.0,
                        ),
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Outlet Temperature (K)"),
                        dbc.Input(
                            id="outlet-temp-input",
                            type="number",
                            value=1023.15,
                            min=273.15,
                            step=10.0,
                        ),
                    ], width=4),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Primary Pressure (Pa)"),
                        dbc.Input(
                            id="pressure-input",
                            type="number",
                            value=7.0e6,
                            min=1.0e5,
                            step=1.0e5,
                        ),
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Heavy Metal Loading (kg)"),
                        dbc.Input(
                            id="hm-loading-input",
                            type="number",
                            value=150.0,
                            min=1.0,
                            step=10.0,
                        ),
                    ], width=6),
                ], className="mb-3"),
            ])
        ], className="mb-4"),
        
        # Action buttons
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    "Create Reactor",
                    id="create-reactor-button",
                    color="primary",
                    size="lg",
                    className="me-2"
                ),
                dbc.Button(
                    "Validate",
                    id="validate-reactor-button",
                    color="secondary",
                    size="lg",
                    className="me-2"
                ),
                dbc.Button(
                    "Reset",
                    id="reset-reactor-button",
                    color="outline-secondary",
                    size="lg",
                ),
            ])
        ]),
        
        # Status/feedback
        html.Div(id="reactor-builder-feedback", className="mt-3"),
        
        # Reactor specification display
        html.Div(id="reactor-spec-display", className="mt-4"),
    ], fluid=True)
