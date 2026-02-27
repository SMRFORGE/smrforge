"""Serve command: launch the SMRForge web dashboard."""

import sys

from smrforge.cli.common import (
    Panel,
    _RICH_AVAILABLE,
    _print_error,
    console,
)


def serve_dashboard(args):
    """
    Launch the SMRForge web dashboard.

    Args:
        args: Parsed command-line arguments
    """
    # Check for Dash dependencies first
    try:
        import dash
        import dash_bootstrap_components
    except ImportError as e:
        if _RICH_AVAILABLE:
            console.print(
                Panel(  # pragma: no cover
                    "[bold red]ERROR: Dashboard dependencies not installed[/bold red]\n\n"
                    "The SMRForge web dashboard requires Dash and related packages.\n\n"
                    "[bold]To install dashboard dependencies:[/bold]\n"
                    "  [cyan]pip install dash dash-bootstrap-components[/cyan]\n\n"
                    "Or install all visualization dependencies:\n"
                    "  [cyan]pip install smrforge[viz][/cyan]\n\n"
                    f"After installation, run:\n"
                    f"  [cyan]smrforge serve --host {args.host} --port {args.port}[/cyan]",
                    title="Dashboard Setup",
                    border_style="red",
                )
            )
        else:  # pragma: no cover
            print("=" * 70)
            print("ERROR: Dashboard dependencies not installed")
            print("=" * 70)
            print("\nThe SMRForge web dashboard requires Dash and related packages.")
            print("\nTo install dashboard dependencies:")
            print("  pip install dash dash-bootstrap-components")
            print("\nOr install all visualization dependencies:")
            print("  pip install smrforge[viz]")
            print("\nAfter installation, run:")
            print(f"  smrforge serve --host {args.host} --port {args.port}")
            print("=" * 70)
        sys.exit(1)
        return  # ensure we don't fall through when exit is mocked

    try:
        from smrforge.gui import run_server

        if _RICH_AVAILABLE:
            console.print(
                Panel(
                    f"[bold cyan]Starting SMRForge Dashboard...[/bold cyan]\n\n"
                    f"Dashboard will be available at: [cyan]http://{args.host}:{args.port}[/cyan]\n"
                    f"Press [bold]Ctrl+C[/bold] to stop the server",
                    title="SMRForge Dashboard",
                    border_style="cyan",
                )
            )
        else:  # pragma: no cover
            print("=" * 70)
            print("Starting SMRForge Dashboard...")
            print("=" * 70)
            print(f"\nDashboard will be available at: http://{args.host}:{args.port}")
            print("Press Ctrl+C to stop the server\n")
            print("=" * 70)

        run_server(
            host=args.host,
            port=args.port,
            debug=args.debug,
        )
    except ImportError as e:  # pragma: no cover
        _print_error(f"Failed to import dashboard module: {e}")  # pragma: no cover
        print(
            "\nThis may indicate a missing dependency or installation issue."
        )  # pragma: no cover
        print("Try installing dashboard dependencies:")  # pragma: no cover
        print("  pip install dash dash-bootstrap-components")  # pragma: no cover
        sys.exit(1)  # pragma: no cover
    except Exception as e:  # pragma: no cover
        _print_error(f"Failed to start dashboard: {e}")
        print("\nPlease check:")
        print(
            "  1. Dashboard dependencies are installed: pip install dash dash-bootstrap-components"
        )
        print("  2. Port is not already in use (try different port with --port)")
        print("  3. Firewall allows connections on the specified port")
        sys.exit(1)
