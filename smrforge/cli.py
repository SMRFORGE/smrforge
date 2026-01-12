"""
SMRForge CLI

Command-line interface for SMRForge, including dashboard launcher.
All features remain available via Python API and CLI.
"""

import argparse
import sys
from pathlib import Path


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
    
    try:
        from smrforge.gui import run_server
        
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
    except ImportError as e:
        print("=" * 70)
        print("ERROR: Failed to import dashboard module")
        print("=" * 70)
        print(f"\nError: {e}")
        print("\nThis may indicate a missing dependency or installation issue.")
        print("Try installing dashboard dependencies:")
        print("  pip install dash dash-bootstrap-components")
        print("=" * 70)
        sys.exit(1)
    except Exception as e:
        print("=" * 70)
        print("ERROR: Failed to start dashboard")
        print("=" * 70)
        print(f"\nError: {e}")
        print("\nPlease check:")
        print("  1. Dashboard dependencies are installed: pip install dash dash-bootstrap-components")
        print("  2. Port is not already in use (try different port with --port)")
        print("  3. Firewall allows connections on the specified port")
        print("=" * 70)
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SMRForge - Small Modular Reactor Design and Analysis Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch web dashboard
  smrforge serve
  
  # Launch dashboard on custom port
  smrforge serve --port 8080
  
  # Launch dashboard in debug mode
  smrforge serve --debug

Note: All features are also available via Python API:
  import smrforge as smr
  reactor = smr.create_reactor("valar-10")
  k_eff = reactor.solve_keff()
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Serve command
    serve_parser = subparsers.add_parser(
        'serve',
        help='Launch the SMRForge web dashboard'
    )
    serve_parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='Host address (default: 127.0.0.1)'
    )
    serve_parser.add_argument(
        '--port',
        type=int,
        default=8050,
        help='Port number (default: 8050)'
    )
    serve_parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    serve_parser.set_defaults(func=serve_dashboard)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    
    args.func(args)


if __name__ == '__main__':
    main()
