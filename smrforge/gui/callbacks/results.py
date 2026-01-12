"""
Results viewer callbacks.
"""

try:
    from dash import Input, Output, dcc
    from dash.exceptions import PreventUpdate
    import dash_bootstrap_components as dbc
    from dash import html
    import plotly.graph_objects as go
    import plotly.express as px
    import numpy as np
    _DASH_AVAILABLE = True
except ImportError:
    _DASH_AVAILABLE = False


def register_results_callbacks(app):
    """Register results callbacks."""
    if not _DASH_AVAILABLE:
        return
    
    @app.callback(
        Output('results-summary', 'children'),
        Input('analysis-results-store', 'data'),
        prevent_initial_call=True
    )
    def update_results_summary(results):
        """Update results summary."""
        if not results:
            return dbc.Alert("No results available. Run an analysis first.", color="info")
        
        summary_items = []
        
        if 'neutronics' in results:
            k_eff = results['neutronics'].get('k_eff', 'N/A')
            summary_items.append(
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("k-effective", className="card-title"),
                                html.H2(f"{k_eff:.6f}" if isinstance(k_eff, (int, float)) else str(k_eff)),
                            ])
                        ])
                    ], width=4)
                ])
            )
        
        if 'burnup' in results:
            summary_items.append(
                dbc.Row([
                    dbc.Col([
                        dbc.Alert("Burnup analysis completed", color="success")
                    ])
                ], className="mt-2")
            )
        
        if 'safety' in results:
            summary_items.append(
                dbc.Row([
                    dbc.Col([
                        dbc.Alert("Safety analysis completed", color="success")
                    ])
                ], className="mt-2")
            )
        
        return html.Div(summary_items)
    
    @app.callback(
        Output('flux-plot-container', 'children'),
        Input('analysis-results-store', 'data'),
        prevent_initial_call=True
    )
    def update_flux_plot(results):
        """Update flux distribution plot."""
        if not results or 'neutronics' not in results:
            return dbc.Alert("No flux data available.", color="info")
        
        # Create sample flux plot (in real implementation, use actual flux data)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=np.linspace(0, 200, 100),
            y=np.random.rand(100) * 1e14,
            mode='lines',
            name='Flux'
        ))
        fig.update_layout(
            title="Neutron Flux Distribution",
            xaxis_title="Position (cm)",
            yaxis_title="Flux (n/cm²/s)",
        )
        
        return dcc.Graph(figure=fig)
    
    @app.callback(
        Output('power-plot-container', 'children'),
        Input('analysis-results-store', 'data'),
        prevent_initial_call=True
    )
    def update_power_plot(results):
        """Update power distribution plot."""
        if not results or 'neutronics' not in results:
            return dbc.Alert("No power data available.", color="info")
        
        # Create sample power plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=np.linspace(0, 200, 100),
            y=np.random.rand(100) * 40,
            mode='lines',
            name='Power Density'
        ))
        fig.update_layout(
            title="Power Distribution",
            xaxis_title="Position (cm)",
            yaxis_title="Power Density (W/cm³)",
        )
        
        return dcc.Graph(figure=fig)
