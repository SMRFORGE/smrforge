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

def sweep_run(args):
    """Run parameter sweep workflow."""
    try:
        from pathlib import Path

        from smrforge.workflows import ParameterSweep, SweepConfig

        # Load config from file or build from args
        if getattr(args, "config", None) and Path(args.config).exists():
            config = SweepConfig.from_file(args.config)  # pragma: no cover
            if args.output:  # pragma: no cover
                config.output_dir = Path(args.output)  # pragma: no cover
            if getattr(args, "no_parallel", False):  # pragma: no cover
                config.parallel = False  # pragma: no cover
            if getattr(args, "workers", None) is not None:  # pragma: no cover
                config.max_workers = args.workers  # pragma: no cover
            if getattr(args, "surrogate", None) is not None:  # pragma: no cover
                config.surrogate_path = Path(args.surrogate)  # pragma: no cover
            if getattr(args, "seed", None) is not None:  # pragma: no cover
                config.seed = args.seed  # pragma: no cover
        else:
            if not getattr(args, "params", None) or not args.params:
                _print_error(
                    "Either --config FILE or --params ... is required"
                )  # pragma: no cover
                sys.exit(1)  # pragma: no cover
            parameters = {}
            for param_spec in args.params:
                parts = param_spec.split(":")
                if len(parts) == 4:
                    name, start, end, step = parts
                    parameters[name] = (float(start), float(end), float(step))
                elif len(parts) == 2:
                    name, values_str = parts
                    values = [float(v) for v in values_str.split(",")]
                    parameters[name] = values
            reactor_template = None
            if args.reactor:
                if Path(args.reactor).exists():
                    import json

                    with open(args.reactor) as f:
                        reactor_template = json.load(f)
                else:
                    reactor_template = {"name": args.reactor}
            config = SweepConfig(
                parameters=parameters,
                analysis_types=args.analysis or ["keff"],
                reactor_template=reactor_template,
                output_dir=Path(args.output) if args.output else Path("sweep_results"),
                parallel=not getattr(args, "no_parallel", False),
                max_workers=getattr(args, "workers", None),
                surrogate_path=getattr(args, "surrogate", None),
                seed=getattr(args, "seed", None),
            )

        sweep = ParameterSweep(config)
        results = sweep.run(
            resume=getattr(args, "resume", False),
            show_progress=getattr(args, "progress", False),
        )

        output_dir = config.output_dir
        output_file = output_dir / "sweep_results.json"
        results.save(output_file)

        _print_success(f"\nSweep complete! Results saved to {output_file}")
        _print_info(f"Total cases: {len(results.results)}")
        _print_info(f"Failed cases: {len(results.failed_cases)}")

    except ImportError as e:  # pragma: no cover
        _print_error(f"Failed to import required modules: {e}")  # pragma: no cover
        sys.exit(1)  # pragma: no cover
    except Exception as e:  # pragma: no cover
        _print_error(f"Failed to run parameter sweep: {e}")  # pragma: no cover
        if args.verbose if hasattr(args, "verbose") else False:  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover


