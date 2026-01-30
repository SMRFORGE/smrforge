"""
Geometry Designer Component

Interactive GUI for designing reactor core geometries.
Provides visual editing capabilities for core layouts, assembly placement, and material assignment.
"""

try:
    import dash_bootstrap_components as dbc
    from dash import html, dcc
    import plotly.graph_objects as go
    import plotly.express as px
    import numpy as np
    _DASH_AVAILABLE = True
except ImportError:
    _DASH_AVAILABLE = False
    dbc = None  # type: ignore[assignment]
    html = None  # type: ignore[assignment]
    dcc = None  # type: ignore[assignment]
    go = None  # type: ignore[assignment]
    px = None  # type: ignore[assignment]
    np = None  # type: ignore[assignment]


def create_geometry_designer():
    """
    Create the geometry designer component.
    
    Provides interactive geometry design interface with:
    - Visual core layout editor (2D grid)
    - Assembly placement and configuration
    - Material assignment
    - Real-time visualization
    - Export/import capabilities
    
    Returns:
        Dash component for geometry design interface.
    """
    if not _DASH_AVAILABLE:
        return "Dash not available"
    
    return dbc.Container([
        html.H2("Geometry Designer", className="mb-4"),
        
        # Toolbar
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Core Type"),
                        dcc.Dropdown(
                            id="geometry-core-type",
                            options=[
                                {"label": "Prismatic HTGR", "value": "prismatic"},
                                {"label": "Pebble Bed HTGR", "value": "pebble_bed"},
                                {"label": "PWR SMR", "value": "pwr_smr"},
                                {"label": "BWR SMR", "value": "bwr_smr"},
                            ],
                            value="prismatic",
                            clearable=False,
                        ),
                    ], width=3),
                    dbc.Col([
                        dbc.Label("Grid Size"),
                        dbc.InputGroup([
                            dbc.Input(
                                id="geometry-grid-size",
                                type="number",
                                value=10,
                                min=5,
                                max=50,
                                step=1,
                            ),
                            dbc.InputGroupText("×"),
                            dbc.Input(
                                id="geometry-grid-size-y",
                                type="number",
                                value=10,
                                min=5,
                                max=50,
                                step=1,
                            ),
                        ]),
                    ], width=3),
                    dbc.Col([
                        dbc.Label("Assembly Size (cm)"),
                        dbc.Input(
                            id="geometry-assembly-size",
                            type="number",
                            value=36.0,
                            min=10.0,
                            step=1.0,
                        ),
                    ], width=2),
                    dbc.Col([
                        dbc.Label("Actions"),
                        dbc.ButtonGroup([
                            dbc.Button("Clear", id="geometry-clear-btn", color="warning", size="sm"),
                            dbc.Button("Reset", id="geometry-reset-btn", color="secondary", size="sm"),
                            dbc.Button("Export", id="geometry-export-btn", color="success", size="sm"),
                            dbc.Button("Import", id="geometry-import-btn", color="info", size="sm"),
                        ]),
                    ], width=4),
                ], className="mb-3"),
            ])
        ], className="mb-4"),
        
        # Main design area
        dbc.Row([
            # Left panel: Material palette and tools
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Material Palette"),
                    dbc.CardBody([
                        html.Div(id="geometry-material-palette", children=_create_material_palette()),
                        html.Hr(),
                        dbc.Label("Selected Material"),
                        dcc.Dropdown(
                            id="geometry-selected-material",
                            options=[
                                {"label": "Fuel", "value": "fuel", "color": "#FF6B6B"},
                                {"label": "Control Rod", "value": "control", "color": "#4ECDC4"},
                                {"label": "Reflector", "value": "reflector", "color": "#95E1D3"},
                                {"label": "Moderator", "value": "moderator", "color": "#F38181"},
                                {"label": "Shield", "value": "shield", "color": "#AA96DA"},
                                {"label": "Empty", "value": "empty", "color": "#FFFFFF"},
                            ],
                            value="fuel",
                        ),
                        html.Hr(),
                        dbc.Label("Assembly Properties"),
                        dbc.InputGroup([
                            dbc.InputGroupText("Enrichment (%)"),
                            dbc.Input(
                                id="geometry-enrichment",
                                type="number",
                                value=19.5,
                                min=0.0,
                                max=20.0,
                                step=0.1,
                            ),
                        ], className="mb-2"),
                        dbc.InputGroup([
                            dbc.InputGroupText("Fuel Type"),
                            dcc.Dropdown(
                                id="geometry-fuel-type",
                                options=[
                                    {"label": "UCO", "value": "UCO"},
                                    {"label": "UO2", "value": "UO2"},
                                    {"label": "TRISO", "value": "TRISO"},
                                ],
                                value="UCO",
                            ),
                        ], className="mb-2"),
                    ])
                ], className="mb-3"),
                
                dbc.Card([
                    dbc.CardHeader("Design Tools"),
                    dbc.CardBody([
                        dbc.ButtonGroup([
                            dbc.Button("Select", id="geometry-tool-select", color="primary", active=True),
                            dbc.Button("Paint", id="geometry-tool-paint", color="primary"),
                            dbc.Button("Fill", id="geometry-tool-fill", color="primary"),
                            dbc.Button("Erase", id="geometry-tool-erase", color="danger"),
                        ], vertical=True, className="w-100 mb-3"),
                        html.Hr(),
                        dbc.Label("Symmetry"),
                        dcc.Dropdown(
                            id="geometry-symmetry",
                            options=[
                                {"label": "None", "value": "none"},
                                {"label": "Quarter", "value": "quarter"},
                                {"label": "Half (X)", "value": "half_x"},
                                {"label": "Half (Y)", "value": "half_y"},
                            ],
                            value="quarter",
                        ),
                    ])
                ]),
            ], width=3),
            
            # Center: Interactive core layout
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Core Layout"),
                    dbc.CardBody([
                        dcc.Graph(
                            id="geometry-core-layout",
                            config={
                                "displayModeBar": True,
                                "modeBarButtonsToRemove": ["lasso2d", "select2d"],
                                "toImageButtonOptions": {
                                    "format": "png",
                                    "filename": "core_layout",
                                    "height": 800,
                                    "width": 800,
                                    "scale": 2,
                                },
                            },
                            style={"height": "800px"},
                        ),
                        html.Div(id="geometry-click-info", className="mt-2 text-muted small"),
                    ])
                ]),
            ], width=6),
            
            # Right panel: Properties and preview
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Assembly Properties"),
                    dbc.CardBody([
                        html.Div(id="geometry-assembly-properties"),
                        html.Hr(),
                        dbc.Label("Core Statistics"),
                        html.Div(id="geometry-core-statistics"),
                    ])
                ], className="mb-3"),
                
                dbc.Card([
                    dbc.CardHeader("3D Preview"),
                    dbc.CardBody([
                        dcc.Graph(
                            id="geometry-3d-preview",
                            config={"displayModeBar": False},
                            style={"height": "400px"},
                        ),
                    ])
                ]),
            ], width=3),
        ]),
        
        # Hidden stores for geometry data
        dcc.Store(id="geometry-data-store", data={"layout": None, "materials": {}}),
        dcc.Store(id="geometry-tool-store", data={"tool": "paint"}),
        
        # File upload for import
        dcc.Upload(
            id="geometry-upload-data",
            children=html.Div(["Drag and Drop or ", html.A("Select File")]),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
            multiple=False,
        ),
    ], fluid=True)


def _create_material_palette():
    """Create material palette visualization."""
    if not _DASH_AVAILABLE:
        return html.Div()
    
    materials = [
        {"name": "Fuel", "value": "fuel", "color": "#FF6B6B"},
        {"name": "Control", "value": "control", "color": "#4ECDC4"},
        {"name": "Reflector", "value": "reflector", "color": "#95E1D3"},
        {"name": "Moderator", "value": "moderator", "color": "#F38181"},
        {"name": "Shield", "value": "shield", "color": "#AA96DA"},
        {"name": "Empty", "value": "empty", "color": "#FFFFFF"},
    ]
    
    palette_items = []
    for mat in materials:
        palette_items.append(
            dbc.Row([
                dbc.Col([
                    html.Div(
                        "",
                        style={
                            "width": "30px",
                            "height": "30px",
                            "backgroundColor": mat["color"],
                            "border": "1px solid #ccc",
                            "borderRadius": "3px",
                        },
                    ),
                ], width=4),
                dbc.Col([
                    html.Small(mat["name"], className="text-muted"),
                ], width=8),
            ], className="mb-2")
        )
    
    return html.Div(palette_items)
