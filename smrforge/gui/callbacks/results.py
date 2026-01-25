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
        
        neutronics = results.get('neutronics', {})
        flux_data = neutronics.get('flux')
        
        if flux_data and 'sample' in flux_data:
            # Use actual flux data from solver
            flux_values = np.array(flux_data['sample'])
            positions = np.linspace(0, 200, len(flux_values))  # Approximate positions
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=positions,
                y=flux_values,
                mode='lines',
                name='Neutron Flux',
                line=dict(color='blue', width=2)
            ))
            fig.update_layout(
                title=f"Neutron Flux Distribution (Max: {flux_data.get('max', 0):.2e} n/cm²/s)",
                xaxis_title="Position (cm)",
                yaxis_title="Flux (n/cm²/s)",
                hovermode='x unified'
            )
        else:
            # Fallback: show summary if no detailed data
            fig = go.Figure()
            if flux_data:
                fig.add_annotation(
                    text=f"Flux Statistics:<br>Max: {flux_data.get('max', 0):.2e}<br>Mean: {flux_data.get('mean', 0):.2e}<br>Min: {flux_data.get('min', 0):.2e}",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=14)
                )
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
        
        neutronics = results.get('neutronics', {})
        power_data = neutronics.get('power')
        
        if power_data and 'sample' in power_data:
            # Use actual power data from solver
            power_values = np.array(power_data['sample'])
            positions = np.linspace(0, 200, len(power_values))  # Approximate positions
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=positions,
                y=power_values,
                mode='lines',
                name='Power Density',
                line=dict(color='red', width=2),
                fill='tozeroy'
            ))
            fig.update_layout(
                title=f"Power Distribution (Max: {power_data.get('max', 0):.2e} W/cm³)",
                xaxis_title="Position (cm)",
                yaxis_title="Power Density (W/cm³)",
                hovermode='x unified'
            )
        else:
            # Fallback: show summary if no detailed data
            fig = go.Figure()
            if power_data:
                fig.add_annotation(
                    text=f"Power Statistics:<br>Max: {power_data.get('max', 0):.2e} W/cm³<br>Mean: {power_data.get('mean', 0):.2e} W/cm³<br>Min: {power_data.get('min', 0):.2e} W/cm³",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=14)
                )
            fig.update_layout(
                title="Power Distribution",
                xaxis_title="Position (cm)",
                yaxis_title="Power Density (W/cm³)",
            )
        
        return dcc.Graph(figure=fig)
    
    @app.callback(
        Output('3d-plot-container', 'children'),
        Input('analysis-results-store', 'data'),
        Input('reactor-spec-store', 'data'),
        prevent_initial_call=True
    )
    def update_3d_plot(results, reactor_spec):
        """Update 3D geometry plot."""
        if not reactor_spec:
            return dbc.Alert("No reactor specification available. Create a reactor first.", color="info")

        try:
            import smrforge as smr
            from smrforge.validation.models import ReactorSpecification
            from smrforge.visualization.advanced import plot_ray_traced_geometry

            spec = ReactorSpecification(**reactor_spec)
            reactor = smr.create_reactor(
                name=spec.name,
                power_mw=spec.power_thermal / 1e6,
                core_height=spec.core_height,
                core_diameter=spec.core_diameter,
                enrichment=spec.enrichment,
                reactor_type=spec.reactor_type,
                fuel_type=spec.fuel_type,
                inlet_temperature=spec.inlet_temperature,
                outlet_temperature=spec.outlet_temperature,
            )
            core = reactor._get_core()
            fig = plot_ray_traced_geometry(
                core,
                origin=(0.0, 0.0, float(spec.core_height) / 2.0),
                width=(float(spec.core_diameter) * 1.2, float(spec.core_diameter) * 1.2, float(spec.core_height) * 1.2),
                basis="xy",
                backend="plotly",
            )
            return dcc.Graph(figure=fig)
        except Exception as e:
            logger.error(f"3D plot failed: {e}", exc_info=True)
            return dbc.Alert(f"3D plot failed: {e}", color="warning")
    
    @app.callback(
        Output('transient-plot-container', 'children'),
        Input('analysis-results-store', 'data'),
        prevent_initial_call=True
    )
    def update_transient_plot(results):
        """Update transient results plot."""
        if not results:
            return dbc.Alert("No transient data available. Run an analysis first.", color="info")

        # Prefer safety, then quick transient, then lumped thermal
        series = None
        title = None
        if isinstance(results, dict) and "safety" in results and results["safety"].get("status") == "success":
            series = results["safety"]
            title = "Safety transient (point kinetics)"
        elif isinstance(results, dict) and "quick_transient" in results and results["quick_transient"].get("status") == "success":
            series = results["quick_transient"]
            title = "Quick transient"
        elif isinstance(results, dict) and "lumped_thermal" in results and results["lumped_thermal"].get("status") == "success":
            series = results["lumped_thermal"].get("result", {})
            title = "Lumped thermal"

        if not series:
            return dbc.Alert("No transient series found. Run a safety / quick transient / lumped thermal analysis.", color="info")

        t = series.get("time", [])
        fig = go.Figure()

        if t and series.get("power"):
            fig.add_trace(go.Scatter(x=t, y=series.get("power", []), mode="lines", name="Power (W)"))

        # Temperature traces (varies by source)
        if t and series.get("T_fuel"):
            fig.add_trace(go.Scatter(x=t, y=series.get("T_fuel", []), mode="lines", name="T_fuel (K)", yaxis="y2"))
        if t and (series.get("T_moderator") or series.get("T_mod")):
            fig.add_trace(go.Scatter(x=t, y=series.get("T_moderator", series.get("T_mod", [])), mode="lines", name="T_moderator (K)", yaxis="y2"))

        if t and series.get("reactivity"):
            fig.add_trace(go.Scatter(x=t, y=series.get("reactivity", []), mode="lines", name="Reactivity (dk/k)", yaxis="y3"))

        fig.update_layout(
            title=title,
            xaxis_title="Time (s)",
            yaxis=dict(title="Power (W)"),
            yaxis2=dict(title="Temperature (K)", overlaying="y", side="right"),
            yaxis3=dict(title="Reactivity (dk/k)", anchor="free", overlaying="y", side="right", position=1.0),
            legend=dict(orientation="h"),
        )
        return dcc.Graph(figure=fig)
    
    @app.callback(
        Output('export-feedback', 'children'),
        Input('export-json-button', 'n_clicks'),
        Input('export-csv-button', 'n_clicks'),
        Input('export-plots-button', 'n_clicks'),
        State('analysis-results-store', 'data'),
        State('reactor-spec-store', 'data'),
        prevent_initial_call=True
    )
    def export_results(json_clicks, csv_clicks, plots_clicks, results, reactor_spec):
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
                # Export to JSON - include both reactor spec and results
                export_data = {
                    'reactor_specification': reactor_spec if reactor_spec else {},
                    'analysis_results': results,
                    'export_timestamp': timestamp,
                    'version': '1.0'
                }
                filename = f"smrforge_results_{timestamp}.json"
                filepath = Path(filename)
                with open(filepath, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                
                logger.info(f"Exported results to {filepath}")
                return dbc.Alert([
                    html.Strong("✓ Results exported to JSON"),
                    html.P(f"Saved to: {filepath.absolute()}")
                ], color="success")
            
            elif button_id == 'export-csv-button':
                # Export to CSV (flatten results and reactor spec)
                filename = f"smrforge_results_{timestamp}.csv"
                filepath = Path(filename)
                
                # Flatten results and reactor spec for CSV
                rows = []
                
                # Add reactor specification data
                if reactor_spec and isinstance(reactor_spec, dict):
                    for key, value in reactor_spec.items():
                        rows.append({
                            'Category': 'Reactor Specification',
                            'Parameter': key,
                            'Value': str(value)
                        })
                
                # Add analysis results
                for category, data in results.items():
                    if isinstance(data, dict):
                        for key, value in data.items():
                            # Skip large arrays in CSV (keep only summary stats)
                            if key in ['flux', 'power'] and isinstance(value, dict):
                                # Include summary statistics
                                if 'max' in value:
                                    rows.append({
                                        'Category': f'{category}_{key}',
                                        'Parameter': 'max',
                                        'Value': str(value.get('max', ''))
                                    })
                                    rows.append({
                                        'Category': f'{category}_{key}',
                                        'Parameter': 'mean',
                                        'Value': str(value.get('mean', ''))
                                    })
                                    rows.append({
                                        'Category': f'{category}_{key}',
                                        'Parameter': 'min',
                                        'Value': str(value.get('min', ''))
                                    })
                            else:
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
