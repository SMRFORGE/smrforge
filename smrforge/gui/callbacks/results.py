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
    
    @app.callback(
        Output('3d-plot-container', 'children'),
        Input('analysis-results-store', 'data'),
        prevent_initial_call=True
    )
    def update_3d_plot(results):
        """Update 3D geometry plot."""
        if not results:
            return dbc.Alert("No 3D geometry data available.", color="info")
        
        # Placeholder for 3D visualization
        return dbc.Alert(
            "3D geometry visualization coming soon. Use CLI for 3D visualization: "
            "from smrforge.visualization import plot_3d_geometry",
            color="info"
        )
    
    @app.callback(
        Output('transient-plot-container', 'children'),
        Input('analysis-results-store', 'data'),
        prevent_initial_call=True
    )
    def update_transient_plot(results):
        """Update transient results plot."""
        if not results or 'safety' not in results:
            return dbc.Alert("No transient data available. Run a safety analysis first.", color="info")
        
        # Placeholder for transient visualization
        return dbc.Alert(
            "Transient visualization coming soon. Use CLI for transient analysis: "
            "from smrforge.safety import run_transient",
            color="info"
        )
    
    @app.callback(
        Output('export-feedback', 'children'),
        Input('export-json-button', 'n_clicks'),
        Input('export-csv-button', 'n_clicks'),
        Input('export-plots-button', 'n_clicks'),
        State('analysis-results-store', 'data'),
        prevent_initial_call=True
    )
    def export_results(json_clicks, csv_clicks, plots_clicks, results):
        """Export results to various formats."""
        from dash import callback_context as ctx
        if not ctx.triggered:
            raise PreventUpdate
        
        if not results or (isinstance(results, dict) and len(results) == 0):
            return dbc.Alert("No results to export. Run an analysis first.", color="warning")
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        logger.info(f"Exporting results: {button_id}")
        
        try:
            import json
            import csv
            from pathlib import Path
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if button_id == 'export-json-button':
                # Export to JSON
                filename = f"smrforge_results_{timestamp}.json"
                filepath = Path(filename)
                with open(filepath, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                
                logger.info(f"Exported results to {filepath}")
                return dbc.Alert([
                    html.Strong("✓ Results exported to JSON"),
                    html.P(f"Saved to: {filepath.absolute()}")
                ], color="success")
            
            elif button_id == 'export-csv-button':
                # Export to CSV (flatten results)
                filename = f"smrforge_results_{timestamp}.csv"
                filepath = Path(filename)
                
                # Flatten results for CSV
                rows = []
                for category, data in results.items():
                    if isinstance(data, dict):
                        for key, value in data.items():
                            rows.append({
                                'Category': category,
                                'Parameter': key,
                                'Value': str(value)
                            })
                
                if rows:
                    with open(filepath, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=['Category', 'Parameter', 'Value'])
                        writer.writeheader()
                        writer.writerows(rows)
                    
                    logger.info(f"Exported results to {filepath}")
                    return dbc.Alert([
                        html.Strong("✓ Results exported to CSV"),
                        html.P(f"Saved to: {filepath.absolute()}")
                    ], color="success")
                else:
                    return dbc.Alert("No data to export to CSV.", color="warning")
            
            elif button_id == 'export-plots-button':
                # Export plots (placeholder)
                return dbc.Alert(
                    "Plot export coming soon. Use CLI: "
                    "from smrforge.visualization import save_plots",
                    color="info"
                )
            
            raise PreventUpdate
        
        except Exception as e:
            logger.error(f"Export error: {e}", exc_info=True)
            return dbc.Alert(f"✗ Export error: {str(e)}", color="danger")
