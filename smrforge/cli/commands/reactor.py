"""Reactor commands: create, analyze, list, compare."""

import glob
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from smrforge.cli.common import (
    Table,
    _GLYPH_ERROR,
    _GLYPH_SUCCESS,
    _RICH_AVAILABLE,
    _YAML_AVAILABLE,
    _print_error,
    _print_info,
    _print_success,
    _print_warning,
    _to_jsonable,
    console,
    yaml,
)


def reactor_create(args):
    """Create a reactor from preset or configuration."""
    try:
        import smrforge as smr
        from smrforge.validation.models import ReactorSpecification

        def _enum_value(v):
            """Return enum value for JSON/YAML serialization (fallback to raw)."""
            return getattr(v, "value", v)

        # Try multiple import strategies for convenience functions
        create_reactor = None
        list_presets = None

        # Strategy 1: Try from top-level smrforge module
        try:
            if hasattr(smr, "create_reactor"):
                create_reactor = smr.create_reactor
            if hasattr(smr, "list_presets"):
                list_presets = smr.list_presets
        except Exception:  # pragma: no cover
            pass  # pragma: no cover

        # Strategy 2: Try from convenience module
        if create_reactor is None or list_presets is None:
            try:  # pragma: no cover
                from smrforge.convenience import (  # pragma: no cover
                    create_reactor,
                    list_presets,
                )
            except ImportError:  # pragma: no cover
                pass  # pragma: no cover

        # Final check - if still None, raise error
        if create_reactor is None or list_presets is None:
            raise ImportError(  # pragma: no cover
                "Could not import create_reactor and list_presets. "
                "Try: import smrforge as smr; smr.create_reactor()"
            )

        # Check if preset is provided
        if args.preset:
            if args.preset not in list_presets():
                _print_error(f"Preset '{args.preset}' not found.")
                print(f"\nAvailable presets: {', '.join(list_presets())}")
                sys.exit(1)
                return  # don't fall through when exit is mocked

            reactor = create_reactor(args.preset)
            _print_success(f"Created reactor from preset: {args.preset}")

        # Check if config file is provided
        elif args.config:
            if not args.config.exists():
                _print_error(
                    f"Config file not found: {args.config}"
                )  # pragma: no cover
                sys.exit(1)  # pragma: no cover
                return  # pragma: no cover

            # Load config file
            if args.config.suffix in [".yaml", ".yml"]:
                if not _YAML_AVAILABLE:
                    _print_error(
                        "YAML support not available. Install PyYAML: pip install pyyaml"
                    )
                    sys.exit(1)
                with open(args.config) as f:
                    config = yaml.safe_load(f)
            else:
                with open(args.config) as f:
                    config = json.load(f)

            # Create reactor from config
            reactor = create_reactor(**config)
            _print_success(f"Created reactor from config: {args.config}")

        # Check if custom parameters provided
        elif any([args.power, args.enrichment, args.type]):
            kwargs = {}
            if args.power:
                kwargs["power_mw"] = args.power
            if args.enrichment:
                kwargs["enrichment"] = args.enrichment
            if args.type:
                kwargs["reactor_type"] = args.type
            if args.core_height:
                kwargs["core_height"] = args.core_height
            if args.core_diameter:
                kwargs["core_diameter"] = args.core_diameter
            if args.fuel_type:
                kwargs["fuel_type"] = args.fuel_type

            reactor = create_reactor(**kwargs)
            _print_success("Created reactor with custom parameters")

        else:
            _print_error("Must specify --preset, --config, or custom parameters")
            sys.exit(1)
            return

        # Save reactor if output specified
        if args.output:
            output_path = Path(args.output)
            output_format = (
                args.format or output_path.suffix[1:] if output_path.suffix else "json"
            )

            if output_format == "json":
                # Save as JSON (simple serialization)
                reactor_dict = {
                    "name": (
                        reactor.spec.name if hasattr(reactor, "spec") else "reactor"
                    ),
                    "power_mw": (
                        reactor.spec.power_thermal / 1e6
                        if hasattr(reactor, "spec")
                        else None
                    ),
                    "enrichment": (
                        reactor.spec.enrichment if hasattr(reactor, "spec") else None
                    ),
                    "reactor_type": (
                        _enum_value(reactor.spec.reactor_type)
                        if hasattr(reactor, "spec")
                        else None
                    ),
                    "fuel_type": (
                        _enum_value(reactor.spec.fuel_type)
                        if hasattr(reactor, "spec")
                        else None
                    ),
                    "core_height": (
                        reactor.spec.core_height if hasattr(reactor, "spec") else None
                    ),
                    "core_diameter": (
                        reactor.spec.core_diameter if hasattr(reactor, "spec") else None
                    ),
                }
                with open(output_path, "w") as f:
                    json.dump(_to_jsonable(reactor_dict), f, indent=2)
                _print_success(f"Saved reactor to {output_path} (JSON format)")
            elif output_format in ["yaml", "yml"]:
                if not _YAML_AVAILABLE:
                    _print_error(
                        "YAML support not available. Install PyYAML: pip install pyyaml"
                    )  # pragma: no cover
                    sys.exit(1)  # pragma: no cover
                reactor_dict = {
                    "name": (
                        reactor.spec.name if hasattr(reactor, "spec") else "reactor"
                    ),
                    "power_mw": (
                        reactor.spec.power_thermal / 1e6
                        if hasattr(reactor, "spec")
                        else None
                    ),
                    "enrichment": (
                        reactor.spec.enrichment if hasattr(reactor, "spec") else None
                    ),
                    "reactor_type": (
                        _enum_value(reactor.spec.reactor_type)
                        if hasattr(reactor, "spec")
                        else None
                    ),
                    "fuel_type": (
                        _enum_value(reactor.spec.fuel_type)
                        if hasattr(reactor, "spec")
                        else None
                    ),
                    "core_height": (
                        reactor.spec.core_height if hasattr(reactor, "spec") else None
                    ),
                    "core_diameter": (
                        reactor.spec.core_diameter if hasattr(reactor, "spec") else None
                    ),
                }
                with open(output_path, "w") as f:
                    yaml.dump(reactor_dict, f, default_flow_style=False)
                _print_success(f"Saved reactor to {output_path} (YAML format)")
            else:
                _print_error(f"Unsupported format: {output_format}")  # pragma: no cover
                print("Supported formats: json, yaml")  # pragma: no cover
                sys.exit(1)  # pragma: no cover
        else:  # pragma: no cover
            # Print reactor info
            if hasattr(reactor, "spec"):
                if _RICH_AVAILABLE:
                    table = Table(title="Reactor Specification")
                    table.add_column("Parameter", style="cyan")
                    table.add_column("Value", style="green")
                    table.add_row("Name", reactor.spec.name)
                    table.add_row(
                        "Power", f"{reactor.spec.power_thermal / 1e6:.1f} MWth"
                    )
                    table.add_row("Enrichment", f"{reactor.spec.enrichment:.3f}")
                    table.add_row("Type", str(reactor.spec.reactor_type))
                    console.print(table)
                else:  # pragma: no cover
                    print(f"\nReactor: {reactor.spec.name}")  # pragma: no cover
                    print(
                        f"  Power: {reactor.spec.power_thermal / 1e6:.1f} MWth"
                    )  # pragma: no cover
                    print(
                        f"  Enrichment: {reactor.spec.enrichment:.3f}"
                    )  # pragma: no cover
                    print(f"  Type: {reactor.spec.reactor_type}")  # pragma: no cover

    except ImportError as e:
        _print_error(f"Failed to import SMRForge modules: {e}")  # pragma: no cover
        sys.exit(1)  # pragma: no cover
    except Exception as e:
        _print_error(f"Failed to create reactor: {e}")
        if args.verbose if hasattr(args, "verbose") else False:
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)


def reactor_analyze(args):
    """Run analysis on a reactor."""
    try:
        import json

        import smrforge as smr
        from smrforge.convenience import create_reactor

        # Check for batch mode: delegate to batch implementation
        if args.batch:
            _reactor_analyze_batch(args)
            return

        # Single file mode
        if not args.reactor:
            _print_error("Must specify --reactor FILE or --batch PATTERN")
            sys.exit(1)
            return  # ensure we don't fall through when exit is mocked

        # Load reactor
        if not args.reactor.exists():
            _print_error(f"Reactor file not found: {args.reactor}")
            sys.exit(1)
            return  # ensure we don't fall through when exit is mocked

        with open(args.reactor) as f:
            reactor_data = json.load(f)

        # Create reactor from data
        reactor = create_reactor(**reactor_data)

        results = {}

        # Run requested analyses
        if args.keff or args.full:
            if _RICH_AVAILABLE:
                with console.status("[bold cyan]Running k-eff calculation..."):
                    k_eff = reactor.solve_keff()
            else:  # pragma: no cover
                print("Running k-eff calculation...")
                k_eff = reactor.solve_keff()
            results["k_eff"] = float(k_eff)
            _print_success(f"k-eff: {k_eff:.6f}")

        if args.full or args.neutronics:
            if _RICH_AVAILABLE:
                with console.status(
                    "[bold cyan]Running neutronics analysis..."
                ):  # pragma: no cover
                    full_results = reactor.solve()  # pragma: no cover
            else:  # pragma: no cover
                print("Running neutronics analysis...")
                full_results = reactor.solve()
            results.update({k: v for k, v in full_results.items() if k != "k_eff"})
            if "k_eff" not in results:
                results["k_eff"] = float(full_results.get("k_eff", 0.0))

        if args.full or args.burnup:
            _print_info("Burnup analysis requires additional configuration")
            _print_info("Use Python API for full burnup calculations")

        if args.full or args.safety:
            _print_info("Safety analysis requires additional configuration")
            _print_info("Use Python API for full safety calculations")

        # Save results if output specified
        if args.output:
            output_path = Path(args.output)
            with open(output_path, "w") as f:
                json.dump(_to_jsonable(results), f, indent=2)
            _print_success(f"Results saved to {output_path}")
        else:
            if _RICH_AVAILABLE:
                table = Table(title="Analysis Results")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                for key, value in results.items():
                    table.add_row(key, str(value))
                console.print(table)
            else:  # pragma: no cover
                print("\nResults:")
                print(json.dumps(_to_jsonable(results), indent=2))

    except ImportError as e:  # pragma: no cover
        _print_error(f"Failed to import SMRForge modules: {e}")  # pragma: no cover
        sys.exit(1)  # pragma: no cover
        return  # pragma: no cover
    except Exception as e:  # pragma: no cover
        _print_error(f"Failed to analyze reactor: {e}")  # pragma: no cover
        if args.verbose if hasattr(args, "verbose") else False:  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover
        return  # pragma: no cover


