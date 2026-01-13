"""
Reactor builder callbacks.
"""

try:
    from dash import Input, Output, State, html
    from dash.exceptions import PreventUpdate
    import dash_bootstrap_components as dbc
    _DASH_AVAILABLE = True
except ImportError:
    _DASH_AVAILABLE = False


def register_reactor_builder_callbacks(app):
    """Register reactor builder callbacks."""
    if not _DASH_AVAILABLE:
        return
    
    @app.callback(
        Output('reactor-spec-store', 'data'),
        Output('reactor-builder-feedback', 'children'),
        Input('create-reactor-button', 'n_clicks'),
        Input('load-preset-button', 'n_clicks'),
        State('preset-dropdown', 'value'),
        State('reactor-name-input', 'value'),
        State('reactor-type-dropdown', 'value'),
        State('power-input', 'value'),
        State('core-height-input', 'value'),
        State('core-diameter-input', 'value'),
        State('enrichment-input', 'value'),
        State('inlet-temp-input', 'value'),
        State('outlet-temp-input', 'value'),
        State('pressure-input', 'value'),
        State('hm-loading-input', 'value'),
        prevent_initial_call=True
    )
    def create_reactor(n_create, n_load, preset, name, rtype, power, height, 
                       diameter, enrichment, inlet_temp, outlet_temp, pressure, hm_loading):
        """Create reactor specification."""
        from dash import callback_context as ctx
        if not ctx.triggered:
            raise PreventUpdate
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        try:
            import smrforge as smr
            
            if button_id == 'load-preset-button' and preset:
                # Load preset
                reactor = smr.create_reactor(preset)
                spec_data = reactor.spec.model_dump()
                
                # Validate that all required fields are present
                from smrforge.validation.models import ReactorSpecification
                try:
                    # Re-validate to ensure completeness
                    validated_spec = ReactorSpecification(**spec_data)
                    spec_data = validated_spec.model_dump()
                    feedback = dbc.Alert(
                        f"✓ Preset '{preset}' loaded successfully!",
                        color="success"
                    )
                    return spec_data, feedback
                except Exception as e:
                    feedback = dbc.Alert(
                        f"✗ Error loading preset '{preset}': {str(e)}",
                        color="danger"
                    )
                    return {}, feedback
            
            elif button_id == 'create-reactor-button':
                # Create custom reactor
                spec_data = {
                    'name': name or 'Custom-Reactor',
                    'reactor_type': rtype or 'prismatic',
                    'power_thermal': (power or 10.0) * 1e6,  # Convert to W
                    'core_height': height or 200.0,
                    'core_diameter': diameter or 100.0,
                    'enrichment': enrichment or 0.195,
                    'inlet_temperature': inlet_temp or 823.15,
                    'outlet_temperature': outlet_temp or 1023.15,
                    'primary_pressure': pressure or 7.0e6,
                    'heavy_metal_loading': hm_loading or 150.0,
                }
                
                # Validate using Pydantic
                from smrforge.validation.models import ReactorSpecification
                try:
                    spec = ReactorSpecification(**spec_data)
                    feedback = dbc.Alert(
                        "✓ Reactor created successfully!",
                        color="success"
                    )
                    return spec.model_dump(), feedback
                except Exception as e:
                    feedback = dbc.Alert(
                        f"✗ Validation error: {str(e)}",
                        color="danger"
                    )
                    return {}, feedback
        
        except Exception as e:
            feedback = dbc.Alert(
                f"✗ Error: {str(e)}",
                color="danger"
            )
            return {}, feedback
        
        raise PreventUpdate
    
    @app.callback(
        Output('reactor-spec-display', 'children'),
        Input('reactor-spec-store', 'data'),
        prevent_initial_call=True
    )
    def display_reactor_spec(spec_data):
        """Display reactor specification."""
        if not spec_data:
            return ""
        
        return dbc.Card([
            dbc.CardHeader("Current Reactor Specification"),
            dbc.CardBody([
                dbc.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("Parameter"),
                            html.Th("Value"),
                        ])
                    ]),
                    html.Tbody([
                        html.Tr([html.Td(k), html.Td(str(v))])
                        for k, v in spec_data.items()
                    ])
                ], bordered=True, hover=True, responsive=True)
            ])
        ])
