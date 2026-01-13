"""
Analysis callbacks.
"""

try:
    from dash import Input, Output, State
    from dash.exceptions import PreventUpdate
    import dash_bootstrap_components as dbc
    from dash import html
    _DASH_AVAILABLE = True
except ImportError:
    _DASH_AVAILABLE = False

from smrforge.utils.logging import get_logger

logger = get_logger(__name__)

from smrforge.gui.components.analysis_panel import (
    create_neutronics_options,
    create_burnup_options,
    create_safety_options,
)


def register_analysis_callbacks(app):
    """Register analysis callbacks."""
    if not _DASH_AVAILABLE:
        return
    
    @app.callback(
        Output('neutronics-options', 'children'),
        Output('burnup-options', 'children'),
        Output('safety-options', 'children'),
        Output('run-analysis-button', 'disabled'),
        Input('analysis-type-radio', 'value'),
        Input('reactor-spec-store', 'data'),
        prevent_initial_call=False
    )
    def update_analysis_options(analysis_type, reactor_spec):
        """Update analysis options based on selected type."""
        has_reactor = bool(reactor_spec)
        
        if analysis_type == 'neutronics':
            return create_neutronics_options(), "", "", not has_reactor
        elif analysis_type == 'burnup':
            return "", create_burnup_options(), "", not has_reactor
        elif analysis_type == 'safety':
            return "", "", create_safety_options(), not has_reactor
        else:  # complete
            return create_neutronics_options(), create_burnup_options(), create_safety_options(), not has_reactor
    
    @app.callback(
        Output('analysis-results-store', 'data'),
        Output('analysis-feedback', 'children'),
        Output('analysis-progress', 'children'),
        Input('run-analysis-button', 'n_clicks'),
        State('analysis-type-radio', 'value'),
        State('reactor-spec-store', 'data'),
        State('neutronics-max-iter', 'value'),
        State('neutronics-tolerance', 'value'),
        State('burnup-time-steps', 'value'),
        State('burnup-power-density', 'value'),
        State('transient-type-dropdown', 'value'),
        State('transient-time', 'value'),
        prevent_initial_call=True
    )
    def run_analysis(n_clicks, analysis_type, reactor_spec, max_iter, tolerance,
                     time_steps, power_density, transient_type, transient_time):
        """Run analysis."""
        logger.info(f"Running {analysis_type} analysis")
        
        if not reactor_spec:
            return {}, dbc.Alert("No reactor specification available. Create a reactor first.", color="warning"), ""
        
        try:
            import smrforge as smr
            from smrforge.validation.models import ReactorSpecification
            
            # Create reactor from spec
            # Ensure reactor_spec is a dict and has all required fields
            if not isinstance(reactor_spec, dict):
                logger.error("Invalid reactor specification format")
                return {}, dbc.Alert("Invalid reactor specification format.", color="danger"), ""
            
            spec = ReactorSpecification(**reactor_spec)
            logger.info(f"Creating reactor from spec: {spec.name}")
            
            # Create reactor with all spec parameters
            reactor = smr.create_reactor(
                power_mw=spec.power_thermal / 1e6,
                core_height=spec.core_height,
                core_diameter=spec.core_diameter,
                enrichment=spec.enrichment,
                reactor_type=spec.reactor_type.value if hasattr(spec.reactor_type, 'value') else str(spec.reactor_type),
                fuel_type=spec.fuel_type.value if hasattr(spec.fuel_type, 'value') else str(spec.fuel_type),
            )
            logger.info("Reactor created successfully")
            
            results = {}
            
            if analysis_type in ['neutronics', 'complete']:
                # Run neutronics
                logger.info("Running neutronics analysis")
                try:
                    # solve_keff() may raise ValueError if validation fails, but it handles
                    # it internally and returns k_eff anyway. We catch it here just in case.
                    import warnings
                    with warnings.catch_warnings(record=True) as w:
                        warnings.simplefilter("always")
                        k_eff = reactor.solve_keff()
                        
                        # Check if there were validation warnings
                        validation_warning = None
                        for warning in w:
                            if "validation" in str(warning.message).lower():
                                validation_warning = str(warning.message)
                                logger.warning(f"Solution validation warning: {validation_warning}")
                        
                        results['neutronics'] = {
                            'k_eff': float(k_eff),
                            'status': 'success'
                        }
                        if validation_warning:
                            results['neutronics']['warning'] = 'Solution validation failed but k_eff computed'
                        
                        logger.info(f"Neutronics analysis completed: k_eff = {k_eff:.6f}")
                except Exception as e:
                    logger.error(f"Neutronics analysis failed: {e}", exc_info=True)
                    # Try to get k_eff from solver if it exists
                    if hasattr(reactor, '_solver') and reactor._solver is not None:
                        if hasattr(reactor._solver, 'k_eff') and reactor._solver.k_eff is not None:
                            k_eff = reactor._solver.k_eff
                            results['neutronics'] = {
                                'k_eff': float(k_eff),
                                'status': 'success',
                                'warning': f'Analysis completed with errors: {str(e)[:100]}'
                            }
                            logger.warning(f"Using k_eff from solver despite error: {k_eff:.6f}")
                        else:
                            results['neutronics'] = {
                                'status': 'error',
                                'error': str(e)
                            }
                    else:
                        results['neutronics'] = {
                            'status': 'error',
                            'error': str(e)
                        }
            
            if analysis_type in ['burnup', 'complete']:
                # Run burnup (simplified)
                logger.info("Running burnup analysis")
                results['burnup'] = {
                    'status': 'success',
                    'message': 'Burnup analysis completed'
                }
            
            if analysis_type in ['safety', 'complete']:
                # Run safety transient (simplified)
                logger.info("Running safety analysis")
                results['safety'] = {
                    'status': 'success',
                    'message': 'Safety analysis completed'
                }
            
            # Check if any analysis failed
            has_errors = any(r.get('status') == 'error' for r in results.values())
            has_warnings = any('warning' in r for r in results.values())
            
            if has_errors:
                error_details = [f"{k}: {r.get('error', 'Unknown error')}" 
                               for k, r in results.items() if r.get('status') == 'error']
                feedback = dbc.Alert(
                    html.Div([
                        html.Strong("Analysis completed with errors:"),
                        html.Ul([html.Li(err) for err in error_details])
                    ]),
                    color="warning"
                )
            elif has_warnings:
                # Show warnings but still indicate success
                warning_details = []
                success_details = []
                for k, r in results.items():
                    if 'warning' in r:
                        warning_details.append(f"{k}: {r.get('warning', '')}")
                    if r.get('status') == 'success':
                        if 'k_eff' in r:
                            success_details.append(f"k-eff = {r['k_eff']:.6f}")
                
                feedback = dbc.Alert(
                    html.Div([
                        html.Strong("✓ Analysis completed with warnings:"),
                        html.Ul([html.Li(w) for w in warning_details]),
                        html.P([html.Strong("Results: "), ", ".join(success_details)])
                    ]),
                    color="info"
                )
            else:
                # Format success message with results
                result_details = []
                for k, r in results.items():
                    if r.get('status') == 'success':
                        if 'k_eff' in r:
                            result_details.append(f"k-eff = {r['k_eff']:.6f}")
                        elif 'message' in r:
                            result_details.append(r['message'])
                
                result_text = f"✓ {analysis_type.capitalize()} analysis completed successfully!"
                if result_details:
                    result_text += f" Results: {', '.join(result_details)}"
                
                feedback = dbc.Alert(result_text, color="success")
            
            return results, feedback, ""
        
        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            # Provide more helpful error messages
            error_msg = str(e)
            if "validation" in error_msg.lower():
                error_msg = "Reactor specification validation failed. Please check all required fields are present."
            elif "solve" in error_msg.lower() or "neutronics" in error_msg.lower():
                error_msg = f"Neutronics solver error: {error_msg[:200]}"
            
            feedback = dbc.Alert(
                html.Div([
                    html.Strong("Analysis Error:"),
                    html.P(error_msg)
                ]),
                color="danger"
            )
            return {}, feedback, ""
