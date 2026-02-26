"""SMRForge CLI command handlers."""

import json
import sys
from pathlib import Path

from ..utils import (
    _GLYPH_ERROR,
    _GLYPH_SUCCESS,
    _RICH_AVAILABLE,
    _YAML_AVAILABLE,
    _print_error,
    _print_info,
    _print_success,
    _print_warning,
    _save_workflow_plot,
    _to_jsonable,
    console,
    rprint,
    yaml,
)
try:
    from rich.panel import Panel
    from rich.table import Table
except ImportError:
    Panel = None  # type: ignore
    Table = None  # type: ignore

def decay_heat_calculate(args):
    """Calculate decay heat over time."""
    try:
        import json

        import numpy as np

        from smrforge.core.reactor_core import NuclearDataCache, Nuclide
        from smrforge.decay_heat import DecayHeatCalculator

        # Initialize cache
        cache = None
        if getattr(args, "endf_dir", None):
            cache = NuclearDataCache()  # pragma: no cover
            cache.set_endf_directory(str(args.endf_dir))  # pragma: no cover

        calculator = DecayHeatCalculator(cache=cache)

        # Load nuclide concentrations
        concentrations = {}

        if getattr(args, "inventory", None):
            # Load from inventory file
            inventory_path = args.inventory  # pragma: no cover
            if not inventory_path.exists():  # pragma: no cover
                _print_error(
                    f"Inventory file not found: {inventory_path}"
                )  # pragma: no cover
                sys.exit(1)  # pragma: no cover

            with open(inventory_path) as f:  # pragma: no cover
                inventory_data = json.load(f)  # pragma: no cover

            # Extract nuclide concentrations
            if (
                "nuclides" in inventory_data and "concentrations" in inventory_data
            ):  # pragma: no cover
                nuclide_names = inventory_data["nuclides"]  # pragma: no cover
                conc_values = inventory_data["concentrations"]  # pragma: no cover

                for name, conc in zip(nuclide_names, conc_values):  # pragma: no cover
                    # Parse nuclide name (e.g., "U235" -> Z=92, A=235)
                    try:  # pragma: no cover
                        from smrforge.convenience_utils import (  # pragma: no cover
                            get_nuclide,
                        )

                        nuclide = get_nuclide(name)  # pragma: no cover
                        concentrations[nuclide] = float(conc)  # pragma: no cover
                    except Exception as e:  # pragma: no cover
                        _print_warning(
                            f"Failed to parse nuclide {name}: {e}"
                        )  # pragma: no cover
            else:  # pragma: no cover
                _print_error(
                    "Inventory file must contain 'nuclides' and 'concentrations' fields"
                )  # pragma: no cover
                sys.exit(1)  # pragma: no cover

        elif getattr(args, "nuclides", None):
            # Parse from command line arguments
            for nuclide_spec in args.nuclides:
                if ":" not in nuclide_spec:
                    _print_error(
                        f"Invalid nuclide specification: {nuclide_spec}. Use format: U235:1e20"
                    )
                    sys.exit(1)

                name, conc_str = nuclide_spec.split(":", 1)
                try:
                    from smrforge.convenience_utils import get_nuclide

                    nuclide = get_nuclide(name.strip())
                    concentrations[nuclide] = float(conc_str.strip())
                except Exception as e:  # pragma: no cover
                    _print_error(
                        f"Failed to parse nuclide {name}: {e}"
                    )  # pragma: no cover
                    sys.exit(1)  # pragma: no cover
        else:
            _print_error("Must specify --inventory or --nuclides")
            sys.exit(1)

        if not concentrations:
            _print_error("No valid nuclide concentrations found")  # pragma: no cover
            sys.exit(1)  # pragma: no cover

        _print_info(f"Calculating decay heat for {len(concentrations)} nuclides...")

        # Determine time points
        if getattr(args, "times", None):
            times = np.array([float(t) for t in args.times])  # pragma: no cover
        elif getattr(args, "time_range", None):
            start, end, num_steps = args.time_range  # pragma: no cover
            times = np.linspace(
                float(start), float(end), int(num_steps)
            )  # pragma: no cover
        else:
            # Default: 0 to 1 week with 100 points
            times = np.linspace(0, 7 * 24 * 3600, 100)
            _print_info("Using default time range: 0 to 1 week (100 points)")

        # Calculate decay heat
        result = calculator.calculate_decay_heat(concentrations, times)

        # Prepare output data
        output_data = {
            "times": times.tolist(),
            "times_days": (times / (24 * 3600)).tolist(),
            "total_decay_heat": result.total_decay_heat.tolist(),
            "gamma_decay_heat": result.gamma_decay_heat.tolist(),
            "beta_decay_heat": result.beta_decay_heat.tolist(),
            "nuclide_contributions": {
                str(nuclide): heat.tolist()
                for nuclide, heat in result.nuclide_contributions.items()
            },
        }

        # Save results
        if getattr(args, "output", None):
            with open(args.output, "w") as f:
                json.dump(_to_jsonable(output_data), f, indent=2)
            _print_success(f"Decay heat results saved to {args.output}")

        # Display summary
        if _RICH_AVAILABLE:
            table = Table(title="Decay Heat Summary")  # pragma: no cover
            table.add_column("Time", style="cyan")  # pragma: no cover
            table.add_column("Total [W]", style="green")  # pragma: no cover
            table.add_column("Gamma [W]", style="yellow")  # pragma: no cover
            table.add_column("Beta [W]", style="magenta")  # pragma: no cover

            # Show key time points
            key_times = [0, 3600, 86400, 604800]  # pragma: no cover
            for t_key in key_times:  # pragma: no cover
                if t_key <= times[-1]:  # pragma: no cover
                    idx = np.argmin(np.abs(times - t_key))  # pragma: no cover
                    time_label = (
                        f"{times[idx] / 3600:.1f} h"
                        if times[idx] < 86400
                        else f"{times[idx] / 86400:.1f} d"
                    )  # pragma: no cover
                    table.add_row(  # pragma: no cover
                        time_label,  # pragma: no cover
                        f"{result.total_decay_heat[idx]:.2e}",  # pragma: no cover
                        f"{result.gamma_decay_heat[idx]:.2e}",  # pragma: no cover
                        f"{result.beta_decay_heat[idx]:.2e}",  # pragma: no cover
                    )  # pragma: no cover

            console.print(table)  # pragma: no cover
        else:  # pragma: no cover
            print("\nDecay Heat Summary:")
            print(f"  Initial (t=0): {result.total_decay_heat[0]:.2e} W")
            print(f"  After 1 hour: {result.get_decay_heat_at_time(3600):.2e} W")
            print(f"  After 1 day: {result.get_decay_heat_at_time(86400):.2e} W")
            print(f"  After 1 week: {result.get_decay_heat_at_time(604800):.2e} W")

        # Generate plot
        if getattr(args, "plot", False) or getattr(args, "plot_output", None):
            try:  # pragma: no cover
                backend = getattr(args, "backend", "plotly")  # pragma: no cover

                if backend == "plotly":  # pragma: no cover
                    try:  # pragma: no cover
                        import plotly.graph_objects as go  # pragma: no cover
                        from plotly.subplots import make_subplots  # pragma: no cover

                        fig = make_subplots(  # pragma: no cover
                            rows=2,
                            cols=1,  # pragma: no cover
                            subplot_titles=(
                                "Total Decay Heat",
                                "Gamma vs Beta Decay Heat",
                            ),  # pragma: no cover
                            shared_xaxes=True,  # pragma: no cover
                            vertical_spacing=0.1,  # pragma: no cover
                        )  # pragma: no cover

                        times_days = times / (24 * 3600)  # pragma: no cover

                        # Total decay heat
                        fig.add_trace(  # pragma: no cover
                            go.Scatter(  # pragma: no cover
                                x=times_days,  # pragma: no cover
                                y=result.total_decay_heat,  # pragma: no cover
                                mode="lines",  # pragma: no cover
                                name="Total",  # pragma: no cover
                                line=dict(width=2, color="blue"),  # pragma: no cover
                            ),  # pragma: no cover
                            row=1,
                            col=1,  # pragma: no cover
                        )  # pragma: no cover

                        # Gamma and beta
                        fig.add_trace(  # pragma: no cover
                            go.Scatter(  # pragma: no cover
                                x=times_days,  # pragma: no cover
                                y=result.gamma_decay_heat,  # pragma: no cover
                                mode="lines",  # pragma: no cover
                                name="Gamma",  # pragma: no cover
                                line=dict(width=2, color="red"),  # pragma: no cover
                            ),  # pragma: no cover
                            row=2,
                            col=1,  # pragma: no cover
                        )  # pragma: no cover

                        fig.add_trace(  # pragma: no cover
                            go.Scatter(  # pragma: no cover
                                x=times_days,  # pragma: no cover
                                y=result.beta_decay_heat,  # pragma: no cover
                                mode="lines",  # pragma: no cover
                                name="Beta",  # pragma: no cover
                                line=dict(width=2, color="green"),  # pragma: no cover
                            ),  # pragma: no cover
                            row=2,
                            col=1,  # pragma: no cover
                        )  # pragma: no cover

                        fig.update_xaxes(
                            title_text="Time [days]", row=2, col=1
                        )  # pragma: no cover
                        fig.update_yaxes(
                            title_text="Decay Heat [W]", row=1, col=1
                        )  # pragma: no cover
                        fig.update_yaxes(
                            title_text="Decay Heat [W]", row=2, col=1
                        )  # pragma: no cover
                        fig.update_layout(  # pragma: no cover
                            title="Decay Heat Over Time",  # pragma: no cover
                            height=700,  # pragma: no cover
                            hovermode="x unified",  # pragma: no cover
                        )  # pragma: no cover

                        if getattr(args, "plot_output", None):  # pragma: no cover
                            plot_path = args.plot_output  # pragma: no cover
                            if plot_path.suffix == ".html":  # pragma: no cover
                                fig.write_html(str(plot_path))  # pragma: no cover
                            else:  # pragma: no cover
                                fig.write_image(str(plot_path))  # pragma: no cover
                            _print_success(
                                f"Plot saved to {plot_path}"
                            )  # pragma: no cover
                        else:  # pragma: no cover
                            fig.show()  # pragma: no cover
                    except ImportError:  # pragma: no cover
                        _print_error(
                            "Plotly not available. Install: pip install plotly"
                        )  # pragma: no cover
                else:  # pragma: no cover
                    import matplotlib.pyplot as plt  # pragma: no cover

                    fig, (ax1, ax2) = plt.subplots(
                        2, 1, figsize=(10, 8)
                    )  # pragma: no cover
                    times_days = times / (24 * 3600)  # pragma: no cover

                    # Total decay heat
                    ax1.plot(
                        times_days,
                        result.total_decay_heat,
                        "b-",
                        linewidth=2,
                        label="Total",
                    )  # pragma: no cover
                    ax1.set_ylabel("Decay Heat [W]")  # pragma: no cover
                    ax1.set_title("Total Decay Heat")  # pragma: no cover
                    ax1.grid(True, alpha=0.3)  # pragma: no cover
                    ax1.legend()  # pragma: no cover
                    ax1.set_yscale("log")  # pragma: no cover

                    # Gamma and beta
                    ax2.plot(
                        times_days,
                        result.gamma_decay_heat,
                        "r-",
                        linewidth=2,
                        label="Gamma",
                    )  # pragma: no cover
                    ax2.plot(
                        times_days,
                        result.beta_decay_heat,
                        "g-",
                        linewidth=2,
                        label="Beta",
                    )  # pragma: no cover
                    ax2.set_xlabel("Time [days]")  # pragma: no cover
                    ax2.set_ylabel("Decay Heat [W]")  # pragma: no cover
                    ax2.set_title("Gamma vs Beta Decay Heat")  # pragma: no cover
                    ax2.grid(True, alpha=0.3)  # pragma: no cover
                    ax2.legend()  # pragma: no cover
                    ax2.set_yscale("log")  # pragma: no cover

                    plt.tight_layout()  # pragma: no cover

                    if getattr(args, "plot_output", None):  # pragma: no cover
                        plot_path = args.plot_output  # pragma: no cover
                        fig.savefig(
                            plot_path, format=args.format, dpi=300, bbox_inches="tight"
                        )  # pragma: no cover
                        _print_success(f"Plot saved to {plot_path}")  # pragma: no cover
                        plt.close(fig)  # pragma: no cover
                    else:  # pragma: no cover
                        plt.show()  # pragma: no cover
            except ImportError as e:  # pragma: no cover
                _print_error(f"Failed to generate plot: {e}")  # pragma: no cover
                _print_info(
                    "Install matplotlib or plotly for plotting support"
                )  # pragma: no cover

    except ImportError as e:
        _print_error(f"Failed to import decay heat modules: {e}")  # pragma: no cover
        sys.exit(1)  # pragma: no cover
    except Exception as e:
        _print_error(f"Failed to calculate decay heat: {e}")  # pragma: no cover
        if getattr(args, "verbose", False):  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover


