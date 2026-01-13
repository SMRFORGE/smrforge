"""
Results viewer callbacks.
"""

try:
    from dash import Input, Output, dcc, State
    from dash.exceptions import PreventUpdate
    import dash_bootstrap_components as dbc
    from dash import html
    import plotly.graph_objects as go
    import plotly.express as px
    import numpy as np
    _DASH_AVAILABLE = True
except ImportError:
    _DASH_AVAILABLE = False

from smrforge.utils.logging import get_logger

logger = get_logger(__name__)


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
        logger.debug(f"Updating results summary: {list(results.keys()) if results else 'No results'}")
        
        if not results or (isinstance(results, dict) and len(results) == 0):
            return dbc.Alert("No results available. Run an analysis first.", color="info")
        
        summary_items = []
        
        if 'neutronics' in results:
            neutronics_data = results['neutronics']
            k_eff = neutronics_data.get('k_eff', 'N/A')
            status = neutronics_data.get('status', 'unknown')
            
            # Format k_eff display
            if isinstance(k_eff, (int, float)):
                k_eff_display = f"{k_eff:.6f}"
                # Add color coding based on k_eff value
                if k_eff < 0.95:
                    color = "danger"  # Subcritical
                elif k_eff < 0.98:
                    color = "warning"  # Below critical
                elif k_eff <= 1.02:
                    color = "success"  # Near critical
                else:
                    color = "warning"  # Supercritical
            else:
                k_eff_display = str(k_eff)
                color = "secondary"
            
            card_content = [
                html.H4("k-effective", className="card-title"),
                html.H2(k_eff_display),
            ]
            
            # Add warning if validation failed
            if 'warning' in neutronics_data:
                card_content.append(
                    html.P(neutronics_data['warning'], className="text-warning small mb-0")
                )
            
            summary_items.append(
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody(card_content)
                        ], color=color, outline=True)
                    ], width=4)
                ])
            )
        
        if 'burnup' in results:
            burnup_data = results['burnup']
            message = burnup_data.get('message', 'Burnup analysis completed')
            summary_items.append(
                dbc.Row([
                    dbc.Col([
                        dbc.Alert(message, color="success")
                    ])
                ], className="mt-2")
            )
        
        if 'safety' in results:
            safety_data = results['safety']
            message = safety_data.get('message', 'Safety analysis completed')
            summary_items.append(
                dbc.Row([
                    dbc.Col([
                        dbc.Alert(message, color="success")
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
