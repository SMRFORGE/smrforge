"""
Burnup command handlers: burnup_run, burnup_visualize.
"""

import json
import sys
from pathlib import Path

from smrforge.cli.common import (
    Table,
    _RICH_AVAILABLE,
    _print_error,
    _print_info,
    _print_success,
    _print_warning,
    _to_jsonable,
    console,
)

import numpy as np


def burnup_run(args):
    """Run burnup/depletion calculation."""
    try:
        import json

        import numpy as np

        from smrforge.burnup import BurnupOptions, BurnupSolver
        from smrforge.convenience import create_reactor
        from smrforge.neutronics.solver import MultiGroupDiffusion
        from smrforge.validation.models import CrossSectionData, SolverOptions

        # Load reactor
        if args.reactor:
            if not args.reactor.exists():
                _print_error(f"Reactor file not found: {args.reactor}")
                sys.exit(1)
                return  # ensure we don't fall through when exit is mocked

            with open(args.reactor) as f:
                reactor_data = json.load(f)

            reactor = create_reactor(**reactor_data)
        else:
            _print_error("Must specify --reactor FILE")
            sys.exit(1)
            return  # ensure we don't fall through when exit is mocked

        # Parse time steps
        if args.time_steps:
            time_steps = [float(t) for t in args.time_steps]
        else:
            time_steps = [0, 365, 730, 1095]  # pragma: no cover

        # Create burnup options with checkpointing support
        burnup_options = BurnupOptions(
            time_steps=time_steps,
            power_density=args.power_density or 1e6,
            adaptive_tracking=args.adaptive_tracking,
            nuclide_threshold=args.nuclide_threshold or 1e15,
            checkpoint_interval=args.checkpoint_interval,
            checkpoint_dir=args.checkpoint_dir,
        )

        _print_info(f"Running burnup calculation...")
        _print_info(f"  Time steps: {time_steps} days")
        _print_info(f"  Power density: {burnup_options.power_density:.2e} W/cm³")
        _print_info(f"  Adaptive tracking: {burnup_options.adaptive_tracking}")
        if args.checkpoint_interval:
            _print_info(
                f"  Checkpoint interval: {args.checkpoint_interval} days"
            )  # pragma: no cover
            _print_info(
                f"  Checkpoint directory: {args.checkpoint_dir or 'checkpoints/'}"
            )  # pragma: no cover
        if args.resume_from:
            _print_info(
                f"  Resuming from checkpoint: {args.resume_from}"
            )  # pragma: no cover

        _print_info(
            "\nNOTE: Burnup calculation requires geometry and cross-section data."
        )
        _print_info("For full burnup calculations, use the Python API:")
        print("  from smrforge.burnup import BurnupSolver, BurnupOptions")
        print("  burnup = BurnupSolver(neutronics_solver, burnup_options)")
        if args.resume_from:
            print(
                f"  inventory = burnup.resume_from_checkpoint('{args.resume_from}')"
            )  # pragma: no cover
        else:  # pragma: no cover
            print("  inventory = burnup.solve()")

        # Save options if output specified
        if args.output:
            output_path = Path(args.output)
            options_dict = {
                "time_steps": time_steps,
                "power_density": float(burnup_options.power_density),
                "adaptive_tracking": burnup_options.adaptive_tracking,
                "nuclide_threshold": float(burnup_options.nuclide_threshold),
            }
            with open(output_path, "w") as f:
                json.dump(_to_jsonable(options_dict), f, indent=2)
            _print_success(f"Burnup options saved to {output_path}")

    except ImportError as e:  # pragma: no cover
        _print_error(f"Failed to import burnup modules: {e}")  # pragma: no cover
        sys.exit(1)  # pragma: no cover
        return  # pragma: no cover
    except Exception as e:  # pragma: no cover
        _print_error(f"Failed to run burnup calculation: {e}")  # pragma: no cover
        if args.verbose if hasattr(args, "verbose") else False:  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover
        return  # pragma: no cover


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
