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

        # Load reactor
        if not args.reactor.exists():
            _print_error(f"Reactor file not found: {args.reactor}")
            sys.exit(1)
            return  # ensure we don't fall through when exit is mocked

        with open(args.reactor) as f:
            reactor_data = json.load(f)

        reactor = create_reactor(**reactor_data)
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
        _print_error(f"Failed to import visualization modules: {e}")  # pragma: no cover
        sys.exit(1)  # pragma: no cover
        return  # pragma: no cover
    except Exception as e:  # pragma: no cover
        _print_error(f"Failed to visualize geometry: {e}")  # pragma: no cover
        if args.verbose if hasattr(args, "verbose") else False:  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover
        return  # pragma: no cover




def visualize_tally(args):
    """Visualize OpenMC mesh tally from statepoint. Pro tier only."""
    try:
        from smrforge_pro.visualization.openmc_tally_viz import visualize_openmc_tallies
    except ImportError:
        _print_error(
            "OpenMC tally visualization requires SMRForge Pro. "
            "pip install smrforge-pro[openmc]"
        )
        sys.exit(1)
    statepoint = Path(getattr(args, "statepoint", None) or "")
    if not statepoint.exists():
        _print_error(f"Statepoint not found: {statepoint}")
        sys.exit(1)
    try:
        fig = visualize_openmc_tallies(
            statepoint,
            tally_id=getattr(args, "tally_id", None),
            score=getattr(args, "score", None),
            output_path=getattr(args, "output", None),
            backend=getattr(args, "backend", "plotly"),
            show_uncertainty=not getattr(args, "no_uncertainty", False),
        )
        if fig is not None:
            _print_success("Tally visualization complete")
    except Exception as e:
        _print_error(f"Tally visualization failed: {e}")
        sys.exit(1)




def visualize_flux(args):
    """Plot flux distribution."""
    try:
        import json

        from smrforge.visualization.geometry import plot_flux_on_geometry

        # Load results
        if not args.results.exists():
            _print_error(f"Results file not found: {args.results}")
            sys.exit(1)

        with open(args.results) as f:
            results_data = json.load(f)

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
        _print_error(f"Failed to import visualization modules: {e}")  # pragma: no cover
        sys.exit(1)  # pragma: no cover
    except Exception as e:
        _print_error(f"Failed to visualize flux: {e}")
        if args.verbose if hasattr(args, "verbose") else False:
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)




def burnup_visualize(args):
    """Visualize burnup results."""
    try:
        import json

        import numpy as np

        # Load results
        if not args.results.exists():
            _print_error(f"Results file not found: {args.results}")
            sys.exit(1)

        results_path = args.results
        results_format = results_path.suffix.lower()

        _print_info(f"Loading burnup results from {results_path}...")

        # Load data based on format
        if results_format in [".json"]:
            with open(results_path) as f:
                results_data = json.load(f)
        elif results_format in [".h5", ".hdf5"]:
            try:
                import h5py

                with h5py.File(results_path, "r") as f:  # pragma: no cover
                    # Convert HDF5 groups to dict (simplified)
                    results_data = {}  # pragma: no cover
                    for key in f.keys():  # pragma: no cover
                        if isinstance(f[key], h5py.Group):  # pragma: no cover
                            results_data[key] = {
                                k: v[()] if hasattr(v, "__getitem__") else v
                                for k, v in f[key].items()
                            }  # pragma: no cover
                        else:  # pragma: no cover
                            results_data[key] = f[key][()]  # pragma: no cover
            except ImportError:
                _print_error(
                    "HDF5 support not available. Install h5py: pip install h5py"
                )
                sys.exit(1)
        else:
            _print_error(f"Unsupported file format: {results_format}")
            print("Supported formats: json, h5, hdf5")
            sys.exit(1)

        _print_info("Generating burnup visualization...")

        # Determine what to plot
        plot_types = []
        if args.composition or (
            not args.keff and not args.burnup and not args.composition
        ):
            plot_types.append("composition")
        if args.keff:
            plot_types.append("keff")
        if args.burnup:
            plot_types.append("burnup")

        # Plot k-eff evolution
        if "keff" in plot_types:
            if "k_eff" in results_data or "k_eff_values" in results_data:
                try:
                    import matplotlib.pyplot as plt

                    # Extract k-eff data
                    if "k_eff_values" in results_data:
                        k_eff_data = results_data["k_eff_values"]
                        time_steps = results_data.get(
                            "time_steps", list(range(len(k_eff_data)))
                        )
                    elif "k_eff" in results_data:  # pragma: no cover
                        k_eff_data = results_data["k_eff"]  # pragma: no cover
                        if isinstance(k_eff_data, list):  # pragma: no cover
                            time_steps = results_data.get(
                                "time_steps", list(range(len(k_eff_data)))
                            )  # pragma: no cover
                        else:  # pragma: no cover
                            k_eff_data = [k_eff_data]  # pragma: no cover
                            time_steps = [0]  # pragma: no cover
                    else:  # pragma: no cover
                        k_eff_data = []  # pragma: no cover

                    if k_eff_data:
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ax.plot(
                            time_steps, k_eff_data, "b-o", linewidth=2, markersize=6
                        )
                        ax.axhline(
                            y=1.0, color="r", linestyle="--", label="Critical (k=1.0)"
                        )
                        ax.set_xlabel("Time [days]", fontsize=12)
                        ax.set_ylabel("k-eff", fontsize=12)
                        ax.set_title(
                            "k-eff Evolution Over Time", fontsize=14, fontweight="bold"
                        )
                        ax.grid(True, alpha=0.3)
                        ax.legend()
                        plt.tight_layout()

                        if args.output:
                            output_path = Path(args.output)
                            if "keff" not in str(output_path.name).lower():
                                stem = output_path.stem  # pragma: no cover
                                suffix = output_path.suffix  # pragma: no cover
                                output_path = (
                                    output_path.parent / f"{stem}_keff{suffix}"
                                )  # pragma: no cover
                            fig.savefig(
                                output_path,
                                format=args.format,
                                dpi=300,
                                bbox_inches="tight",
                            )
                            _print_success(f"k-eff plot saved to {output_path}")
                            plt.close(fig)
                        else:
                            plt.show()  # pragma: no cover
                    else:  # pragma: no cover
                        _print_info(
                            "No k-eff data found in results file"
                        )  # pragma: no cover
                except ImportError:  # pragma: no cover
                    _print_error(
                        "Matplotlib not available. Install matplotlib: pip install matplotlib"
                    )  # pragma: no cover
            else:
                _print_info("No k-eff data found in results file")
                _print_info("Use Python API to include k-eff in burnup results")

        # Plot burnup over time
        if "burnup" in plot_types:
            if "burnup" in results_data or "burnup_values" in results_data:
                try:
                    import matplotlib.pyplot as plt

                    # Extract burnup data
                    if "burnup_values" in results_data:
                        burnup_data = results_data["burnup_values"]
                        time_steps = results_data.get(
                            "time_steps", list(range(len(burnup_data)))
                        )
                    elif "burnup" in results_data:
                        burnup_data = results_data["burnup"]
                        if isinstance(burnup_data, list):
                            time_steps = results_data.get(
                                "time_steps", list(range(len(burnup_data)))
                            )
                        else:
                            burnup_data = [burnup_data]  # pragma: no cover
                            time_steps = [0]  # pragma: no cover
                    else:  # pragma: no cover
                        burnup_data = []  # pragma: no cover

                    if burnup_data:
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ax.plot(
                            time_steps, burnup_data, "g-s", linewidth=2, markersize=6
                        )
                        ax.set_xlabel("Time [days]", fontsize=12)
                        ax.set_ylabel("Burnup [MWd/kgU]", fontsize=12)
                        ax.set_title("Burnup Over Time", fontsize=14, fontweight="bold")
                        ax.grid(True, alpha=0.3)
                        plt.tight_layout()

                        if args.output:
                            output_path = Path(args.output)
                            if "burnup" not in str(output_path.name).lower():
                                stem = output_path.stem  # pragma: no cover
                                suffix = output_path.suffix  # pragma: no cover
                                output_path = (
                                    output_path.parent / f"{stem}_burnup{suffix}"
                                )  # pragma: no cover
                            fig.savefig(
                                output_path,
                                format=args.format,
                                dpi=300,
                                bbox_inches="tight",
                            )
                            _print_success(f"Burnup plot saved to {output_path}")
                            plt.close(fig)
                        else:
                            plt.show()  # pragma: no cover
                    else:  # pragma: no cover
                        _print_info(
                            "No burnup data found in results file"
                        )  # pragma: no cover
                except ImportError:
                    _print_error(
                        "Matplotlib not available. Install matplotlib: pip install matplotlib"
                    )  # pragma: no cover
            else:  # pragma: no cover
                _print_info("No burnup data found in results file")  # pragma: no cover
                _print_info(
                    "Use Python API to include burnup data in results"
                )  # pragma: no cover

        # Plot composition (note: requires inventory and geometry, use Python API)
        if "composition" in plot_types:
            _print_info(
                "NOTE: Composition plotting requires inventory data and geometry"
            )
            _print_info("Use Python API for full composition visualization:")
            print(
                "  from smrforge.visualization.material_composition import plot_burnup_composition"
            )
            print("  from smrforge.core.reactor_core import Nuclide")
            print("  fig = plot_burnup_composition(inventory, geometry, nuclides)")

        # Enhanced visualization features
        backend = getattr(args, "backend", "plotly")

        # Batch comparison
        if getattr(args, "batch_comparison", False):
            try:
                from smrforge.burnup.visualization import plot_batch_comparison

                # Load batch inventories
                batch_inventories = {}
                if getattr(args, "batch_results", None):
                    for batch_file in args.batch_results:
                        if not batch_file.exists():  # pragma: no cover
                            _print_error(
                                f"Batch results file not found: {batch_file}"
                            )  # pragma: no cover
                            continue  # pragma: no cover

                        with open(batch_file) as f:  # pragma: no cover
                            batch_data = json.load(f)  # pragma: no cover

                        # Try to extract inventory from results
                        # This assumes results contain inventory-like data
                        if "inventory" in batch_data:  # pragma: no cover
                            batch_inventories[len(batch_inventories)] = batch_data[
                                "inventory"
                            ]  # pragma: no cover
                        elif (
                            "nuclides" in batch_data and "concentrations" in batch_data
                        ):  # pragma: no cover
                            # Create a simple inventory-like object
                            class SimpleInventory:  # pragma: no cover
                                def __init__(self, data):  # pragma: no cover
                                    self.times = data.get(
                                        "times", [0]
                                    )  # pragma: no cover
                                    self.burnup = data.get(
                                        "burnup", [0]
                                    )  # pragma: no cover
                                    self.nuclides = data.get(
                                        "nuclides", []
                                    )  # pragma: no cover
                                    self.concentrations = data.get(
                                        "concentrations", []
                                    )  # pragma: no cover

                            batch_inventories[len(batch_inventories)] = SimpleInventory(
                                batch_data
                            )  # pragma: no cover

                if batch_inventories:  # pragma: no cover
                    fig = plot_batch_comparison(
                        batch_inventories, backend=backend
                    )  # pragma: no cover

                    if args.output:  # pragma: no cover
                        output_path = Path(args.output)  # pragma: no cover
                        if (
                            "batch" not in str(output_path.name).lower()
                        ):  # pragma: no cover
                            stem = output_path.stem  # pragma: no cover
                            suffix = output_path.suffix  # pragma: no cover
                            output_path = (
                                output_path.parent / f"{stem}_batch_comparison{suffix}"
                            )  # pragma: no cover

                        if backend == "plotly":  # pragma: no cover
                            (
                                fig.write_html(str(output_path))
                                if output_path.suffix == ".html"
                                else fig.write_image(str(output_path))
                            )  # pragma: no cover
                        else:  # pragma: no cover
                            fig[0].savefig(
                                output_path,
                                format=args.format,
                                dpi=300,
                                bbox_inches="tight",
                            )  # pragma: no cover

                        _print_success(
                            f"Batch comparison plot saved to {output_path}"
                        )  # pragma: no cover
                    else:  # pragma: no cover
                        if backend == "plotly":  # pragma: no cover
                            fig.show()  # pragma: no cover
                        else:  # pragma: no cover
                            import matplotlib.pyplot as plt  # pragma: no cover

                            plt.show()  # pragma: no cover
                else:  # pragma: no cover
                    _print_info(
                        "No batch data found. Use --batch-results to specify batch result files."
                    )  # pragma: no cover
            except ImportError as e:
                _print_error(
                    f"Failed to import batch comparison visualization: {e}"
                )  # pragma: no cover

        # Refueling cycles
        if getattr(args, "refueling_cycles", False):  # pragma: no cover
            try:  # pragma: no cover
                from smrforge.burnup.visualization import (  # pragma: no cover
                    plot_refueling_cycles,
                )

                _print_info(
                    "Refueling cycle visualization requires cycle inventory data"
                )  # pragma: no cover
                _print_info(
                    "Use Python API for full refueling cycle visualization:"
                )  # pragma: no cover
                print(
                    "  from smrforge.burnup.visualization import plot_refueling_cycles"
                )  # pragma: no cover
                print(
                    "  fig = plot_refueling_cycles(cycle_inventories, backend='plotly')"
                )  # pragma: no cover
            except ImportError as e:  # pragma: no cover
                _print_error(
                    f"Failed to import refueling cycle visualization: {e}"
                )  # pragma: no cover

        # Control rod effects
        if getattr(args, "control_rod_effects", False):  # pragma: no cover
            try:  # pragma: no cover
                from smrforge.burnup.visualization import (  # pragma: no cover
                    plot_control_rod_effects,
                )

                # Load with-rods inventory from main results
                with_rods_inventory = None  # pragma: no cover
                if "inventory" in results_data:  # pragma: no cover
                    with_rods_inventory = results_data["inventory"]  # pragma: no cover
                elif "nuclides" in results_data:  # pragma: no cover

                    class SimpleInventory:  # pragma: no cover
                        def __init__(self, data):  # pragma: no cover
                            self.times = data.get("times", [0])  # pragma: no cover
                            self.burnup = data.get("burnup", [0])  # pragma: no cover
                            self.nuclides = data.get("nuclides", [])  # pragma: no cover
                            self.concentrations = data.get(
                                "concentrations", []
                            )  # pragma: no cover

                    with_rods_inventory = SimpleInventory(
                        results_data
                    )  # pragma: no cover

                # Load without-rods inventory if provided
                without_rods_inventory = None  # pragma: no cover
                if getattr(args, "without_rods_results", None):  # pragma: no cover
                    without_rods_path = args.without_rods_results  # pragma: no cover
                    if without_rods_path.exists():  # pragma: no cover
                        with open(without_rods_path) as f:  # pragma: no cover
                            without_rods_data = json.load(f)  # pragma: no cover

                        if "inventory" in without_rods_data:  # pragma: no cover
                            without_rods_inventory = without_rods_data[
                                "inventory"
                            ]  # pragma: no cover
                        elif "nuclides" in without_rods_data:  # pragma: no cover

                            class SimpleInventory:  # pragma: no cover
                                def __init__(self, data):  # pragma: no cover
                                    self.times = data.get(
                                        "times", [0]
                                    )  # pragma: no cover
                                    self.burnup = data.get(
                                        "burnup", [0]
                                    )  # pragma: no cover
                                    self.nuclides = data.get(
                                        "nuclides", []
                                    )  # pragma: no cover
                                    self.concentrations = data.get(
                                        "concentrations", []
                                    )  # pragma: no cover

                            without_rods_inventory = SimpleInventory(
                                without_rods_data
                            )  # pragma: no cover

                if with_rods_inventory:  # pragma: no cover
                    fig = plot_control_rod_effects(  # pragma: no cover
                        with_rods_inventory,  # pragma: no cover
                        without_rods_inventory,  # pragma: no cover
                        backend=backend,  # pragma: no cover
                    )  # pragma: no cover

                    if args.output:  # pragma: no cover
                        output_path = Path(args.output)  # pragma: no cover
                        if (
                            "control_rod" not in str(output_path.name).lower()
                        ):  # pragma: no cover
                            stem = output_path.stem  # pragma: no cover
                            suffix = output_path.suffix  # pragma: no cover
                            output_path = (
                                output_path.parent / f"{stem}_control_rods{suffix}"
                            )  # pragma: no cover

                        if backend == "plotly":  # pragma: no cover
                            (
                                fig.write_html(str(output_path))
                                if output_path.suffix == ".html"
                                else fig.write_image(str(output_path))
                            )  # pragma: no cover
                        else:  # pragma: no cover
                            fig[0].savefig(
                                output_path,
                                format=args.format,
                                dpi=300,
                                bbox_inches="tight",
                            )  # pragma: no cover

                        _print_success(
                            f"Control rod effects plot saved to {output_path}"
                        )  # pragma: no cover
                    else:  # pragma: no cover
                        if backend == "plotly":  # pragma: no cover
                            fig.show()  # pragma: no cover
                        else:  # pragma: no cover
                            import matplotlib.pyplot as plt  # pragma: no cover

                            plt.show()  # pragma: no cover
                else:  # pragma: no cover
                    _print_info(
                        "No inventory data found in results file for control rod effects visualization"
                    )  # pragma: no cover
            except ImportError as e:  # pragma: no cover
                _print_error(
                    f"Failed to import control rod effects visualization: {e}"
                )  # pragma: no cover

        # Enhanced dashboard
        if getattr(args, "dashboard", False):  # pragma: no cover
            try:  # pragma: no cover
                from smrforge.burnup.visualization import (  # pragma: no cover
                    plot_burnup_dashboard_enhanced,
                )

                # Load inventory from results
                inventory = None  # pragma: no cover
                if "inventory" in results_data:  # pragma: no cover
                    inventory = results_data["inventory"]  # pragma: no cover
                elif "nuclides" in results_data:  # pragma: no cover

                    class SimpleInventory:  # pragma: no cover
                        def __init__(self, data):  # pragma: no cover
                            self.times = data.get("times", [0])  # pragma: no cover
                            self.burnup = data.get("burnup", [0])  # pragma: no cover
                            self.nuclides = data.get("nuclides", [])  # pragma: no cover
                            self.concentrations = data.get(
                                "concentrations", []
                            )  # pragma: no cover

                    inventory = SimpleInventory(results_data)  # pragma: no cover

                # Load batch inventories if provided
                batch_inventories = None  # pragma: no cover
                if getattr(args, "batch_results", None):  # pragma: no cover
                    batch_inventories = {}  # pragma: no cover
                    for batch_file in args.batch_results:  # pragma: no cover
                        if batch_file.exists():  # pragma: no cover
                            with open(batch_file) as f:  # pragma: no cover
                                batch_data = json.load(f)  # pragma: no cover
                            if (
                                "inventory" in batch_data or "nuclides" in batch_data
                            ):  # pragma: no cover
                                if "inventory" in batch_data:  # pragma: no cover
                                    batch_inventories[len(batch_inventories)] = (
                                        batch_data["inventory"]
                                    )  # pragma: no cover
                                else:  # pragma: no cover

                                    class SimpleInventory:  # pragma: no cover
                                        def __init__(self, data):  # pragma: no cover
                                            self.times = data.get(
                                                "times", [0]
                                            )  # pragma: no cover
                                            self.burnup = data.get(
                                                "burnup", [0]
                                            )  # pragma: no cover
                                            self.nuclides = data.get(
                                                "nuclides", []
                                            )  # pragma: no cover
                                            self.concentrations = data.get(
                                                "concentrations", []
                                            )  # pragma: no cover

                                    batch_inventories[len(batch_inventories)] = (
                                        SimpleInventory(batch_data)
                                    )  # pragma: no cover

                if inventory:  # pragma: no cover
                    fig = plot_burnup_dashboard_enhanced(  # pragma: no cover
                        inventory,  # pragma: no cover
                        batch_inventories,  # pragma: no cover
                        backend=backend,  # pragma: no cover
                    )  # pragma: no cover

                    if args.output:  # pragma: no cover
                        output_path = Path(args.output)  # pragma: no cover
                        if (
                            "dashboard" not in str(output_path.name).lower()
                        ):  # pragma: no cover
                            stem = output_path.stem  # pragma: no cover
                            suffix = output_path.suffix  # pragma: no cover
                            output_path = (
                                output_path.parent / f"{stem}_dashboard{suffix}"
                            )  # pragma: no cover

                        if backend == "plotly":  # pragma: no cover
                            (
                                fig.write_html(str(output_path))
                                if output_path.suffix == ".html"
                                else fig.write_image(str(output_path))
                            )  # pragma: no cover
                        else:  # pragma: no cover
                            fig[0].savefig(
                                output_path,
                                format=args.format,
                                dpi=300,
                                bbox_inches="tight",
                            )  # pragma: no cover

                        _print_success(
                            f"Enhanced dashboard saved to {output_path}"
                        )  # pragma: no cover
                    else:  # pragma: no cover
                        if backend == "plotly":  # pragma: no cover
                            fig.show()  # pragma: no cover
                        else:  # pragma: no cover
                            import matplotlib.pyplot as plt  # pragma: no cover

                            plt.show()  # pragma: no cover
                else:  # pragma: no cover
                    _print_info(
                        "No inventory data found in results file for dashboard visualization"
                    )  # pragma: no cover
            except ImportError as e:  # pragma: no cover
                _print_error(
                    f"Failed to import enhanced dashboard visualization: {e}"
                )  # pragma: no cover

    except ImportError as e:
        _print_error(f"Failed to import visualization modules: {e}")  # pragma: no cover
        sys.exit(1)  # pragma: no cover
    except Exception as e:
        _print_error(f"Failed to visualize burnup results: {e}")
        if args.verbose if hasattr(args, "verbose") else False:
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)


