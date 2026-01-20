"""
Sidebar navigation component for SMRForge Dashboard.
"""

try:
    import dash_bootstrap_components as dbc
    from dash import html, dcc
    _DASH_AVAILABLE = True
except ImportError:
    _DASH_AVAILABLE = False


def create_sidebar():
    """
    Create the sidebar navigation component.
    
    Returns:
        Dash component for sidebar navigation.
    """
    if not _DASH_AVAILABLE:
        return html.Div("Dash not available")
    
    return dbc.Nav([
        dbc.NavItem([
            dbc.NavLink(
                "Reactor Builder",
                href="#",
                id="nav-reactor-builder",
                active=True,
                className="nav-link"
            )
        ]),
        dbc.NavItem([
            dbc.NavLink(
                "Geometry Designer",
                href="#",
                id="nav-geometry-designer",
                className="nav-link"
            )
        ]),
        dbc.NavItem([
            dbc.NavLink(
                "Analysis",
                href="#",
                id="nav-analysis",
                className="nav-link"
            )
        ]),
        dbc.NavItem([
            dbc.NavLink(
                "Results",
                href="#",
                id="nav-results",
                className="nav-link"
            )
        ]),
        dbc.NavItem([
            dbc.NavLink(
                "Data Manager",
                href="#",
                id="nav-data-manager",
                className="nav-link"
            )
        ]),
        html.Hr(),
        dbc.NavItem([
            dbc.Button(
                "📁 Open Project",
                id="nav-open-project",
                color="link",
                className="nav-link text-start w-100 px-3",
                style={"text-decoration": "none", "border": "none", "background": "none"}
            )
        ]),
        dbc.NavItem([
            dbc.Button(
                "💾 Save Project",
                id="nav-save-project",
                color="link",
                className="nav-link text-start w-100 px-3",
                style={"text-decoration": "none", "border": "none", "background": "none"}
            )
        ]),
        html.Div(id="project-feedback", className="px-3 mt-2"),
        html.Hr(),
        # Theme selector
        dbc.NavItem([
            dbc.Label("Theme", className="px-3 mb-2", style={"fontSize": "0.9rem", "fontWeight": "bold"}),
            dcc.Dropdown(
                id="theme-selector",
                options=[
                    {"label": "☀️ Light", "value": "light"},
                    {"label": "🌙 Dark", "value": "dark"},
                    {"label": "🌓 Gray", "value": "gray"},
                ],
                value="light",
                clearable=False,
                className="px-3 mb-3",
                style={"fontSize": "0.9rem"},
            ),
        ]),
        html.Hr(),
        dbc.NavItem([
            html.Small(
                "💡 Tip: All features are also available via CLI",
                className="text-muted px-3"
            )
        ]),
    ], vertical=True, pills=True, className="sticky-top")
