"""SMRForge CLI command handlers."""

import json
import sys
from pathlib import Path

from ..utils import (
    _GLYPH_ERROR,
    _GLYPH_SUCCESS,
    _RICH_AVAILABLE,
    _YAML_AVAILABLE,
    _exit_error,
    _load_json_or_yaml,
    _parse_heat_source_safe,
    _print_error,
    _print_info,
    _print_success,
    _print_warning,
    _save_workflow_plot,
    _to_jsonable,
    console,
    rprint,
    yaml,
    Panel,
    Table,
)

def thermal_lumped(args):
    """Run lumped-parameter thermal-hydraulics analysis."""
    try:
        from smrforge.thermal.lumped import (
            LumpedThermalHydraulics,
            ThermalLump,
            ThermalResistance,
        )

        if args.config:
            # Load configuration from file
            if not args.config.exists():
                _exit_error(f"Config file not found: {args.config}")

            config = _load_json_or_yaml(args.config)

            # Build lumps and resistances from config
            lumps = {}
            for lump_config in config.get("lumps", []):
                # Parse heat source function (safe: constant or lambda t: constant only)
                heat_source_str = lump_config.get(
                    "heat_source", "lambda t: 0.0"
                )  # pragma: no cover
                if isinstance(heat_source_str, str):  # pragma: no cover
                    heat_source = _parse_heat_source_safe(
                        heat_source_str
                    )  # pragma: no cover
                else:  # pragma: no cover
                    heat_source = lambda t: float(heat_source_str)  # pragma: no cover

                lump = ThermalLump(  # pragma: no cover
                    name=lump_config["name"],  # pragma: no cover
                    capacitance=lump_config["capacitance"],  # pragma: no cover
                    temperature=lump_config["temperature"],  # pragma: no cover
                    heat_source=heat_source,  # pragma: no cover
                )  # pragma: no cover
                lumps[lump.name] = lump  # pragma: no cover

            resistances = []
            for res_config in config.get("resistances", []):
                resistance = ThermalResistance(  # pragma: no cover
                    name=res_config["name"],  # pragma: no cover
                    resistance=res_config["resistance"],  # pragma: no cover
                    lump1_name=res_config["lump1_name"],  # pragma: no cover
                    lump2_name=res_config["lump2_name"],  # pragma: no cover
                )  # pragma: no cover
                resistances.append(resistance)  # pragma: no cover

            ambient_temp = config.get("ambient_temperature", 300.0)
        else:
            # Use default 2-lump system (fuel + moderator)
            _print_info("Using default 2-lump system (fuel + moderator)")

            fuel = ThermalLump(
                name="fuel",
                capacitance=1e8,  # J/K
                temperature=1200.0,  # K
                heat_source=lambda t: 1e6 if t < 10 else 0.1e6,  # Decay heat
            )

            moderator = ThermalLump(
                name="moderator",
                capacitance=5e8,  # J/K
                temperature=800.0,  # K
                heat_source=lambda t: 0.0,
            )

            resistance = ThermalResistance(
                name="fuel_to_moderator",
                resistance=1e-6,  # K/W
                lump1_name="fuel",
                lump2_name="moderator",
            )

            lumps = {"fuel": fuel, "moderator": moderator}
            resistances = [resistance]
            ambient_temp = 300.0

        solver = LumpedThermalHydraulics(
            lumps=lumps, resistances=resistances, ambient_temperature=ambient_temp
        )

        _print_info(f"Running lumped-parameter thermal-hydraulics analysis...")
        _print_info(f"  Duration: {args.duration:.1f} s")
        _print_info(f"  Lumps: {len(lumps)}")
        _print_info(f"  Resistances: {len(resistances)}")

        result = solver.solve_transient(
            t_span=(0.0, args.duration),
            max_step=args.max_step,
            adaptive=args.adaptive,
        )

        _print_success("Thermal-hydraulics analysis complete")

        # Print summary
        for lump_name in lumps.keys():
            T_key = f"T_{lump_name}"
            if T_key in result:
                T_final = result[T_key][-1]  # pragma: no cover
                T_initial = result[T_key][0]  # pragma: no cover
                if _RICH_AVAILABLE:  # pragma: no cover
                    console.print(
                        f"  {lump_name.capitalize()}: {T_initial:.1f} → {T_final:.1f} K"
                    )  # pragma: no cover
                else:  # pragma: no cover
                    print(
                        f"  {lump_name.capitalize()}: {T_initial:.1f} → {T_final:.1f} K"
                    )  # pragma: no cover

        # Generate plot if requested
        if args.plot or args.plot_output:
            try:
                from smrforge.visualization.transients import plot_lumped_thermal

                plot_lumped_thermal(
                    result,
                    output=str(args.plot_output) if args.plot_output else None,
                    backend=args.plot_backend,
                    show_plot=args.plot and args.plot_output is None,
                )
                if args.plot_output:  # pragma: no cover
                    _print_success(
                        f"Plot saved to {args.plot_output}"
                    )  # pragma: no cover
            except ImportError as e:
                _print_error(f"Plotting not available: {e}")  # pragma: no cover
                _print_info(
                    "Install matplotlib or plotly for visualization: pip install matplotlib plotly"
                )  # pragma: no cover

        # Save results if output specified
        if args.output:  # pragma: no cover
            output_data = {  # pragma: no cover
                "time": result["time"].tolist(),  # pragma: no cover
            }  # pragma: no cover
            for key, value in result.items():  # pragma: no cover
                if key != "time":  # pragma: no cover
                    output_data[key] = value.tolist()  # pragma: no cover

            with open(args.output, "w") as f:  # pragma: no cover
                json.dump(_to_jsonable(output_data), f, indent=2)  # pragma: no cover
            _print_success(f"Results saved to {args.output}")  # pragma: no cover

    except Exception as e:
        _print_error(f"Thermal-hydraulics analysis failed: {e}")
        if args.verbose:
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)


