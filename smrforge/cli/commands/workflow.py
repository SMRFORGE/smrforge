"""SMRForge CLI command handlers."""

import glob
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
from .reactor import _load_reactor_from_args

def workflow_run(args):
    """Run workflow from YAML file."""
    try:
        if not _YAML_AVAILABLE:
            _print_error(
                "YAML support not available. Install PyYAML: pip install pyyaml"
            )
            sys.exit(1)

        # Load workflow file
        if not args.workflow.exists():
            _print_error(f"Workflow file not found: {args.workflow}")
            sys.exit(1)

        with open(args.workflow) as f:
            workflow_data = yaml.safe_load(f)

        if not workflow_data or "steps" not in workflow_data:
            _print_error("Invalid workflow file: must contain 'steps' key")
            sys.exit(1)

        _print_info(f"Running workflow: {args.workflow}")
        _print_info(f"Steps: {len(workflow_data['steps'])}")

        # Import required modules
        import smrforge as smr
        from smrforge.convenience import create_reactor

        # Execute workflow steps
        context = {}  # Store intermediate results

        for i, step in enumerate(workflow_data["steps"], 1):
            step_type = step.get("type", "")
            _print_info(f"\nStep {i}/{len(workflow_data['steps'])}: {step_type}")

            if step_type == "create_reactor":
                preset = step.get("preset")
                config = step.get("config")
                output = step.get("output")

                if preset:
                    reactor = create_reactor(preset)
                    _print_success(f"Created reactor from preset: {preset}")
                elif config:
                    config_path = Path(config)
                    if not config_path.exists():
                        _print_error(
                            f"Config file not found: {config_path}"
                        )  # pragma: no cover
                        continue  # pragma: no cover

                    with open(config_path) as f:
                        if config_path.suffix.lower() in [".yaml", ".yml"]:
                            config_data = yaml.safe_load(f)  # pragma: no cover
                        else:
                            config_data = json.load(f)

                    reactor = create_reactor(**config_data)
                    _print_success(f"Created reactor from config: {config_path}")
                else:
                    _print_error("create_reactor step requires 'preset' or 'config'")
                    continue

                context["reactor"] = reactor

                if output:
                    # Save reactor
                    output_path = Path(output)
                    # Resolve relative paths relative to workflow file's directory
                    if not output_path.is_absolute():
                        output_path = args.workflow.parent / output_path
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    reactor_dict = {
                        "name": (
                            reactor.spec.name if hasattr(reactor, "spec") else "reactor"
                        ),
                        "power_thermal": (
                            reactor.spec.power_thermal
                            if hasattr(reactor, "spec")
                            else 0
                        ),
                        "enrichment": (
                            reactor.spec.enrichment if hasattr(reactor, "spec") else 0
                        ),
                        "reactor_type": (
                            getattr(
                                reactor.spec.reactor_type,
                                "value",
                                str(reactor.spec.reactor_type),
                            )
                            if hasattr(reactor, "spec")
                            else "unknown"
                        ),
                    }

                    with open(output_path, "w") as f:
                        if output_path.suffix.lower() in [".yaml", ".yml"]:
                            yaml.safe_dump(reactor_dict, f)  # pragma: no cover
                        else:
                            json.dump(_to_jsonable(reactor_dict), f, indent=2)
                    _print_success(f"Saved reactor to: {output_path}")

            elif step_type == "analyze":
                if "reactor" not in context:
                    _print_error(
                        "No reactor in context. Create reactor first."
                    )  # pragma: no cover
                    continue  # pragma: no cover

                reactor = context["reactor"]
                results = {}

                if step.get("keff", False) or step.get("full", False):
                    _print_info("Running k-eff calculation...")
                    k_eff = reactor.solve_keff()
                    results["k_eff"] = float(k_eff)
                    _print_success(f"k-eff: {k_eff:.6f}")

                if step.get("neutronics", False) or step.get("full", False):
                    _print_info("Running neutronics analysis...")
                    full_results = reactor.solve()
                    results.update(
                        {k: v for k, v in full_results.items() if k != "k_eff"}
                    )
                    if "k_eff" not in results:
                        results["k_eff"] = float(full_results.get("k_eff", 0.0))

                context["results"] = results

                # Save results if output specified
                output = step.get("output")
                if output:
                    output_path = Path(output)
                    # Resolve relative paths relative to current working directory
                    if not output_path.is_absolute():
                        output_path = Path.cwd() / output_path
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "w") as f:
                        json.dump(_to_jsonable(results), f, indent=2)
                    _print_success(f"Saved results to: {output_path}")

            elif step_type == "visualize":
                _print_info(
                    "Visualization step (use Python API for full visualization)"
                )
                # Visualization would need full implementation
                output = step.get("output")
                if output:
                    _print_info(f"Visualization output would be saved to: {output}")

            else:
                _print_warning(f"Unknown step type: {step_type}")

        _print_success("\nWorkflow completed successfully!")

    except ImportError as e:
        _print_error(f"Failed to import required modules: {e}")  # pragma: no cover
        sys.exit(1)  # pragma: no cover
    except Exception as e:
        _print_error(f"Failed to run workflow: {e}")
        if args.verbose if hasattr(args, "verbose") else False:
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)




