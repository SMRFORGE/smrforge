"""
Geometry Designer Callbacks

Interactive callbacks for geometry design interface.
"""

from __future__ import annotations

try:
    from dash import Input, Output, State, html, callback_context
    from dash.exceptions import PreventUpdate
    import dash_bootstrap_components as dbc
    import plotly.graph_objects as go
    import numpy as np
    import json
    import base64
    _DASH_AVAILABLE = True
except ImportError:
    _DASH_AVAILABLE = False

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge.gui.callbacks.geometry_designer")


def register_geometry_designer_callbacks(app):
    """Register geometry designer callbacks."""
    if not _DASH_AVAILABLE:
        return
    
    @app.callback(
        [
            Output("geometry-core-layout", "figure"),
            Output("geometry-data-store", "data"),
            Output("geometry-material-palette", "children"),
        ],
        [
            Input("geometry-core-type", "value"),
            Input("geometry-grid-size", "value"),
            Input("geometry-grid-size-y", "value"),
            Input("geometry-assembly-size", "value"),
            Input("geometry-core-layout", "clickData"),
            Input("geometry-selected-material", "value"),
            Input("geometry-tool-store", "data"),
            Input("geometry-clear-btn", "n_clicks"),
            Input("geometry-reset-btn", "n_clicks"),
        ],
        [
            State("geometry-data-store", "data"),
            State("geometry-enrichment", "value"),
            State("geometry-fuel-type", "value"),
        ],
        prevent_initial_call=False,
    )
    def update_core_layout(
        core_type,
        grid_size_x,
        grid_size_y,
        assembly_size,
        click_data,
        selected_material,
        tool_data,
        clear_clicks,
        reset_clicks,
        geometry_data,
        enrichment,
        fuel_type,
    ):
        """Update core layout visualization and handle interactions."""
        ctx = callback_context
        
        # Initialize geometry data if needed
        if geometry_data is None or geometry_data.get("layout") is None:
            grid_size_x = grid_size_x or 10
            grid_size_y = grid_size_y or 10
            geometry_data = {
                "layout": np.zeros((grid_size_y, grid_size_x), dtype=int),
                "materials": {},
                "properties": {},
            }
        
        # Handle button clicks
        if ctx.triggered:
            trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
            
            if trigger_id == "geometry-clear-btn":
                # Clear all assemblies
                geometry_data["layout"] = np.zeros_like(geometry_data["layout"])
                geometry_data["materials"] = {}
                geometry_data["properties"] = {}
            
            elif trigger_id == "geometry-reset-btn":
                # Reset to default layout
                grid_size_x = grid_size_x or 10
                grid_size_y = grid_size_y or 10
                geometry_data = {
                    "layout": np.zeros((grid_size_y, grid_size_x), dtype=int),
                    "materials": {},
                    "properties": {},
                }
            
            elif trigger_id == "geometry-core-layout" and click_data:
                # Handle click on core layout
                if click_data.get("points"):
                    point = click_data["points"][0]
                    x = int(point.get("x", 0))
                    y = int(point.get("y", 0))
                    
                    # Get current tool
                    tool = tool_data.get("tool", "paint") if tool_data else "paint"
                    
                    # Update layout based on tool
                    if tool == "paint" and selected_material:
                        # Map material to integer code
                        material_map = {
                            "fuel": 1,
                            "control": 2,
                            "reflector": 3,
                            "moderator": 4,
                            "shield": 5,
                            "empty": 0,
                        }
                        material_code = material_map.get(selected_material, 0)
                        
                        # Update cell
                        if 0 <= y < geometry_data["layout"].shape[0] and 0 <= x < geometry_data["layout"].shape[1]:
                            geometry_data["layout"][y, x] = material_code
                            
                            # Store material properties
                            cell_key = f"{y},{x}"
                            geometry_data["materials"][cell_key] = selected_material
                            geometry_data["properties"][cell_key] = {
                                "enrichment": enrichment or 19.5,
                                "fuel_type": fuel_type or "UCO",
                            }
                    
                    elif tool == "erase":
                        if 0 <= y < geometry_data["layout"].shape[0] and 0 <= x < geometry_data["layout"].shape[1]:
                            geometry_data["layout"][y, x] = 0
                            cell_key = f"{y},{x}"
                            if cell_key in geometry_data["materials"]:
                                del geometry_data["materials"][cell_key]
                            if cell_key in geometry_data["properties"]:
                                del geometry_data["properties"][cell_key]
        
        # Create visualization
        layout = geometry_data["layout"]
        fig = _create_core_layout_figure(layout, assembly_size or 36.0)
        
        # Create material palette
        from smrforge.gui.components.geometry_designer import _create_material_palette
        palette = _create_material_palette()
        
        return fig, geometry_data, palette
    
    @app.callback(
        [
            Output("geometry-3d-preview", "figure"),
            Output("geometry-core-statistics", "children"),
            Output("geometry-assembly-properties", "children"),
        ],
        [
            Input("geometry-data-store", "data"),
            Input("geometry-core-layout", "hoverData"),
        ],
        prevent_initial_call=False,
    )
    def update_preview_and_stats(geometry_data, hover_data):
        """Update 3D preview and statistics."""
        if geometry_data is None or geometry_data.get("layout") is None:
            return go.Figure(), html.Div("No geometry data"), html.Div("No assembly selected")
        
        layout = geometry_data["layout"]
        
        # Create 3D preview
        fig_3d = _create_3d_preview(layout)
        
        # Calculate statistics
        stats = _calculate_core_statistics(geometry_data)
        
        # Assembly properties (from hover)
        assembly_props = html.Div("Hover over an assembly to see properties")
        if hover_data and hover_data.get("points"):
            point = hover_data["points"][0]
            x = int(point.get("x", 0))
            y = int(point.get("y", 0))
            cell_key = f"{y},{x}"
            
            if cell_key in geometry_data.get("properties", {}):
                props = geometry_data["properties"][cell_key]
                assembly_props = html.Div([
                    html.Strong(f"Assembly ({x}, {y})"),
                    html.Br(),
                    html.Small(f"Material: {geometry_data['materials'].get(cell_key, 'Unknown')}"),
                    html.Br(),
                    html.Small(f"Enrichment: {props.get('enrichment', 'N/A')}%"),
                    html.Br(),
                    html.Small(f"Fuel Type: {props.get('fuel_type', 'N/A')}"),
                ])
        
        return fig_3d, stats, assembly_props
    
    @app.callback(
        Output("geometry-tool-store", "data"),
        [
            Input("geometry-tool-select", "n_clicks"),
            Input("geometry-tool-paint", "n_clicks"),
            Input("geometry-tool-fill", "n_clicks"),
            Input("geometry-tool-erase", "n_clicks"),
        ],
        prevent_initial_call=True,
    )
    def update_tool(select_clicks, paint_clicks, fill_clicks, erase_clicks):
        """Update selected tool."""
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        tool_map = {
            "geometry-tool-select": "select",
            "geometry-tool-paint": "paint",
            "geometry-tool-fill": "fill",
            "geometry-tool-erase": "erase",
        }
        
        tool = tool_map.get(trigger_id, "paint")
        return {"tool": tool}
    
    @app.callback(
        Output("geometry-click-info", "children"),
        Input("geometry-core-layout", "clickData"),
        prevent_initial_call=True,
    )
    def update_click_info(click_data):
        """Update click information display."""
        if click_data and click_data.get("points"):
            point = click_data["points"][0]
            x = int(point.get("x", 0))
            y = int(point.get("y", 0))
            return html.Small(f"Clicked: ({x}, {y})")
        return html.Small("Click on the core layout to place assemblies")


def _create_core_layout_figure(layout: np.ndarray, assembly_size: float) -> go.Figure:
    """Create 2D core layout visualization."""
    # Material color map
    color_map = {
        0: "#FFFFFF",  # Empty
        1: "#FF6B6B",  # Fuel
        2: "#4ECDC4",  # Control
        3: "#95E1D3",  # Reflector
        4: "#F38181",  # Moderator
        5: "#AA96DA",  # Shield
    }
    
    # Create heatmap
    colors = np.array([[color_map.get(int(val), "#FFFFFF") for val in row] for row in layout])
    
    fig = go.Figure(data=go.Heatmap(
        z=layout,
        colorscale=[
            [0, "#FFFFFF"],
            [0.2, "#FF6B6B"],
            [0.4, "#4ECDC4"],
            [0.6, "#95E1D3"],
            [0.8, "#F38181"],
            [1.0, "#AA96DA"],
        ],
        showscale=True,
        colorbar=dict(
            title="Material Type",
            tickvals=[0, 1, 2, 3, 4, 5],
            ticktext=["Empty", "Fuel", "Control", "Reflector", "Moderator", "Shield"],
        ),
        hovertemplate="Position: (%{x}, %{y})<br>Material: %{z}<extra></extra>",
    ))
    
    fig.update_layout(
        title="Core Layout (Click to Place Assemblies)",
        xaxis_title="X Position",
        yaxis_title="Y Position",
        width=800,
        height=800,
        xaxis=dict(scaleanchor="y", scaleratio=1),
        yaxis=dict(autorange="reversed"),  # Reverse Y axis for matrix-like display
    )
    
    return fig


def _create_3d_preview(layout: np.ndarray) -> go.Figure:
    """Create 3D preview of core layout."""
    # Create 3D bar chart
    y_coords, x_coords = np.meshgrid(
        np.arange(layout.shape[0]), np.arange(layout.shape[1]), indexing="ij"
    )
    
    # Flatten for 3D plot
    x_flat = x_coords.flatten()
    y_flat = y_coords.flatten()
    z_flat = layout.flatten()
    
    # Only show non-zero assemblies
    mask = z_flat > 0
    x_flat = x_flat[mask]
    y_flat = y_flat[mask]
    z_flat = z_flat[mask]
    
    fig = go.Figure(data=go.Scatter3d(
        x=x_flat,
        y=y_flat,
        z=z_flat,
        mode="markers",
        marker=dict(
            size=5,
            color=z_flat,
            colorscale="Viridis",
            showscale=True,
        ),
    ))
    
    fig.update_layout(
        title="3D Preview",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Material Type",
        ),
        height=400,
    )
    
    return fig


def _calculate_core_statistics(geometry_data: dict) -> html.Div:
    """Calculate and display core statistics."""
    if geometry_data is None or geometry_data.get("layout") is None:
        return html.Div("No geometry data")
    
    layout = geometry_data["layout"]
    
    # Count assemblies by type
    total_cells = layout.size
    empty_cells = np.sum(layout == 0)
    fuel_cells = np.sum(layout == 1)
    control_cells = np.sum(layout == 2)
    reflector_cells = np.sum(layout == 3)
    
    stats = [
        html.Strong("Core Statistics"),
        html.Br(),
        html.Small(f"Total Cells: {total_cells}"),
        html.Br(),
        html.Small(f"Fuel Assemblies: {fuel_cells}"),
        html.Br(),
        html.Small(f"Control Rods: {control_cells}"),
        html.Br(),
        html.Small(f"Reflector: {reflector_cells}"),
        html.Br(),
        html.Small(f"Empty: {empty_cells}"),
        html.Br(),
        html.Small(f"Fill Fraction: {(total_cells - empty_cells) / total_cells * 100:.1f}%"),
    ]
    
    return html.Div(stats)
