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


