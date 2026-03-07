"""
Visualize command handlers: visualize_geometry, visualize_flux.
"""

import json
import sys
from pathlib import Path

from smrforge.cli.common import (
    _exit_error,
    _exit_pro_required,
    _load_json_or_yaml,
    _print_info,
    _print_success,
    load_reactor_from_path,
    _require_path,
)


def visualize_geometry(args):
    """Visualize reactor geometry."""
    try:
        import json

        import smrforge as smr
        from smrforge.convenience import create_reactor
        from smrforge.visualization.advanced import (
            export_visualization,
            plot_ray_traced_geometry,
        )

        reactor_path = _require_path(args, "reactor", "Reactor file not found")
        reactor = load_reactor_from_path(reactor_path)
        core = reactor._get_core()

        _print_info("Generating geometry visualization...")

        # Create visualization
        if args.d3d:
            fig = plot_ray_traced_geometry(
                core,
                backend="plotly" if args.backend == "plotly" else "pyvista",
            )
        else:  # pragma: no cover
            # 2D visualization
            from smrforge.visualization.geometry import plot_core_layout

            fig = plot_core_layout(core)

        # Save or show
        if args.output:
            export_visualization(fig, args.output, format=args.format or "png")
            _print_success(f"Visualization saved to {args.output}")
        elif args.interactive:
            if hasattr(fig, "show"):
                fig.show()
            else:  # pragma: no cover
                _print_info(
                    "Interactive display requires plotly backend"
                )  # pragma: no cover
        else:
            if hasattr(fig, "show"):
                fig.show()
            else:  # pragma: no cover
                _print_info(
                    "Figure object created. Use --output to save or --interactive to display"
                )  # pragma: no cover

    except ImportError as e:  # pragma: no cover
        _exit_error(f"Failed to import visualization modules: {e}")  # pragma: no cover
    except Exception as e:  # pragma: no cover
        _exit_error(f"Failed to visualize geometry: {e}")  # pragma: no cover


def visualize_flux(args):
    """Plot flux distribution."""
    try:
        import json

        from smrforge.visualization.geometry import plot_flux_on_geometry

        results_path = _require_path(args, "results", "Results file not found")
        results_data = _load_json_or_yaml(results_path)

        _print_info("Generating flux visualization...")

        # Note: This would need flux data from results
        _print_info("NOTE: Flux visualization requires flux data in results file")
        _print_info("Use Python API for full flux visualization:")
        print("  from smrforge.visualization.geometry import plot_flux_on_geometry")
        print("  fig = plot_flux_on_geometry(geometry, flux_data)")

        if args.output:
            _print_info(f"Output file specified: {args.output}")  # pragma: no cover
            _print_info("Save visualization using Python API")  # pragma: no cover

    except ImportError as e:
        _exit_error(f"Failed to import visualization modules: {e}")  # pragma: no cover
    except Exception as e:
        _exit_error(f"Failed to visualize flux: {e}")


def visualize_tally(args):
    """Visualize OpenMC tally from statepoint (Pro tier)."""
    _exit_pro_required("Tally visualization")
