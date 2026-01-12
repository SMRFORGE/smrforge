"""
Analysis Panel Component

Interface for running neutronics, burnup, and safety analysis.
"""

try:
    import dash_bootstrap_components as dbc
    from dash import html, dcc
    _DASH_AVAILABLE = True
except ImportError:
    _DASH_AVAILABLE = False


def create_analysis_panel():
    """
    Create the analysis panel component.
    
    Returns:
        Dash component for analysis interface.
    """
    if not _DASH_AVAILABLE:
        return html.Div("Dash not available")
    
    return dbc.Container([
        html.H2("Analysis Panel", className="mb-4"),
        
        # Analysis type selection
        dbc.Card([
            dbc.CardHeader("Analysis Type"),
            dbc.CardBody([
                dbc.RadioItems(
                    id="analysis-type-radio",
                    options=[
                        {"label": "Neutronics (k-eff calculation)", "value": "neutronics"},
                        {"label": "Burnup Analysis", "value": "burnup"},
                        {"label": "Safety Transient", "value": "safety"},
                        {"label": "Complete Analysis", "value": "complete"},
                    ],
                    value="neutronics",
                    inline=False,
                ),
            ])
        ], className="mb-4"),
        
        # Neutronics options
        html.Div(id="neutronics-options", className="mb-4"),
        
        # Burnup options
        html.Div(id="burnup-options", className="mb-4"),
        
        # Safety transient options
        html.Div(id="safety-options", className="mb-4"),
        
        # Run button
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    "Run Analysis",
                    id="run-analysis-button",
                    color="primary",
                    size="lg",
                    disabled=True,
                ),
            ])
        ], className="mb-3"),
        
        # Progress indicator
        html.Div(id="analysis-progress", className="mb-3"),
        
        # Status/feedback
        html.Div(id="analysis-feedback", className="mb-3"),
        
        # Note about CLI
        dbc.Alert(
            "💡 All analyses can also be run via CLI. See documentation for examples.",
            color="info",
            className="mt-3"
        ),
    ], fluid=True)


def create_neutronics_options():
    """Create neutronics analysis options."""
    return dbc.Card([
        dbc.CardHeader("Neutronics Options"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Max Iterations"),
                    dbc.Input(
                        id="neutronics-max-iter",
                        type="number",
                        value=1000,
                        min=10,
                        step=10,
                    ),
                ], width=6),
                dbc.Col([
                    dbc.Label("Tolerance"),
                    dbc.Input(
                        id="neutronics-tolerance",
                        type="number",
                        value=1e-6,
                        min=1e-10,
                        step=1e-6,
                    ),
                ], width=6),
            ]),
        ])
    ])


def create_burnup_options():
    """Create burnup analysis options."""
    return dbc.Card([
        dbc.CardHeader("Burnup Options"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Time Steps (days, comma-separated)"),
                    dbc.Input(
                        id="burnup-time-steps",
                        type="text",
                        placeholder="0, 365, 730, 1095",
                        value="0, 365, 730",
                    ),
                ], width=12),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Power Density (W/cm³)"),
                    dbc.Input(
                        id="burnup-power-density",
                        type="number",
                        value=1e6,
                        min=1e5,
                        step=1e5,
                    ),
                ], width=6),
            ]),
        ])
    ])


def create_safety_options():
    """Create safety transient analysis options."""
    return dbc.Card([
        dbc.CardHeader("Safety Transient Options"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Transient Type"),
                    dcc.Dropdown(
                        id="transient-type-dropdown",
                        options=[
                            {"label": "Steam Line Break (SLB)", "value": "slb"},
                            {"label": "Feedwater Line Break (FWLB)", "value": "fwlb"},
                            {"label": "Small Break LOCA", "value": "sb_loca"},
                            {"label": "Large Break LOCA", "value": "lb_loca"},
                            {"label": "Loss of Flow (LOFC)", "value": "lofc"},
                        ],
                        value="slb",
                    ),
                ], width=6),
                dbc.Col([
                    dbc.Label("Simulation Time (s)"),
                    dbc.Input(
                        id="transient-time",
                        type="number",
                        value=3600.0,
                        min=1.0,
                        step=100.0,
                    ),
                ], width=6),
            ]),
        ])
    ])