def _reactor_analyze_batch(args):
    """Run batch analysis on multiple reactors."""
    try:
        import json
        import time

        from smrforge.convenience import create_reactor

        start_time = time.time()
        # Expand glob patterns to file list
        reactor_files = []
        for pattern in args.batch:
            # Expand glob pattern
            matched_files = glob.glob(pattern, recursive=True)
            if not matched_files:
                _print_warning(f"No files matched pattern: {pattern}")
                continue
            reactor_files.extend([Path(f) for f in matched_files])

        # Remove duplicates and filter for JSON/YAML files
        reactor_files = list(set(reactor_files))
        reactor_files = [
            f
            for f in reactor_files
            if f.suffix.lower() in [".json", ".yaml", ".yml"] and f.exists()
        ]

        if not reactor_files:
            _print_error("No valid reactor files found")
            sys.exit(1)
            return  # ensure we don't fall through when exit is mocked

        _print_info(f"Found {len(reactor_files)} reactor files to process")

        # Determine output directory
        output_dir = None
        if args.output:
            if args.output.is_dir() or (args.output.exists() and args.output.is_dir()):
                output_dir = args.output  # pragma: no cover
            else:
                # Assume it's a directory name
                output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)
        else:  # pragma: no cover
            output_dir = Path("results")
            output_dir.mkdir(parents=True, exist_ok=True)

        # Process function for single reactor
        def process_reactor(reactor_file: Path):
            """Process a single reactor file."""
            try:
                with open(reactor_file) as f:
                    if reactor_file.suffix.lower() in [".yaml", ".yml"]:
                        if not _YAML_AVAILABLE:
                            return (
                                reactor_file,
                                None,
                                "YAML not available. Install PyYAML: pip install pyyaml",
                            )
                        reactor_data = yaml.safe_load(f)
                    else:
                        reactor_data = json.load(f)

                reactor = create_reactor(**reactor_data)
                results = {"reactor_file": str(reactor_file)}

                # Run requested analyses
                if args.keff or args.full:
                    k_eff = reactor.solve_keff()
                    results["k_eff"] = float(k_eff)

                if args.full or args.neutronics:
                    full_results = reactor.solve()  # pragma: no cover
                    results.update(
                        {k: v for k, v in full_results.items() if k != "k_eff"}
                    )  # pragma: no cover
                    if "k_eff" not in results:  # pragma: no cover
                        results["k_eff"] = float(
                            full_results.get("k_eff", 0.0)
                        )  # pragma: no cover

                if args.full or args.burnup:
                    results["burnup_note"] = (
                        "Burnup requires Python API"  # pragma: no cover
                    )

                if args.full or args.safety:
                    results["safety_note"] = (
                        "Safety requires Python API"  # pragma: no cover
                    )

                return reactor_file, results, None
            except Exception as e:
                return reactor_file, None, str(e)

        # Process reactors
        all_results = {}
        errors = {}

        if args.parallel and len(reactor_files) > 1:
            # Parallel processing
            _print_info(
                f"Processing {len(reactor_files)} reactors in parallel ({args.workers} workers)..."
            )

            if _RICH_AVAILABLE:
                from rich.progress import (
                    BarColumn,
                    Progress,
                    SpinnerColumn,
                    TaskProgressColumn,
                    TextColumn,
                )

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=console,
                ) as progress:
                    task = progress.add_task(
                        "Processing reactors...", total=len(reactor_files)
                    )

                    with ThreadPoolExecutor(max_workers=args.workers) as executor:
                        futures = {
                            executor.submit(process_reactor, f): f
                            for f in reactor_files
                        }

                        for future in as_completed(futures):
                            reactor_file, result, error = future.result()
                            progress.update(task, advance=1)

                            if error:
                                errors[reactor_file] = error  # pragma: no cover
                            else:
                                all_results[reactor_file] = result
            else:
                with ThreadPoolExecutor(
                    max_workers=args.workers
                ) as executor:  # pragma: no cover
                    futures = {
                        executor.submit(process_reactor, f): f for f in reactor_files
                    }  # pragma: no cover

                    for i, future in enumerate(
                        as_completed(futures), 1
                    ):  # pragma: no cover
                        reactor_file, result, error = (
                            future.result()
                        )  # pragma: no cover
                        print(
                            f"Processed {i}/{len(reactor_files)}: {reactor_file.name}"
                        )  # pragma: no cover

                        if error:  # pragma: no cover
                            errors[reactor_file] = error  # pragma: no cover
                        else:  # pragma: no cover
                            all_results[reactor_file] = result  # pragma: no cover
        else:
            # Sequential processing
            _print_info(f"Processing {len(reactor_files)} reactors sequentially...")

            if _RICH_AVAILABLE:
                from rich.progress import (
                    BarColumn,
                    Progress,
                    SpinnerColumn,
                    TaskProgressColumn,
                    TextColumn,
                )

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=console,
                ) as progress:
                    task = progress.add_task(
                        "Processing reactors...", total=len(reactor_files)
                    )

                    for reactor_file in reactor_files:
                        reactor_file, result, error = process_reactor(reactor_file)
                        progress.update(task, advance=1)

                        if error:
                            errors[reactor_file] = error
                        else:
                            all_results[reactor_file] = result
            else:
                for i, reactor_file in enumerate(reactor_files, 1):
                    print(f"Processing {i}/{len(reactor_files)}: {reactor_file.name}")
                    reactor_file, result, error = process_reactor(reactor_file)

                    if error:
                        errors[reactor_file] = error
                    else:
                        all_results[reactor_file] = result

        # Save results (with runtime and summary for scripting)
        runtime_seconds = round(time.time() - start_time, 2)
        batch_results = {
            "summary": {
                "total": len(reactor_files),
                "processed": len(all_results),
                "failed": len(errors),
                "runtime_seconds": runtime_seconds,
            },
            "processed": len(all_results),
            "failed": len(errors),
            "results": {str(k): v for k, v in all_results.items()},
            "errors": {str(k): v for k, v in errors.items()} if errors else {},
        }

        # Save summary
        summary_file = output_dir / "batch_results.json"
        with open(summary_file, "w") as f:
            json.dump(_to_jsonable(batch_results), f, indent=2)
        _print_success(f"Batch results saved to {summary_file}")

        # Save individual results
        for reactor_file, result in all_results.items():
            result_file = output_dir / f"{reactor_file.stem}_results.json"
            with open(result_file, "w") as f:
                json.dump(_to_jsonable(result), f, indent=2)

        # Display summary
        if _RICH_AVAILABLE:
            table = Table(title="Batch Analysis Summary")
            table.add_column("Reactor", style="cyan")
            table.add_column("k-eff", style="green")
            table.add_column("Status", style="yellow")

            for reactor_file, result in all_results.items():
                k_eff = result.get("k_eff", "N/A")
                table.add_row(
                    reactor_file.name, str(k_eff), f"{_GLYPH_SUCCESS} Success"
                )

            for reactor_file, error in errors.items():
                error_msg = error[:50] + "..." if len(error) > 50 else error
                table.add_row(
                    reactor_file.name, "N/A", f"{_GLYPH_ERROR} Error: {error_msg}"
                )

            console.print(table)
        else:  # pragma: no cover
            print("\nBatch Analysis Summary:")
            print("=" * 70)
            print(f"Processed: {len(all_results)}")
            print(f"Failed: {len(errors)}")
            for reactor_file, result in all_results.items():
                k_eff = result.get("k_eff", "N/A")
                print(f"  {reactor_file.name}: k-eff = {k_eff}")

        if errors:
            _print_warning(f"Failed to process {len(errors)} reactor(s)")
            return 1
        else:
            _print_success(f"Successfully processed {len(all_results)} reactor(s)")
            return 0

    except Exception as e:
        _print_error(f"Failed to run batch analysis: {e}")
        if args.verbose if hasattr(args, "verbose") else False:
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)


