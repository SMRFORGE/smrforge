"""
Theme switching callbacks for dark/gray mode support.
"""

try:
    from dash import Input, Output, clientside_callback
    import dash_bootstrap_components as dbc
    _DASH_AVAILABLE = True
except ImportError:
    _DASH_AVAILABLE = False


def register_theme_callbacks(app):
    """Register theme switching callbacks."""
    if not _DASH_AVAILABLE:
        return
    
    # Clientside callback for theme switching using Bootswatch CDN
    clientside_callback(
        """
        function(theme) {
            if (!theme) {
                return window.dash_clientside.no_update;
            }
            
            // Theme URLs from Bootswatch CDN
            const themeUrls = {
                'light': 'https://cdn.jsdelivr.net/npm/bootswatch@5/dist/bootstrap/bootstrap.min.css',
                'dark': 'https://cdn.jsdelivr.net/npm/bootswatch@5/dist/darkly/bootstrap.min.css',
                'gray': 'https://cdn.jsdelivr.net/npm/bootswatch@5/dist/slate/bootstrap.min.css'
            };
            
            // Find the main Bootstrap stylesheet link
            const links = document.querySelectorAll('link[rel="stylesheet"]');
            let themeLink = null;
            
            // Look for existing Bootswatch or Bootstrap theme link
            links.forEach(link => {
                const href = link.getAttribute('href') || '';
                if (href.includes('bootswatch') || 
                    (href.includes('bootstrap') && 
                     (href.includes('darkly') || href.includes('slate') || 
                      href.includes('/bootstrap/bootstrap.min.css')))) {
                    themeLink = link;
                }
            });
            
            // If no theme link found, find the default Bootstrap link from dash-bootstrap-components
            if (!themeLink) {
                links.forEach(link => {
                    const href = link.getAttribute('href') || '';
                    if (href.includes('bootstrap') && !href.includes('bootswatch')) {
                        // This is likely the default DBC Bootstrap link
                        themeLink = link;
                    }
                });
            }
            
            // If still no link found, create one
            if (!themeLink) {
                themeLink = document.createElement('link');
                themeLink.rel = 'stylesheet';
                themeLink.id = 'smrforge-theme-stylesheet';
                document.head.appendChild(themeLink);
            }
            
            // Update the href to the selected theme
            const newUrl = themeUrls[theme] || themeUrls['light'];
            if (themeLink.href !== newUrl) {
                themeLink.href = newUrl;
            }
            
            // Update body class for custom CSS
            document.body.className = document.body.className
                .replace(/theme-light|theme-dark|theme-gray/g, '');
            document.body.classList.add(`theme-${theme}`);
            
            // Store preference in localStorage
            localStorage.setItem('smrforge-theme', theme);
            
            return window.dash_clientside.no_update;
        }
        """,
        Output('theme-store', 'data', allow_duplicate=True),
        Input('theme-selector', 'value'),
        prevent_initial_call='initial_duplicate',
    )
    
    # Load theme from localStorage on page load
    app.clientside_callback(
        """
        function() {
            const savedTheme = localStorage.getItem('smrforge-theme') || 'light';
            
            // Apply theme immediately
            const themeUrls = {
                'light': 'https://cdn.jsdelivr.net/npm/bootswatch@5/dist/bootstrap/bootstrap.min.css',
                'dark': 'https://cdn.jsdelivr.net/npm/bootswatch@5/dist/darkly/bootstrap.min.css',
                'gray': 'https://cdn.jsdelivr.net/npm/bootswatch@5/dist/slate/bootstrap.min.css'
            };
            
            // Find or create theme link
            const links = document.querySelectorAll('link[rel="stylesheet"]');
            let themeLink = null;
            
            links.forEach(link => {
                const href = link.getAttribute('href') || '';
                if (href.includes('bootswatch') || 
                    (href.includes('bootstrap') && 
                     (href.includes('darkly') || href.includes('slate') || 
                      href.includes('/bootstrap/bootstrap.min.css')))) {
                    themeLink = link;
                }
            });
            
            if (!themeLink) {
                links.forEach(link => {
                    const href = link.getAttribute('href') || '';
                    if (href.includes('bootstrap') && !href.includes('bootswatch')) {
                        themeLink = link;
                    }
                });
            }
            
            if (!themeLink) {
                themeLink = document.createElement('link');
                themeLink.rel = 'stylesheet';
                themeLink.id = 'smrforge-theme-stylesheet';
                document.head.appendChild(themeLink);
            }
            
            const newUrl = themeUrls[savedTheme] || themeUrls['light'];
            if (themeLink.href !== newUrl) {
                themeLink.href = newUrl;
            }
            
            // Update body class
            document.body.className = document.body.className
                .replace(/theme-light|theme-dark|theme-gray/g, '');
            document.body.classList.add(`theme-${savedTheme}`);
            
            return {'theme': savedTheme};
        }
        """,
        Output('theme-store', 'data'),
        Input('theme-store', 'id'),
    )
    
    # Sync theme selector with stored preference
    app.clientside_callback(
        """
        function(storedTheme) {
            if (storedTheme && storedTheme.theme) {
                return storedTheme.theme;
            }
            const savedTheme = localStorage.getItem('smrforge-theme') || 'light';
            return savedTheme;
        }
        """,
        Output('theme-selector', 'value'),
        Input('theme-store', 'data'),
    )