def batch_keff_run(args):
    """Run batch k-eff on multiple reactor files (glob or list)."""
    try:
        import json

        from smrforge.convenience import create_reactor
        from smrforge.utils.parallel_batch import batch_solve_keff

        patterns = getattr(args, "reactors", None) or []
        if not patterns:
            _print_error(
                "Specify at least one reactor file or glob (e.g. reactors/*.json)"
            )
            sys.exit(1)
        reactor_files = []
        for pattern in patterns:
            matched = glob.glob(pattern, recursive=True)
            for f in matched:
                p = Path(f)
                if p.suffix.lower() in (".json", ".yaml", ".yml") and p.exists():
                    reactor_files.append(p)
        reactor_files = list(dict.fromkeys(reactor_files))
        if not reactor_files:
            _print_error("No valid reactor files found")  # pragma: no cover
            sys.exit(1)  # pragma: no cover

        _print_info(f"Loading {len(reactor_files)} reactor(s)...")
        reactors = []
        for p in reactor_files:
            try:
                with open(p, encoding="utf-8") as f:
                    raw = f.read()
                if p.suffix.lower() in (".yaml", ".yml"):
                    if not _YAML_AVAILABLE:  # pragma: no cover
                        _print_error(
                            "YAML file given but PyYAML not installed. Install: pip install pyyaml"
                        )  # pragma: no cover
                        sys.exit(1)  # pragma: no cover
                    data = yaml.safe_load(raw)  # pragma: no cover
                else:
                    data = json.loads(raw)
                reactors.append(create_reactor(**data))
            except Exception as e:  # pragma: no cover
                _print_error(f"Failed to load {p}: {e}")  # pragma: no cover
                sys.exit(1)  # pragma: no cover

        parallel = not getattr(args, "no_parallel", False)
        workers = getattr(args, "workers", None)
        k_effs = batch_solve_keff(
            reactors,
            parallel=parallel,
            max_workers=workers,
            show_progress=not getattr(args, "no_progress", False),
        )

        out_path = getattr(args, "output", None)
        if out_path:
            out_path = Path(out_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "reactors": [str(p) for p in reactor_files],
                "k_eff": [
                    float(k) if not isinstance(k, Exception) else None for k in k_effs
                ],
                "errors": [
                    str(k) if isinstance(k, Exception) else None for k in k_effs
                ],
            }
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            _print_success(f"Results saved to {out_path}")

        if _RICH_AVAILABLE:
            table = Table(title="Batch k-eff")
            table.add_column("Reactor", style="cyan")
            table.add_column("k-eff", justify="right", style="green")
            for p, k in zip(reactor_files, k_effs):
                table.add_row(
                    p.name, str(k) if not isinstance(k, Exception) else f"Error: {k}"
                )
            console.print(table)
        else:  # pragma: no cover
            for p, k in zip(reactor_files, k_effs):  # pragma: no cover
                print(f"{p.name}: {k}")  # pragma: no cover
    except Exception as e:
        _print_error(f"Batch k-eff failed: {e}")  # pragma: no cover
        if getattr(args, "verbose", False):  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover




def workflow_design_point(args):
    """Print or save steady-state design point summary for a reactor."""
    try:
        from smrforge.convenience import create_reactor, get_design_point

        reactor = _load_reactor_from_args(args)
        point = get_design_point(reactor)
        out = getattr(args, "output", None)
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                json.dump(point, f, indent=2)
            _print_success(f"Design point saved to {out}")
        if _RICH_AVAILABLE:
            table = Table(title="Design point")  # pragma: no cover
            table.add_column("Metric", style="cyan")  # pragma: no cover
            table.add_column("Value", justify="right")  # pragma: no cover
            for k, v in point.items():  # pragma: no cover
                table.add_row(
                    k, f"{v:.6g}" if isinstance(v, (int, float)) else str(v)
                )  # pragma: no cover
            console.print(table)  # pragma: no cover
        else:  # pragma: no cover
            print(json.dumps(point, indent=2))
    except Exception as e:  # pragma: no cover
        _print_error(f"Design point failed: {e}")  # pragma: no cover
        if getattr(args, "verbose", False):  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover




def workflow_safety_report(args):
    """Generate coupled safety margin report (nominal + optional UQ vs limits)."""
    try:
        from smrforge.convenience import create_reactor
        from smrforge.validation.safety_report import safety_margin_report

        reactor = _load_reactor_from_args(args)
        constraint_set = None
        if getattr(args, "constraints", None) and Path(args.constraints).exists():
            from smrforge.validation.constraints import (  # pragma: no cover
                ConstraintSet,
            )

            constraint_set = ConstraintSet.load(
                Path(args.constraints)
            )  # pragma: no cover
        report = safety_margin_report(reactor, constraint_set=constraint_set)
        out = getattr(args, "output", None)
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                json.dump(report.to_dict(), f, indent=2)
            _print_success(f"Safety report saved to {out}")
        if _RICH_AVAILABLE:
            table = Table(title="Safety margins")  # pragma: no cover
            table.add_column("Constraint", style="cyan")  # pragma: no cover
            table.add_column("Value", justify="right")  # pragma: no cover
            table.add_column("Limit", justify="right")  # pragma: no cover
            table.add_column("Margin", justify="right")  # pragma: no cover
            table.add_column("OK", justify="center")  # pragma: no cover
            for m in report.margins:  # pragma: no cover
                table.add_row(
                    m.name,
                    f"{m.value:.4g} {m.unit}",
                    f"{m.limit:.4g} {m.unit}",
                    f"{m.margin:.4g}",
                    "[green]yes[/green]" if m.within_limit else "[red]no[/red]",
                )  # pragma: no cover
            console.print(table)  # pragma: no cover
            console.print(
                f"Passed: {'[green]yes[/green]' if report.passed else '[red]no[/red]'}"
            )  # pragma: no cover
        else:  # pragma: no cover
            print(json.dumps(report.to_dict(), indent=2))
    except Exception as e:  # pragma: no cover
        _print_error(f"Safety report failed: {e}")  # pragma: no cover
        if getattr(args, "verbose", False):  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover




def workflow_doe(args):
    """Generate Design of Experiments (factorial, LHS, Sobol, random)."""
    try:
        from smrforge.workflows.doe import (
            full_factorial,
            latin_hypercube,
            random_space_filling,
            sobol_space_filling,
        )

        method = (getattr(args, "method", None) or "lhs").strip().lower()
        factors = getattr(args, "factors", None) or []
        n_samples = int(getattr(args, "samples", 10))
        seed = getattr(args, "seed", None)
        if seed is not None:
            seed = int(seed)
        names = []
        bounds = []
        levels = {}
        for spec in factors:
            parts = spec.split(":")
            if len(parts) == 3:
                name, low, high = parts
                names.append(name.strip())
                bounds.append((float(low), float(high)))
            elif len(parts) >= 2:
                name = parts[0].strip()
                vals = [float(x) for x in parts[1].replace(",", " ").split()]
                names.append(name)
                levels[name] = vals
        if method == "factorial" and levels:
            design = full_factorial(levels)
        elif method in ("lhs", "sobol", "random") and names and bounds:
            if method == "lhs":
                design = latin_hypercube(names, bounds, n_samples, seed=seed)
            elif method == "sobol":  # pragma: no cover
                design = sobol_space_filling(
                    names, bounds, n_samples, seed=seed
                )  # pragma: no cover
            else:  # pragma: no cover
                design = random_space_filling(
                    names, bounds, n_samples, seed=seed
                )  # pragma: no cover
        else:
            _print_error(
                "For factorial use --factors name:v1,v2,v3 (repeat). For lhs/sobol/random use --factors name:low:high (repeat) and --samples N"
            )
            sys.exit(1)
        out = getattr(args, "output", None)
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                json.dump(
                    {"method": method, "n_samples": len(design), "design": design},
                    f,
                    indent=2,
                )
            _print_success(f"DoE ({len(design)} points) saved to {out}")
        else:  # pragma: no cover
            print(json.dumps(design, indent=2))  # pragma: no cover
    except Exception as e:
        _print_error(f"DoE failed: {e}")  # pragma: no cover
        if getattr(args, "verbose", False):  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover




def workflow_pareto(args):
    """Compute and export Pareto front from sweep results."""
    try:
        from smrforge.visualization.sweep_plots import _pareto_front_mask, _to_dataframe

        p = Path(getattr(args, "sweep_results", None) or "")
        if not p.exists():
            _print_error("--sweep-results FILE.json required")  # pragma: no cover
            sys.exit(1)  # pragma: no cover
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        results = data.get("results", data) if isinstance(data, dict) else data
        # Use _to_dataframe for consistent handling (supports Polars fast path)
        df = _to_dataframe(
            {"results": results} if isinstance(results, list) else results,
            include_failed=True,
        )
        if df.empty:
            _print_error("No results in sweep file")  # pragma: no cover
            sys.exit(1)  # pragma: no cover
        mx = getattr(args, "metric_x", "k_eff")
        my = getattr(args, "metric_y", None)
        if not my:
            numeric = df.select_dtypes(
                include=[np.number]
            ).columns.tolist()  # pragma: no cover
            my = (
                [c for c in numeric if c != mx][0] if len(numeric) > 1 else numeric[0]
            )  # pragma: no cover
        if mx not in df.columns or my not in df.columns:
            _print_error(
                f"Metrics {mx}, {my} not in results. Columns: {list(df.columns)}"
            )  # pragma: no cover
            sys.exit(1)  # pragma: no cover
        import pandas as pd
        x = pd.to_numeric(df[mx], errors="coerce").to_numpy()
        y = pd.to_numeric(df[my], errors="coerce").to_numpy()
        ok = np.isfinite(x) & np.isfinite(y)
        x, y = x[ok], y[ok]
        mask = _pareto_front_mask(x, y, maximize_x=True, maximize_y=True)
        pareto_results = [results[i] for i in np.where(ok)[0][mask]]
        out = getattr(args, "output", None)
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            from smrforge.workflows.pareto_report import pareto_summary_report

            summary = pareto_summary_report(
                pareto_results, mx, my, maximize_x=True, maximize_y=True
            )
            payload = {
                "metric_x": mx,
                "metric_y": my,
                "n_pareto": len(pareto_results),
                "pareto": pareto_results,
                "summary": summary,
            }
            with open(out, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            _print_success(
                f"Pareto set ({len(pareto_results)} points) + summary saved to {out}"
            )
        else:
            print(json.dumps(pareto_results, indent=2))  # pragma: no cover
        plot_path = getattr(args, "plot", None)
        if plot_path and len(x) > 0:
            from smrforge.visualization.design_study_plots import (  # pragma: no cover
                plot_pareto_with_knee,
            )
            from smrforge.workflows.pareto_report import (  # pragma: no cover
                pareto_knee_point,
            )

            x_p, y_p = x[mask], y[mask]  # pragma: no cover
            knee_idx = (
                pareto_knee_point(x_p, y_p, maximize_x=True, maximize_y=True)
                if len(x_p) > 0
                else None
            )  # pragma: no cover
            fig = plot_pareto_with_knee(
                x,
                y,
                mask,
                knee_index=knee_idx,
                metric_x=mx,
                metric_y=my,
                backend="plotly",
            )  # pragma: no cover
            _save_workflow_plot(fig, Path(plot_path))  # pragma: no cover
            _print_success(f"Pareto plot saved to {plot_path}")  # pragma: no cover
    except Exception as e:  # pragma: no cover
        _print_error(f"Pareto failed: {e}")  # pragma: no cover
        if getattr(args, "verbose", False):  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover




def workflow_optimize(args):
    """Run design optimization (optionally constraint-aware)."""
    try:
        import numpy as np

        from smrforge.convenience import create_reactor, get_design_point
        from smrforge.optimization.design import DesignOptimizer

        reactor_path = getattr(args, "reactor", None)
        if not reactor_path:
            _print_error("--reactor base design file or preset required")
            sys.exit(1)
        with open(Path(reactor_path), encoding="utf-8") as f:
            base_spec = json.load(f)
        param_specs = getattr(args, "params", None) or []
        bounds = []
        param_names = []
        for spec in param_specs:
            parts = spec.split(":")
            if len(parts) != 3:
                _print_error(
                    "Each --params must be name:low:high (e.g. enrichment:0.1:0.2)"
                )  # pragma: no cover
                sys.exit(1)  # pragma: no cover
            name, low, high = parts[0].strip(), float(parts[1]), float(parts[2])
            param_names.append(name)
            bounds.append((low, high))
        if not param_names:
            _print_error(
                "At least one --params name:low:high required"
            )  # pragma: no cover
            sys.exit(1)  # pragma: no cover

        def reactor_from_x(x):
            spec = dict(base_spec)  # pragma: no cover
            for i, name in enumerate(param_names):  # pragma: no cover
                spec[name] = float(x[i])  # pragma: no cover
            return create_reactor(**spec)  # pragma: no cover

        objective_name = (
            (getattr(args, "objective", None) or "min_neg_keff").strip().lower()
        )
        if objective_name == "min_neg_keff":

            def obj(x):
                r = reactor_from_x(x)  # pragma: no cover
                return -get_design_point(r)["k_eff"]  # pragma: no cover

        else:  # pragma: no cover
            _print_error(
                "Only objective min_neg_keff (maximize k_eff) supported in CLI for now"
            )  # pragma: no cover
            sys.exit(1)  # pragma: no cover
        use_constraints = getattr(args, "constraints", False)
        if use_constraints and Path(use_constraints).exists():
            from smrforge.optimization.design import DesignOptimizer  # pragma: no cover
            from smrforge.validation.constraints import (  # pragma: no cover
                ConstraintSet,
            )

            constraint_set = ConstraintSet.load(
                Path(use_constraints)
            )  # pragma: no cover
            obj = DesignOptimizer.with_constraint_penalty(
                obj, reactor_from_x, constraint_set=constraint_set
            )  # pragma: no cover
        opt = DesignOptimizer(
            obj,
            bounds,
            method=getattr(args, "method", "differential_evolution")
            or "differential_evolution",
        )
        result = opt.optimize(max_iterations=int(getattr(args, "max_iter", 50)))
        _print_success(f"Optimal f = {result.f_opt:.6g}, success = {result.success}")
        optimal_point = dict(zip(param_names, result.x_opt.tolist()))
        optimal_point["k_eff"] = (
            -result.f_opt if objective_name == "min_neg_keff" else result.f_opt
        )
        out = getattr(args, "output", None)
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "x_opt": result.x_opt.tolist(),
                        "param_names": param_names,
                        "f_opt": result.f_opt,
                        "optimal_point": optimal_point,
                    },
                    f,
                    indent=2,
                )
            _print_success(f"Results saved to {out}")
        if _RICH_AVAILABLE:
            table = Table(title="Optimal parameters")
            for k, v in optimal_point.items():
                table.add_row(k, f"{v:.6g}")
            console.print(table)
        try:
            from smrforge.workflows.audit_log import append_run

            log_path = Path(out).parent / "runs.json" if out else None
            append_run(
                "optimize",
                args_summary={"reactor": str(reactor_path), "params": param_names},
                results_summary={"f_opt": result.f_opt, "success": result.success},
                passed=result.success,
                log_path=log_path,
            )
        except Exception:  # pragma: no cover
            pass  # pragma: no cover
    except Exception as e:
        try:  # pragma: no cover
            from smrforge.workflows.audit_log import append_run  # pragma: no cover

            append_run(
                "optimize",
                args_summary={"reactor": getattr(args, "reactor", None)},
                passed=False,
                error=str(e),
            )  # pragma: no cover
        except Exception:  # pragma: no cover
            pass  # pragma: no cover
        _print_error(f"Optimize failed: {e}")  # pragma: no cover
        if getattr(args, "verbose", False):  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover




def workflow_uq(args):
    """Run uncertainty quantification on a reactor (Monte Carlo sampling)."""
    try:
        from smrforge.convenience import create_reactor, get_design_point
        from smrforge.uncertainty.uq import UncertainParameter, UncertaintyPropagation

        n_samples = int(getattr(args, "samples", 100))
        reactor_path = getattr(args, "reactor", None)
        if not reactor_path:
            _print_error("--reactor base design file required")
            sys.exit(1)
        with open(Path(reactor_path), encoding="utf-8") as f:
            base_spec = json.load(f)
        param_specs = getattr(args, "params", None) or []
        uncertain = []
        for spec in param_specs:
            parts = spec.split(":")
            if len(parts) < 3:
                continue  # pragma: no cover
            name, nominal, dist = (
                parts[0].strip(),
                float(parts[1]),
                (parts[2].strip().lower() if len(parts) > 2 else "normal"),
            )
            unc = float(parts[3]) if len(parts) > 3 else 0.1
            if dist == "uniform" and len(parts) >= 5:
                b = (float(parts[3]), float(parts[4]))  # pragma: no cover
                uncertain.append(
                    UncertainParameter(name, "uniform", nominal, b)
                )  # pragma: no cover
            else:
                uncertain.append(UncertainParameter(name, dist, nominal, unc))
        if not uncertain:
            _print_error(
                "At least one --params name:nominal:distribution[:uncertainty] required (e.g. enrichment:0.2:normal:0.02)"
            )  # pragma: no cover
            sys.exit(1)  # pragma: no cover

        def model(x_dict):
            spec = dict(base_spec)  # pragma: no cover
            for k, v in x_dict.items():  # pragma: no cover
                spec[k] = v  # pragma: no cover
            r = create_reactor(**spec)  # pragma: no cover
            return get_design_point(r)  # pragma: no cover

        output_names = ["k_eff", "power_thermal_mw"]
        prop = UncertaintyPropagation(uncertain, model, output_names)
        uq_results = prop.propagate(
            n_samples=n_samples,
            method="lhs",
            random_state=int(getattr(args, "seed", 42) or 0),
        )
        out = getattr(args, "output", None)
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            summary = {
                "mean": uq_results.mean.tolist() if uq_results.mean is not None else [],
                "std": uq_results.std.tolist() if uq_results.std is not None else [],
                "output_names": getattr(uq_results, "output_names", []),
            }
            with open(out, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
            _print_success(f"UQ summary saved to {out}")  # pragma: no cover
        if _RICH_AVAILABLE and uq_results.mean is not None:  # pragma: no cover
            table = Table(title="UQ summary")  # pragma: no cover
            table.add_column("Output", style="cyan")  # pragma: no cover
            table.add_column("Mean", justify="right")  # pragma: no cover
            table.add_column("Std", justify="right")  # pragma: no cover
            for i, oname in enumerate(
                getattr(
                    uq_results,
                    "output_names",
                    ["output_" + str(i) for i in range(len(uq_results.mean))],
                )
            ):  # pragma: no cover
                table.add_row(
                    str(oname),
                    f"{uq_results.mean[i]:.6g}",
                    f"{uq_results.std[i]:.6g}" if uq_results.std is not None else "N/A",
                )  # pragma: no cover
            console.print(table)  # pragma: no cover
        try:  # pragma: no cover
            from smrforge.workflows.audit_log import append_run  # pragma: no cover

            out_path = getattr(args, "output", None)  # pragma: no cover
            log_path = (
                Path(out_path).parent / "runs.json" if out_path else None
            )  # pragma: no cover
            append_run(
                "uq",
                args_summary={"reactor": str(reactor_path), "samples": n_samples},
                results_summary={
                    "mean": (
                        uq_results.mean.tolist() if uq_results.mean is not None else []
                    )
                },
                passed=True,
                log_path=log_path,
            )  # pragma: no cover
        except Exception:  # pragma: no cover
            pass  # pragma: no cover
    except Exception as e:
        try:
            from smrforge.workflows.audit_log import append_run

            append_run(
                "uq",
                args_summary={"reactor": getattr(args, "reactor", None)},
                passed=False,
                error=str(e),
            )
        except Exception:  # pragma: no cover
            pass  # pragma: no cover
        _print_error(f"UQ failed: {e}")
        if getattr(args, "verbose", False):
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)




