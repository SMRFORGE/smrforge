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

from smrforge.utils.logging import get_logger

logger = get_logger(__name__)


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
                logger.info(f"Loading preset: {preset}")
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
                logger.info("Creating custom reactor")
                # Create custom reactor with all required fields
                # Use sensible defaults for fields not provided in the form
                power_thermal = (power or 10.0) * 1e6  # Convert MW to W
                inlet_temp = inlet_temp or 823.15
                outlet_temp = outlet_temp or 1023.15
                
                spec_data = {
                    'name': name or 'Custom-Reactor',
                    'reactor_type': rtype or 'prismatic',
                    'power_thermal': power_thermal,
                    'power_electric': None,  # Optional, will be calculated if needed
                    'core_height': height or 200.0,
                    'core_diameter': diameter or 100.0,
                    'enrichment': enrichment or 0.195,
                    'inlet_temperature': inlet_temp,
                    'outlet_temperature': outlet_temp,
                    'max_fuel_temperature': outlet_temp + 500.0,  # Reasonable default: outlet + 500K
                    'primary_pressure': pressure or 7.0e6,
                    'reflector_thickness': 30.0,  # Default 30 cm
                    'fuel_type': 'UCO',  # Default fuel type
                    'heavy_metal_loading': hm_loading or 150.0,
                    'coolant_flow_rate': 8.0,  # Default 8 kg/s
                    'cycle_length': 3650.0,  # Default 10 years
                    'capacity_factor': 0.95,  # Default 95%
                    'target_burnup': 150.0,  # Default 150 MWd/kg
                    'doppler_coefficient': -3.5e-5,  # Default for HTGR
                    'shutdown_margin': 0.05,  # Default 5% shutdown margin
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
                    logger.error(f"Validation error creating reactor: {e}", exc_info=True)
                    # Extract more detailed error message if it's a Pydantic validation error
                    error_msg = str(e)
                    if "validation error" in error_msg.lower():
                        # Try to extract field-specific errors
                        error_msg = f"Validation failed: {error_msg[:200]}"
                    feedback = dbc.Alert(
                        f"✗ Validation error: {error_msg}",
                        color="danger"
                    )
                    return {}, feedback
        
        except Exception as e:
            logger.error(f"Error in create_reactor callback: {e}", exc_info=True)
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
        
        # Format values for better display
        def format_value(key, value):
            """Format values for display."""
            if value is None:
                return "N/A"
            if isinstance(value, float):
                # Format large numbers and small numbers appropriately
                if abs(value) >= 1e6:
                    return f"{value/1e6:.2f} M"
                elif abs(value) >= 1e3:
                    return f"{value/1e3:.2f} k"
                elif abs(value) < 0.01 and abs(value) > 0:
                    return f"{value:.2e}"
                else:
                    return f"{value:.2f}"
            return str(value)
        
        # Group parameters by category for better organization
        categories = {
            "Identification": ["name", "reactor_type", "description", "design_reference", "maturity_level"],
            "Power": ["power_thermal", "power_electric"],
            "Temperatures": ["inlet_temperature", "outlet_temperature", "max_fuel_temperature"],
            "Geometry": ["core_height", "core_diameter", "reflector_thickness"],
            "Fuel": ["fuel_type", "enrichment", "heavy_metal_loading"],
            "Operating Conditions": ["primary_pressure", "coolant_flow_rate"],
            "Performance": ["cycle_length", "capacity_factor", "target_burnup"],
            "Safety": ["doppler_coefficient", "shutdown_margin"],
            "Economics": ["capital_cost", "fuel_cost"],
        }
        
        rows = []
        for category, fields in categories.items():
            category_rows = []
            for field in fields:
                if field in spec_data:
                    value = spec_data[field]
                    if value is not None:  # Skip None values
                        category_rows.append(
                            html.Tr([
                                html.Td(html.Strong(field.replace('_', ' ').title())),
                                html.Td(format_value(field, value))
                            ])
                        )
            if category_rows:
                rows.append(html.Tr([
                    html.Td(html.Strong(category), colSpan=2, style={"backgroundColor": "#f8f9fa", "fontSize": "1.1em"})
                ]))
                rows.extend(category_rows)
        
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
                    html.Tbody(rows)
                ], bordered=True, hover=True, responsive=True, size="sm")
            ])
        ])