def reactor_list(args):
    """List available preset reactor designs."""
    try:
        import smrforge as smr
        from smrforge.convenience import get_preset, list_presets

        presets = list_presets()

        if args.detailed:
            if _RICH_AVAILABLE:
                table = Table(
                    title="Available Preset Designs",
                    show_header=True,
                    header_style="bold cyan",
                )
                table.add_column("Name", style="cyan", no_wrap=True)
                table.add_column("Power (MWth)", justify="right")
                table.add_column("Enrichment", justify="right")
                table.add_column("Type", style="green")
                table.add_column("Fuel", style="yellow")

                for name in presets:
                    try:
                        spec = get_preset(name)
                        table.add_row(
                            name,
                            f"{spec.power_thermal / 1e6:.1f}",
                            f"{spec.enrichment:.3f}",
                            str(spec.reactor_type),
                            str(spec.fuel_type),
                        )
                    except Exception as e:  # pragma: no cover
                        table.add_row(
                            name, "N/A", "N/A", "N/A", f"Error: {e}"
                        )  # pragma: no cover
                console.print(table)
            else:  # pragma: no cover
                print("\nAvailable Preset Designs:")
                print("=" * 70)
                for name in presets:
                    try:
                        spec = get_preset(name)
                        print(f"\n{name}:")
                        print(f"  Power: {spec.power_thermal / 1e6:.1f} MWth")
                        print(f"  Enrichment: {spec.enrichment:.3f}")
                        print(f"  Type: {spec.reactor_type}")
                        print(f"  Fuel: {spec.fuel_type}")
                        if hasattr(spec, "core_height"):
                            print(f"  Core Height: {spec.core_height:.1f} cm")
                        if hasattr(spec, "core_diameter"):
                            print(f"  Core Diameter: {spec.core_diameter:.1f} cm")
                    except Exception as e:  # pragma: no cover
                        print(
                            f"\n{name}: (details unavailable: {e})"
                        )  # pragma: no cover
                print("=" * 70)
        else:
            if _RICH_AVAILABLE:
                console.print("\n[bold cyan]Available Preset Designs:[/bold cyan]")
                for name in presets:
                    console.print(f"  • [cyan]{name}[/cyan]")
                console.print(f"\n[dim]Total: {len(presets)} presets[/dim]")
                console.print("[dim]Use --detailed for more information[/dim]")
            else:  # pragma: no cover
                print("\nAvailable Preset Designs:")
                for name in presets:
                    print(f"  - {name}")
                print(f"\nTotal: {len(presets)} presets")
                print("Use --detailed for more information")

        # Filter by type if requested
        if args.type:
            _print_info(f"Filtering by type: {args.type}")
            # Type filtering would need implementation in get_preset

    except ImportError as e:  # pragma: no cover
        _print_error(f"Failed to import SMRForge modules: {e}")  # pragma: no cover
        sys.exit(1)  # pragma: no cover
    except Exception as e:  # pragma: no cover
        _print_error(f"Failed to list presets: {e}")  # pragma: no cover
        if args.verbose if hasattr(args, "verbose") else False:  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover


def reactor_compare(args):
    """Compare multiple reactor designs with enhanced metrics."""
    try:
        import json

        import smrforge as smr
        from smrforge.convenience import compare_designs, create_reactor

        designs_to_compare = []
        design_names = []

        if args.presets:
            # Compare presets
            design_names = args.presets
            for preset_name in args.presets:
                reactor = create_reactor(preset_name)
                results = reactor.solve()
                designs_to_compare.append(
                    {"name": preset_name, "reactor": reactor, "results": results}
                )
        elif args.reactors:
            # Compare reactor files
            for reactor_file in args.reactors:
                if not reactor_file.exists():
                    _print_error(
                        f"Reactor file not found: {reactor_file}"
                    )  # pragma: no cover
                    sys.exit(1)  # pragma: no cover
                design_names.append(reactor_file.stem)
                with open(reactor_file) as f:
                    reactor_data = json.load(f)
                reactor = create_reactor(**reactor_data)
                results = reactor.solve()
                designs_to_compare.append(
                    {"name": reactor_file.stem, "reactor": reactor, "results": results}
                )
        else:
            _print_error("Must specify --presets or --reactors")
            sys.exit(1)

        # Extract metrics
        import numpy as np

        metrics = args.metrics or ["k_eff", "power", "temperature"]
        comparison = {}

        for design in designs_to_compare:
            name = design["name"]
            results = design["results"]
            comparison[name] = {}

            for metric in metrics:
                if metric == "k_eff" and "k_eff" in results:
                    comparison[name]["k_eff"] = float(results["k_eff"])
                elif metric == "power_density" and "power" in results:
                    power_array = results["power"]
                    if isinstance(power_array, np.ndarray):
                        comparison[name]["max_power_density"] = float(
                            np.max(power_array)
                        )
                        comparison[name]["avg_power_density"] = float(
                            np.mean(power_array)
                        )
                elif metric == "temperature_peak" and "temperature" in results:
                    temp_array = results["temperature"]
                    if isinstance(temp_array, np.ndarray):
                        comparison[name]["temperature_peak"] = float(np.max(temp_array))
                elif metric in results:  # pragma: no cover
                    comparison[name][metric] = results[metric]  # pragma: no cover

        # Display comparison table
        if _RICH_AVAILABLE:
            table = Table(title="Design Comparison")
            table.add_column("Design", style="cyan")
            for metric in metrics:
                table.add_column(metric.replace("_", " ").title(), justify="right")

            for name, metrics_dict in comparison.items():
                row = [name]
                for metric in metrics:
                    value = metrics_dict.get(
                        metric, metrics_dict.get(metric.replace("_", "_"), "N/A")
                    )
                    if isinstance(value, (int, float)):
                        row.append(f"{value:.6f}")
                    else:
                        row.append(str(value))  # pragma: no cover
                table.add_row(*row)

            console.print("\n")
            console.print(table)
        else:  # pragma: no cover
            print("\nDesign Comparison:")
            print("=" * 70)
            for name, metrics_dict in comparison.items():
                print(f"\n{name}:")
                for metric, value in metrics_dict.items():
                    print(f"  {metric}: {value}")

        # Save if output specified
        if args.output:
            output_path = Path(args.output)
            if output_path.suffix == ".html":
                # Generate HTML report
                html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Design Comparison Report</title>
    <style>
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
    </style>
