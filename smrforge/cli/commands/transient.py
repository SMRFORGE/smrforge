"""SMRForge CLI command handlers."""

import json
import sys

import numpy as np
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

def transient_run(args):
    """Run transient analysis using simplified API."""
    try:
        from smrforge.convenience.transients import quick_transient

        kwargs = {
            "power": args.power,
            "temperature": args.temperature,
            "transient_type": args.type,
            "duration": args.duration,
            "scram_available": args.scram_available,
            "scram_delay": args.scram_delay,
        }

        if args.reactivity is not None:
            kwargs["reactivity_insertion"] = args.reactivity

        if args.long_term:
            kwargs["long_term_optimization"] = True

        # Add plotting options
        if args.plot:
            kwargs["plot"] = True
        if args.plot_output:
            kwargs["plot_output"] = str(args.plot_output)
            kwargs["plot"] = True  # Enable plotting if output specified
        kwargs["plot_backend"] = args.plot_backend

        _print_info(f"Running {args.type} transient analysis...")
        _print_info(f"  Power: {args.power/1e6:.2f} MWth")
        _print_info(f"  Temperature: {args.temperature:.1f} K")
        _print_info(f"  Duration: {args.duration:.1f} s")

        result = quick_transient(**kwargs)

        _print_success("Transient analysis complete")

        # Print summary
        peak_power = np.max(result["power"])
        final_power = result["power"][-1]
        peak_temp = np.max(result["T_fuel"])
        final_temp = result["T_fuel"][-1]

        if _RICH_AVAILABLE:
            table = Table(title="Transient Results Summary")  # pragma: no cover
            table.add_column("Metric", style="cyan")  # pragma: no cover
            table.add_column("Value", style="magenta")  # pragma: no cover
            table.add_row("Peak Power", f"{peak_power/1e6:.2f} MW")  # pragma: no cover
            table.add_row(
                "Final Power", f"{final_power/1e6:.2f} MW"
            )  # pragma: no cover
            table.add_row(
                "Peak Temperature", f"{peak_temp:.1f} K ({peak_temp-273:.1f}°C)"
            )  # pragma: no cover
            table.add_row(
                "Final Temperature", f"{final_temp:.1f} K ({final_temp-273:.1f}°C)"
            )  # pragma: no cover
            console.print(table)  # pragma: no cover
        else:
            print("\nTransient Results Summary:")
            print(f"  Peak Power: {peak_power/1e6:.2f} MW")
            print(f"  Final Power: {final_power/1e6:.2f} MW")
            print(f"  Peak Temperature: {peak_temp:.1f} K ({peak_temp-273:.1f}°C)")
            print(f"  Final Temperature: {final_temp:.1f} K ({final_temp-273:.1f}°C)")

        # Save results if output specified
        if args.output:
            output_data = {
                "transient_type": args.type,
                "time": result["time"].tolist(),
                "power": result["power"].tolist(),
                "T_fuel": result["T_fuel"].tolist(),
                "T_moderator": result["T_moderator"].tolist(),
                "reactivity": (
                    result.get("reactivity", result.get("rho_external", [])).tolist()
                    if isinstance(result.get("reactivity"), np.ndarray)
                    else None
                ),
            }

            with open(args.output, "w") as f:
                json.dump(_to_jsonable(output_data), f, indent=2)
            _print_success(f"Results saved to {args.output}")

    except Exception as e:
        _print_error(f"Transient analysis failed: {e}")
        if args.verbose:
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)


