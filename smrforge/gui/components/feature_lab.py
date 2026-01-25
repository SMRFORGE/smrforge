"""
Feature Lab Component

One place in the dashboard to exercise SMRForge's major feature areas with small,
fast demos. Designed to run without external nuclear data (ENDF) by relying on
the convenience API's simplified defaults where possible.
"""

try:
    import dash_bootstrap_components as dbc
    from dash import dcc, html

    _DASH_AVAILABLE = True
except ImportError:  # pragma: no cover
    _DASH_AVAILABLE = False


_DEMO_OPTIONS = [
    {"label": "Presets + create reactor", "value": "presets"},
    {"label": "Neutronics (k-eff) via convenience API", "value": "keff"},
    {"label": "Visualization (ray-traced geometry)", "value": "viz_geometry"},
    {"label": "Neutronics dashboard (spectrum + map)", "value": "neutronics_dashboard"},
    {"label": "Quick transient (point kinetics)", "value": "quick_transient"},
    {"label": "Lumped thermal-hydraulics (0-D)", "value": "lumped_thermal"},
    {"label": "Parameter sweep workflow (small)", "value": "parameter_sweep"},
    {"label": "Parameter sweep visualization (heatmap)", "value": "sweep_heatmap"},
    {"label": "Parameter sweep visualization (tornado)", "value": "sweep_tornado"},
    {"label": "Uncertainty quantification (Monte Carlo sampling)", "value": "uq_mc"},
    {"label": "Uncertainty quantification (distribution)", "value": "uq_distribution"},
    {"label": "Uncertainty quantification (correlations)", "value": "uq_correlations"},
    {"label": "Burnup evolution dashboard (synthetic)", "value": "burnup_dashboard"},
    {"label": "Mesh diagnostics (quality summary)", "value": "mesh_diagnostics"},
    {"label": "Validation summary + issues", "value": "validation_viz"},
    {"label": "Optimization (design optimizer demo)", "value": "optimization"},
    {"label": "Optimization trace (synthetic history)", "value": "optimization_trace"},
    {"label": "Economics (capital + O&M)", "value": "economics"},
    {"label": "Economics (CAPEX waterfall)", "value": "economics_capex"},
    {"label": "Economics (LCOE breakdown)", "value": "economics_lcoe"},
    {"label": "Control (PID step response)", "value": "control_pid"},
]


def create_feature_lab():
    """Create the feature lab page."""
    if not _DASH_AVAILABLE:  # pragma: no cover
        return html.Div("Dash not available")

    return dbc.Container(
        [
            html.H2("Feature Lab", className="mb-2"),
            html.P(
                "Run small, representative demos to exercise SMRForge features. "
                "These are designed to be fast and to work out-of-the-box.",
                className="text-muted mb-4",
            ),
            dbc.Card(
                [
                    dbc.CardHeader("Choose a demo"),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label("Demo"),
                                            dcc.Dropdown(
                                                id="feature-demo-dropdown",
                                                options=_DEMO_OPTIONS,
                                                value="presets",
                                                clearable=False,
                                            ),
                                        ],
                                        width=8,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label(" "),
                                            dbc.Button(
                                                "Run demo",
                                                id="run-feature-demo-button",
                                                color="primary",
                                                size="lg",
                                                className="w-100",
                                            ),
                                        ],
                                        width=4,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            dbc.Alert(
                                id="feature-demo-status",
                                color="info",
                                is_open=False,
                            ),
                            dcc.Loading(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardHeader("Output"),
                                            dbc.CardBody(
                                                html.Pre(
                                                    id="feature-demo-output",
                                                    style={
                                                        "whiteSpace": "pre-wrap",
                                                        "fontFamily": "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
                                                        "fontSize": "0.9rem",
                                                    },
                                                )
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    dbc.Card(
                                        [
                                            dbc.CardHeader("Plot (if available)"),
                                            dbc.CardBody(
                                                dcc.Graph(
                                                    id="feature-demo-graph",
                                                    figure={
                                                        "data": [],
                                                        "layout": {
                                                            "title": "Run a demo to generate a plot"
                                                        },
                                                    },
                                                )
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                            dbc.Alert(
                                "Tip: For fully scripted end-to-end runs, see the interactive notebooks "
                                "in `testing/notebooks/` and the guide in `docs/guides/testing-notebooks.md`.",
                                color="secondary",
                                className="mt-3",
                            ),
                        ]
                    ),
                ]
            ),
        ],
        fluid=True,
    )