# GitHub Actions: feature IDs and metadata (must match scripts/github_workflow_check.py)
GITHUB_ACTIONS_FEATURES = [
    {
        "id": "ci",
        "name": "CI",
        "description": "Tests, lint, build, validation, coverage",
    },
    {
        "id": "ci-quick",
        "name": "CI (quick)",
        "description": "Fast check: single Python, tests without coverage",
    },
    {
        "id": "docs",
        "name": "Docs",
        "description": "Build and deploy documentation (GitHub Pages)",
    },
    {
        "id": "performance",
        "name": "Performance",
        "description": "Performance benchmarks",
    },
    {
        "id": "security",
        "name": "Security",
        "description": "Security audit (pip-audit, bandit)",
    },
    {
        "id": "release",
        "name": "Release",
        "description": "Build and publish to PyPI on version tags",
    },
    {
        "id": "nightly",
        "name": "Nightly",
        "description": "Scheduled full test and validation run",
    },
    {
        "id": "docker",
        "name": "Docker",
        "description": "Build and push container image (GHCR)",
    },
    {
        "id": "dependabot",
        "name": "Dependabot",
        "description": "Run tests on Dependabot dependency PRs",
    },
    {
        "id": "stale",
        "name": "Stale",
        "description": "Mark and close stale issues and PRs",
    },
]


