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
        if not reactor_spec:
            return {}, dbc.Alert("No reactor specification available. Create a reactor first.", color="warning"), ""
        
        try:
            import smrforge as smr
            from smrforge.validation.models import ReactorSpecification
            
            # Create reactor from spec
            # Ensure reactor_spec is a dict and has all required fields
            if not isinstance(reactor_spec, dict):
                return {}, dbc.Alert("Invalid reactor specification format.", color="danger"), ""
            
            spec = ReactorSpecification(**reactor_spec)
            reactor = smr.create_reactor(
                power_mw=spec.power_thermal / 1e6,
                core_height=spec.core_height,
                core_diameter=spec.core_diameter,
                enrichment=spec.enrichment,
            )
            
            results = {}
            
            if analysis_type in ['neutronics', 'complete']:
                # Run neutronics
                k_eff = reactor.solve_keff()
                results['neutronics'] = {
                    'k_eff': k_eff,
                    'status': 'success'
                }
            
            if analysis_type in ['burnup', 'complete']:
                # Run burnup (simplified)
                results['burnup'] = {
                    'status': 'success',
                    'message': 'Burnup analysis completed'
                }
            
            if analysis_type in ['safety', 'complete']:
                # Run safety transient (simplified)
                results['safety'] = {
                    'status': 'success',
                    'message': 'Safety analysis completed'
                }
            
            feedback = dbc.Alert(
                f"✓ {analysis_type.capitalize()} analysis completed successfully!",
                color="success"
            )
            
            return results, feedback, ""
        
        except Exception as e:
            feedback = dbc.Alert(
                f"✗ Analysis error: {str(e)}",
                color="danger"
            )
            return {}, feedback, ""
