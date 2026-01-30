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
    dbc = None  # type: ignore[assignment]
    html = None  # type: ignore[assignment]
    dcc = None  # type: ignore[assignment]


def create_analysis_panel():
    """
    Create the analysis panel component.
    
    Returns:
        Dash component for analysis interface.
    """
    if not _DASH_AVAILABLE:
        return "Dash not available"
    
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
                        {"label": "Quick Transient Analysis", "value": "quick_transient"},
                        {"label": "Safety Transient", "value": "safety"},
                        {"label": "Lumped Thermal Hydraulics", "value": "lumped_thermal"},
                        {"label": "Complete Analysis", "value": "complete"},
                    ],
                    value="neutronics",
                    inline=False,
                ),
            ])
        ], className="mb-4"),
        
        # Neutronics options (always present in layout for State validation)
        html.Div(
            create_neutronics_options(),
            id="neutronics-options",
            className="mb-4",
            style={'display': 'block'}  # Visible initially (default analysis type)
        ),
        
        # Burnup options (always present in layout for State validation)
        html.Div(
            create_burnup_options(),
            id="burnup-options",
            className="mb-4",
            style={'display': 'none'}  # Hidden initially, callback will show/hide
        ),
        
        # Quick transient options (always present but conditionally visible)
        # Initialize with empty to avoid callback validation errors
        html.Div(
            create_quick_transient_options(),
            id="quick-transient-options",
            className="mb-4",
            style={'display': 'none'}  # Hidden initially
        ),
        
        # Safety transient options (always present in layout for State validation)
        html.Div(
            create_safety_options(),
            id="safety-options",
            className="mb-4",
            style={'display': 'none'}  # Hidden initially, callback will show/hide
        ),
        
        # Lumped thermal options (always present in layout for State validation)
        html.Div(
            create_lumped_thermal_options(),
            id="lumped-thermal-options",
            className="mb-4",
            style={'display': 'none'}  # Hidden initially, callback will show/hide
        ),
        
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


def create_quick_transient_options():
    """Create quick transient analysis options."""
    return dbc.Card([
        dbc.CardHeader("Quick Transient Analysis Options"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Transient Type"),
                    dcc.Dropdown(
                        id="quick-transient-type-dropdown",
                        options=[
                            {"label": "Reactivity Insertion Accident (RIA)", "value": "reactivity_insertion"},
                            {"label": "Reactivity Step Change", "value": "reactivity_step"},
                            {"label": "Power Change Transient", "value": "power_change"},
                            {"label": "Decay Heat Removal (Long-term)", "value": "decay_heat"},
                        ],
                        value="reactivity_insertion",
                    ),
                ], width=6),
                dbc.Col([
                    dbc.Label("Duration (s)"),
                    dbc.Input(
                        id="quick-transient-duration",
                        type="number",
                        value=100.0,
                        min=1.0,
                        step=10.0,
                    ),
                ], width=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Initial Power (W)"),
                    dbc.Input(
                        id="quick-transient-power",
                        type="number",
                        value=1e6,
                        min=1e3,
                        step=1e5,
                    ),
                ], width=6),
                dbc.Col([
                    dbc.Label("Initial Temperature (K)"),
                    dbc.Input(
                        id="quick-transient-temperature",
                        type="number",
                        value=1200.0,
                        min=273.15,
                        step=50.0,
                    ),
                ], width=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Reactivity Insertion (dk/k)"),
                    dbc.Input(
                        id="quick-transient-reactivity",
                        type="number",
                        value=0.001,
                        min=-1.0,
                        max=1.0,
                        step=0.001,
                    ),
                    dbc.FormText("Only used for reactivity insertion/step types"),
                ], width=6),
                dbc.Col([
                    dbc.Label("Scram Available"),
                    dbc.Checklist(
                        id="quick-transient-scram-available",
                        options=[{"label": "Enable scram", "value": True}],
                        value=[True],
                    ),
                ], width=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Scram Delay (s)"),
                    dbc.Input(
                        id="quick-transient-scram-delay",
                        type="number",
                        value=1.0,
                        min=0.1,
                        step=0.1,
                    ),
                ], width=6),
                dbc.Col([
                    dbc.Label("Long-term Optimization"),
                    dbc.Checklist(
                        id="quick-transient-long-term",
                        options=[{"label": "Enable for transients > 1 day", "value": True}],
                        value=[],
                    ),
                ], width=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Generate Plot"),
                    dbc.Checklist(
                        id="quick-transient-plot",
                        options=[{"label": "Show plot after analysis", "value": True}],
                        value=[True],
                    ),
                ], width=6),
                dbc.Col([
                    dbc.Label("Plot Backend"),
                    dcc.Dropdown(
                        id="quick-transient-plot-backend",
                        options=[
                            {"label": "Plotly (Interactive)", "value": "plotly"},
                            {"label": "Matplotlib (Publication)", "value": "matplotlib"},
                        ],
                        value="plotly",
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


def create_lumped_thermal_options():
    """Create lumped-parameter thermal hydraulics options."""
    return dbc.Card([
        dbc.CardHeader("Lumped Thermal Hydraulics Options"),
        dbc.CardBody([
            dbc.Alert(
                "Fast 0-D thermal circuit model for long transients (72+ hours). "
                "Useful for decay heat removal and preliminary safety assessments.",
                color="info",
                className="mb-3"
            ),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Duration (s)"),
                    dbc.Input(
                        id="lumped-thermal-duration",
                        type="number",
                        value=3600.0,
                        min=1.0,
                        step=100.0,
                    ),
                ], width=6),
                dbc.Col([
                    dbc.Label("Max Time Step (s)"),
                    dbc.Input(
                        id="lumped-thermal-max-step",
                        type="number",
                        value=3600.0,
                        min=0.1,
                        step=100.0,
                    ),
                ], width=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Adaptive Time Stepping"),
                    dbc.Checklist(
                        id="lumped-thermal-adaptive",
                        options=[{"label": "Enable adaptive stepping", "value": True}],
                        value=[True],
                    ),
                ], width=6),
                dbc.Col([
                    dbc.Label("Generate Plot"),
                    dbc.Checklist(
                        id="lumped-thermal-plot",
                        options=[{"label": "Show plot after analysis", "value": True}],
                        value=[True],
                    ),
                ], width=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Configuration"),
                    dbc.Select(
                        id="lumped-thermal-config",
                        options=[
                            {"label": "Default (2-lump: fuel + moderator)", "value": "default"},
                            {"label": "Custom (specify in config file)", "value": "custom"},
                        ],
                        value="default",
                    ),
                ], width=12),
            ]),
        ])
    ])