def _write_design_study_html(out_dir, design_point, safety_report):
    """Write a simple combined HTML report (design point + safety margins)."""
    from smrforge.validation.safety_report import margin_narrative

    report_dict = (
        safety_report.to_dict() if hasattr(safety_report, "to_dict") else safety_report
    )
    try:
        narrative = (
            margin_narrative(safety_report)
            if hasattr(safety_report, "margins")
            and isinstance(getattr(safety_report, "margins", None), list)
            else ""
        )
    except Exception:  # pragma: no cover
        narrative = ""  # pragma: no cover
    rows_dp = "".join(
        f"<tr><td>{k}</td><td>{v}</td></tr>"
        for k, v in sorted(design_point.items())
        if isinstance(v, (int, float))
    )
    rows_margins = ""
    for m in report_dict.get("margins", []):
        name = m.get("name", "")
        value = m.get("value", "")
        limit = m.get("limit", "")
        unit = m.get("unit", "") or ""
        within = "pass" if m.get("within_limit") else "fail"
        rows_margins += f"<tr><td>{name}</td><td>{value} {unit}</td><td>{limit} {unit}</td><td>{within}</td></tr>"
    violations = report_dict.get("violations", [])
    passed = report_dict.get("passed", False)
    status = "PASS" if passed else "FAIL"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Design Study Report</title>
<style>
  body {{ font-family: system-ui,sans-serif; max-width: 800px; margin: 1rem auto; padding: 0 1rem; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ccc; padding: 0.4rem 0.6rem; text-align: left; }}
  th {{ background: #eee; }}
  .pass {{ color: green; }} .fail {{ color: #c00; }}
  h1 {{ font-size: 1.2rem; }} h2 {{ font-size: 1rem; margin-top: 1.2rem; }}
</style>
</head>
<body>
<h1>Design Study Report</h1>
<p><strong>Overall: <span class="{('pass' if passed else 'fail')}">{status}</span></strong></p>
<p>{narrative}</p>
<h2>Design Point</h2>
<table><tr><th>Metric</th><th>Value</th></tr>{rows_dp}</table>
<h2>Safety Margins</h2>
<table><tr><th>Constraint</th><th>Value</th><th>Limit</th><th>Status</th></tr>{rows_margins}</table>
<h2>Violations</h2>
<ul>{''.join(f'<li>{v}</li>' for v in violations) if violations else '<li>None</li>'}</ul>
</body>
</html>
"""
    (out_dir / "design_study_report.html").write_text(html, encoding="utf-8")




def workflow_design_study(args):
    """Run design point + safety report (unified design study step)."""
    try:
        from smrforge.convenience import create_reactor, get_design_point
        from smrforge.validation.safety_report import safety_margin_report

        reactor = _load_reactor_from_args(args)
        out_dir = getattr(args, "output_dir", None) or Path("design_study_output")
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        point = get_design_point(reactor)
        with open(out_dir / "design_point.json", "w", encoding="utf-8") as f:
            json.dump(point, f, indent=2)
        constraint_set = None
        if getattr(args, "constraints", None) and Path(args.constraints).exists():
            from smrforge.validation.constraints import (  # pragma: no cover
                ConstraintSet,
            )

            constraint_set = ConstraintSet.load(
                Path(args.constraints)
            )  # pragma: no cover
        report = safety_margin_report(reactor, constraint_set=constraint_set)
        with open(out_dir / "safety_report.json", "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2)
        if getattr(args, "html", False):
            _write_design_study_html(out_dir, point, report)  # pragma: no cover
        plot_path = getattr(args, "plot", None)
        if plot_path and report.margins:
            from smrforge.visualization.design_study_plots import (  # pragma: no cover
                plot_safety_margins,
            )

            fig = plot_safety_margins(report, backend="plotly")  # pragma: no cover
            _save_workflow_plot(fig, Path(plot_path))  # pragma: no cover
            _print_success(
                f"Safety margins plot saved to {plot_path}"
            )  # pragma: no cover
        _print_success(f"Design study written to {out_dir}")
        if _RICH_AVAILABLE:
            console.print(f"  design_point.json  – steady-state metrics")
            console.print(f"  safety_report.json – margins and pass/fail")
        if getattr(args, "html", False):
            console.print(
                f"  design_study_report.html – combined report"
            )  # pragma: no cover
        try:
            from smrforge.workflows.audit_log import append_run

            append_run(
                "design-study",
                args_summary={
                    "reactor": getattr(args, "reactor"),
                    "output_dir": str(out_dir),
                },
                results_summary={
                    "k_eff": point.get("k_eff"),
                    "power_thermal_mw": point.get("power_thermal_mw"),
                    "passed": report.passed,
                },
                passed=report.passed,
                log_path=out_dir / "runs.json",
            )
        except Exception:  # pragma: no cover
            pass  # pragma: no cover
    except Exception as e:  # pragma: no cover
        try:  # pragma: no cover
            from smrforge.workflows.audit_log import append_run  # pragma: no cover

            append_run(
                "design-study",
                args_summary={"reactor": getattr(args, "reactor", None)},
                passed=False,
                error=str(e),
            )  # pragma: no cover
        except Exception:  # pragma: no cover
            pass  # pragma: no cover
        _print_error(f"Design study failed: {e}")  # pragma: no cover
        if getattr(args, "verbose", False):  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover




def workflow_variant(args):
    """Save reactor design as a named variant."""
    try:
        from smrforge.convenience import create_reactor, save_variant

        reactor = _load_reactor_from_args(args)
        name = getattr(args, "name", None) or "variant"
        out_dir = getattr(args, "output_dir", None)
        path = save_variant(reactor, name, output_dir=out_dir)
        _print_success(f"Variant saved to {path}")
    except Exception as e:  # pragma: no cover
        _print_error(f"Variant save failed: {e}")  # pragma: no cover
        if getattr(args, "verbose", False):  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover




def workflow_sensitivity(args):
    """Rank parameters by sensitivity (OAT or Morris) from sweep results."""
    try:
        from smrforge.workflows.sensitivity import (
            morris_screening,
            one_at_a_time_from_sweep,
        )

        p = Path(getattr(args, "sweep_results", None) or "")
        if not p.exists():
            _print_error("--sweep-results FILE.json required")
            sys.exit(1)
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        results = data.get("results", data) if isinstance(data, dict) else data
        if not isinstance(results, list):
            results = [results]  # pragma: no cover
        params = getattr(args, "params", None) or []
        if not params:
            if results and isinstance(results[0], dict):  # pragma: no cover
                p0 = results[0].get("parameters", results[0])  # pragma: no cover
                params = [
                    k for k in p0 if isinstance(p0.get(k), (int, float))
                ]  # pragma: no cover
        if not params:
            _print_error(
                "--params name1 name2 ... or sweep results with parameter keys required"
            )  # pragma: no cover
            sys.exit(1)  # pragma: no cover
        metric = getattr(args, "metric", "k_eff")
        rankings = one_at_a_time_from_sweep(results, params, output_metric=metric)
        out = getattr(args, "output", None)
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                json.dump(
                    [
                        {"parameter": r.parameter, "effect": r.effect, "rank": r.rank}
                        for r in rankings
                    ],
                    f,
                    indent=2,
                )
            _print_success(f"Sensitivity ranking saved to {out}")
        else:  # pragma: no cover
            for r in rankings:  # pragma: no cover
                print(
                    f"  {r.rank}. {r.parameter}: effect={r.effect:.4f}"
                )  # pragma: no cover
        plot_path = getattr(args, "plot", None)
        if plot_path and rankings:
            from smrforge.visualization.design_study_plots import (  # pragma: no cover
                plot_sensitivity_ranking,
            )

            fig = plot_sensitivity_ranking(
                rankings, backend="plotly"
            )  # pragma: no cover
            _save_workflow_plot(fig, Path(plot_path))  # pragma: no cover
            _print_success(f"Sensitivity plot saved to {plot_path}")  # pragma: no cover
    except Exception as e:
        _print_error(f"Sensitivity failed: {e}")  # pragma: no cover
        if getattr(args, "verbose", False):  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover




def workflow_sobol(args):
    """Compute Sobol indices from sweep or UQ results."""
    try:
        from smrforge.workflows.sobol_indices import sobol_indices_from_sweep_results

        p = Path(getattr(args, "sweep_results", None) or "")
        if not p.exists():
            _print_error("--sweep-results FILE.json required")
            sys.exit(1)
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        results = data.get("results", data) if isinstance(data, dict) else data
        if not isinstance(results, list):
            results = [results]  # pragma: no cover
        params = getattr(args, "params", None) or []
        if not params and results and isinstance(results[0], dict):
            p0 = results[0].get("parameters", results[0])  # pragma: no cover
            params = [
                k for k in p0 if isinstance(p0.get(k), (int, float))
            ]  # pragma: no cover
        if not params:
            _print_error(
                "--params name1 name2 ... or sweep results with parameter keys required"
            )  # pragma: no cover
            sys.exit(1)  # pragma: no cover
        metric = getattr(args, "metric", "k_eff")
        sobol_dict = sobol_indices_from_sweep_results(
            results, params, output_metric=metric
        )
        out = getattr(args, "output", None)
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                json.dump(sobol_dict, f, indent=2)
            _print_success(f"Sobol indices saved to {out}")
        else:  # pragma: no cover
            for label, si in sobol_dict.items():  # pragma: no cover
                print(
                    f"{label}: S1={si.get('S1', [])}, ST={si.get('ST', [])}"
                )  # pragma: no cover
        plot_path = getattr(args, "plot", None)
        if plot_path and sobol_dict:
            from smrforge.visualization.design_study_plots import (  # pragma: no cover
                plot_sobol_workflow,
            )

            fig = plot_sobol_workflow(
                sobol_dict, output_key="Y0", backend="plotly"
            )  # pragma: no cover
            _save_workflow_plot(fig, Path(plot_path))  # pragma: no cover
            _print_success(f"Sobol plot saved to {plot_path}")  # pragma: no cover
    except Exception as e:
        _print_error(f"Sobol failed: {e}")  # pragma: no cover
        if getattr(args, "verbose", False):  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover




def workflow_scenario(args):
    """Run scenario-based design (multiple constraint sets / missions)."""
    try:  # pragma: no cover
        from smrforge.workflows.scenario_design import (  # pragma: no cover
            run_scenario_design,
            scenario_comparison_report,
        )

        reactor = _load_reactor_from_args(args)  # pragma: no cover
        scenarios = getattr(args, "scenarios", None) or []  # pragma: no cover
        if not scenarios:  # pragma: no cover
            _print_error(
                "--scenarios name:path_or_preset ... required (e.g. baseload:regulatory_limits)"
            )  # pragma: no cover
            sys.exit(1)  # pragma: no cover
        scenario_dict = {}  # pragma: no cover
        for s in scenarios:  # pragma: no cover
            part = s.split(":", 1)  # pragma: no cover
            name = part[0].strip()  # pragma: no cover
            val = (
                part[1].strip() if len(part) > 1 else "regulatory_limits"
            )  # pragma: no cover
            scenario_dict[name] = val  # pragma: no cover
        results = run_scenario_design(reactor, scenario_dict)  # pragma: no cover
        out_dir = Path(
            getattr(args, "output_dir", None) or "scenario_output"
        )  # pragma: no cover
        out_dir.mkdir(parents=True, exist_ok=True)  # pragma: no cover
        report_path = out_dir / "scenario_comparison.md"  # pragma: no cover
        scenario_comparison_report(results, output_path=report_path)  # pragma: no cover
        out_json = out_dir / "scenario_results.json"  # pragma: no cover
        with open(out_json, "w", encoding="utf-8") as f:  # pragma: no cover
            json.dump(
                {
                    k: {
                        "passed": v.passed,
                        "violations": v.violations,
                        "metrics": v.metrics,
                    }
                    for k, v in results.items()
                },
                f,
                indent=2,
            )  # pragma: no cover
        _print_success(
            f"Scenario comparison written to {report_path} and {out_json}"
        )  # pragma: no cover
        plot_path = getattr(args, "plot", None)  # pragma: no cover
        if plot_path and results:  # pragma: no cover
            from smrforge.visualization.design_study_plots import (  # pragma: no cover
                plot_scenario_comparison,
            )

            fig = plot_scenario_comparison(
                results, backend="plotly"
            )  # pragma: no cover
            _save_workflow_plot(fig, Path(plot_path))  # pragma: no cover
            _print_success(f"Scenario plot saved to {plot_path}")  # pragma: no cover
    except Exception as e:  # pragma: no cover
        _print_error(f"Scenario design failed: {e}")  # pragma: no cover
        if getattr(args, "verbose", False):  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover




def workflow_atlas(args):
    """Build design space atlas (catalog of presets with design point + safety)."""
    try:
        from smrforge.workflows.atlas import build_atlas, filter_atlas

        out_dir = Path(getattr(args, "output_dir", None) or "atlas_output")
        presets = getattr(args, "presets", None)
        if presets:
            presets = [p.strip() for p in presets]  # pragma: no cover
        entries = build_atlas(out_dir, presets=presets)
        passed = sum(1 for e in entries if e.passed)
        _print_success(
            f"Atlas built: {len(entries)} designs, {passed} passed. Index: {out_dir / 'atlas_index.json'}"
        )
        plot_path = getattr(args, "plot", None)
        if plot_path and entries:
            from smrforge.visualization.design_study_plots import (  # pragma: no cover
                plot_atlas_designs,
            )

            fig = plot_atlas_designs(
                entries, x_metric="power_mw", y_metric="k_eff", backend="plotly"
            )  # pragma: no cover
            _save_workflow_plot(fig, Path(plot_path))  # pragma: no cover
            _print_success(f"Atlas plot saved to {plot_path}")  # pragma: no cover
    except Exception as e:  # pragma: no cover
        _print_error(f"Atlas failed: {e}")  # pragma: no cover
        if getattr(args, "verbose", False):  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover




def workflow_surrogate(args):
    """Fit surrogate model from sweep results for fast evaluation. Pro tier only."""
    try:
        from smrforge_pro.workflows.surrogate import surrogate_from_sweep_results
    except ImportError:
        _print_error(
            "Surrogate workflow requires SMRForge Pro. Upgrade at https://smrforge.io"
        )
        sys.exit(1)
    p = Path(getattr(args, "sweep_results", None) or "")
    if not p.exists():
        _print_error(f"Sweep results file not found: {p}")
        sys.exit(1)
    import json

    with open(p) as f:
        data = json.load(f)
    results = data.get("results", data) if isinstance(data, dict) else data
    params = getattr(args, "params", None) or []
    if not params:
        _print_error("--params name1 name2 ... required")
        sys.exit(1)
    metric = getattr(args, "metric", "k_eff") or "k_eff"
    method = getattr(args, "method", "rbf") or "rbf"
    out_path = getattr(args, "output", None)
    surr = surrogate_from_sweep_results(
        results, params, output_metric=metric, method=method, output_path=out_path
    )
    if out_path:
        _print_success(f"Surrogate saved to {out_path}")
    else:
        _print_success("Surrogate fitted successfully (use --output to save)")




def workflow_ml_export(args):
    """Export sweep results to Parquet/HDF5 for ML. Pro tier only."""
    try:
        from smrforge.workflows.ml_export import export_ml_dataset
    except ImportError:
        _print_error(
            "ML export requires SMRForge Pro. Upgrade at https://smrforge.io"
        )
        sys.exit(1)
    results_path = Path(getattr(args, "results", None) or "")
    output_path = getattr(args, "output", None)
    if not results_path.exists():
        _print_error(f"Results file not found: {results_path}")
        sys.exit(1)
    output_path = Path(output_path) if output_path else results_path.parent / "design_points.parquet"
    import json
    with open(results_path) as f:
        data = json.load(f)
    results = data.get("results", data) if isinstance(data, dict) else data
    if not isinstance(results, list):
        _print_error("Results must be a list of design points")
        sys.exit(1)
    try:
        out = export_ml_dataset(results, output_path)
        _print_success(f"ML dataset saved to {out}")
    except Exception as e:
        _print_error(f"ML export failed: {e}")
        sys.exit(1)




def workflow_requirements_to_constraints(args):
    """Parse requirements YAML/JSON into ConstraintSet and save."""
    try:
        from smrforge.validation.requirements_parser import (
            parse_requirements_to_constraint_set,
        )

        spec_path = getattr(args, "requirements", None)
        if not spec_path or not Path(spec_path).exists():
            _print_error("--requirements FILE.yaml|.json required")  # pragma: no cover
            sys.exit(1)  # pragma: no cover
        cs = parse_requirements_to_constraint_set(
            Path(spec_path), name=getattr(args, "name", "from_requirements")
        )
        out = getattr(args, "output", None)
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            cs.save(Path(out))
            _print_success(f"Constraint set saved to {out}")
        else:
            _print_error(
                "--output FILE.json required to save constraint set"
            )  # pragma: no cover
            sys.exit(1)  # pragma: no cover
    except Exception as e:  # pragma: no cover
        _print_error(f"Requirements-to-constraints failed: {e}")  # pragma: no cover
        if getattr(args, "verbose", False):  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover


def workflow_nl_design(args):
    """Natural-language reactor design. Pro tier."""
    try:
        from smrforge_pro.ai.nl_design import design_from_nl
    except ImportError:
        _print_error(
            "Natural-language design requires SMRForge Pro. pip install smrforge-pro"
        )
        sys.exit(1)
    text = getattr(args, "text", None) or ""
    if not text:
        _print_error("--text required (e.g. '10 MW HTGR with k-eff 1.0-1.05')")
        sys.exit(1)
    try:
        result = design_from_nl(text, run_analysis=True)
        _print_success("Design created and analyzed")
        if result.analysis and "k_eff" in result.analysis:
            _print_info(f"k_eff: {result.analysis['k_eff']:.6f}")
        if result.constraints_met is not None:
            _print_info(f"Constraints met: {result.constraints_met}")
        out = getattr(args, "output", None)
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            spec = result.spec
            if spec and hasattr(spec, "model_dump"):
                data = spec.model_dump()
            else:
                data = {"intent": result.intent_parsed}
            with open(out, "w") as f:
                json.dump(_to_jsonable(data), f, indent=2)
            _print_success(f"Saved to {out}")
    except Exception as e:
        _print_error(f"NL design failed: {e}")
        sys.exit(1)


def workflow_code_verify(args):
    """Unified code-to-code verification. Pro tier."""
    try:
        from smrforge_pro.workflows.code_verification import run_code_verification
    except ImportError:
        _print_error(
            "Code verification requires SMRForge Pro. pip install smrforge-pro"
        )
        sys.exit(1)
    reactor = getattr(args, "reactor", None) or ""
    output = getattr(args, "output", None) or Path("verification_output")
    if not reactor:
        _print_error("--reactor preset or file required")
        sys.exit(1)
    try:
        report = run_code_verification(reactor, output_dir=output)
        _print_success(f"Verification report: {output / 'verification_report.json'}")
        if _RICH_AVAILABLE and Table and console:
            table = Table(title="Code Verification")
            table.add_column("Code", style="cyan")
            table.add_column("k_eff", justify="right")
            table.add_column("Status")
            for r in report.results:
                k = f"{r.k_eff:.6f}" if r.k_eff is not None else (r.error or "export only")
                table.add_row(r.code, k, "OK" if r.error is None else "export only")
            console.print(table)
    except Exception as e:
        _print_error(f"Code verification failed: {e}")
        sys.exit(1)


def workflow_regulatory_package(args):
    """Generate regulatory submission package. Pro tier."""
    try:
        from smrforge_pro.workflows.regulatory_package import (
            RegulatoryPackageConfig,
            generate_regulatory_package,
        )
    except ImportError:
        _print_error(
            "Regulatory package requires SMRForge Pro. pip install smrforge-pro"
        )
        sys.exit(1)
    reactor = getattr(args, "reactor", None)
    output = getattr(args, "output", None) or Path("regulatory_package")
    if not reactor:
        _print_error("--reactor preset or file required")
        sys.exit(1)
    reactor_obj = _load_reactor_from_args(args)
    try:
        cfg = RegulatoryPackageConfig(framework=getattr(args, "framework", "NRC"))
        path = generate_regulatory_package(reactor_obj, output_dir=output, config=cfg)
        _print_success(f"Regulatory package: {path}")
    except Exception as e:
        _print_error(f"Regulatory package failed: {e}")
        sys.exit(1)


def workflow_benchmark(args):
    """One-click benchmark reproduction. Pro tier."""
    try:
        from smrforge_pro.workflows.benchmark_reproduction import (
            list_benchmarks,
            reproduce_benchmark,
        )
    except ImportError:
        _print_error(
            "Benchmark reproduction requires SMRForge Pro. pip install smrforge-pro"
        )
        sys.exit(1)
    bid = getattr(args, "benchmark_id", None) or getattr(args, "id", None)
    if not bid:
        _print_info("Available benchmarks: " + ", ".join(list_benchmarks()))
        _print_error("--id BENCHMARK_ID required")
        sys.exit(1)
    output = getattr(args, "output", None)
    try:
        result = reproduce_benchmark(bid, output_dir=output)
        if isinstance(result, tuple):
            results_list, out_path = result
            n_pass = sum(1 for r in results_list if getattr(r, "passed", False))
            n_total = len(results_list)
            _print_success(f"Benchmark suite {bid}: {n_pass}/{n_total} passed")
            _print_info(f"Report: {out_path / 'BENCHMARK_SUMMARY.md'}")
        else:
            status = "PASS" if result.passed else "FAIL"
            _print_success(f"Benchmark {bid}: {status}")
            _print_info(f"Report: {result.output_dir / 'report.json'}")
    except Exception as e:
        _print_error(f"Benchmark failed: {e}")
        sys.exit(1)


def workflow_multi_optimize(args):
    """Multi-objective design optimization. Pro tier."""
    try:
        from smrforge_pro.workflows.multi_objective_optimization import (
            multi_objective_optimize,
        )
    except ImportError:
        _print_error(
            "Multi-objective optimization requires SMRForge Pro. pip install smrforge-pro"
        )
        sys.exit(1)
    reactor_path = getattr(args, "reactor", None)
    params = getattr(args, "params", None) or []
    if not reactor_path or not params:
        _print_error("--reactor and --params name:low:high required")
        sys.exit(1)
    with open(Path(reactor_path)) as f:
        base_spec = json.load(f)
    bounds = []
    param_names = []
    for spec in params:
        parts = spec.split(":")
        if len(parts) != 3:
            _print_error("Each --params must be name:low:high")
            sys.exit(1)
        name, low, high = parts[0].strip(), float(parts[1]), float(parts[2])
        param_names.append(name)
        bounds.append((low, high))

    def reactor_from_x(x):
        sp = dict(base_spec)
        for i, n in enumerate(param_names):
            sp[n] = float(x[i])
        from smrforge.convenience import create_reactor

        return create_reactor(**sp)

    try:
        result = multi_objective_optimize(
            reactor_from_x,
            bounds,
            param_names,
            max_evaluations=int(getattr(args, "max_eval", 100)),
            seed=getattr(args, "seed"),
        )
        _print_success(f"Optimization: success={result.success}")
        for k, v in result.objectives.items():
            _print_info(f"  {k}: {v:.6g}")
        out = getattr(args, "output", None)
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w") as f:
                json.dump(
                    {
                        "x_opt": result.x_opt.tolist(),
                        "param_names": param_names,
                        "objectives": result.objectives,
                        "success": result.success,
                    },
                    f,
                    indent=2,
                )
            _print_success(f"Saved to {out}")
    except Exception as e:
        _print_error(f"Multi-objective optimization failed: {e}")
        sys.exit(1)