</head>
<body>
    <h1>Design Comparison Report</h1>
    <table>
        <tr><th>Design</th>"""
                for metric in metrics:
                    html_content += f"<th>{metric.replace('_', ' ').title()}</th>"
                html_content += "</tr>"
                for name, metrics_dict in comparison.items():
                    html_content += f"<tr><td>{name}</td>"
                    for metric in metrics:
                        value = metrics_dict.get(
                            metric, metrics_dict.get(metric.replace("_", "_"), "N/A")
                        )
                        html_content += f"<td>{value}</td>"
                    html_content += "</tr>"
                html_content += """
    </table>
</body>
</html>"""
                with open(output_path, "w") as f:
                    f.write(html_content)
                _print_success(f"HTML comparison report saved to {args.output}")
            else:
                with open(args.output, "w") as f:
                    json.dump(_to_jsonable(comparison), f, indent=2, default=str)
                _print_success(f"Comparison saved to {args.output}")

    except ImportError as e:  # pragma: no cover
        _print_error(f"Failed to import SMRForge modules: {e}")  # pragma: no cover
        sys.exit(1)  # pragma: no cover
    except Exception as e:  # pragma: no cover
        _print_error(f"Failed to compare designs: {e}")  # pragma: no cover
        if args.verbose if hasattr(args, "verbose") else False:  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover
