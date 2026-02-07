"""
SMRForge CLI

Command-line interface for SMRForge, including dashboard launcher.
All features remain available via Python API and CLI.
"""

import argparse
import smrforge
import json
import sys
import glob
from pathlib import Path
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

# Rich library for better UX (progress bars, colored output, tables)
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.panel import Panel
    from rich import print as rprint
    _RICH_AVAILABLE = True
except ImportError:
    _RICH_AVAILABLE = False
    # Fallback to basic print
    rprint = print

console = Console() if _RICH_AVAILABLE else None


def _supports_unicode(text: str) -> bool:
    """Best-effort check whether the active output encoding supports `text`."""
    stream = None
    if _RICH_AVAILABLE and console is not None:
        stream = getattr(console, "file", None)
    if stream is None:
        stream = sys.stdout
    encoding = getattr(stream, "encoding", None) or "utf-8"
    try:
        text.encode(encoding)
        return True
    except Exception:
        return False


_GLYPH_SUCCESS = "✓" if _supports_unicode("✓") else "OK"
_GLYPH_ERROR = "✗" if _supports_unicode("✗") else "X"
_GLYPH_INFO = "ℹ" if _supports_unicode("ℹ") else "i"
_GLYPH_WARNING = "⚠" if _supports_unicode("⚠") else "!"


def _to_jsonable(obj: Any) -> Any:
    """Convert common non-JSON types (e.g., numpy arrays) into JSON-safe values."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, set):
        return [_to_jsonable(v) for v in sorted(obj, key=str)]
    return obj


def _print_success(message: str):
    """Print success message with styling if rich is available."""
    if _RICH_AVAILABLE:
        try:
            console.print(f"[bold green]{_GLYPH_SUCCESS}[/bold green] {message}")
        except UnicodeEncodeError:
            print(f"{_GLYPH_SUCCESS} {message}")
    else:
        print(f"{_GLYPH_SUCCESS} {message}")


def _print_error(message: str):
    """Print error message with styling if rich is available."""
    if _RICH_AVAILABLE:
        try:
            console.print(f"[bold red]{_GLYPH_ERROR}[/bold red] {message}")
        except UnicodeEncodeError:
            print(f"{_GLYPH_ERROR} {message}")
    else:
        print(f"{_GLYPH_ERROR} {message}")


def _print_info(message: str):
    """Print info message with styling if rich is available."""
    if _RICH_AVAILABLE:
        try:
            console.print(f"[blue]{_GLYPH_INFO}[/blue] {message}")
        except UnicodeEncodeError:
            print(f"{_GLYPH_INFO} {message}")
    else:
        print(f"{_GLYPH_INFO} {message}")


def _print_warning(message: str):
    """Print warning message with styling if rich is available."""
    if _RICH_AVAILABLE:
        try:
            console.print(f"[bold yellow]{_GLYPH_WARNING}[/bold yellow] {message}")
        except UnicodeEncodeError:
            print(f"{_GLYPH_WARNING} {message}")
    else:
        print(f"{_GLYPH_WARNING} {message}")


def serve_dashboard(args):
    """
    Launch the SMRForge web dashboard.
    
    Args:
        args: Parsed command-line arguments
    """
    # Check for Dash dependencies first
    try:
        import dash
        import dash_bootstrap_components
    except ImportError as e:
        if _RICH_AVAILABLE:
            console.print(Panel(
                "[bold red]ERROR: Dashboard dependencies not installed[/bold red]\n\n"
                "The SMRForge web dashboard requires Dash and related packages.\n\n"
                "[bold]To install dashboard dependencies:[/bold]\n"
                "  [cyan]pip install dash dash-bootstrap-components[/cyan]\n\n"
                "Or install all visualization dependencies:\n"
                "  [cyan]pip install smrforge[viz][/cyan]\n\n"
                f"After installation, run:\n"
                f"  [cyan]smrforge serve --host {args.host} --port {args.port}[/cyan]",
                title="Dashboard Setup",
                border_style="red"
            ))
        else:
            print("=" * 70)
            print("ERROR: Dashboard dependencies not installed")
            print("=" * 70)
            print("\nThe SMRForge web dashboard requires Dash and related packages.")
            print("\nTo install dashboard dependencies:")
            print("  pip install dash dash-bootstrap-components")
            print("\nOr install all visualization dependencies:")
            print("  pip install smrforge[viz]")
            print("\nAfter installation, run:")
            print(f"  smrforge serve --host {args.host} --port {args.port}")
            print("=" * 70)
        sys.exit(1)
        return  # ensure we don't fall through when exit is mocked
    
    try:
        from smrforge.gui import run_server
        
        if _RICH_AVAILABLE:
            console.print(Panel(
                f"[bold cyan]Starting SMRForge Dashboard...[/bold cyan]\n\n"
                f"Dashboard will be available at: [cyan]http://{args.host}:{args.port}[/cyan]\n"
                f"Press [bold]Ctrl+C[/bold] to stop the server",
                title="SMRForge Dashboard",
                border_style="cyan"
            ))
        else:
            print("=" * 70)
            print("Starting SMRForge Dashboard...")
            print("=" * 70)
            print(f"\nDashboard will be available at: http://{args.host}:{args.port}")
            print("Press Ctrl+C to stop the server\n")
            print("=" * 70)
        
        run_server(
            host=args.host,
            port=args.port,
            debug=args.debug,
        )
    except ImportError as e:
        _print_error(f"Failed to import dashboard module: {e}")
        print("\nThis may indicate a missing dependency or installation issue.")
        print("Try installing dashboard dependencies:")
        print("  pip install dash dash-bootstrap-components")
        sys.exit(1)
    except Exception as e:
        _print_error(f"Failed to start dashboard: {e}")
        print("\nPlease check:")
        print("  1. Dashboard dependencies are installed: pip install dash dash-bootstrap-components")
        print("  2. Port is not already in use (try different port with --port)")
        print("  3. Firewall allows connections on the specified port")
        sys.exit(1)


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
            if hasattr(smr, 'create_reactor'):
                create_reactor = smr.create_reactor
            if hasattr(smr, 'list_presets'):
                list_presets = smr.list_presets
        except Exception:
            pass
        
        # Strategy 2: Try from convenience module
        if create_reactor is None or list_presets is None:
            try:
                from smrforge.convenience import create_reactor, list_presets
            except ImportError:
                pass
        
        # Strategy 3: Fallback - try importing convenience.py directly
        if create_reactor is None or list_presets is None:
            try:
                import importlib.util
                convenience_file = Path(__file__).parent.parent / "convenience.py"
                if convenience_file.exists():
                    spec = importlib.util.spec_from_file_location("_convenience_cli", convenience_file)
                    convenience_mod = importlib.util.module_from_spec(spec)
                    # Add parent to path so relative imports work
                    parent_dir = str(convenience_file.parent)
                    if parent_dir not in sys.path:
                        sys.path.insert(0, parent_dir)
                    spec.loader.exec_module(convenience_mod)
                    create_reactor = convenience_mod.create_reactor
                    list_presets = convenience_mod.list_presets
            except Exception:
                pass
        
        # Final check - if still None, raise error
        if create_reactor is None or list_presets is None:
            raise ImportError(
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
                _print_error(f"Config file not found: {args.config}")
                sys.exit(1)
                return
            
            # Load config file
            if args.config.suffix in ['.yaml', '.yml']:
                if not _YAML_AVAILABLE:
                    _print_error("YAML support not available. Install PyYAML: pip install pyyaml")
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
                kwargs['power_mw'] = args.power
            if args.enrichment:
                kwargs['enrichment'] = args.enrichment
            if args.type:
                kwargs['reactor_type'] = args.type
            if args.core_height:
                kwargs['core_height'] = args.core_height
            if args.core_diameter:
                kwargs['core_diameter'] = args.core_diameter
            if args.fuel_type:
                kwargs['fuel_type'] = args.fuel_type
            
            reactor = create_reactor(**kwargs)
            _print_success("Created reactor with custom parameters")
            
        else:
            _print_error("Must specify --preset, --config, or custom parameters")
            sys.exit(1)
            return
        
        # Save reactor if output specified
        if args.output:
            output_path = Path(args.output)
            output_format = args.format or output_path.suffix[1:] if output_path.suffix else 'json'
            
            if output_format == 'json':
                # Save as JSON (simple serialization)
                reactor_dict = {
                    'name': reactor.spec.name if hasattr(reactor, 'spec') else 'reactor',
                    'power_mw': reactor.spec.power_thermal / 1e6 if hasattr(reactor, 'spec') else None,
                    'enrichment': reactor.spec.enrichment if hasattr(reactor, 'spec') else None,
                    'reactor_type': _enum_value(reactor.spec.reactor_type) if hasattr(reactor, 'spec') else None,
                    'fuel_type': _enum_value(reactor.spec.fuel_type) if hasattr(reactor, 'spec') else None,
                    'core_height': reactor.spec.core_height if hasattr(reactor, 'spec') else None,
                    'core_diameter': reactor.spec.core_diameter if hasattr(reactor, 'spec') else None,
                }
                with open(output_path, 'w') as f:
                    json.dump(_to_jsonable(reactor_dict), f, indent=2)
                _print_success(f"Saved reactor to {output_path} (JSON format)")
            elif output_format in ['yaml', 'yml']:
                if not _YAML_AVAILABLE:
                    _print_error("YAML support not available. Install PyYAML: pip install pyyaml")
                    sys.exit(1)
                reactor_dict = {
                    'name': reactor.spec.name if hasattr(reactor, 'spec') else 'reactor',
                    'power_mw': reactor.spec.power_thermal / 1e6 if hasattr(reactor, 'spec') else None,
                    'enrichment': reactor.spec.enrichment if hasattr(reactor, 'spec') else None,
                    'reactor_type': _enum_value(reactor.spec.reactor_type) if hasattr(reactor, 'spec') else None,
                    'fuel_type': _enum_value(reactor.spec.fuel_type) if hasattr(reactor, 'spec') else None,
                    'core_height': reactor.spec.core_height if hasattr(reactor, 'spec') else None,
                    'core_diameter': reactor.spec.core_diameter if hasattr(reactor, 'spec') else None,
                }
                with open(output_path, 'w') as f:
                    yaml.dump(reactor_dict, f, default_flow_style=False)
                _print_success(f"Saved reactor to {output_path} (YAML format)")
            else:
                _print_error(f"Unsupported format: {output_format}")
                print("Supported formats: json, yaml")
                sys.exit(1)
        else:
            # Print reactor info
            if hasattr(reactor, 'spec'):
                if _RICH_AVAILABLE:
                    table = Table(title="Reactor Specification")
                    table.add_column("Parameter", style="cyan")
                    table.add_column("Value", style="green")
                    table.add_row("Name", reactor.spec.name)
                    table.add_row("Power", f"{reactor.spec.power_thermal / 1e6:.1f} MWth")
                    table.add_row("Enrichment", f"{reactor.spec.enrichment:.3f}")
                    table.add_row("Type", str(reactor.spec.reactor_type))
                    console.print(table)
                else:
                    print(f"\nReactor: {reactor.spec.name}")
                    print(f"  Power: {reactor.spec.power_thermal / 1e6:.1f} MWth")
                    print(f"  Enrichment: {reactor.spec.enrichment:.3f}")
                    print(f"  Type: {reactor.spec.reactor_type}")
        
    except ImportError as e:
        _print_error(f"Failed to import SMRForge modules: {e}")
        sys.exit(1)
    except Exception as e:
        _print_error(f"Failed to create reactor: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def reactor_analyze(args):
    """Run analysis on a reactor."""
    try:
        import smrforge as smr
        from smrforge.convenience import create_reactor
        import json
        
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
            else:
                print("Running k-eff calculation...")
                k_eff = reactor.solve_keff()
            results['k_eff'] = float(k_eff)
            _print_success(f"k-eff: {k_eff:.6f}")
        
        if args.full or args.neutronics:
            if _RICH_AVAILABLE:
                with console.status("[bold cyan]Running neutronics analysis..."):
                    full_results = reactor.solve()
            else:
                print("Running neutronics analysis...")
                full_results = reactor.solve()
            results.update({k: v for k, v in full_results.items() if k != 'k_eff'})
            if 'k_eff' not in results:
                results['k_eff'] = float(full_results.get('k_eff', 0.0))
        
        if args.full or args.burnup:
            _print_info("Burnup analysis requires additional configuration")
            _print_info("Use Python API for full burnup calculations")
        
        if args.full or args.safety:
            _print_info("Safety analysis requires additional configuration")
            _print_info("Use Python API for full safety calculations")
        
        # Save results if output specified
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
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
            else:
                print("\nResults:")
                print(json.dumps(_to_jsonable(results), indent=2))
        
    except ImportError as e:
        _print_error(f"Failed to import SMRForge modules: {e}")
        sys.exit(1)
        return
    except Exception as e:
        _print_error(f"Failed to analyze reactor: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)
        return


def _reactor_analyze_batch(args):
    """Run batch analysis on multiple reactors."""
    try:
        import time
        from smrforge.convenience import create_reactor
        import json
        
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
        reactor_files = [f for f in reactor_files if f.suffix.lower() in ['.json', '.yaml', '.yml'] and f.exists()]
        
        if not reactor_files:
            _print_error("No valid reactor files found")
            sys.exit(1)
            return  # ensure we don't fall through when exit is mocked
        
        _print_info(f"Found {len(reactor_files)} reactor files to process")
        
        # Determine output directory
        output_dir = None
        if args.output:
            if args.output.is_dir() or (args.output.exists() and args.output.is_dir()):
                output_dir = args.output
            else:
                # Assume it's a directory name
                output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = Path('results')
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process function for single reactor
        def process_reactor(reactor_file: Path):
            """Process a single reactor file."""
            try:
                with open(reactor_file) as f:
                    if reactor_file.suffix.lower() in ['.yaml', '.yml']:
                        if not _YAML_AVAILABLE:
                            return reactor_file, None, "YAML not available. Install PyYAML: pip install pyyaml"
                        reactor_data = yaml.safe_load(f)
                    else:
                        reactor_data = json.load(f)
                
                reactor = create_reactor(**reactor_data)
                results = {'reactor_file': str(reactor_file)}
                
                # Run requested analyses
                if args.keff or args.full:
                    k_eff = reactor.solve_keff()
                    results['k_eff'] = float(k_eff)
                
                if args.full or args.neutronics:
                    full_results = reactor.solve()
                    results.update({k: v for k, v in full_results.items() if k != 'k_eff'})
                    if 'k_eff' not in results:
                        results['k_eff'] = float(full_results.get('k_eff', 0.0))
                
                if args.full or args.burnup:
                    results['burnup_note'] = "Burnup requires Python API"
                
                if args.full or args.safety:
                    results['safety_note'] = "Safety requires Python API"
                
                return reactor_file, results, None
            except Exception as e:
                return reactor_file, None, str(e)
        
        # Process reactors
        all_results = {}
        errors = {}
        
        if args.parallel and len(reactor_files) > 1:
            # Parallel processing
            _print_info(f"Processing {len(reactor_files)} reactors in parallel ({args.workers} workers)...")
            
            if _RICH_AVAILABLE:
                from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task("Processing reactors...", total=len(reactor_files))
                    
                    with ThreadPoolExecutor(max_workers=args.workers) as executor:
                        futures = {executor.submit(process_reactor, f): f for f in reactor_files}
                        
                        for future in as_completed(futures):
                            reactor_file, result, error = future.result()
                            progress.update(task, advance=1)
                            
                            if error:
                                errors[reactor_file] = error
                            else:
                                all_results[reactor_file] = result
            else:
                with ThreadPoolExecutor(max_workers=args.workers) as executor:
                    futures = {executor.submit(process_reactor, f): f for f in reactor_files}
                    
                    for i, future in enumerate(as_completed(futures), 1):
                        reactor_file, result, error = future.result()
                        print(f"Processed {i}/{len(reactor_files)}: {reactor_file.name}")
                        
                        if error:
                            errors[reactor_file] = error
                        else:
                            all_results[reactor_file] = result
        else:
            # Sequential processing
            _print_info(f"Processing {len(reactor_files)} reactors sequentially...")
            
            if _RICH_AVAILABLE:
                from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task("Processing reactors...", total=len(reactor_files))
                    
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
            'summary': {
                'total': len(reactor_files),
                'processed': len(all_results),
                'failed': len(errors),
                'runtime_seconds': runtime_seconds,
            },
            'processed': len(all_results),
            'failed': len(errors),
            'results': {str(k): v for k, v in all_results.items()},
            'errors': {str(k): v for k, v in errors.items()} if errors else {}
        }
        
        # Save summary
        summary_file = output_dir / 'batch_results.json'
        with open(summary_file, 'w') as f:
            json.dump(_to_jsonable(batch_results), f, indent=2)
        _print_success(f"Batch results saved to {summary_file}")
        
        # Save individual results
        for reactor_file, result in all_results.items():
            result_file = output_dir / f"{reactor_file.stem}_results.json"
            with open(result_file, 'w') as f:
                json.dump(_to_jsonable(result), f, indent=2)
        
        # Display summary
        if _RICH_AVAILABLE:
            table = Table(title="Batch Analysis Summary")
            table.add_column("Reactor", style="cyan")
            table.add_column("k-eff", style="green")
            table.add_column("Status", style="yellow")
            
            for reactor_file, result in all_results.items():
                k_eff = result.get('k_eff', 'N/A')
                table.add_row(reactor_file.name, str(k_eff), f"{_GLYPH_SUCCESS} Success")
            
            for reactor_file, error in errors.items():
                error_msg = error[:50] + "..." if len(error) > 50 else error
                table.add_row(reactor_file.name, "N/A", f"{_GLYPH_ERROR} Error: {error_msg}")
            
            console.print(table)
        else:
            print("\nBatch Analysis Summary:")
            print("=" * 70)
            print(f"Processed: {len(all_results)}")
            print(f"Failed: {len(errors)}")
            for reactor_file, result in all_results.items():
                k_eff = result.get('k_eff', 'N/A')
                print(f"  {reactor_file.name}: k-eff = {k_eff}")
        
        if errors:
            _print_warning(f"Failed to process {len(errors)} reactor(s)")
            return 1
        else:
            _print_success(f"Successfully processed {len(all_results)} reactor(s)")
            return 0
    
    except Exception as e:
        _print_error(f"Failed to run batch analysis: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def reactor_list(args):
    """List available preset reactor designs."""
    try:
        import smrforge as smr
        from smrforge.convenience import list_presets, get_preset
        
        presets = list_presets()
        
        if args.detailed:
            if _RICH_AVAILABLE:
                table = Table(title="Available Preset Designs", show_header=True, header_style="bold cyan")
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
                            str(spec.fuel_type)
                        )
                    except Exception as e:
                        table.add_row(name, "N/A", "N/A", "N/A", f"Error: {e}")
                console.print(table)
            else:
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
                        if hasattr(spec, 'core_height'):
                            print(f"  Core Height: {spec.core_height:.1f} cm")
                        if hasattr(spec, 'core_diameter'):
                            print(f"  Core Diameter: {spec.core_diameter:.1f} cm")
                    except Exception as e:
                        print(f"\n{name}: (details unavailable: {e})")
                print("=" * 70)
        else:
            if _RICH_AVAILABLE:
                console.print("\n[bold cyan]Available Preset Designs:[/bold cyan]")
                for name in presets:
                    console.print(f"  • [cyan]{name}[/cyan]")
                console.print(f"\n[dim]Total: {len(presets)} presets[/dim]")
                console.print("[dim]Use --detailed for more information[/dim]")
            else:
                print("\nAvailable Preset Designs:")
                for name in presets:
                    print(f"  - {name}")
                print(f"\nTotal: {len(presets)} presets")
                print("Use --detailed for more information")
        
        # Filter by type if requested
        if args.type:
            _print_info(f"Filtering by type: {args.type}")
            # Type filtering would need implementation in get_preset
        
    except ImportError as e:
        _print_error(f"Failed to import SMRForge modules: {e}")
        sys.exit(1)
    except Exception as e:
        _print_error(f"Failed to list presets: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def reactor_compare(args):
    """Compare multiple reactor designs with enhanced metrics."""
    try:
        import smrforge as smr
        from smrforge.convenience import create_reactor, compare_designs
        import json
        
        designs_to_compare = []
        design_names = []
        
        if args.presets:
            # Compare presets
            design_names = args.presets
            for preset_name in args.presets:
                reactor = create_reactor(preset_name)
                results = reactor.solve()
                designs_to_compare.append({
                    "name": preset_name,
                    "reactor": reactor,
                    "results": results
                })
        elif args.reactors:
            # Compare reactor files
            for reactor_file in args.reactors:
                if not reactor_file.exists():
                    _print_error(f"Reactor file not found: {reactor_file}")
                    sys.exit(1)
                design_names.append(reactor_file.stem)
                with open(reactor_file) as f:
                    reactor_data = json.load(f)
                reactor = create_reactor(**reactor_data)
                results = reactor.solve()
                designs_to_compare.append({
                    "name": reactor_file.stem,
                    "reactor": reactor,
                    "results": results
                })
        else:
            _print_error("Must specify --presets or --reactors")
            sys.exit(1)
        
        # Extract metrics
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
                        comparison[name]["max_power_density"] = float(np.max(power_array))
                        comparison[name]["avg_power_density"] = float(np.mean(power_array))
                elif metric == "temperature_peak" and "temperature" in results:
                    temp_array = results["temperature"]
                    if isinstance(temp_array, np.ndarray):
                        comparison[name]["temperature_peak"] = float(np.max(temp_array))
                elif metric in results:
                    comparison[name][metric] = results[metric]
        
        # Display comparison table
        if _RICH_AVAILABLE:
            from rich.table import Table
            table = Table(title="Design Comparison")
            table.add_column("Design", style="cyan")
            for metric in metrics:
                table.add_column(metric.replace("_", " ").title(), justify="right")
            
            for name, metrics_dict in comparison.items():
                row = [name]
                for metric in metrics:
                    value = metrics_dict.get(metric, metrics_dict.get(metric.replace("_", "_"), "N/A"))
                    if isinstance(value, (int, float)):
                        row.append(f"{value:.6f}")
                    else:
                        row.append(str(value))
                table.add_row(*row)
            
            console.print("\n")
            console.print(table)
        else:
            print("\nDesign Comparison:")
            print("=" * 70)
            for name, metrics_dict in comparison.items():
                print(f"\n{name}:")
                for metric, value in metrics_dict.items():
                    print(f"  {metric}: {value}")
        
        # Save if output specified
        if args.output:
            output_path = Path(args.output)
            if output_path.suffix == '.html':
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
                        value = metrics_dict.get(metric, metrics_dict.get(metric.replace("_", "_"), "N/A"))
                        html_content += f"<td>{value}</td>"
                    html_content += "</tr>"
                html_content += """
    </table>
</body>
</html>"""
                with open(output_path, 'w') as f:
                    f.write(html_content)
                _print_success(f"HTML comparison report saved to {args.output}")
            else:
                with open(args.output, 'w') as f:
                    json.dump(_to_jsonable(comparison), f, indent=2, default=str)
                _print_success(f"Comparison saved to {args.output}")
        
    except ImportError as e:
        _print_error(f"Failed to import SMRForge modules: {e}")
        sys.exit(1)
    except Exception as e:
        _print_error(f"Failed to compare designs: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def data_setup(args):
    """Setup ENDF data directory (integrate existing command)."""
    try:
        from smrforge.core.endf_setup import setup_endf_data_interactive
        
        if args.endf_dir:
            endf_dir = Path(args.endf_dir)
            if not endf_dir.exists():
                _print_error(f"ENDF directory not found: {endf_dir}")
                sys.exit(1)
            
            # Non-interactive setup (would need implementation)
            _print_info(f"Setting up ENDF data from: {endf_dir}")
            _print_info("NOTE: Interactive setup is recommended. Use without --endf-dir for interactive mode.")
            # For now, call interactive setup
            setup_endf_data_interactive()
        else:
            # Interactive setup
            setup_endf_data_interactive()
        
    except ImportError as e:
        _print_error(f"Failed to import ENDF setup module: {e}")
        sys.exit(1)
    except Exception as e:
        _print_error(f"Failed to setup ENDF data: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def data_download(args):
    """Download ENDF nuclear data."""
    try:
        from smrforge.data_downloader import download_endf_data
        
        kwargs = {}
        if args.library:
            kwargs['library'] = args.library
        if args.nuclide_set:
            kwargs['nuclide_set'] = args.nuclide_set
        if args.nuclides:
            kwargs['isotopes'] = args.nuclides
        if args.output:
            kwargs['output_dir'] = str(args.output)
        if args.max_workers:
            kwargs['max_workers'] = args.max_workers
        if args.validate:
            kwargs['validate'] = True
        if args.resume:
            kwargs['resume'] = True
        
        _print_info(f"Downloading ENDF data...")
        _print_info(f"  Library: {kwargs.get('library', 'ENDF-B-VIII.1')}")
        
        stats = download_endf_data(**kwargs)
        
        if _RICH_AVAILABLE:
            table = Table(title="Download Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Downloaded", str(stats.get('downloaded', 0)))
            table.add_row("Skipped", str(stats.get('skipped', 0)))
            table.add_row("Failed", str(stats.get('failed', 0)))
            table.add_row("Output Directory", str(stats.get('output_dir', 'N/A')))
            console.print(table)
        else:
            print(f"\n✓ Download complete:")
            print(f"  Downloaded: {stats.get('downloaded', 0)} files")
            print(f"  Skipped: {stats.get('skipped', 0)} files")
            print(f"  Failed: {stats.get('failed', 0)} files")
            print(f"  Output: {stats.get('output_dir', 'N/A')}")
        
    except ImportError as e:
        _print_error(f"Data downloader not available: {e}")
        print("Install required dependencies or use manual ENDF setup")
        sys.exit(1)
    except Exception as e:
        _print_error(f"Failed to download data: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def data_validate(args):
    """Validate ENDF files."""
    try:
        from smrforge.core.reactor_core import NuclearDataCache, scan_endf_directory
        
        if args.endf_dir:
            endf_dir = Path(args.endf_dir)
            if not endf_dir.exists():
                _print_error(f"ENDF directory not found: {endf_dir}")
                sys.exit(1)
            
            _print_info(f"Scanning ENDF directory: {endf_dir}")
            
            # Scan directory
            scan_results = scan_endf_directory(endf_dir)
            
            # Validate files
            total_files = scan_results.get('total_files', 0)
            valid_files = scan_results.get('valid_files', 0)
            nuclides = scan_results.get('nuclides', [])
            
            if _RICH_AVAILABLE:
                table = Table(title="ENDF Validation Results")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                table.add_row("Total Files", str(total_files))
                table.add_row("Valid Files", str(valid_files))
                table.add_row("Invalid Files", str(total_files - valid_files))
                table.add_row("Unique Nuclides", str(len(nuclides)))
                table.add_row("Directory Structure", scan_results.get('directory_structure', 'unknown'))
                console.print(table)
                
                if nuclides:
                    console.print(f"\n[bold]Sample nuclides found:[/bold] {', '.join(nuclides[:10])}")
                    if len(nuclides) > 10:
                        console.print(f"[dim]... and {len(nuclides) - 10} more[/dim]")
            else:
                print(f"\nENDF Validation Results:")
                print(f"  Total Files: {total_files}")
                print(f"  Valid Files: {valid_files}")
                print(f"  Invalid Files: {total_files - valid_files}")
                print(f"  Unique Nuclides: {len(nuclides)}")
                print(f"  Directory Structure: {scan_results.get('directory_structure', 'unknown')}")
                if nuclides:
                    print(f"\nSample nuclides: {', '.join(nuclides[:10])}")
            
            # Save report if output specified
            if args.output:
                report = {
                    'validation_date': str(Path.cwd()),
                    'endf_directory': str(endf_dir),
                    'results': scan_results
                }
                with open(args.output, 'w') as f:
                    json.dump(_to_jsonable(report), f, indent=2)
                _print_success(f"Validation report saved to {args.output}")
            
        elif args.files:
            # Validate specific files
            valid_count = 0
            invalid_count = 0
            
            for file_path in args.files:
                file_path = Path(file_path)
                if not file_path.exists():
                    _print_error(f"File not found: {file_path}")
                    invalid_count += 1
                    continue
                
                is_valid = NuclearDataCache._validate_endf_file(file_path)
                if is_valid:
                    valid_count += 1
                    _print_success(f"{file_path.name}: Valid")
                else:
                    invalid_count += 1
                    _print_error(f"{file_path.name}: Invalid")
            
            if _RICH_AVAILABLE:
                console.print(f"\n[bold]Summary:[/bold] {valid_count} valid, {invalid_count} invalid")
            else:
                print(f"\nSummary: {valid_count} valid, {invalid_count} invalid")
        else:
            _print_error("Must specify --endf-dir or --files")
            sys.exit(1)
        
    except ImportError as e:
        _print_error(f"Failed to import validation modules: {e}")
        sys.exit(1)
    except Exception as e:
        _print_error(f"Failed to validate ENDF files: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def data_interpolate(args):
    """Interpolate cross-sections at different temperatures."""
    try:
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide
        from smrforge.core.temperature_interpolation import (
            interpolate_cross_section_temperature,
            InterpolationMethod
        )
        from smrforge.convenience_utils import get_nuclide
        
        # Parse nuclide
        nuclide = get_nuclide(args.nuclide)
        if nuclide is None:
            _print_error(f"Invalid nuclide: {args.nuclide}")
            sys.exit(1)
        
        # Parse interpolation method
        method_map = {
            'linear': InterpolationMethod.LINEAR,
            'log_log': InterpolationMethod.LOG_LOG,
            'spline': InterpolationMethod.SPLINE
        }
        method = method_map[args.method]
        
        # Setup cache
        cache = NuclearDataCache()
        if args.endf_dir:
            cache.local_endf_dir = Path(args.endf_dir)
        
        # Get available temperatures
        available_temps = args.available_temps
        if available_temps is None:
            available_temps = np.array([293.6, 600.0, 900.0, 1200.0])
        else:
            available_temps = np.array(available_temps)
        
        _print_info(f"Interpolating {nuclide.name} {args.reaction} cross-section at {args.temperature:.1f} K")
        _print_info(f"Using {args.method} interpolation method")
        
        # Interpolate
        energy, xs = interpolate_cross_section_temperature(
            cache=cache,
            nuclide=nuclide,
            reaction=args.reaction,
            target_temperature=args.temperature,
            available_temperatures=available_temps,
            method=method
        )
        
        # Display results
        if _RICH_AVAILABLE:
            table = Table(title=f"{nuclide.name} {args.reaction} Cross-Section at {args.temperature:.1f} K")
            table.add_column("Energy [eV]", style="cyan")
            table.add_column("Cross-Section [barn]", style="green")
            
            # Show sample points
            n_points = min(20, len(energy))
            indices = np.linspace(0, len(energy) - 1, n_points, dtype=int)
            for idx in indices:
                table.add_row(f"{energy[idx]:.2e}", f"{xs[idx]:.6e}")
            
            console.print(table)
            console.print(f"\n[bold]Total points:[/bold] {len(energy)}")
            console.print(f"[bold]Energy range:[/bold] {energy[0]:.2e} - {energy[-1]:.2e} eV")
            console.print(f"[bold]XS range:[/bold] {np.min(xs):.6e} - {np.max(xs):.6e} barn")
        else:
            print(f"\n{nuclide.name} {args.reaction} Cross-Section at {args.temperature:.1f} K")
            print(f"  Total points: {len(energy)}")
            print(f"  Energy range: {energy[0]:.2e} - {energy[-1]:.2e} eV")
            print(f"  XS range: {np.min(xs):.6e} - {np.max(xs):.6e} barn")
        
        # Save output
        if args.output:
            output_path = Path(args.output)
            if output_path.suffix.lower() == '.csv':
                import csv
                with open(output_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Energy [eV]', 'Cross-Section [barn]'])
                    for e, x in zip(energy, xs):
                        writer.writerow([e, x])
            else:
                # JSON format
                data = {
                    'nuclide': nuclide.name,
                    'reaction': args.reaction,
                    'temperature': args.temperature,
                    'method': args.method,
                    'energy': energy.tolist(),
                    'cross_section': xs.tolist()
                }
                with open(output_path, 'w') as f:
                    json.dump(_to_jsonable(data), f, indent=2)
            _print_success(f"Results saved to {args.output}")
        
        # Plot if requested
        if args.plot or args.plot_output:
            try:
                import matplotlib.pyplot as plt
                plt.figure(figsize=(10, 6))
                plt.loglog(energy, xs, 'b-', linewidth=2, label=f'{nuclide.name} {args.reaction}')
                plt.xlabel('Energy [eV]')
                plt.ylabel('Cross-Section [barn]')
                plt.title(f'{nuclide.name} {args.reaction} at {args.temperature:.1f} K ({args.method} interpolation)')
                plt.grid(True, alpha=0.3)
                plt.legend()
                
                if args.plot_output:
                    plt.savefig(args.plot_output, dpi=150, bbox_inches='tight')
                    _print_success(f"Plot saved to {args.plot_output}")
                else:
                    plt.show()
            except ImportError:
                _print_warning("Matplotlib not available for plotting")
        
    except Exception as e:
        _print_error(f"Failed to interpolate cross-section: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def data_shield(args):
    """Calculate self-shielded cross-sections."""
    try:
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide
        from smrforge.core.self_shielding_integration import get_cross_section_with_self_shielding
        from smrforge.convenience_utils import get_nuclide
        
        # Parse nuclide
        nuclide = get_nuclide(args.nuclide)
        if nuclide is None:
            _print_error(f"Invalid nuclide: {args.nuclide}")
            sys.exit(1)
        
        # Setup cache
        cache = NuclearDataCache()
        if args.endf_dir:
            cache.local_endf_dir = Path(args.endf_dir)
        
        _print_info(f"Calculating self-shielded {nuclide.name} {args.reaction} cross-section")
        _print_info(f"Method: {args.method}, Temperature: {args.temperature:.1f} K, σ₀: {args.sigma_0:.2f} barn")
        
        # Get shielded cross-section
        energy_shielded, xs_shielded = get_cross_section_with_self_shielding(
            cache=cache,
            nuclide=nuclide,
            reaction=args.reaction,
            temperature=args.temperature,
            sigma_0=args.sigma_0,
            method=args.method,
            enable_self_shielding=True
        )
        
        # Get unshielded for comparison if requested
        if args.compare or args.plot:
            energy_unshielded, xs_unshielded = get_cross_section_with_self_shielding(
                cache=cache,
                nuclide=nuclide,
                reaction=args.reaction,
                temperature=args.temperature,
                sigma_0=args.sigma_0,
                method=args.method,
                enable_self_shielding=False
            )
        
        # Display results
        if _RICH_AVAILABLE:
            table = Table(title=f"{nuclide.name} {args.reaction} Self-Shielded Cross-Section")
            table.add_column("Energy [eV]", style="cyan")
            table.add_column("Shielded XS [barn]", style="green")
            if args.compare:
                table.add_column("Unshielded XS [barn]", style="yellow")
                table.add_column("Shielding Factor", style="magenta")
            
            # Show sample points
            n_points = min(20, len(energy_shielded))
            indices = np.linspace(0, len(energy_shielded) - 1, n_points, dtype=int)
            for idx in indices:
                row = [f"{energy_shielded[idx]:.2e}", f"{xs_shielded[idx]:.6e}"]
                if args.compare:
                    unshielded_val = np.interp(energy_shielded[idx], energy_unshielded, xs_unshielded)
                    shielding_factor = xs_shielded[idx] / unshielded_val if unshielded_val > 0 else 1.0
                    row.append(f"{unshielded_val:.6e}")
                    row.append(f"{shielding_factor:.4f}")
                table.add_row(*row)
            
            console.print(table)
            console.print(f"\n[bold]Total points:[/bold] {len(energy_shielded)}")
            console.print(f"[bold]Energy range:[/bold] {energy_shielded[0]:.2e} - {energy_shielded[-1]:.2e} eV")
            console.print(f"[bold]Shielded XS range:[/bold] {np.min(xs_shielded):.6e} - {np.max(xs_shielded):.6e} barn")
            if args.compare:
                avg_shielding = np.mean(xs_shielded) / np.mean(xs_unshielded) if np.mean(xs_unshielded) > 0 else 1.0
                console.print(f"[bold]Average shielding factor:[/bold] {avg_shielding:.4f}")
        else:
            print(f"\n{nuclide.name} {args.reaction} Self-Shielded Cross-Section")
            print(f"  Total points: {len(energy_shielded)}")
            print(f"  Energy range: {energy_shielded[0]:.2e} - {energy_shielded[-1]:.2e} eV")
            print(f"  Shielded XS range: {np.min(xs_shielded):.6e} - {np.max(xs_shielded):.6e} barn")
        
        # Save output
        if args.output:
            output_path = Path(args.output)
            if output_path.suffix.lower() == '.csv':
                import csv
                with open(output_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    if args.compare:
                        writer.writerow(['Energy [eV]', 'Shielded XS [barn]', 'Unshielded XS [barn]', 'Shielding Factor'])
                        for e, xs_s, xs_u in zip(energy_shielded, xs_shielded, 
                                                  np.interp(energy_shielded, energy_unshielded, xs_unshielded)):
                            factor = xs_s / xs_u if xs_u > 0 else 1.0
                            writer.writerow([e, xs_s, xs_u, factor])
                    else:
                        writer.writerow(['Energy [eV]', 'Cross-Section [barn]'])
                        for e, x in zip(energy_shielded, xs_shielded):
                            writer.writerow([e, x])
            else:
                # JSON format
                data = {
                    'nuclide': nuclide.name,
                    'reaction': args.reaction,
                    'temperature': args.temperature,
                    'sigma_0': args.sigma_0,
                    'method': args.method,
                    'energy': energy_shielded.tolist(),
                    'cross_section_shielded': xs_shielded.tolist()
                }
                if args.compare:
                    data['cross_section_unshielded'] = xs_unshielded.tolist()
                    data['shielding_factors'] = (xs_shielded / xs_unshielded).tolist()
                with open(output_path, 'w') as f:
                    json.dump(_to_jsonable(data), f, indent=2)
            _print_success(f"Results saved to {args.output}")
        
        # Plot if requested
        if args.plot or args.plot_output:
            try:
                import matplotlib.pyplot as plt
                plt.figure(figsize=(10, 6))
                plt.loglog(energy_shielded, xs_shielded, 'b-', linewidth=2, 
                          label=f'{nuclide.name} {args.reaction} (shielded)')
                if args.compare:
                    plt.loglog(energy_unshielded, xs_unshielded, 'r--', linewidth=2, 
                              label=f'{nuclide.name} {args.reaction} (unshielded)')
                plt.xlabel('Energy [eV]')
                plt.ylabel('Cross-Section [barn]')
                plt.title(f'{nuclide.name} {args.reaction} Self-Shielding\n'
                         f'T={args.temperature:.1f} K, σ₀={args.sigma_0:.2f} barn, Method={args.method}')
                plt.grid(True, alpha=0.3)
                plt.legend()
                
                if args.plot_output:
                    plt.savefig(args.plot_output, dpi=150, bbox_inches='tight')
                    _print_success(f"Plot saved to {args.plot_output}")
                else:
                    plt.show()
            except ImportError:
                _print_warning("Matplotlib not available for plotting")
        
    except Exception as e:
        _print_error(f"Failed to calculate self-shielded cross-section: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def burnup_run(args):
    """Run burnup/depletion calculation."""
    try:
        from smrforge.burnup import BurnupSolver, BurnupOptions
        from smrforge.convenience import create_reactor
        from smrforge.neutronics.solver import MultiGroupDiffusion
        from smrforge.validation.models import CrossSectionData, SolverOptions
        import json
        import numpy as np
        
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
            time_steps = [0, 365, 730, 1095]  # Default: 0, 1, 2, 3 years
        
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
            _print_info(f"  Checkpoint interval: {args.checkpoint_interval} days")
            _print_info(f"  Checkpoint directory: {args.checkpoint_dir or 'checkpoints/'}")
        if args.resume_from:
            _print_info(f"  Resuming from checkpoint: {args.resume_from}")
        
        _print_info("\nNOTE: Burnup calculation requires geometry and cross-section data.")
        _print_info("For full burnup calculations, use the Python API:")
        print("  from smrforge.burnup import BurnupSolver, BurnupOptions")
        print("  burnup = BurnupSolver(neutronics_solver, burnup_options)")
        if args.resume_from:
            print(f"  inventory = burnup.resume_from_checkpoint('{args.resume_from}')")
        else:
            print("  inventory = burnup.solve()")
        
        # Save options if output specified
        if args.output:
            output_path = Path(args.output)
            options_dict = {
                'time_steps': time_steps,
                'power_density': float(burnup_options.power_density),
                'adaptive_tracking': burnup_options.adaptive_tracking,
                'nuclide_threshold': float(burnup_options.nuclide_threshold),
            }
            with open(output_path, 'w') as f:
                json.dump(_to_jsonable(options_dict), f, indent=2)
            _print_success(f"Burnup options saved to {output_path}")
        
    except ImportError as e:
        _print_error(f"Failed to import burnup modules: {e}")
        sys.exit(1)
        return
    except Exception as e:
        _print_error(f"Failed to run burnup calculation: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)
        return


def validate_run(args):
    """
    Run validation tests with real ENDF files.
    
    This command executes comprehensive validation tests using the validation
    framework. It can use real ENDF files and generate benchmark comparison reports.
    
    Args:
        args: Parsed command-line arguments containing:
            - endf_dir: Path to ENDF-B-VIII.1 directory (optional)
            - tests: Specific test suites to run (optional)
            - benchmarks: Benchmark database file for comparison (optional)
            - output: Output file for validation report (optional)
            - verbose: Enable verbose output (flag)
    
    Raises:
        SystemExit: If validation tests fail or dependencies are missing
    
    Example:
        >>> # Run validation with ENDF files
        >>> smrforge validate run --endf-dir ~/ENDF-B-VIII.1 --verbose
        
        >>> # Run with benchmark comparison
        >>> smrforge validate run --endf-dir ~/ENDF-B-VIII.1 --benchmarks benchmarks.json --output report.txt
    """
    try:
        import subprocess
        from pathlib import Path
        
        # Use the run_validation.py script for proper validation execution
        import os
        # Handle case where Path operations might fail (e.g., in tests with mocked Path)
        try:
            script_path = Path(__file__).parent.parent / "scripts" / "run_validation.py"
            if not script_path.exists():
                script_path = None
        except (TypeError, AttributeError):
            # Path operations failed (likely due to mocking in tests)
            script_path = None
        
        if script_path is None or not script_path.exists():
            _print_error(f"Validation script not found: {script_path}")
            _print_info("Fallback: Running pytest directly...")
            
            # Fallback to direct pytest
            cmd = ['pytest', 'tests/test_validation_comprehensive.py', 'tests/test_endf_workflows_e2e.py', '-v']
            
            if args.endf_dir:
                import os
                # Handle both string and Path objects, and Mock objects in tests
                try:
                    # Check if it's already a Path (but isinstance might fail with mocks)
                    if hasattr(args.endf_dir, 'absolute') and hasattr(args.endf_dir, 'exists'):
                        endf_path = args.endf_dir
                        endf_str = str(endf_path.absolute())
                    else:
                        endf_path = Path(args.endf_dir)
                        endf_str = str(endf_path.absolute())
                    # Keep both env vars for compatibility (tests/scripts vs core auto-detection)
                    os.environ['LOCAL_ENDF_DIR'] = endf_str
                    os.environ['SMRFORGE_ENDF_DIR'] = endf_str
                    cmd.extend(['--endf-dir', endf_str])
                except (TypeError, AttributeError):
                    # Handle Mock objects or other non-Path types
                    endf_str = str(args.endf_dir)
                    os.environ['LOCAL_ENDF_DIR'] = endf_str
                    os.environ['SMRFORGE_ENDF_DIR'] = endf_str
                    cmd.extend(['--endf-dir', endf_str])
                _print_info(f"Using ENDF directory: {args.endf_dir}")
            
            if args.verbose:
                cmd.append('-s')  # Don't capture output
            else:
                cmd.append('-q')  # Quiet mode
            
            if args.tests:
                # Replace default tests with specified ones
                cmd = cmd[:-2]  # Remove default test files
                cmd.extend(args.tests)
            
            _print_info("Running validation tests...")
            result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
            
            if result.returncode == 0:
                _print_success("Validation tests passed")
            else:
                _print_error("Validation tests failed")
                sys.exit(result.returncode)
            
            return
        
        # Build command for run_validation.py script
        cmd = ['python', str(script_path)]
        
        if args.endf_dir:
            endf_path = Path(args.endf_dir) if not isinstance(args.endf_dir, Path) else args.endf_dir
            cmd.extend(['--endf-dir', str(endf_path.absolute())])
            _print_info(f"Using ENDF directory: {args.endf_dir}")
        
        if args.tests:
            cmd.extend(['--tests'] + args.tests)
        
        if args.benchmarks:
            cmd.extend(['--benchmarks', str(args.benchmarks)])

        if args.output:
            cmd.extend(['--output', str(args.output)])
            # Also write structured JSON results next to the report for tooling.
            try:
                json_out = Path(args.output).with_suffix(".json")
                cmd.extend(["--json-output", str(json_out)])
            except Exception:
                pass
        
        if args.verbose:
            cmd.append('--verbose')
        
        _print_info("Running comprehensive validation tests...")
        if _RICH_AVAILABLE:
            console.print(f"[dim]Command: {' '.join(cmd)}[/dim]")
        
        # Run validation script
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent.parent,
            capture_output=not args.verbose
        )
        
        # Print output if not verbose (script will print its own output if verbose)
        if not args.verbose and result.stdout:
            print(result.stdout.decode('utf-8', errors='ignore'))
        
        if result.returncode == 0:
            _print_success("Validation tests completed successfully")
            
            if args.output and Path(args.output).exists():
                _print_success(f"Validation report saved to {args.output}")
            
            if args.benchmarks:
                _print_info("\nTo generate benchmark comparison report:")
                if args.output:
                    print(f"  python scripts/generate_validation_report.py --results {args.output} --benchmarks {args.benchmarks}")
                else:
                    print(f"  python scripts/generate_validation_report.py --benchmarks {args.benchmarks}")
        else:
            _print_error("Validation tests failed")
            if result.stderr:
                print(result.stderr.decode('utf-8', errors='ignore'))
            sys.exit(result.returncode)
        
    except FileNotFoundError as e:
        _print_error(f"Required tool not found: {e}")
        _print_info("Install pytest: pip install pytest")
        sys.exit(1)
    except Exception as e:
        _print_error(f"Failed to run validation tests: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def visualize_geometry(args):
    """Visualize reactor geometry."""
    try:
        import smrforge as smr
        from smrforge.convenience import create_reactor
        from smrforge.visualization.advanced import plot_ray_traced_geometry, export_visualization
        import json
        
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
                backend='plotly' if args.backend == 'plotly' else 'pyvista',
            )
        else:
            # 2D visualization
            from smrforge.visualization.geometry import plot_core_layout
            fig = plot_core_layout(core)
        
        # Save or show
        if args.output:
            export_visualization(fig, args.output, format=args.format or 'png')
            _print_success(f"Visualization saved to {args.output}")
        elif args.interactive:
            if hasattr(fig, 'show'):
                fig.show()
            else:
                _print_info("Interactive display requires plotly backend")
        else:
            if hasattr(fig, 'show'):
                fig.show()
            else:
                _print_info("Figure object created. Use --output to save or --interactive to display")
        
    except ImportError as e:
        _print_error(f"Failed to import visualization modules: {e}")
        sys.exit(1)
        return
    except Exception as e:
        _print_error(f"Failed to visualize geometry: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)
        return


def visualize_flux(args):
    """Plot flux distribution."""
    try:
        from smrforge.visualization.geometry import plot_flux_on_geometry
        import json
        
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
            _print_info(f"Output file specified: {args.output}")
            _print_info("Save visualization using Python API")
        
    except ImportError as e:
        _print_error(f"Failed to import visualization modules: {e}")
        sys.exit(1)
    except Exception as e:
        _print_error(f"Failed to visualize flux: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
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
        if results_format in ['.json']:
            with open(results_path) as f:
                results_data = json.load(f)
        elif results_format in ['.h5', '.hdf5']:
            try:
                import h5py
                with h5py.File(results_path, 'r') as f:
                    # Convert HDF5 groups to dict (simplified)
                    results_data = {}
                    for key in f.keys():
                        if isinstance(f[key], h5py.Group):
                            results_data[key] = {k: v[()] if hasattr(v, '__getitem__') else v for k, v in f[key].items()}
                        else:
                            results_data[key] = f[key][()]
            except ImportError:
                _print_error("HDF5 support not available. Install h5py: pip install h5py")
                sys.exit(1)
        else:
            _print_error(f"Unsupported file format: {results_format}")
            print("Supported formats: json, h5, hdf5")
            sys.exit(1)
        
        _print_info("Generating burnup visualization...")
        
        # Determine what to plot
        plot_types = []
        if args.composition or (not args.keff and not args.burnup and not args.composition):
            plot_types.append('composition')
        if args.keff:
            plot_types.append('keff')
        if args.burnup:
            plot_types.append('burnup')
        
        # Plot k-eff evolution
        if 'keff' in plot_types:
            if 'k_eff' in results_data or 'k_eff_values' in results_data:
                try:
                    import matplotlib.pyplot as plt
                    
                    # Extract k-eff data
                    if 'k_eff_values' in results_data:
                        k_eff_data = results_data['k_eff_values']
                        time_steps = results_data.get('time_steps', list(range(len(k_eff_data))))
                    elif 'k_eff' in results_data:
                        k_eff_data = results_data['k_eff']
                        if isinstance(k_eff_data, list):
                            time_steps = results_data.get('time_steps', list(range(len(k_eff_data))))
                        else:
                            k_eff_data = [k_eff_data]
                            time_steps = [0]
                    else:
                        k_eff_data = []
                    
                    if k_eff_data:
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ax.plot(time_steps, k_eff_data, 'b-o', linewidth=2, markersize=6)
                        ax.axhline(y=1.0, color='r', linestyle='--', label='Critical (k=1.0)')
                        ax.set_xlabel('Time [days]', fontsize=12)
                        ax.set_ylabel('k-eff', fontsize=12)
                        ax.set_title('k-eff Evolution Over Time', fontsize=14, fontweight='bold')
                        ax.grid(True, alpha=0.3)
                        ax.legend()
                        plt.tight_layout()
                        
                        if args.output:
                            output_path = Path(args.output)
                            if 'keff' not in str(output_path.name).lower():
                                stem = output_path.stem
                                suffix = output_path.suffix
                                output_path = output_path.parent / f"{stem}_keff{suffix}"
                            fig.savefig(output_path, format=args.format, dpi=300, bbox_inches='tight')
                            _print_success(f"k-eff plot saved to {output_path}")
                            plt.close(fig)
                        else:
                            plt.show()
                    else:
                        _print_info("No k-eff data found in results file")
                except ImportError:
                    _print_error("Matplotlib not available. Install matplotlib: pip install matplotlib")
            else:
                _print_info("No k-eff data found in results file")
                _print_info("Use Python API to include k-eff in burnup results")
        
        # Plot burnup over time
        if 'burnup' in plot_types:
            if 'burnup' in results_data or 'burnup_values' in results_data:
                try:
                    import matplotlib.pyplot as plt
                    
                    # Extract burnup data
                    if 'burnup_values' in results_data:
                        burnup_data = results_data['burnup_values']
                        time_steps = results_data.get('time_steps', list(range(len(burnup_data))))
                    elif 'burnup' in results_data:
                        burnup_data = results_data['burnup']
                        if isinstance(burnup_data, list):
                            time_steps = results_data.get('time_steps', list(range(len(burnup_data))))
                        else:
                            burnup_data = [burnup_data]
                            time_steps = [0]
                    else:
                        burnup_data = []
                    
                    if burnup_data:
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ax.plot(time_steps, burnup_data, 'g-s', linewidth=2, markersize=6)
                        ax.set_xlabel('Time [days]', fontsize=12)
                        ax.set_ylabel('Burnup [MWd/kgU]', fontsize=12)
                        ax.set_title('Burnup Over Time', fontsize=14, fontweight='bold')
                        ax.grid(True, alpha=0.3)
                        plt.tight_layout()
                        
                        if args.output:
                            output_path = Path(args.output)
                            if 'burnup' not in str(output_path.name).lower():
                                stem = output_path.stem
                                suffix = output_path.suffix
                                output_path = output_path.parent / f"{stem}_burnup{suffix}"
                            fig.savefig(output_path, format=args.format, dpi=300, bbox_inches='tight')
                            _print_success(f"Burnup plot saved to {output_path}")
                            plt.close(fig)
                        else:
                            plt.show()
                    else:
                        _print_info("No burnup data found in results file")
                except ImportError:
                    _print_error("Matplotlib not available. Install matplotlib: pip install matplotlib")
            else:
                _print_info("No burnup data found in results file")
                _print_info("Use Python API to include burnup data in results")
        
        # Plot composition (note: requires inventory and geometry, use Python API)
        if 'composition' in plot_types:
            _print_info("NOTE: Composition plotting requires inventory data and geometry")
            _print_info("Use Python API for full composition visualization:")
            print("  from smrforge.visualization.material_composition import plot_burnup_composition")
            print("  from smrforge.core.reactor_core import Nuclide")
            print("  fig = plot_burnup_composition(inventory, geometry, nuclides)")
        
        # Enhanced visualization features
        backend = getattr(args, 'backend', 'plotly')
        
        # Batch comparison
        if getattr(args, 'batch_comparison', False):
            try:
                from smrforge.burnup.visualization import plot_batch_comparison
                
                # Load batch inventories
                batch_inventories = {}
                if getattr(args, 'batch_results', None):
                    for batch_file in args.batch_results:
                        if not batch_file.exists():
                            _print_error(f"Batch results file not found: {batch_file}")
                            continue
                        
                        with open(batch_file) as f:
                            batch_data = json.load(f)
                        
                        # Try to extract inventory from results
                        # This assumes results contain inventory-like data
                        if 'inventory' in batch_data:
                            batch_inventories[len(batch_inventories)] = batch_data['inventory']
                        elif 'nuclides' in batch_data and 'concentrations' in batch_data:
                            # Create a simple inventory-like object
                            class SimpleInventory:
                                def __init__(self, data):
                                    self.times = data.get('times', [0])
                                    self.burnup = data.get('burnup', [0])
                                    self.nuclides = data.get('nuclides', [])
                                    self.concentrations = data.get('concentrations', [])
                            
                            batch_inventories[len(batch_inventories)] = SimpleInventory(batch_data)
                
                if batch_inventories:
                    fig = plot_batch_comparison(batch_inventories, backend=backend)
                    
                    if args.output:
                        output_path = Path(args.output)
                        if 'batch' not in str(output_path.name).lower():
                            stem = output_path.stem
                            suffix = output_path.suffix
                            output_path = output_path.parent / f"{stem}_batch_comparison{suffix}"
                        
                        if backend == 'plotly':
                            fig.write_html(str(output_path)) if output_path.suffix == '.html' else fig.write_image(str(output_path))
                        else:
                            fig[0].savefig(output_path, format=args.format, dpi=300, bbox_inches='tight')
                        
                        _print_success(f"Batch comparison plot saved to {output_path}")
                    else:
                        if backend == 'plotly':
                            fig.show()
                        else:
                            import matplotlib.pyplot as plt
                            plt.show()
                else:
                    _print_info("No batch data found. Use --batch-results to specify batch result files.")
            except ImportError as e:
                _print_error(f"Failed to import batch comparison visualization: {e}")
        
        # Refueling cycles
        if getattr(args, 'refueling_cycles', False):
            try:
                from smrforge.burnup.visualization import plot_refueling_cycles
                
                _print_info("Refueling cycle visualization requires cycle inventory data")
                _print_info("Use Python API for full refueling cycle visualization:")
                print("  from smrforge.burnup.visualization import plot_refueling_cycles")
                print("  fig = plot_refueling_cycles(cycle_inventories, backend='plotly')")
            except ImportError as e:
                _print_error(f"Failed to import refueling cycle visualization: {e}")
        
        # Control rod effects
        if getattr(args, 'control_rod_effects', False):
            try:
                from smrforge.burnup.visualization import plot_control_rod_effects
                
                # Load with-rods inventory from main results
                with_rods_inventory = None
                if 'inventory' in results_data:
                    with_rods_inventory = results_data['inventory']
                elif 'nuclides' in results_data:
                    class SimpleInventory:
                        def __init__(self, data):
                            self.times = data.get('times', [0])
                            self.burnup = data.get('burnup', [0])
                            self.nuclides = data.get('nuclides', [])
                            self.concentrations = data.get('concentrations', [])
                    with_rods_inventory = SimpleInventory(results_data)
                
                # Load without-rods inventory if provided
                without_rods_inventory = None
                if getattr(args, 'without_rods_results', None):
                    without_rods_path = args.without_rods_results
                    if without_rods_path.exists():
                        with open(without_rods_path) as f:
                            without_rods_data = json.load(f)
                        
                        if 'inventory' in without_rods_data:
                            without_rods_inventory = without_rods_data['inventory']
                        elif 'nuclides' in without_rods_data:
                            class SimpleInventory:
                                def __init__(self, data):
                                    self.times = data.get('times', [0])
                                    self.burnup = data.get('burnup', [0])
                                    self.nuclides = data.get('nuclides', [])
                                    self.concentrations = data.get('concentrations', [])
                            without_rods_inventory = SimpleInventory(without_rods_data)
                
                if with_rods_inventory:
                    fig = plot_control_rod_effects(
                        with_rods_inventory,
                        without_rods_inventory,
                        backend=backend
                    )
                    
                    if args.output:
                        output_path = Path(args.output)
                        if 'control_rod' not in str(output_path.name).lower():
                            stem = output_path.stem
                            suffix = output_path.suffix
                            output_path = output_path.parent / f"{stem}_control_rods{suffix}"
                        
                        if backend == 'plotly':
                            fig.write_html(str(output_path)) if output_path.suffix == '.html' else fig.write_image(str(output_path))
                        else:
                            fig[0].savefig(output_path, format=args.format, dpi=300, bbox_inches='tight')
                        
                        _print_success(f"Control rod effects plot saved to {output_path}")
                    else:
                        if backend == 'plotly':
                            fig.show()
                        else:
                            import matplotlib.pyplot as plt
                            plt.show()
                else:
                    _print_info("No inventory data found in results file for control rod effects visualization")
            except ImportError as e:
                _print_error(f"Failed to import control rod effects visualization: {e}")
        
        # Enhanced dashboard
        if getattr(args, 'dashboard', False):
            try:
                from smrforge.burnup.visualization import plot_burnup_dashboard_enhanced
                
                # Load inventory from results
                inventory = None
                if 'inventory' in results_data:
                    inventory = results_data['inventory']
                elif 'nuclides' in results_data:
                    class SimpleInventory:
                        def __init__(self, data):
                            self.times = data.get('times', [0])
                            self.burnup = data.get('burnup', [0])
                            self.nuclides = data.get('nuclides', [])
                            self.concentrations = data.get('concentrations', [])
                    inventory = SimpleInventory(results_data)
                
                # Load batch inventories if provided
                batch_inventories = None
                if getattr(args, 'batch_results', None):
                    batch_inventories = {}
                    for batch_file in args.batch_results:
                        if batch_file.exists():
                            with open(batch_file) as f:
                                batch_data = json.load(f)
                            if 'inventory' in batch_data or 'nuclides' in batch_data:
                                if 'inventory' in batch_data:
                                    batch_inventories[len(batch_inventories)] = batch_data['inventory']
                                else:
                                    class SimpleInventory:
                                        def __init__(self, data):
                                            self.times = data.get('times', [0])
                                            self.burnup = data.get('burnup', [0])
                                            self.nuclides = data.get('nuclides', [])
                                            self.concentrations = data.get('concentrations', [])
                                    batch_inventories[len(batch_inventories)] = SimpleInventory(batch_data)
                
                if inventory:
                    fig = plot_burnup_dashboard_enhanced(
                        inventory,
                        batch_inventories,
                        backend=backend
                    )
                    
                    if args.output:
                        output_path = Path(args.output)
                        if 'dashboard' not in str(output_path.name).lower():
                            stem = output_path.stem
                            suffix = output_path.suffix
                            output_path = output_path.parent / f"{stem}_dashboard{suffix}"
                        
                        if backend == 'plotly':
                            fig.write_html(str(output_path)) if output_path.suffix == '.html' else fig.write_image(str(output_path))
                        else:
                            fig[0].savefig(output_path, format=args.format, dpi=300, bbox_inches='tight')
                        
                        _print_success(f"Enhanced dashboard saved to {output_path}")
                    else:
                        if backend == 'plotly':
                            fig.show()
                        else:
                            import matplotlib.pyplot as plt
                            plt.show()
                else:
                    _print_info("No inventory data found in results file for dashboard visualization")
            except ImportError as e:
                _print_error(f"Failed to import enhanced dashboard visualization: {e}")
        
    except ImportError as e:
        _print_error(f"Failed to import visualization modules: {e}")
        sys.exit(1)
    except Exception as e:
        _print_error(f"Failed to visualize burnup results: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def decay_heat_calculate(args):
    """Calculate decay heat over time."""
    try:
        from smrforge.decay_heat import DecayHeatCalculator
        from smrforge.core.reactor_core import Nuclide, NuclearDataCache
        import json
        import numpy as np
        
        # Initialize cache
        cache = None
        if getattr(args, 'endf_dir', None):
            cache = NuclearDataCache()
            cache.set_endf_directory(str(args.endf_dir))
        
        calculator = DecayHeatCalculator(cache=cache)
        
        # Load nuclide concentrations
        concentrations = {}
        
        if getattr(args, 'inventory', None):
            # Load from inventory file
            inventory_path = args.inventory
            if not inventory_path.exists():
                _print_error(f"Inventory file not found: {inventory_path}")
                sys.exit(1)
            
            with open(inventory_path) as f:
                inventory_data = json.load(f)
            
            # Extract nuclide concentrations
            if 'nuclides' in inventory_data and 'concentrations' in inventory_data:
                nuclide_names = inventory_data['nuclides']
                conc_values = inventory_data['concentrations']
                
                for name, conc in zip(nuclide_names, conc_values):
                    # Parse nuclide name (e.g., "U235" -> Z=92, A=235)
                    try:
                        from smrforge.convenience_utils import get_nuclide
                        nuclide = get_nuclide(name)
                        concentrations[nuclide] = float(conc)
                    except Exception as e:
                        _print_warning(f"Failed to parse nuclide {name}: {e}")
            else:
                _print_error("Inventory file must contain 'nuclides' and 'concentrations' fields")
                sys.exit(1)
        
        elif getattr(args, 'nuclides', None):
            # Parse from command line arguments
            for nuclide_spec in args.nuclides:
                if ':' not in nuclide_spec:
                    _print_error(f"Invalid nuclide specification: {nuclide_spec}. Use format: U235:1e20")
                    sys.exit(1)
                
                name, conc_str = nuclide_spec.split(':', 1)
                try:
                    from smrforge.convenience_utils import get_nuclide
                    nuclide = get_nuclide(name.strip())
                    concentrations[nuclide] = float(conc_str.strip())
                except Exception as e:
                    _print_error(f"Failed to parse nuclide {name}: {e}")
                    sys.exit(1)
        else:
            _print_error("Must specify --inventory or --nuclides")
            sys.exit(1)
        
        if not concentrations:
            _print_error("No valid nuclide concentrations found")
            sys.exit(1)
        
        _print_info(f"Calculating decay heat for {len(concentrations)} nuclides...")
        
        # Determine time points
        if getattr(args, 'times', None):
            times = np.array([float(t) for t in args.times])
        elif getattr(args, 'time_range', None):
            start, end, num_steps = args.time_range
            times = np.linspace(float(start), float(end), int(num_steps))
        else:
            # Default: 0 to 1 week with 100 points
            times = np.linspace(0, 7 * 24 * 3600, 100)
            _print_info("Using default time range: 0 to 1 week (100 points)")
        
        # Calculate decay heat
        result = calculator.calculate_decay_heat(concentrations, times)
        
        # Prepare output data
        output_data = {
            'times': times.tolist(),
            'times_days': (times / (24 * 3600)).tolist(),
            'total_decay_heat': result.total_decay_heat.tolist(),
            'gamma_decay_heat': result.gamma_decay_heat.tolist(),
            'beta_decay_heat': result.beta_decay_heat.tolist(),
            'nuclide_contributions': {
                str(nuclide): heat.tolist()
                for nuclide, heat in result.nuclide_contributions.items()
            }
        }
        
        # Save results
        if getattr(args, 'output', None):
            with open(args.output, 'w') as f:
                json.dump(_to_jsonable(output_data), f, indent=2)
            _print_success(f"Decay heat results saved to {args.output}")
        
        # Display summary
        if _RICH_AVAILABLE:
            table = Table(title="Decay Heat Summary")
            table.add_column("Time", style="cyan")
            table.add_column("Total [W]", style="green")
            table.add_column("Gamma [W]", style="yellow")
            table.add_column("Beta [W]", style="magenta")
            
            # Show key time points
            key_times = [0, 3600, 86400, 604800]  # 0, 1h, 1d, 1w
            for t_key in key_times:
                if t_key <= times[-1]:
                    idx = np.argmin(np.abs(times - t_key))
                    time_label = f"{times[idx] / 3600:.1f} h" if times[idx] < 86400 else f"{times[idx] / 86400:.1f} d"
                    table.add_row(
                        time_label,
                        f"{result.total_decay_heat[idx]:.2e}",
                        f"{result.gamma_decay_heat[idx]:.2e}",
                        f"{result.beta_decay_heat[idx]:.2e}"
                    )
            
            console.print(table)
        else:
            print("\nDecay Heat Summary:")
            print(f"  Initial (t=0): {result.total_decay_heat[0]:.2e} W")
            print(f"  After 1 hour: {result.get_decay_heat_at_time(3600):.2e} W")
            print(f"  After 1 day: {result.get_decay_heat_at_time(86400):.2e} W")
            print(f"  After 1 week: {result.get_decay_heat_at_time(604800):.2e} W")
        
        # Generate plot
        if getattr(args, 'plot', False) or getattr(args, 'plot_output', None):
            try:
                backend = getattr(args, 'backend', 'plotly')
                
                if backend == 'plotly':
                    try:
                        import plotly.graph_objects as go
                        from plotly.subplots import make_subplots
                        
                        fig = make_subplots(
                            rows=2, cols=1,
                            subplot_titles=("Total Decay Heat", "Gamma vs Beta Decay Heat"),
                            shared_xaxes=True,
                            vertical_spacing=0.1
                        )
                        
                        times_days = times / (24 * 3600)
                        
                        # Total decay heat
                        fig.add_trace(
                            go.Scatter(
                                x=times_days,
                                y=result.total_decay_heat,
                                mode='lines',
                                name='Total',
                                line=dict(width=2, color='blue')
                            ),
                            row=1, col=1
                        )
                        
                        # Gamma and beta
                        fig.add_trace(
                            go.Scatter(
                                x=times_days,
                                y=result.gamma_decay_heat,
                                mode='lines',
                                name='Gamma',
                                line=dict(width=2, color='red')
                            ),
                            row=2, col=1
                        )
                        
                        fig.add_trace(
                            go.Scatter(
                                x=times_days,
                                y=result.beta_decay_heat,
                                mode='lines',
                                name='Beta',
                                line=dict(width=2, color='green')
                            ),
                            row=2, col=1
                        )
                        
                        fig.update_xaxes(title_text="Time [days]", row=2, col=1)
                        fig.update_yaxes(title_text="Decay Heat [W]", row=1, col=1)
                        fig.update_yaxes(title_text="Decay Heat [W]", row=2, col=1)
                        fig.update_layout(
                            title="Decay Heat Over Time",
                            height=700,
                            hovermode="x unified"
                        )
                        
                        if getattr(args, 'plot_output', None):
                            plot_path = args.plot_output
                            if plot_path.suffix == '.html':
                                fig.write_html(str(plot_path))
                            else:
                                fig.write_image(str(plot_path))
                            _print_success(f"Plot saved to {plot_path}")
                        else:
                            fig.show()
                    except ImportError:
                        _print_error("Plotly not available. Install: pip install plotly")
                else:
                    import matplotlib.pyplot as plt
                    
                    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
                    times_days = times / (24 * 3600)
                    
                    # Total decay heat
                    ax1.plot(times_days, result.total_decay_heat, 'b-', linewidth=2, label='Total')
                    ax1.set_ylabel('Decay Heat [W]')
                    ax1.set_title('Total Decay Heat')
                    ax1.grid(True, alpha=0.3)
                    ax1.legend()
                    ax1.set_yscale('log')
                    
                    # Gamma and beta
                    ax2.plot(times_days, result.gamma_decay_heat, 'r-', linewidth=2, label='Gamma')
                    ax2.plot(times_days, result.beta_decay_heat, 'g-', linewidth=2, label='Beta')
                    ax2.set_xlabel('Time [days]')
                    ax2.set_ylabel('Decay Heat [W]')
                    ax2.set_title('Gamma vs Beta Decay Heat')
                    ax2.grid(True, alpha=0.3)
                    ax2.legend()
                    ax2.set_yscale('log')
                    
                    plt.tight_layout()
                    
                    if getattr(args, 'plot_output', None):
                        plot_path = args.plot_output
                        fig.savefig(plot_path, format=args.format, dpi=300, bbox_inches='tight')
                        _print_success(f"Plot saved to {plot_path}")
                        plt.close(fig)
                    else:
                        plt.show()
            except ImportError as e:
                _print_error(f"Failed to generate plot: {e}")
                _print_info("Install matplotlib or plotly for plotting support")
        
    except ImportError as e:
        _print_error(f"Failed to import decay heat modules: {e}")
        sys.exit(1)
    except Exception as e:
        _print_error(f"Failed to calculate decay heat: {e}")
        if getattr(args, 'verbose', False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


# GitHub Actions: feature IDs and metadata (must match scripts/github_workflow_check.py)
GITHUB_ACTIONS_FEATURES = [
    {"id": "ci", "name": "CI", "description": "Tests, lint, build, validation, coverage"},
    {"id": "ci-quick", "name": "CI (quick)", "description": "Fast check: single Python, tests without coverage"},
    {"id": "docs", "name": "Docs", "description": "Build and deploy documentation (GitHub Pages)"},
    {"id": "performance", "name": "Performance", "description": "Performance benchmarks"},
    {"id": "security", "name": "Security", "description": "Security audit (pip-audit, bandit)"},
    {"id": "release", "name": "Release", "description": "Build and publish to PyPI on version tags"},
    {"id": "nightly", "name": "Nightly", "description": "Scheduled full test and validation run"},
    {"id": "docker", "name": "Docker", "description": "Build and push container image (GHCR)"},
    {"id": "dependabot", "name": "Dependabot", "description": "Run tests on Dependabot dependency PRs"},
    {"id": "stale", "name": "Stale", "description": "Mark and close stale issues and PRs"},
]


def _github_repo_root(args: Any) -> Path:
    """Repo root for GitHub commands (--repo-root or cwd)."""
    root = getattr(args, "repo_root", None)
    if root is not None:
        p = Path(root).resolve()
        if not p.is_dir():
            _print_error(f"Repo root is not a directory: {p}")
            sys.exit(1)
        return p
    return Path.cwd().resolve()


def _github_paths(root: Path) -> tuple[Path, Path]:
    """Return (workflows-enabled path, workflows-config path)."""
    gh = root / ".github"
    return gh / "workflows-enabled", gh / "workflows-config.json"


def _read_workflows_enabled(root: Path) -> bool:
    """True if workflows-enabled exists and is 'true'."""
    p, _ = _github_paths(root)
    if not p.exists():
        return False
    return p.read_text().strip().lower() == "true"


def _read_workflows_config(root: Path) -> Dict[str, bool]:
    """Read per-feature config; missing file or key => use default True for backward compat."""
    _, config_path = _github_paths(root)
    out = {f["id"]: True for f in GITHUB_ACTIONS_FEATURES}
    if not config_path.exists():
        return out
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            for fid in out:
                if fid in data and isinstance(data[fid], bool):
                    out[fid] = data[fid]
    except (json.JSONDecodeError, OSError):
        pass
    return out


def _write_workflows_config(root: Path, config: Dict[str, bool]) -> None:
    """Write workflows-config.json (creates .github if needed)."""
    _, config_path = _github_paths(root)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    # Only include known feature IDs
    out = {f["id"]: config.get(f["id"], True) for f in GITHUB_ACTIONS_FEATURES}
    config_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")


def github_actions_status(args: Any) -> None:
    """Show GitHub Actions status (global and per-feature)."""
    try:
        root = _github_repo_root(args)
        enabled_path, config_path = _github_paths(root)
        global_on = _read_workflows_enabled(root)
        config = _read_workflows_config(root)

        if _RICH_AVAILABLE:
            status = "[bold green]ENABLED[/bold green]" if global_on else "[bold red]DISABLED[/bold red]"
            console.print(f"\nGitHub Actions (global): {status}")
            console.print(f"Control file: {enabled_path}")
            if config_path.exists():
                table = Table(title="Feature status")
                table.add_column("Feature", style="cyan")
                table.add_column("Description", style="dim")
                table.add_column("Status", justify="center")
                for f in GITHUB_ACTIONS_FEATURES:
                    on = config.get(f["id"], True)
                    s = "[green]on[/green]" if on else "[red]off[/red]"
                    table.add_row(f["name"], f["description"], s)
                console.print(table)
                console.print(f"Config: {config_path}")
            else:
                _print_info("No per-feature config; all features follow global setting.")
        else:
            status = "ENABLED" if global_on else "DISABLED"
            print(f"\nGitHub Actions (global): {status}")
            print(f"Control file: {enabled_path}")
            if config_path.exists():
                for f in GITHUB_ACTIONS_FEATURES:
                    on = config.get(f["id"], True)
                    print(f"  {f['name']}: {'on' if on else 'off'}")
            else:
                print("No per-feature config; all features follow global.")
        if getattr(args, "output", None):
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump({
                    "enabled": global_on,
                    "file": str(enabled_path),
                    "config_file": str(config_path) if config_path.exists() else None,
                    "features": config,
                }, f, indent=2)
            _print_success(f"Status saved to {args.output}")
    except Exception as e:
        _print_error(f"Failed to check GitHub Actions status: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def github_actions_enable(args: Any) -> None:
    """Enable GitHub Actions (global)."""
    try:
        root = _github_repo_root(args)
        enabled_path, _ = _github_paths(root)
        enabled_path.parent.mkdir(parents=True, exist_ok=True)
        enabled_path.write_text("true\n", encoding="utf-8")
        _print_success("GitHub Actions enabled")
        _print_info(f"Control file updated: {enabled_path}")
        _print_info("Workflows will run on next push or pull request (subject to per-feature config)")
    except Exception as e:
        _print_error(f"Failed to enable GitHub Actions: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def github_actions_disable(args: Any) -> None:
    """Disable GitHub Actions (global)."""
    try:
        root = _github_repo_root(args)
        enabled_path, _ = _github_paths(root)
        enabled_path.parent.mkdir(parents=True, exist_ok=True)
        enabled_path.write_text("false\n", encoding="utf-8")
        _print_success("GitHub Actions disabled")
        _print_info(f"Control file updated: {enabled_path}")
        _print_info("Workflows will be skipped on next push or pull request")
    except Exception as e:
        _print_error(f"Failed to disable GitHub Actions: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def github_actions_list(args: Any) -> None:
    """List GitHub Actions features and their status."""
    try:
        root = _github_repo_root(args)
        global_on = _read_workflows_enabled(root)
        config = _read_workflows_config(root)
        if _RICH_AVAILABLE:
            table = Table(title="GitHub Actions features")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Description", style="dim")
            table.add_column("Runs", justify="center")
            for f in GITHUB_ACTIONS_FEATURES:
                on = config.get(f["id"], True)
                runs = global_on and on
                run_str = "[green]yes[/green]" if runs else "[red]no[/red]"
                table.add_row(f["id"], f["name"], f["description"], run_str)
            console.print(table)
            console.print(f"\nGlobal: {'ON' if global_on else 'OFF'}  |  Use [cyan]smrforge github configure[/cyan] to change features")
        else:
            print("ID          Name         Description                                    Runs")
            print("-" * 70)
            for f in GITHUB_ACTIONS_FEATURES:
                on = config.get(f["id"], True)
                runs = "yes" if (global_on and on) else "no"
                print(f"{f['id']:<11} {f['name']:<12} {f['description']:<44} {runs}")
    except Exception as e:
        _print_error(f"Failed to list features: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def github_actions_set(args: Any) -> None:
    """Set one feature on or off."""
    try:
        root = _github_repo_root(args)
        fid = getattr(args, "feature", "").strip().lower()
        if fid not in [f["id"] for f in GITHUB_ACTIONS_FEATURES]:
            _print_error(f"Unknown feature: {fid}. Use: {', '.join(f['id'] for f in GITHUB_ACTIONS_FEATURES)}")
            sys.exit(1)
        on = getattr(args, "value", "on").strip().lower() in ("on", "true", "1", "yes")
        config = _read_workflows_config(root)
        config[fid] = on
        _write_workflows_config(root, config)
        name = next(f["name"] for f in GITHUB_ACTIONS_FEATURES if f["id"] == fid)
        _print_success(f"Feature '{name}' ({fid}) set to {'on' if on else 'off'}")
    except Exception as e:
        _print_error(f"Failed to set feature: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def github_actions_configure(args: Any) -> None:
    """Interactive or flag-based configuration of which features run in GitHub Actions."""
    try:
        root = _github_repo_root(args)
        _, config_path = _github_paths(root)
        config = _read_workflows_config(root)
        # Apply any --ci/--docs/--performance/--security flags (set by parser)
        for f in GITHUB_ACTIONS_FEATURES:
            key = f["id"].replace("-", "_")
            val = getattr(args, key, None)
            if val is not None:
                config[f["id"]] = val in ("on", "true", "1", "yes")
        # Interactive: prompt for each only when no feature flags were given
        feature_flags = [f["id"].replace("-", "_") for f in GITHUB_ACTIONS_FEATURES]
        any_flag = any(getattr(args, k, None) is not None for k in feature_flags)
        if not any_flag:
            if _RICH_AVAILABLE:
                console.print("\n[bold]GitHub Actions feature selection[/bold]")
                console.print("Choose which workflows run when Actions are enabled. [y] on, [n] off, [Enter] keep current.\n")
            else:
                print("\nGitHub Actions feature selection")
                print("y/n = enable/disable; Enter = keep current\n")
            for f in GITHUB_ACTIONS_FEATURES:
                cur = config.get(f["id"], True)
                prompt = f"  {f['name']} ({f['id']}): {'on' if cur else 'off'} [y/n/Enter]: "
                try:
                    raw = input(prompt).strip().lower()
                except EOFError:
                    break
                if raw in ("y", "yes", "on", "1", "true"):
                    config[f["id"]] = True
                elif raw in ("n", "no", "off", "0", "false"):
                    config[f["id"]] = False
        config_path.parent.mkdir(parents=True, exist_ok=True)
        _write_workflows_config(root, config)
        _print_success("GitHub Actions feature config updated")
        _print_info(f"Config file: {config_path}")
        if _RICH_AVAILABLE:
            table = Table()
            table.add_column("Feature", style="cyan")
            table.add_column("Status", justify="center")
            for f in GITHUB_ACTIONS_FEATURES:
                on = config[f["id"]]
                table.add_row(f["name"], "[green]on[/green]" if on else "[red]off[/red]")
            console.print(table)
    except Exception as e:
        _print_error(f"Failed to configure GitHub Actions: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def config_show(args):
    """Show current configuration."""
    try:
        config_dir = Path.home() / ".smrforge"
        config_file = config_dir / "config.yaml"
        
        if not config_file.exists():
            _print_info("No configuration file found")
            _print_info(f"Configuration file location: {config_file}")
            _print_info("Use 'smrforge config init' to create a default configuration file")
            return
        
        if not _YAML_AVAILABLE:
            _print_error("PyYAML not available. Install PyYAML: pip install pyyaml")
            sys.exit(1)
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f) or {}
        
        if args.key:
            # Show specific key
            keys = args.key.split('.')
            value = config
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    _print_error(f"Configuration key not found: {args.key}")
                    sys.exit(1)
            
            if _RICH_AVAILABLE:
                console.print(f"[cyan]{args.key}[/cyan]: {value}")
            else:
                print(f"{args.key}: {value}")
        else:
            # Show all config
            if _RICH_AVAILABLE:
                table = Table(title="SMRForge Configuration")
                table.add_column("Key", style="cyan")
                table.add_column("Value", style="green")
                
                def add_config_rows(data, prefix=""):
                    for key, value in data.items():
                        full_key = f"{prefix}.{key}" if prefix else key
                        if isinstance(value, dict):
                            add_config_rows(value, full_key)
                        else:
                            table.add_row(full_key, str(value))
                
                add_config_rows(config)
                console.print(table)
            else:
                print("\nSMRForge Configuration:")
                print("=" * 60)
                
                def print_config(data, prefix=""):
                    for key, value in data.items():
                        full_key = f"{prefix}.{key}" if prefix else key
                        if isinstance(value, dict):
                            print_config(value, full_key)
                        else:
                            print(f"{full_key}: {value}")
                
                print_config(config)
                print("=" * 60)
            
            _print_info(f"\nConfiguration file: {config_file}")
    
    except Exception as e:
        _print_error(f"Failed to show configuration: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def config_set(args):
    """Set configuration value."""
    try:
        if not _YAML_AVAILABLE:
            _print_error("PyYAML not available. Install PyYAML: pip install pyyaml")
            sys.exit(1)
            return  # ensure we don't fall through when exit is mocked
        
        config_dir = Path.home() / ".smrforge"
        config_file = config_dir / "config.yaml"
        
        # Load existing config or create new
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}
            config_dir.mkdir(parents=True, exist_ok=True)
        
        # Parse key and set value
        keys = args.key.split('.')
        value = args.value
        
        # Convert value to appropriate type
        try:
            # Try to convert to number
            if '.' in value:
                value = float(value)
            else:
                value = int(value)
        except ValueError:
            # Keep as string, but check for boolean strings
            if value.lower() in ('true', 'yes', 'on'):
                value = True
            elif value.lower() in ('false', 'no', 'off'):
                value = False
        
        # Navigate/create nested structure
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the value
        old_value = current.get(keys[-1], None)
        current[keys[-1]] = value
        
        # Save config
        with open(config_file, 'w') as f:
            yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
        
        if old_value is not None:
            _print_success(f"Updated {args.key}: {old_value} -> {value}")
        else:
            _print_success(f"Set {args.key} = {value}")
        
        _print_info(f"Configuration saved to: {config_file}")
    
    except Exception as e:
        _print_error(f"Failed to set configuration: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)
        return


def config_init(args):
    """Initialize configuration file."""
    try:
        if not _YAML_AVAILABLE:
            _print_error("PyYAML not available. Install PyYAML: pip install pyyaml")
            sys.exit(1)
            return  # ensure we don't fall through when exit is mocked
        
        config_dir = Path.home() / ".smrforge"
        config_file = config_dir / "config.yaml"
        
        if config_file.exists() and not args.force:
            _print_error(f"Configuration file already exists: {config_file}")
            _print_info("Use --force to overwrite existing configuration")
            sys.exit(1)
            return  # ensure we don't fall through when exit is mocked
        
        # Create default config
        default_config = {
            'endf': {
                'default_directory': str(Path.home() / "ENDF-Data"),
                'default_library': 'ENDF-B-VIII.1',
            },
            'cache': {
                'directory': str(config_dir / "cache"),
            },
            'output': {
                'default_directory': './results',
            },
            'log_level': 'INFO',
        }
        
        # Template-specific configs
        if args.template == 'production':
            default_config['log_level'] = 'WARNING'
            default_config['cache'] = {
                'directory': str(config_dir / "cache"),
                'cleanup_interval_days': 30,
            }
        elif args.template == 'development':
            default_config['log_level'] = 'DEBUG'
        
        # Create directory
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Write config
        with open(config_file, 'w') as f:
            yaml.safe_dump(default_config, f, default_flow_style=False, sort_keys=False)
        
        _print_success(f"Initialized configuration file: {config_file}")
        
        if _RICH_AVAILABLE:
            console.print(f"\n[bold]Default configuration:[/bold]")
            table = Table(show_header=False, box=None)
            table.add_column("", style="cyan")
            table.add_column("", style="green")
            for key, value in default_config.items():
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        table.add_row(f"  {key}.{subkey}", str(subvalue))
                else:
                    table.add_row(key, str(value))
            console.print(table)
        else:
            print("\nDefault configuration:")
            for key, value in default_config.items():
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        print(f"  {key}.{subkey}: {subvalue}")
                else:
                    print(f"  {key}: {value}")
        
        _print_info("\nYou can modify the configuration using:")
        print("  smrforge config set <key> <value>")
        print("  smrforge config show")
    
    except Exception as e:
        _print_error(f"Failed to initialize configuration: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)
        return


def shell_interactive(args):
    """Launch interactive Python shell with SMRForge pre-loaded."""
    try:
        # Try IPython first (better UX)
        try:
            from IPython import embed
            from IPython.terminal.embed import InteractiveShellEmbed
            
            # Pre-import SMRForge modules
            import smrforge as smr
            
            # Try multiple import strategies for convenience functions
            create_reactor = getattr(smr, 'create_reactor', None)
            list_presets = getattr(smr, 'list_presets', None)
            
            if create_reactor is None or list_presets is None:
                try:
                    from smrforge.convenience import create_reactor, list_presets
                except ImportError:
                    # Fallback to direct import
                    import importlib.util
                    from pathlib import Path
                    convenience_file = Path(__file__).parent.parent / "convenience.py"
                    if convenience_file.exists():
                        spec = importlib.util.spec_from_file_location("_convenience_shell", convenience_file)
                        convenience_mod = importlib.util.module_from_spec(spec)
                        parent_dir = str(convenience_file.parent)
                        if parent_dir not in sys.path:
                            sys.path.insert(0, parent_dir)
                        spec.loader.exec_module(convenience_mod)
                        create_reactor = convenience_mod.create_reactor
                        list_presets = convenience_mod.list_presets
            
            from smrforge.burnup import BurnupSolver, BurnupOptions
            from smrforge.visualization import plot_core_layout
            
            # Setup banner
            banner = """
╔═══════════════════════════════════════════════════════════════╗
║           SMRForge Interactive Shell (IPython)                ║
╚═══════════════════════════════════════════════════════════════╝

Pre-loaded objects:
  • smr - SMRForge main module
  • create_reactor() - Create reactor from preset or config
  • list_presets() - List available preset designs
  • BurnupSolver, BurnupOptions - Burnup calculation
  • plot_core_layout() - Visualization

Quick start:
  >>> reactor = create_reactor("valar-10")
  >>> k_eff = reactor.solve_keff()
  >>> print(f"k-eff: {k_eff:.6f}")

Type 'help(smr)' for more information or 'exit' to quit.
"""
            exit_msg = "\nExiting SMRForge shell. Goodbye!"
            
            # Launch IPython shell
            ipshell = InteractiveShellEmbed(banner1=banner, exit_msg=exit_msg)
            ipshell()
            
        except ImportError:
            # Fallback to standard Python REPL
            import code
            import sys
            
            # Pre-import SMRForge modules
            import smrforge as smr
            
            # Try multiple import strategies for convenience functions
            create_reactor = getattr(smr, 'create_reactor', None)
            list_presets = getattr(smr, 'list_presets', None)
            
            if create_reactor is None or list_presets is None:
                try:
                    from smrforge.convenience import create_reactor, list_presets
                except ImportError:
                    # Fallback to direct import
                    import importlib.util
                    from pathlib import Path
                    convenience_file = Path(__file__).parent.parent / "convenience.py"
                    if convenience_file.exists():
                        spec = importlib.util.spec_from_file_location("_convenience_shell_repl", convenience_file)
                        convenience_mod = importlib.util.module_from_spec(spec)
                        parent_dir = str(convenience_file.parent)
                        if parent_dir not in sys.path:
                            sys.path.insert(0, parent_dir)
                        spec.loader.exec_module(convenience_mod)
                        create_reactor = convenience_mod.create_reactor
                        list_presets = convenience_mod.list_presets
            
            # Setup banner
            banner = """
╔═══════════════════════════════════════════════════════════════╗
║           SMRForge Interactive Shell (Python REPL)            ║
╚═══════════════════════════════════════════════════════════════╝

Pre-loaded objects:
  • smr - SMRForge main module
  • create_reactor() - Create reactor from preset or config
  • list_presets() - List available preset designs

Quick start:
  >>> reactor = create_reactor("valar-10")
  >>> k_eff = reactor.solve_keff()
  >>> print(f"k-eff: {k_eff:.6f}")

Note: Install IPython for enhanced features: pip install ipython
Type 'help(smr)' for more information or 'exit()' to quit.
"""
            
            print(banner)
            
            # Launch standard Python REPL with pre-loaded globals
            variables = {
                'smr': smr,
                'create_reactor': create_reactor,
                'list_presets': list_presets,
                'exit': sys.exit,
                'quit': sys.exit,
            }
            
            shell = code.InteractiveConsole(variables)
            shell.interact(banner='')
    
    except ImportError as e:
        _print_error(f"Failed to import SMRForge modules: {e}")
        sys.exit(1)
    except Exception as e:
        _print_error(f"Failed to launch interactive shell: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def workflow_run(args):
    """Run workflow from YAML file."""
    try:
        if not _YAML_AVAILABLE:
            _print_error("YAML support not available. Install PyYAML: pip install pyyaml")
            sys.exit(1)
        
        # Load workflow file
        if not args.workflow.exists():
            _print_error(f"Workflow file not found: {args.workflow}")
            sys.exit(1)
        
        with open(args.workflow) as f:
            workflow_data = yaml.safe_load(f)
        
        if not workflow_data or 'steps' not in workflow_data:
            _print_error("Invalid workflow file: must contain 'steps' key")
            sys.exit(1)
        
        _print_info(f"Running workflow: {args.workflow}")
        _print_info(f"Steps: {len(workflow_data['steps'])}")
        
        # Import required modules
        import smrforge as smr
        from smrforge.convenience import create_reactor
        
        # Execute workflow steps
        context = {}  # Store intermediate results
        
        for i, step in enumerate(workflow_data['steps'], 1):
            step_type = step.get('type', '')
            _print_info(f"\nStep {i}/{len(workflow_data['steps'])}: {step_type}")
            
            if step_type == 'create_reactor':
                preset = step.get('preset')
                config = step.get('config')
                output = step.get('output')
                
                if preset:
                    reactor = create_reactor(preset)
                    _print_success(f"Created reactor from preset: {preset}")
                elif config:
                    config_path = Path(config)
                    if not config_path.exists():
                        _print_error(f"Config file not found: {config_path}")
                        continue
                    
                    with open(config_path) as f:
                        if config_path.suffix.lower() in ['.yaml', '.yml']:
                            config_data = yaml.safe_load(f)
                        else:
                            config_data = json.load(f)
                    
                    reactor = create_reactor(**config_data)
                    _print_success(f"Created reactor from config: {config_path}")
                else:
                    _print_error("create_reactor step requires 'preset' or 'config'")
                    continue
                
                context['reactor'] = reactor
                
                if output:
                    # Save reactor
                    output_path = Path(output)
                    # Resolve relative paths relative to workflow file's directory
                    if not output_path.is_absolute():
                        output_path = args.workflow.parent / output_path
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    reactor_dict = {
                        'name': reactor.spec.name if hasattr(reactor, 'spec') else 'reactor',
                        'power_thermal': reactor.spec.power_thermal if hasattr(reactor, 'spec') else 0,
                        'enrichment': reactor.spec.enrichment if hasattr(reactor, 'spec') else 0,
                        'reactor_type': getattr(reactor.spec.reactor_type, "value", str(reactor.spec.reactor_type)) if hasattr(reactor, 'spec') else 'unknown',
                    }
                    
                    with open(output_path, 'w') as f:
                        if output_path.suffix.lower() in ['.yaml', '.yml']:
                            yaml.safe_dump(reactor_dict, f)
                        else:
                            json.dump(_to_jsonable(reactor_dict), f, indent=2)
                    _print_success(f"Saved reactor to: {output_path}")
            
            elif step_type == 'analyze':
                if 'reactor' not in context:
                    _print_error("No reactor in context. Create reactor first.")
                    continue
                
                reactor = context['reactor']
                results = {}
                
                if step.get('keff', False) or step.get('full', False):
                    _print_info("Running k-eff calculation...")
                    k_eff = reactor.solve_keff()
                    results['k_eff'] = float(k_eff)
                    _print_success(f"k-eff: {k_eff:.6f}")
                
                if step.get('neutronics', False) or step.get('full', False):
                    _print_info("Running neutronics analysis...")
                    full_results = reactor.solve()
                    results.update({k: v for k, v in full_results.items() if k != 'k_eff'})
                    if 'k_eff' not in results:
                        results['k_eff'] = float(full_results.get('k_eff', 0.0))
                
                context['results'] = results
                
                # Save results if output specified
                output = step.get('output')
                if output:
                    output_path = Path(output)
                    # Resolve relative paths relative to current working directory
                    if not output_path.is_absolute():
                        output_path = Path.cwd() / output_path
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'w') as f:
                        json.dump(_to_jsonable(results), f, indent=2)
                    _print_success(f"Saved results to: {output_path}")
            
            elif step_type == 'visualize':
                _print_info("Visualization step (use Python API for full visualization)")
                # Visualization would need full implementation
                output = step.get('output')
                if output:
                    _print_info(f"Visualization output would be saved to: {output}")
            
            else:
                _print_warning(f"Unknown step type: {step_type}")
        
        _print_success("\nWorkflow completed successfully!")
    
    except ImportError as e:
        _print_error(f"Failed to import required modules: {e}")
        sys.exit(1)
    except Exception as e:
        _print_error(f"Failed to run workflow: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def sweep_run(args):
    """Run parameter sweep workflow."""
    try:
        from smrforge.workflows import ParameterSweep, SweepConfig
        from pathlib import Path
        
        # Load config from file or build from args
        if getattr(args, "config", None) and Path(args.config).exists():
            config = SweepConfig.from_file(args.config)
            if args.output:
                config.output_dir = Path(args.output)
            if getattr(args, "no_parallel", False):
                config.parallel = False
            if getattr(args, "workers", None) is not None:
                config.max_workers = args.workers
        else:
            if not getattr(args, "params", None) or not args.params:
                _print_error("Either --config FILE or --params ... is required")
                sys.exit(1)
            parameters = {}
            for param_spec in args.params:
                parts = param_spec.split(':')
                if len(parts) == 4:
                    name, start, end, step = parts
                    parameters[name] = (float(start), float(end), float(step))
                elif len(parts) == 2:
                    name, values_str = parts
                    values = [float(v) for v in values_str.split(',')]
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
        
    except ImportError as e:
        _print_error(f"Failed to import required modules: {e}")
        sys.exit(1)
    except Exception as e:
        _print_error(f"Failed to run parameter sweep: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def batch_keff_run(args):
    """Run batch k-eff on multiple reactor files (glob or list)."""
    try:
        from smrforge.convenience import create_reactor
        from smrforge.utils.parallel_batch import batch_solve_keff
        import json
        
        patterns = getattr(args, "reactors", None) or []
        if not patterns:
            _print_error("Specify at least one reactor file or glob (e.g. reactors/*.json)")
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
            _print_error("No valid reactor files found")
            sys.exit(1)
        
        _print_info(f"Loading {len(reactor_files)} reactor(s)...")
        reactors = []
        for p in reactor_files:
            try:
                with open(p, encoding="utf-8") as f:
                    raw = f.read()
                if p.suffix.lower() in (".yaml", ".yml"):
                    if not _YAML_AVAILABLE:
                        _print_error("YAML file given but PyYAML not installed. Install: pip install pyyaml")
                        sys.exit(1)
                    data = yaml.safe_load(raw)
                else:
                    data = json.loads(raw)
                reactors.append(create_reactor(**data))
            except Exception as e:
                _print_error(f"Failed to load {p}: {e}")
                sys.exit(1)
        
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
                "k_eff": [float(k) if not isinstance(k, Exception) else None for k in k_effs],
                "errors": [str(k) if isinstance(k, Exception) else None for k in k_effs],
            }
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            _print_success(f"Results saved to {out_path}")
        
        if _RICH_AVAILABLE:
            table = Table(title="Batch k-eff")
            table.add_column("Reactor", style="cyan")
            table.add_column("k-eff", justify="right", style="green")
            for p, k in zip(reactor_files, k_effs):
                table.add_row(p.name, str(k) if not isinstance(k, Exception) else f"Error: {k}")
            console.print(table)
        else:
            for p, k in zip(reactor_files, k_effs):
                print(f"{p.name}: {k}")
    except Exception as e:
        _print_error(f"Batch k-eff failed: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


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
            table = Table(title="Design point")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", justify="right")
            for k, v in point.items():
                table.add_row(k, f"{v:.6g}" if isinstance(v, (int, float)) else str(v))
            console.print(table)
        else:
            print(json.dumps(point, indent=2))
    except Exception as e:
        _print_error(f"Design point failed: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def workflow_safety_report(args):
    """Generate coupled safety margin report (nominal + optional UQ vs limits)."""
    try:
        from smrforge.convenience import create_reactor
        from smrforge.validation.safety_report import safety_margin_report
        reactor = _load_reactor_from_args(args)
        constraint_set = None
        if getattr(args, "constraints", None) and Path(args.constraints).exists():
            from smrforge.validation.constraints import ConstraintSet
            constraint_set = ConstraintSet.load(Path(args.constraints))
        report = safety_margin_report(reactor, constraint_set=constraint_set)
        out = getattr(args, "output", None)
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                json.dump(report.to_dict(), f, indent=2)
            _print_success(f"Safety report saved to {out}")
        if _RICH_AVAILABLE:
            table = Table(title="Safety margins")
            table.add_column("Constraint", style="cyan")
            table.add_column("Value", justify="right")
            table.add_column("Limit", justify="right")
            table.add_column("Margin", justify="right")
            table.add_column("OK", justify="center")
            for m in report.margins:
                table.add_row(m.name, f"{m.value:.4g} {m.unit}", f"{m.limit:.4g} {m.unit}", f"{m.margin:.4g}", "[green]yes[/green]" if m.within_limit else "[red]no[/red]")
            console.print(table)
            console.print(f"Passed: {'[green]yes[/green]' if report.passed else '[red]no[/red]'}")
        else:
            print(json.dumps(report.to_dict(), indent=2))
    except Exception as e:
        _print_error(f"Safety report failed: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _load_reactor_from_args(args):
    """Load reactor from --reactor (file or preset name)."""
    from smrforge.convenience import create_reactor
    r = getattr(args, "reactor", None)
    if not r:
        _print_error("--reactor FILE or preset name required")
        sys.exit(1)
    r = Path(r) if isinstance(r, str) and (r.endswith(".json") or r.endswith(".yaml") or r.endswith(".yml")) else r
    if isinstance(r, Path) and r.exists():
        with open(r, encoding="utf-8") as f:
            raw = f.read()
        if r.suffix.lower() in (".yaml", ".yml"):
            if not _YAML_AVAILABLE:
                _print_error("PyYAML required for YAML reactor files")
                sys.exit(1)
            data = yaml.safe_load(raw)
        else:
            data = json.loads(raw)
        return create_reactor(**data)
    return create_reactor(name=str(r))


def workflow_doe(args):
    """Generate Design of Experiments (factorial, LHS, Sobol, random)."""
    try:
        from smrforge.workflows.doe import full_factorial, latin_hypercube, random_space_filling, sobol_space_filling
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
            elif method == "sobol":
                design = sobol_space_filling(names, bounds, n_samples, seed=seed)
            else:
                design = random_space_filling(names, bounds, n_samples, seed=seed)
        else:
            _print_error("For factorial use --factors name:v1,v2,v3 (repeat). For lhs/sobol/random use --factors name:low:high (repeat) and --samples N")
            sys.exit(1)
        out = getattr(args, "output", None)
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                json.dump({"method": method, "n_samples": len(design), "design": design}, f, indent=2)
            _print_success(f"DoE ({len(design)} points) saved to {out}")
        else:
            print(json.dumps(design, indent=2))
    except Exception as e:
        _print_error(f"DoE failed: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def workflow_pareto(args):
    """Compute and export Pareto front from sweep results."""
    try:
        from smrforge.visualization.sweep_plots import _to_dataframe, _pareto_front_mask
        import pandas as pd
        p = Path(getattr(args, "sweep_results", None) or "")
        if not p.exists():
            _print_error("--sweep-results FILE.json required")
            sys.exit(1)
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        results = data.get("results", data) if isinstance(data, dict) else data
        df = pd.DataFrame(results) if isinstance(results, list) else pd.DataFrame([results])
        if df.empty:
            _print_error("No results in sweep file")
            sys.exit(1)
        mx = getattr(args, "metric_x", "k_eff")
        my = getattr(args, "metric_y", None)
        if not my:
            numeric = df.select_dtypes(include=[np.number]).columns.tolist()
            my = [c for c in numeric if c != mx][0] if len(numeric) > 1 else numeric[0]
        if mx not in df.columns or my not in df.columns:
            _print_error(f"Metrics {mx}, {my} not in results. Columns: {list(df.columns)}")
            sys.exit(1)
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
            summary = pareto_summary_report(pareto_results, mx, my, maximize_x=True, maximize_y=True)
            payload = {"metric_x": mx, "metric_y": my, "n_pareto": len(pareto_results), "pareto": pareto_results, "summary": summary}
            with open(out, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            _print_success(f"Pareto set ({len(pareto_results)} points) + summary saved to {out}")
        else:
            print(json.dumps(pareto_results, indent=2))
    except Exception as e:
        _print_error(f"Pareto failed: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def workflow_optimize(args):
    """Run design optimization (optionally constraint-aware)."""
    try:
        from smrforge.convenience import create_reactor, get_design_point
        from smrforge.optimization.design import DesignOptimizer
        import numpy as np
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
                _print_error("Each --params must be name:low:high (e.g. enrichment:0.1:0.2)")
                sys.exit(1)
            name, low, high = parts[0].strip(), float(parts[1]), float(parts[2])
            param_names.append(name)
            bounds.append((low, high))
        if not param_names:
            _print_error("At least one --params name:low:high required")
            sys.exit(1)
        def reactor_from_x(x):
            spec = dict(base_spec)
            for i, name in enumerate(param_names):
                spec[name] = float(x[i])
            return create_reactor(**spec)
        objective_name = (getattr(args, "objective", None) or "min_neg_keff").strip().lower()
        if objective_name == "min_neg_keff":
            def obj(x):
                r = reactor_from_x(x)
                return -get_design_point(r)["k_eff"]
        else:
            _print_error("Only objective min_neg_keff (maximize k_eff) supported in CLI for now")
            sys.exit(1)
        use_constraints = getattr(args, "constraints", False)
        if use_constraints and Path(use_constraints).exists():
            from smrforge.validation.constraints import ConstraintSet
            from smrforge.optimization.design import DesignOptimizer
            constraint_set = ConstraintSet.load(Path(use_constraints))
            obj = DesignOptimizer.with_constraint_penalty(obj, reactor_from_x, constraint_set=constraint_set)
        opt = DesignOptimizer(obj, bounds, method=getattr(args, "method", "differential_evolution") or "differential_evolution")
        result = opt.optimize(max_iterations=int(getattr(args, "max_iter", 50)))
        _print_success(f"Optimal f = {result.f_opt:.6g}, success = {result.success}")
        optimal_point = dict(zip(param_names, result.x_opt.tolist()))
        optimal_point["k_eff"] = -result.f_opt if objective_name == "min_neg_keff" else result.f_opt
        out = getattr(args, "output", None)
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                json.dump({"x_opt": result.x_opt.tolist(), "param_names": param_names, "f_opt": result.f_opt, "optimal_point": optimal_point}, f, indent=2)
            _print_success(f"Results saved to {out}")
        if _RICH_AVAILABLE:
            table = Table(title="Optimal parameters")
            for k, v in optimal_point.items():
                table.add_row(k, f"{v:.6g}")
            console.print(table)
        try:
            from smrforge.workflows.audit_log import append_run
            log_path = Path(out).parent / "runs.json" if out else None
            append_run("optimize", args_summary={"reactor": str(reactor_path), "params": param_names}, results_summary={"f_opt": result.f_opt, "success": result.success}, passed=result.success, log_path=log_path)
        except Exception:
            pass
    except Exception as e:
        try:
            from smrforge.workflows.audit_log import append_run
            append_run("optimize", args_summary={"reactor": getattr(args, "reactor", None)}, passed=False, error=str(e))
        except Exception:
            pass
        _print_error(f"Optimize failed: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


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
                continue
            name, nominal, dist = parts[0].strip(), float(parts[1]), (parts[2].strip().lower() if len(parts) > 2 else "normal")
            unc = (float(parts[3]) if len(parts) > 3 else 0.1)
            if dist == "uniform" and len(parts) >= 5:
                b = (float(parts[3]), float(parts[4]))
                uncertain.append(UncertainParameter(name, "uniform", nominal, b))
            else:
                uncertain.append(UncertainParameter(name, dist, nominal, unc))
        if not uncertain:
            _print_error("At least one --params name:nominal:distribution[:uncertainty] required (e.g. enrichment:0.2:normal:0.02)")
            sys.exit(1)
        def model(x_dict):
            spec = dict(base_spec)
            for k, v in x_dict.items():
                spec[k] = v
            r = create_reactor(**spec)
            return get_design_point(r)
        output_names = ["k_eff", "power_thermal_mw"]
        prop = UncertaintyPropagation(uncertain, model, output_names)
        uq_results = prop.propagate(n_samples=n_samples, method="lhs", random_state=int(getattr(args, "seed", 42) or 0))
        out = getattr(args, "output", None)
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            summary = {"mean": uq_results.mean.tolist() if uq_results.mean is not None else [], "std": uq_results.std.tolist() if uq_results.std is not None else [], "output_names": getattr(uq_results, "output_names", [])}
            with open(out, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
            _print_success(f"UQ summary saved to {out}")
        if _RICH_AVAILABLE and uq_results.mean is not None:
            table = Table(title="UQ summary")
            table.add_column("Output", style="cyan")
            table.add_column("Mean", justify="right")
            table.add_column("Std", justify="right")
            for i, oname in enumerate(getattr(uq_results, "output_names", ["output_" + str(i) for i in range(len(uq_results.mean))])):
                table.add_row(str(oname), f"{uq_results.mean[i]:.6g}", f"{uq_results.std[i]:.6g}" if uq_results.std is not None else "N/A")
            console.print(table)
        try:
            from smrforge.workflows.audit_log import append_run
            out_path = getattr(args, "output", None)
            log_path = Path(out_path).parent / "runs.json" if out_path else None
            append_run("uq", args_summary={"reactor": str(reactor_path), "samples": n_samples}, results_summary={"mean": uq_results.mean.tolist() if uq_results.mean is not None else []}, passed=True, log_path=log_path)
        except Exception:
            pass
    except Exception as e:
        try:
            from smrforge.workflows.audit_log import append_run
            append_run("uq", args_summary={"reactor": getattr(args, "reactor", None)}, passed=False, error=str(e))
        except Exception:
            pass
        _print_error(f"UQ failed: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _write_design_study_html(out_dir, design_point, safety_report):
    """Write a simple combined HTML report (design point + safety margins)."""
    from smrforge.validation.safety_report import margin_narrative
    report_dict = safety_report.to_dict() if hasattr(safety_report, "to_dict") else safety_report
    try:
        narrative = margin_narrative(safety_report) if hasattr(safety_report, "margins") and isinstance(getattr(safety_report, "margins", None), list) else ""
    except Exception:
        narrative = ""
    rows_dp = "".join(
        f"<tr><td>{k}</td><td>{v}</td></tr>"
        for k, v in sorted(design_point.items()) if isinstance(v, (int, float))
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
            from smrforge.validation.constraints import ConstraintSet
            constraint_set = ConstraintSet.load(Path(args.constraints))
        report = safety_margin_report(reactor, constraint_set=constraint_set)
        with open(out_dir / "safety_report.json", "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2)
        if getattr(args, "html", False):
            _write_design_study_html(out_dir, point, report)
        _print_success(f"Design study written to {out_dir}")
        if _RICH_AVAILABLE:
            console.print(f"  design_point.json  – steady-state metrics")
            console.print(f"  safety_report.json – margins and pass/fail")
        if getattr(args, "html", False):
            console.print(f"  design_study_report.html – combined report")
        try:
            from smrforge.workflows.audit_log import append_run
            append_run(
                "design-study",
                args_summary={"reactor": getattr(args, "reactor"), "output_dir": str(out_dir)},
                results_summary={"k_eff": point.get("k_eff"), "power_thermal_mw": point.get("power_thermal_mw"), "passed": report.passed},
                passed=report.passed,
                log_path=out_dir / "runs.json",
            )
        except Exception:
            pass
    except Exception as e:
        try:
            from smrforge.workflows.audit_log import append_run
            append_run("design-study", args_summary={"reactor": getattr(args, "reactor", None)}, passed=False, error=str(e))
        except Exception:
            pass
        _print_error(f"Design study failed: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def workflow_variant(args):
    """Save reactor design as a named variant."""
    try:
        from smrforge.convenience import create_reactor, save_variant
        reactor = _load_reactor_from_args(args)
        name = getattr(args, "name", None) or "variant"
        out_dir = getattr(args, "output_dir", None)
        path = save_variant(reactor, name, output_dir=out_dir)
        _print_success(f"Variant saved to {path}")
    except Exception as e:
        _print_error(f"Variant save failed: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def workflow_sensitivity(args):
    """Rank parameters by sensitivity (OAT or Morris) from sweep results."""
    try:
        from smrforge.workflows.sensitivity import one_at_a_time_from_sweep, morris_screening
        p = Path(getattr(args, "sweep_results", None) or "")
        if not p.exists():
            _print_error("--sweep-results FILE.json required")
            sys.exit(1)
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        results = data.get("results", data) if isinstance(data, dict) else data
        if not isinstance(results, list):
            results = [results]
        params = getattr(args, "params", None) or []
        if not params:
            if results and isinstance(results[0], dict):
                p0 = results[0].get("parameters", results[0])
                params = [k for k in p0 if isinstance(p0.get(k), (int, float))]
        if not params:
            _print_error("--params name1 name2 ... or sweep results with parameter keys required")
            sys.exit(1)
        metric = getattr(args, "metric", "k_eff")
        rankings = one_at_a_time_from_sweep(results, params, output_metric=metric)
        out = getattr(args, "output", None)
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                json.dump([{"parameter": r.parameter, "effect": r.effect, "rank": r.rank} for r in rankings], f, indent=2)
            _print_success(f"Sensitivity ranking saved to {out}")
        else:
            for r in rankings:
                print(f"  {r.rank}. {r.parameter}: effect={r.effect:.4f}")
    except Exception as e:
        _print_error(f"Sensitivity failed: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


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
            results = [results]
        params = getattr(args, "params", None) or []
        if not params and results and isinstance(results[0], dict):
            p0 = results[0].get("parameters", results[0])
            params = [k for k in p0 if isinstance(p0.get(k), (int, float))]
        if not params:
            _print_error("--params name1 name2 ... or sweep results with parameter keys required")
            sys.exit(1)
        metric = getattr(args, "metric", "k_eff")
        sobol_dict = sobol_indices_from_sweep_results(results, params, output_metric=metric)
        out = getattr(args, "output", None)
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                json.dump(sobol_dict, f, indent=2)
            _print_success(f"Sobol indices saved to {out}")
        else:
            for label, si in sobol_dict.items():
                print(f"{label}: S1={si.get('S1', [])}, ST={si.get('ST', [])}")
    except Exception as e:
        _print_error(f"Sobol failed: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def workflow_scenario(args):
    """Run scenario-based design (multiple constraint sets / missions)."""
    try:
        from smrforge.workflows.scenario_design import run_scenario_design, scenario_comparison_report
        reactor = _load_reactor_from_args(args)
        scenarios = getattr(args, "scenarios", None) or []
        if not scenarios:
            _print_error("--scenarios name:path_or_preset ... required (e.g. baseload:regulatory_limits)")
            sys.exit(1)
        scenario_dict = {}
        for s in scenarios:
            part = s.split(":", 1)
            name = part[0].strip()
            val = part[1].strip() if len(part) > 1 else "regulatory_limits"
            scenario_dict[name] = val
        results = run_scenario_design(reactor, scenario_dict)
        out_dir = Path(getattr(args, "output_dir", None) or "scenario_output")
        out_dir.mkdir(parents=True, exist_ok=True)
        report_path = out_dir / "scenario_comparison.md"
        scenario_comparison_report(results, output_path=report_path)
        out_json = out_dir / "scenario_results.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump({k: {"passed": v.passed, "violations": v.violations, "metrics": v.metrics} for k, v in results.items()}, f, indent=2)
        _print_success(f"Scenario comparison written to {report_path} and {out_json}")
    except Exception as e:
        _print_error(f"Scenario design failed: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def workflow_atlas(args):
    """Build design space atlas (catalog of presets with design point + safety)."""
    try:
        from smrforge.workflows.atlas import build_atlas, filter_atlas
        out_dir = Path(getattr(args, "output_dir", None) or "atlas_output")
        presets = getattr(args, "presets", None)
        if presets:
            presets = [p.strip() for p in presets]
        entries = build_atlas(out_dir, presets=presets)
        passed = sum(1 for e in entries if e.passed)
        _print_success(f"Atlas built: {len(entries)} designs, {passed} passed. Index: {out_dir / 'atlas_index.json'}")
    except Exception as e:
        _print_error(f"Atlas failed: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def workflow_surrogate(args):
    """Fit surrogate model from sweep results for fast evaluation."""
    try:
        from smrforge.workflows.surrogate import surrogate_from_sweep_results
        p = Path(getattr(args, "sweep_results", None) or "")
        if not p.exists():
            _print_error("--sweep-results FILE.json required")
            sys.exit(1)
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        results = data.get("results", data) if isinstance(data, dict) else data
        if not isinstance(results, list):
            results = [results]
        params = getattr(args, "params", None) or []
        if not params and results and isinstance(results[0], dict):
            p0 = results[0].get("parameters", results[0])
            params = [k for k in p0 if isinstance(p0.get(k), (int, float))]
        if not params:
            _print_error("--params name1 name2 ... required")
            sys.exit(1)
        metric = getattr(args, "metric", "k_eff")
        method = getattr(args, "method", "rbf")
        sur = surrogate_from_sweep_results(results, params, output_metric=metric, method=method)
        _print_success(f"Surrogate fitted ({method}, n={sur.n_samples}). Use programmatically: sur.predict(X).")
        out = getattr(args, "output", None)
        if out:
            import pickle
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            with open(out, "wb") as f:
                pickle.dump(sur, f)
            _print_success(f"Surrogate saved to {out}")
    except Exception as e:
        _print_error(f"Surrogate failed: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def workflow_requirements_to_constraints(args):
    """Parse requirements YAML/JSON into ConstraintSet and save."""
    try:
        from smrforge.validation.requirements_parser import parse_requirements_to_constraint_set
        spec_path = getattr(args, "requirements", None)
        if not spec_path or not Path(spec_path).exists():
            _print_error("--requirements FILE.yaml|.json required")
            sys.exit(1)
        cs = parse_requirements_to_constraint_set(Path(spec_path), name=getattr(args, "name", "from_requirements"))
        out = getattr(args, "output", None)
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            cs.save(Path(out))
            _print_success(f"Constraint set saved to {out}")
        else:
            _print_error("--output FILE.json required to save constraint set")
            sys.exit(1)
    except Exception as e:
        _print_error(f"Requirements-to-constraints failed: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def template_create(args):
    """Create reactor template from preset or existing design."""
    try:
        from smrforge.workflows.templates import ReactorTemplate, TemplateLibrary
        
        if args.from_preset:
            template = ReactorTemplate.from_preset(args.from_preset, name=args.name)
        elif args.from_file:
            from pathlib import Path
            import json
            with open(Path(args.from_file)) as f:
                reactor_data = json.load(f)
            template = ReactorTemplate(
                name=args.name or "template",
                description=args.description or "Template from file",
                base_preset=reactor_data.get("name"),
                parameters={}
            )
        else:
            _print_error("Must specify --from-preset or --from-file")
            sys.exit(1)
        
        # Save template
        output_file = Path(args.output) if args.output else Path(f"{template.name}.json")
        template.save(output_file)
        
        if args.library:
            library = TemplateLibrary()
            library.save_template(template)
            _print_success(f"Template saved to library and {output_file}")
        else:
            _print_success(f"Template saved to {output_file}")
        
    except Exception as e:
        _print_error(f"Failed to create template: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def template_modify(args):
    """Modify reactor template parameters."""
    try:
        from smrforge.workflows.templates import ReactorTemplate
        
        template = ReactorTemplate.load(Path(args.template))
        
        # Modify parameters
        if args.param:
            for param_spec in args.param:
                # Format: name=value
                if '=' not in param_spec:
                    _print_error(f"Invalid parameter format: {param_spec}. Use name=value")
                    sys.exit(1)
                name, value = param_spec.split('=', 1)
                # Try to convert to number
                try:
                    value = float(value) if '.' in value else int(value)
                except ValueError:
                    pass  # Keep as string
                
                if name not in template.parameters:
                    template.parameters[name] = {"default": value, "type": type(value).__name__, "description": ""}
                else:
                    template.parameters[name]["default"] = value
        
        # Save modified template
        template.save(Path(args.template))
        _print_success(f"Template modified: {args.template}")
        
    except Exception as e:
        _print_error(f"Failed to modify template: {e}")
        sys.exit(1)


def template_validate(args):
    """Validate reactor template."""
    try:
        from smrforge.workflows.templates import ReactorTemplate
        
        template = ReactorTemplate.load(Path(args.template))
        errors = template.validate()
        
        if errors:
            _print_error("Template validation failed:")
            for error in errors:
                _print_error(f"  - {error}")
            sys.exit(1)
        else:
            _print_success("Template is valid!")
        
    except Exception as e:
        _print_error(f"Failed to validate template: {e}")
        sys.exit(1)


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
            table = Table(title="Transient Results Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")
            table.add_row("Peak Power", f"{peak_power/1e6:.2f} MW")
            table.add_row("Final Power", f"{final_power/1e6:.2f} MW")
            table.add_row("Peak Temperature", f"{peak_temp:.1f} K ({peak_temp-273:.1f}°C)")
            table.add_row("Final Temperature", f"{final_temp:.1f} K ({final_temp-273:.1f}°C)")
            console.print(table)
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
                "reactivity": result.get("reactivity", result.get("rho_external", [])).tolist() if isinstance(result.get("reactivity"), np.ndarray) else None,
            }
            
            with open(args.output, 'w') as f:
                json.dump(_to_jsonable(output_data), f, indent=2)
            _print_success(f"Results saved to {args.output}")
        
    except Exception as e:
        _print_error(f"Transient analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


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
                _print_error(f"Config file not found: {args.config}")
                sys.exit(1)
            
            if args.config.suffix in ['.yaml', '.yml']:
                if not _YAML_AVAILABLE:
                    _print_error("YAML support not available. Install PyYAML: pip install pyyaml")
                    sys.exit(1)
                with open(args.config) as f:
                    config = yaml.safe_load(f)
            else:
                with open(args.config) as f:
                    config = json.load(f)
            
            # Build lumps and resistances from config
            lumps = {}
            for lump_config in config.get("lumps", []):
                # Parse heat source function (simplified: constant or lambda expression)
                heat_source_str = lump_config.get("heat_source", "lambda t: 0.0")
                if isinstance(heat_source_str, str):
                    heat_source = eval(heat_source_str)
                else:
                    heat_source = lambda t: heat_source_str
                
                lump = ThermalLump(
                    name=lump_config["name"],
                    capacitance=lump_config["capacitance"],
                    temperature=lump_config["temperature"],
                    heat_source=heat_source,
                )
                lumps[lump.name] = lump
            
            resistances = []
            for res_config in config.get("resistances", []):
                resistance = ThermalResistance(
                    name=res_config["name"],
                    resistance=res_config["resistance"],
                    lump1_name=res_config["lump1_name"],
                    lump2_name=res_config["lump2_name"],
                )
                resistances.append(resistance)
            
            ambient_temp = config.get("ambient_temperature", 300.0)
        else:
            # Use default 2-lump system (fuel + moderator)
            _print_info("Using default 2-lump system (fuel + moderator)")
            
            fuel = ThermalLump(
                name="fuel",
                capacitance=1e8,  # J/K
                temperature=1200.0,  # K
                heat_source=lambda t: 1e6 if t < 10 else 0.1e6  # Decay heat
            )
            
            moderator = ThermalLump(
                name="moderator",
                capacitance=5e8,  # J/K
                temperature=800.0,  # K
                heat_source=lambda t: 0.0
            )
            
            resistance = ThermalResistance(
                name="fuel_to_moderator",
                resistance=1e-6,  # K/W
                lump1_name="fuel",
                lump2_name="moderator"
            )
            
            lumps = {"fuel": fuel, "moderator": moderator}
            resistances = [resistance]
            ambient_temp = 300.0
        
        solver = LumpedThermalHydraulics(
            lumps=lumps,
            resistances=resistances,
            ambient_temperature=ambient_temp
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
                T_final = result[T_key][-1]
                T_initial = result[T_key][0]
                if _RICH_AVAILABLE:
                    console.print(f"  {lump_name.capitalize()}: {T_initial:.1f} → {T_final:.1f} K")
                else:
                    print(f"  {lump_name.capitalize()}: {T_initial:.1f} → {T_final:.1f} K")
        
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
                if args.plot_output:
                    _print_success(f"Plot saved to {args.plot_output}")
            except ImportError as e:
                _print_error(f"Plotting not available: {e}")
                _print_info("Install matplotlib or plotly for visualization: pip install matplotlib plotly")
        
        # Save results if output specified
        if args.output:
            output_data = {
                "time": result["time"].tolist(),
            }
            for key, value in result.items():
                if key != "time":
                    output_data[key] = value.tolist()
            
            with open(args.output, 'w') as f:
                json.dump(_to_jsonable(output_data), f, indent=2)
            _print_success(f"Results saved to {args.output}")
        
    except Exception as e:
        _print_error(f"Thermal-hydraulics analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def validate_design(args):
    """Validate reactor design against constraints."""
    try:
        from smrforge.validation.constraints import DesignValidator, ConstraintSet
        from smrforge.convenience import create_reactor
        import json
        
        # Load reactor
        if args.reactor:
            with open(Path(args.reactor)) as f:
                reactor_data = json.load(f)
            reactor = create_reactor(**reactor_data)
        elif args.preset:
            reactor = create_reactor(args.preset)
        else:
            _print_error("Must specify --reactor or --preset")
            sys.exit(1)
            return  # ensure we don't fall through when exit is mocked
        
        # Load constraint set
        if args.constraints:
            with open(Path(args.constraints)) as f:
                constraints_data = json.load(f)
            constraint_set = ConstraintSet(**constraints_data)
        else:
            # Use default regulatory limits
            constraint_set = ConstraintSet.get_regulatory_limits()
        
        # Run validation
        validator = DesignValidator(constraint_set)
        validation = validator.validate(reactor)
        
        # Display results
        if validation.passed:
            _print_success("Design validation passed!")
        else:
            _print_error("Design validation failed!")
            if validation.violations:
                _print_error("\nViolations:")
                for viol in validation.violations:
                    _print_error(f"  - {viol.message}")
        
        if validation.warnings:
            _print_warning("\nWarnings:")
            for warn in validation.warnings:
                _print_warning(f"  - {warn.message}")
        
        # Save report if output specified
        if args.output:
            report = {
                "passed": validation.passed,
                "violations": [{"constraint": v.constraint_name, "message": v.message} 
                              for v in validation.violations],
                "warnings": [{"constraint": w.constraint_name, "message": w.message} 
                            for w in validation.warnings],
                "metrics": validation.metrics
            }
            with open(Path(args.output), 'w') as f:
                json.dump(_to_jsonable(report), f, indent=2)
            _print_success(f"Validation report saved to {args.output}")
        
    except Exception as e:
        _print_error(f"Failed to validate design: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)
        return


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SMRForge - Small Modular Reactor Design and Analysis Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch web dashboard
  smrforge serve
  
  # Create reactor from preset
  smrforge reactor create --preset valar-10 --output reactor.json
  
  # Analyze reactor
  smrforge reactor analyze --reactor reactor.json --keff
  
  # List available presets
  smrforge reactor list
  
  # Setup ENDF data
  smrforge data setup
  
  # Download ENDF data
  smrforge data download --library ENDF-B-VIII.1 --nuclide-set common_smr
  
  # Validate ENDF files
  smrforge data validate --endf-dir ~/ENDF-Data
  
  # Run burnup calculation
  smrforge burnup run --reactor reactor.json --time-steps 0 365 730

Note: All features are also available via Python API:
  import smrforge as smr
  reactor = smr.create_reactor("valar-10")
  k_eff = reactor.solve_keff()
        """
    )
    
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--version', action='version', version=f'%(prog)s {smrforge.__version__}')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Serve command
    serve_parser = subparsers.add_parser(
        'serve',
        help='Launch the SMRForge web dashboard'
    )
    serve_parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='Host address (default: 127.0.0.1)'
    )
    serve_parser.add_argument(
        '--port',
        type=int,
        default=8050,
        help='Port number (default: 8050)'
    )
    serve_parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    serve_parser.set_defaults(func=serve_dashboard)
    
    # Shell command
    shell_parser = subparsers.add_parser(
        'shell',
        help='Launch interactive Python shell with SMRForge pre-loaded'
    )
    shell_parser.set_defaults(func=shell_interactive)
    
    # Workflow subcommands
    workflow_parser = subparsers.add_parser(
        'workflow',
        help='Workflow operations'
    )
    workflow_subparsers = workflow_parser.add_subparsers(dest='workflow_command', help='Workflow commands')
    
    # workflow run
    workflow_run_parser = workflow_subparsers.add_parser(
        'run',
        help='Run workflow from YAML file'
    )
    workflow_run_parser.add_argument('workflow', type=Path, help='Workflow YAML file')
    workflow_run_parser.set_defaults(func=workflow_run)
    
    # workflow batch-keff
    batch_keff_parser = workflow_subparsers.add_parser(
        'batch-keff',
        help='Run k-eff only on multiple reactor files in parallel'
    )
    batch_keff_parser.add_argument('reactors', nargs='+', type=str, help='Reactor files or glob patterns (e.g. configs/*.json)')
    batch_keff_parser.add_argument('--no-parallel', action='store_true', dest='no_parallel', help='Run sequentially')
    batch_keff_parser.add_argument('--workers', type=int, help='Max parallel workers (default: auto; see SMRFORGE_MAX_BATCH_WORKERS)')
    batch_keff_parser.add_argument('--no-progress', action='store_true', dest='no_progress', help='Disable progress bar')
    batch_keff_parser.add_argument('--output', type=Path, help='Save results to JSON file')
    batch_keff_parser.set_defaults(func=batch_keff_run)

    # workflow design-point
    dp_parser = workflow_subparsers.add_parser('design-point', help='Steady-state design point summary')
    dp_parser.add_argument('--reactor', type=str, required=True, help='Reactor file or preset name')
    dp_parser.add_argument('--output', type=Path, help='Save JSON')
    dp_parser.set_defaults(func=workflow_design_point)

    # workflow safety-report
    sr_parser = workflow_subparsers.add_parser('safety-report', help='Coupled safety margin report')
    sr_parser.add_argument('--reactor', type=str, required=True, help='Reactor file or preset name')
    sr_parser.add_argument('--constraints', type=Path, help='Constraint set JSON')
    sr_parser.add_argument('--output', type=Path, help='Save JSON')
    sr_parser.set_defaults(func=workflow_safety_report)

    # workflow doe
    doe_parser = workflow_subparsers.add_parser('doe', help='Design of Experiments (factorial, LHS, Sobol, random)')
    doe_parser.add_argument('--method', type=str, choices=['factorial', 'lhs', 'sobol', 'random'], default='lhs')
    doe_parser.add_argument('--factors', nargs='+', required=True, help='name:low:high or name:v1,v2,v3 for factorial')
    doe_parser.add_argument('--samples', type=int, default=10, help='Samples for lhs/sobol/random')
    doe_parser.add_argument('--seed', type=int, help='Random seed')
    doe_parser.add_argument('--output', type=Path, help='Save JSON')
    doe_parser.set_defaults(func=workflow_doe)

    # workflow pareto
    pareto_parser = workflow_subparsers.add_parser('pareto', help='Compute Pareto front from sweep results')
    pareto_parser.add_argument('--sweep-results', type=Path, required=True, help='Sweep results JSON')
    pareto_parser.add_argument('--metric-x', type=str, default='k_eff')
    pareto_parser.add_argument('--metric-y', type=str, help='Second metric (default: first other numeric)')
    pareto_parser.add_argument('--output', type=Path, help='Save Pareto set JSON')
    pareto_parser.set_defaults(func=workflow_pareto)

    # workflow optimize
    opt_parser = workflow_subparsers.add_parser('optimize', help='Design optimization (optionally constraint-aware)')
    opt_parser.add_argument('--reactor', type=Path, required=True, help='Base design JSON file')
    opt_parser.add_argument('--params', nargs='+', required=True, help='name:low:high per parameter')
    opt_parser.add_argument('--objective', type=str, default='min_neg_keff')
    opt_parser.add_argument('--constraints', type=Path, help='Constraint set JSON for penalty')
    opt_parser.add_argument('--method', type=str, default='differential_evolution')
    opt_parser.add_argument('--max-iter', type=int, default=50)
    opt_parser.add_argument('--output', type=Path, help='Save results JSON')
    opt_parser.set_defaults(func=workflow_optimize)

    # workflow uq
    uq_parser = workflow_subparsers.add_parser('uq', help='Uncertainty quantification (Monte Carlo / LHS)')
    uq_parser.add_argument('--reactor', type=Path, required=True, help='Base design JSON file')
    uq_parser.add_argument('--params', nargs='+', required=True, help='name:nominal:distribution[:uncertainty]')
    uq_parser.add_argument('--samples', type=int, default=100)
    uq_parser.add_argument('--seed', type=int, default=42)
    uq_parser.add_argument('--output', type=Path, help='Save UQ summary JSON')
    uq_parser.set_defaults(func=workflow_uq)

    # workflow design-study
    ds_parser = workflow_subparsers.add_parser('design-study', help='Run design point + safety report')
    ds_parser.add_argument('--reactor', type=str, required=True, help='Reactor file or preset name')
    ds_parser.add_argument('--constraints', type=Path, help='Constraint set JSON')
    ds_parser.add_argument('--output-dir', type=Path, default=Path('design_study_output'))
    ds_parser.add_argument('--html', action='store_true', help='Also write design_study_report.html')
    ds_parser.set_defaults(func=workflow_design_study)

    # workflow variant
    var_parser = workflow_subparsers.add_parser('variant', help='Save design as named variant')
    var_parser.add_argument('--reactor', type=str, required=True, help='Reactor file or preset name')
    var_parser.add_argument('--name', type=str, default='variant')
    var_parser.add_argument('--output-dir', type=Path, help='Output directory')
    var_parser.set_defaults(func=workflow_variant)

    # workflow sensitivity
    sens_parser = workflow_subparsers.add_parser('sensitivity', help='Sensitivity ranking (OAT) from sweep results')
    sens_parser.add_argument('--sweep-results', type=Path, required=True, help='Sweep results JSON')
    sens_parser.add_argument('--params', nargs='+', help='Parameter names (default: from results)')
    sens_parser.add_argument('--metric', type=str, default='k_eff')
    sens_parser.add_argument('--output', type=Path, help='Save ranking JSON')
    sens_parser.set_defaults(func=workflow_sensitivity)

    # workflow sobol
    sobol_parser = workflow_subparsers.add_parser('sobol', help='Sobol sensitivity indices from sweep results')
    sobol_parser.add_argument('--sweep-results', type=Path, required=True, help='Sweep results JSON')
    sobol_parser.add_argument('--params', nargs='+', help='Parameter names (default: from results)')
    sobol_parser.add_argument('--metric', type=str, default='k_eff')
    sobol_parser.add_argument('--output', type=Path, help='Save Sobol JSON')
    sobol_parser.set_defaults(func=workflow_sobol)

    # workflow scenario
    scenario_parser = workflow_subparsers.add_parser('scenario', help='Scenario-based design (multiple missions)')
    scenario_parser.add_argument('--reactor', type=str, required=True, help='Reactor file or preset')
    scenario_parser.add_argument('--scenarios', nargs='+', required=True, help='name:path_or_preset (e.g. baseload:regulatory_limits)')
    scenario_parser.add_argument('--output-dir', type=Path, help='Output directory')
    scenario_parser.set_defaults(func=workflow_scenario)

    # workflow atlas
    atlas_parser = workflow_subparsers.add_parser('atlas', help='Build design space atlas (catalog of presets)')
    atlas_parser.add_argument('--output-dir', type=Path, default=Path('atlas_output'))
    atlas_parser.add_argument('--presets', nargs='+', help='Preset names (default: all from list_presets)')
    atlas_parser.set_defaults(func=workflow_atlas)

    # workflow surrogate
    sur_parser = workflow_subparsers.add_parser('surrogate', help='Fit surrogate model from sweep results')
    sur_parser.add_argument('--sweep-results', type=Path, required=True, help='Sweep results JSON')
    sur_parser.add_argument('--params', nargs='+', required=True, help='Parameter names')
    sur_parser.add_argument('--metric', type=str, default='k_eff')
    sur_parser.add_argument('--method', type=str, choices=['rbf', 'linear'], default='rbf')
    sur_parser.add_argument('--output', type=Path, help='Save pickle surrogate')
    sur_parser.set_defaults(func=workflow_surrogate)

    # workflow requirements-to-constraints
    req_parser = workflow_subparsers.add_parser('requirements-to-constraints', help='Parse requirements YAML/JSON to ConstraintSet')
    req_parser.add_argument('--requirements', type=Path, required=True, help='Requirements YAML or JSON file')
    req_parser.add_argument('--name', type=str, default='from_requirements')
    req_parser.add_argument('--output', type=Path, required=True, help='Output constraint set JSON')
    req_parser.set_defaults(func=workflow_requirements_to_constraints)
    
    # Reactor subcommands
    reactor_parser = subparsers.add_parser(
        'reactor',
        help='Reactor operations'
    )
    reactor_subparsers = reactor_parser.add_subparsers(dest='reactor_command', help='Reactor commands')
    
    # reactor create
    create_parser = reactor_subparsers.add_parser(
        'create',
        help='Create a reactor from preset or configuration'
    )
    create_parser.add_argument('--preset', type=str, help='Preset design name')
    create_parser.add_argument('--config', type=Path, help='Configuration file (JSON or YAML)')
    create_parser.add_argument('--power', type=float, help='Thermal power [MW]')
    create_parser.add_argument('--enrichment', type=float, help='Fuel enrichment')
    create_parser.add_argument('--type', type=str, help='Reactor type (htgr, pwr, bwr, fast)')
    create_parser.add_argument('--core-height', type=float, dest='core_height', help='Core height [cm]')
    create_parser.add_argument('--core-diameter', type=float, dest='core_diameter', help='Core diameter [cm]')
    create_parser.add_argument('--fuel-type', type=str, dest='fuel_type', help='Fuel type')
    create_parser.add_argument('--output', type=Path, help='Output file')
    create_parser.add_argument('--format', type=str, choices=['json', 'yaml'], help='Output format')
    create_parser.set_defaults(func=reactor_create)
    
    # reactor analyze
    analyze_parser = reactor_subparsers.add_parser(
        'analyze',
        help='Run analysis on a reactor'
    )
    analyze_parser.add_argument('--reactor', type=Path, help='Reactor file (JSON)')
    analyze_parser.add_argument('--batch', nargs='+', type=str, help='Batch process multiple reactor files (glob patterns allowed)')
    analyze_parser.add_argument('--parallel', action='store_true', help='Process batch in parallel')
    analyze_parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers (default: 4)')
    analyze_parser.add_argument('--keff', action='store_true', help='Calculate k-effective only')
    analyze_parser.add_argument('--neutronics', action='store_true', help='Full neutronics analysis')
    analyze_parser.add_argument('--burnup', action='store_true', help='Burnup calculation')
    analyze_parser.add_argument('--safety', action='store_true', help='Safety transient analysis')
    analyze_parser.add_argument('--full', action='store_true', help='Run all analyses')
    analyze_parser.add_argument('--max-iterations', type=int, dest='max_iterations', help='Solver max iterations')
    analyze_parser.add_argument('--tolerance', type=float, help='Solver tolerance')
    analyze_parser.add_argument('--output', type=Path, help='Output file for results')
    analyze_parser.set_defaults(func=reactor_analyze)
    
    # reactor list
    list_parser = reactor_subparsers.add_parser(
        'list',
        help='List available preset reactor designs'
    )
    list_parser.add_argument('--detailed', action='store_true', help='Show detailed information')
    list_parser.add_argument('--type', type=str, help='Filter by reactor type')
    list_parser.set_defaults(func=reactor_list)
    
    # reactor compare
    compare_parser = reactor_subparsers.add_parser(
        'compare',
        help='Compare multiple reactor designs'
    )
    compare_parser.add_argument('--presets', nargs='+', help='Preset design names to compare')
    compare_parser.add_argument('--reactors', nargs='+', type=Path, help='Reactor files to compare')
    compare_parser.add_argument('--metrics', nargs='+', help='Metrics to compare (e.g., keff,power_density,temperature_peak)', 
                               default=['k_eff'])
    compare_parser.add_argument('--output', type=Path, help='Output file for comparison (JSON or HTML)')
    compare_parser.add_argument('--visualize', action='store_true', help='Generate visualization (future feature)')
    compare_parser.set_defaults(func=reactor_compare)
    
    # Data subcommands
    data_parser = subparsers.add_parser(
        'data',
        help='Data management operations'
    )
    data_subparsers = data_parser.add_subparsers(dest='data_command', help='Data commands')
    
    # data setup
    setup_parser = data_subparsers.add_parser(
        'setup',
        help='Setup ENDF data directory (interactive)'
    )
    setup_parser.add_argument('--endf-dir', type=Path, dest='endf_dir', help='ENDF directory path')
    setup_parser.set_defaults(func=data_setup)
    
    # data download
    download_parser = data_subparsers.add_parser(
        'download',
        help='Download ENDF nuclear data'
    )
    download_parser.add_argument('--library', type=str, default='ENDF-B-VIII.1', help='ENDF library name')
    download_parser.add_argument('--nuclide-set', type=str, dest='nuclide_set', help='Predefined nuclide set')
    download_parser.add_argument('--nuclides', nargs='+', help='Specific nuclides to download')
    download_parser.add_argument('--output', type=Path, help='Output directory')
    download_parser.add_argument('--max-workers', type=int, dest='max_workers', help='Parallel downloads')
    download_parser.add_argument('--validate', action='store_true', help='Validate downloaded files')
    download_parser.add_argument('--resume', action='store_true', help='Resume interrupted download')
    download_parser.set_defaults(func=data_download)
    
    # data validate
    validate_data_parser = data_subparsers.add_parser(
        'validate',
        help='Validate ENDF files'
    )
    validate_data_parser.add_argument('--endf-dir', type=Path, dest='endf_dir', help='ENDF directory to validate')
    validate_data_parser.add_argument('--files', nargs='+', type=Path, help='Specific ENDF files to validate')
    validate_data_parser.add_argument('--output', type=Path, help='Output file for validation report')
    validate_data_parser.set_defaults(func=data_validate)
    
    # data interpolate (temperature interpolation)
    interpolate_parser = data_subparsers.add_parser(
        'interpolate',
        help='Interpolate cross-sections at different temperatures'
    )
    interpolate_parser.add_argument('--nuclide', type=str, required=True, help='Nuclide (e.g., U235, Pu239)')
    interpolate_parser.add_argument('--reaction', type=str, required=True, help='Reaction type (fission, capture, total, elastic)')
    interpolate_parser.add_argument('--temperature', type=float, required=True, help='Target temperature [K]')
    interpolate_parser.add_argument('--available-temps', nargs='+', type=float, dest='available_temps', 
                                    help='Available temperatures [K] (default: 293.6, 600.0, 900.0, 1200.0)')
    interpolate_parser.add_argument('--method', type=str, choices=['linear', 'log_log', 'spline'], 
                                    default='linear', help='Interpolation method (default: linear)')
    interpolate_parser.add_argument('--endf-dir', type=Path, dest='endf_dir', help='ENDF directory path')
    interpolate_parser.add_argument('--output', type=Path, help='Output file (JSON or CSV)')
    interpolate_parser.add_argument('--plot', action='store_true', help='Plot interpolated cross-section')
    interpolate_parser.add_argument('--plot-output', type=Path, dest='plot_output', help='Plot output file')
    interpolate_parser.set_defaults(func=data_interpolate)
    
    # data shield (self-shielding)
    shield_parser = data_subparsers.add_parser(
        'shield',
        help='Calculate self-shielded cross-sections'
    )
    shield_parser.add_argument('--nuclide', type=str, required=True, help='Nuclide (e.g., U235, U238)')
    shield_parser.add_argument('--reaction', type=str, required=True, help='Reaction type (fission, capture, total, elastic)')
    shield_parser.add_argument('--temperature', type=float, required=True, help='Temperature [K]')
    shield_parser.add_argument('--sigma-0', type=float, dest='sigma_0', default=1.0, 
                               help='Background cross-section [barns] (default: 1.0)')
    shield_parser.add_argument('--method', type=str, choices=['bondarenko', 'subgroup', 'equivalence'], 
                               default='bondarenko', help='Self-shielding method (default: bondarenko)')
    shield_parser.add_argument('--endf-dir', type=Path, dest='endf_dir', help='ENDF directory path')
    shield_parser.add_argument('--output', type=Path, help='Output file (JSON or CSV)')
    shield_parser.add_argument('--plot', action='store_true', help='Plot shielded vs unshielded cross-section')
    shield_parser.add_argument('--plot-output', type=Path, dest='plot_output', help='Plot output file')
    shield_parser.add_argument('--compare', action='store_true', help='Compare shielded and unshielded cross-sections')
    shield_parser.set_defaults(func=data_shield)
    
    # Burnup subcommands
    burnup_parser = subparsers.add_parser(
        'burnup',
        help='Burnup/depletion operations'
    )
    burnup_subparsers = burnup_parser.add_subparsers(dest='burnup_command', help='Burnup commands')
    
    # burnup run
    burnup_run_parser = burnup_subparsers.add_parser(
        'run',
        help='Run burnup/depletion calculation'
    )
    burnup_run_parser.add_argument('--reactor', type=Path, required=True, help='Reactor file (JSON)')
    burnup_run_parser.add_argument('--time-steps', nargs='+', dest='time_steps', help='Time steps [days]')
    burnup_run_parser.add_argument('--power-density', type=float, dest='power_density', help='Power density [W/cm³]')
    burnup_run_parser.add_argument('--checkpoint-interval', type=float, dest='checkpoint_interval', 
                                  help='Checkpoint every N days (enables checkpointing)')
    burnup_run_parser.add_argument('--checkpoint-dir', type=Path, dest='checkpoint_dir', 
                                  help='Directory for checkpoint files')
    burnup_run_parser.add_argument('--resume-from', type=Path, dest='resume_from', 
                                  help='Resume from checkpoint file')
    burnup_run_parser.add_argument('--adaptive-tracking', action='store_true', dest='adaptive_tracking', help='Enable adaptive nuclide tracking')
    burnup_run_parser.add_argument('--nuclide-threshold', type=float, dest='nuclide_threshold', help='Nuclide concentration threshold')
    burnup_run_parser.add_argument('--output', type=Path, help='Output file for results')
    burnup_run_parser.set_defaults(func=burnup_run)
    
    # burnup visualize
    burnup_visualize_parser = burnup_subparsers.add_parser(
        'visualize',
        help='Visualize burnup results'
    )
    burnup_visualize_parser.add_argument('--results', type=Path, required=True, help='Burnup results file (JSON or HDF5)')
    burnup_visualize_parser.add_argument('--nuclides', nargs='+', help='Specific nuclides to plot (e.g., U235 U238 Pu239)')
    burnup_visualize_parser.add_argument('--burnup', action='store_true', help='Plot burnup over time')
    burnup_visualize_parser.add_argument('--keff', action='store_true', help='Plot k-eff evolution')
    burnup_visualize_parser.add_argument('--composition', action='store_true', help='Plot composition changes')
    burnup_visualize_parser.add_argument('--batch-comparison', action='store_true', help='Compare burnup across multiple fuel batches')
    burnup_visualize_parser.add_argument('--refueling-cycles', action='store_true', help='Visualize multi-cycle burnup evolution')
    burnup_visualize_parser.add_argument('--control-rod-effects', action='store_true', help='Compare burnup with/without control rods')
    burnup_visualize_parser.add_argument('--dashboard', action='store_true', help='Generate enhanced burnup dashboard')
    burnup_visualize_parser.add_argument('--batch-results', type=Path, nargs='+', help='Additional batch result files for comparison')
    burnup_visualize_parser.add_argument('--without-rods-results', type=Path, help='Results file without control rods for comparison')
    burnup_visualize_parser.add_argument('--output', type=Path, help='Output file for plot')
    burnup_visualize_parser.add_argument('--format', type=str, choices=['png', 'pdf', 'svg', 'html'], default='png', help='Output format')
    burnup_visualize_parser.add_argument('--backend', type=str, choices=['plotly', 'matplotlib'], default='plotly', help='Visualization backend')
    burnup_visualize_parser.set_defaults(func=burnup_visualize)
    
    # Decay heat subcommands
    decay_parser = subparsers.add_parser(
        'decay',
        help='Decay heat calculations'
    )
    decay_subparsers = decay_parser.add_subparsers(dest='decay_command', help='Decay heat commands')
    
    # decay calculate
    decay_calculate_parser = decay_subparsers.add_parser(
        'calculate',
        help='Calculate decay heat over time'
    )
    decay_calculate_parser.add_argument('--inventory', type=Path, help='Nuclide inventory file (JSON)')
    decay_calculate_parser.add_argument('--nuclides', nargs='+', help='Nuclide concentrations (format: U235:1e20 Cs137:1e19)')
    decay_calculate_parser.add_argument('--times', nargs='+', type=float, help='Time points after shutdown [seconds]')
    decay_calculate_parser.add_argument('--time-range', nargs=3, type=float, metavar=('START', 'END', 'STEPS'), help='Time range: start end num_steps')
    decay_calculate_parser.add_argument('--output', type=Path, help='Output file for results (JSON)')
    decay_calculate_parser.add_argument('--plot', action='store_true', help='Generate decay heat plot')
    decay_calculate_parser.add_argument('--plot-output', type=Path, help='Output file for plot')
    decay_calculate_parser.add_argument('--format', type=str, choices=['png', 'pdf', 'svg', 'html'], default='png', help='Plot format')
    decay_calculate_parser.add_argument('--backend', type=str, choices=['plotly', 'matplotlib'], default='plotly', help='Visualization backend')
    decay_calculate_parser.add_argument('--endf-dir', type=Path, dest='endf_dir', help='ENDF directory for decay data')
    decay_calculate_parser.set_defaults(func=decay_heat_calculate)
    
    # Validate subcommands
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validation and testing operations'
    )
    validate_subparsers = validate_parser.add_subparsers(dest='validate_command', help='Validation commands')
    
    # validate run
    validate_run_parser = validate_subparsers.add_parser(
        'run',
        help='Run validation tests'
    )
    validate_run_parser.add_argument('--endf-dir', type=Path, dest='endf_dir', help='ENDF directory')
    validate_run_parser.add_argument('--tests', nargs='+', help='Specific test suites to run')
    validate_run_parser.add_argument('--benchmarks', type=Path, help='Benchmark database file')
    validate_run_parser.add_argument('--output', type=Path, help='Output file for results')
    validate_run_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    validate_run_parser.set_defaults(func=validate_run)
    
    # Visualize subcommands
    visualize_parser = subparsers.add_parser(
        'visualize',
        help='Visualization operations'
    )
    visualize_subparsers = visualize_parser.add_subparsers(dest='visualize_command', help='Visualization commands')
    
    # visualize geometry
    visualize_geom_parser = visualize_subparsers.add_parser(
        'geometry',
        help='Visualize reactor geometry'
    )
    visualize_geom_parser.add_argument('--reactor', type=Path, required=True, help='Reactor file (JSON)')
    visualize_geom_parser.add_argument('--output', type=Path, help='Output file for visualization')
    visualize_geom_parser.add_argument('--format', type=str, choices=['png', 'pdf', 'svg', 'html'], default='png', help='Output format')
    visualize_geom_parser.add_argument('--3d', dest='d3d', action='store_true', help='Generate 3D visualization')
    visualize_geom_parser.add_argument('--backend', type=str, choices=['plotly', 'pyvista'], default='plotly', help='Visualization backend')
    visualize_geom_parser.add_argument('--interactive', action='store_true', help='Display interactive visualization')
    visualize_geom_parser.set_defaults(func=visualize_geometry)
    
    # visualize flux
    visualize_flux_parser = visualize_subparsers.add_parser(
        'flux',
        help='Plot flux distribution'
    )
    visualize_flux_parser.add_argument('--results', type=Path, required=True, help='Results file (JSON)')
    visualize_flux_parser.add_argument('--output', type=Path, help='Output file for plot')
    visualize_flux_parser.add_argument('--format', type=str, choices=['png', 'pdf', 'svg'], default='png', help='Output format')
    visualize_flux_parser.add_argument('--group', type=int, help='Energy group index')
    visualize_flux_parser.set_defaults(func=visualize_flux)
    
    # Sweep subcommands
    sweep_parser = subparsers.add_parser(
        'sweep',
        help='Parameter sweep and sensitivity analysis'
    )
    sweep_parser.add_argument('--config', type=Path, help='Load sweep config from JSON or YAML file (optional; else use --params)')
    sweep_parser.add_argument('--reactor', type=str, help='Reactor file or preset name')
    sweep_parser.add_argument('--params', nargs='+',
                            help='Parameter ranges (format: name:start:end:step or name:val1,val2,val3); required if no --config')
    sweep_parser.add_argument('--analysis', nargs='+', default=['keff'],
                            help='Analysis types to run (default: keff)')
    sweep_parser.add_argument('--output', type=Path, help='Output directory for results')
    sweep_parser.add_argument('--no-parallel', action='store_true', dest='no_parallel',
                            help='Disable parallel execution')
    sweep_parser.add_argument('--workers', type=int, help='Number of parallel workers')
    sweep_parser.add_argument('--resume', action='store_true', help='Resume from latest intermediate file in output dir')
    sweep_parser.add_argument('--progress', action='store_true', help='Show progress bar (Rich)')
    sweep_parser.set_defaults(func=sweep_run)
    
    # Reactor template subcommands
    template_parser = reactor_subparsers.add_parser(
        'template',
        help='Template-based reactor design library'
    )
    template_subparsers = template_parser.add_subparsers(dest='template_command', help='Template commands')
    
    # template create
    template_create_parser = template_subparsers.add_parser(
        'create',
        help='Create reactor template'
    )
    template_create_parser.add_argument('--from-preset', dest='from_preset', type=str, help='Create from preset')
    template_create_parser.add_argument('--from-file', dest='from_file', type=str, help='Create from reactor file')
    template_create_parser.add_argument('--name', type=str, help='Template name')
    template_create_parser.add_argument('--description', type=str, help='Template description')
    template_create_parser.add_argument('--output', type=Path, help='Output file')
    template_create_parser.add_argument('--library', action='store_true', help='Save to template library')
    template_create_parser.set_defaults(func=template_create)
    
    # template modify
    template_modify_parser = template_subparsers.add_parser(
        'modify',
        help='Modify reactor template'
    )
    template_modify_parser.add_argument('template', type=Path, help='Template file')
    template_modify_parser.add_argument('--param', nargs='+', help='Parameters to modify (format: name=value)')
    template_modify_parser.set_defaults(func=template_modify)
    
    # template validate
    template_validate_parser = template_subparsers.add_parser(
        'validate',
        help='Validate reactor template'
    )
    template_validate_parser.add_argument('template', type=Path, help='Template file')
    template_validate_parser.set_defaults(func=template_validate)
    
    # validate design (add to existing validate_subparsers from line 2361)
    # Note: validate_parser and validate_subparsers are already defined at line 2357-2361
    validate_design_parser = validate_subparsers.add_parser(
        'design',
        help='Validate reactor design against constraints'
    )
    validate_design_parser.add_argument('--reactor', type=Path, help='Reactor file')
    validate_design_parser.add_argument('--preset', type=str, help='Preset name')
    validate_design_parser.add_argument('--constraints', type=Path, help='Constraint set file (JSON)')
    validate_design_parser.add_argument('--output', type=Path, help='Output file for validation report')
    validate_design_parser.set_defaults(func=validate_design)
    
    # Config subcommands
    config_parser = subparsers.add_parser(
        'config',
        help='Configuration management'
    )
    config_subparsers = config_parser.add_subparsers(dest='config_command', help='Config commands')
    
    # config show
    config_show_parser = config_subparsers.add_parser(
        'show',
        help='Show current configuration'
    )
    config_show_parser.add_argument('--key', type=str, help='Show specific configuration key (e.g., endf.default_directory)')
    config_show_parser.set_defaults(func=config_show)
    
    # config set
    config_set_parser = config_subparsers.add_parser(
        'set',
        help='Set configuration value'
    )
    config_set_parser.add_argument('key', type=str, help='Configuration key (e.g., endf.default_directory)')
    config_set_parser.add_argument('value', type=str, help='Configuration value')
    config_set_parser.set_defaults(func=config_set)
    
    # config init
    config_init_parser = config_subparsers.add_parser(
        'init',
        help='Initialize configuration file'
    )
    config_init_parser.add_argument('--template', type=str, choices=['default', 'production', 'development'], default='default', help='Configuration template')
    config_init_parser.add_argument('--force', action='store_true', help='Overwrite existing configuration file')
    config_init_parser.set_defaults(func=config_init)
    
    # GitHub Actions subcommands
    github_parser = subparsers.add_parser(
        'github',
        help='GitHub Actions management: enable/disable workflows and select which features run'
    )
    github_parser.add_argument(
        '--repo-root',
        type=Path,
        default=None,
        metavar='DIR',
        help='Repository root (default: current directory)'
    )
    github_subparsers = github_parser.add_subparsers(dest='github_command', help='GitHub Actions commands')
    
    # github actions status
    github_status_parser = github_subparsers.add_parser(
        'status',
        help='Show GitHub Actions status (global and per-feature)'
    )
    github_status_parser.add_argument('--output', type=Path, help='Output file for status (JSON)')
    github_status_parser.set_defaults(func=github_actions_status)
    
    # github actions list
    github_list_parser = github_subparsers.add_parser(
        'list',
        help='List available workflow features and whether they run'
    )
    github_list_parser.set_defaults(func=github_actions_list)
    
    # github actions configure (interactive or with flags)
    github_configure_parser = github_subparsers.add_parser(
        'configure',
        help='Select which features run in GitHub Actions (interactive or use --ci/--docs/... on|off)'
    )
    _feat_ids = [f["id"] for f in GITHUB_ACTIONS_FEATURES]
    github_configure_parser.add_argument('--ci', choices=['on', 'off'], default=None, help='CI workflow (tests, lint, build)')
    github_configure_parser.add_argument('--ci-quick', dest='ci_quick', choices=['on', 'off'], default=None, help='Quick CI (single Python, no coverage)')
    github_configure_parser.add_argument('--docs', choices=['on', 'off'], default=None, help='Docs build and deploy')
    github_configure_parser.add_argument('--performance', choices=['on', 'off'], default=None, help='Performance benchmarks')
    github_configure_parser.add_argument('--security', choices=['on', 'off'], default=None, help='Security audit workflow')
    github_configure_parser.add_argument('--release', choices=['on', 'off'], default=None, help='Release to PyPI on version tags')
    github_configure_parser.add_argument('--nightly', choices=['on', 'off'], default=None, help='Scheduled nightly full run')
    github_configure_parser.add_argument('--docker', choices=['on', 'off'], default=None, help='Build and push Docker image')
    github_configure_parser.add_argument('--dependabot', choices=['on', 'off'], default=None, help='Run CI on Dependabot PRs')
    github_configure_parser.add_argument('--stale', choices=['on', 'off'], default=None, help='Stale issue/PR management')
    github_configure_parser.set_defaults(func=github_actions_configure)
    
    # github actions set <feature> on|off
    github_set_parser = github_subparsers.add_parser(
        'set',
        help='Set one feature on or off'
    )
    github_set_parser.add_argument('feature', choices=_feat_ids, help='Feature ID')
    github_set_parser.add_argument('value', choices=['on', 'off'], help='Enable or disable')
    github_set_parser.set_defaults(func=github_actions_set)
    
    # github actions enable
    github_enable_parser = github_subparsers.add_parser(
        'enable',
        help='Enable GitHub Actions workflows (global master switch)'
    )
    github_enable_parser.set_defaults(func=github_actions_enable)
    
    # github actions disable
    github_disable_parser = github_subparsers.add_parser(
        'disable',
        help='Disable GitHub Actions workflows (global master switch)'
    )
    github_disable_parser.set_defaults(func=github_actions_disable)
    
    # Transient subcommands (NEW)
    transient_parser = subparsers.add_parser(
        'transient',
        help='Transient analysis operations'
    )
    transient_subparsers = transient_parser.add_subparsers(dest='transient_command', help='Transient commands')
    
    # transient run
    transient_run_parser = transient_subparsers.add_parser(
        'run',
        help='Run transient analysis'
    )
    transient_run_parser.add_argument('--power', type=float, required=True, help='Initial reactor power [W]')
    transient_run_parser.add_argument('--temperature', type=float, required=True, help='Initial temperature [K]')
    transient_run_parser.add_argument('--type', type=str, choices=['reactivity_insertion', 'reactivity_step', 'power_change', 'decay_heat'], 
                                     default='reactivity_insertion', help='Transient type')
    transient_run_parser.add_argument('--reactivity', type=float, help='Reactivity inserted [dk/k] (for reactivity_insertion/step)')
    transient_run_parser.add_argument('--duration', type=float, default=100.0, help='Simulation duration [s]')
    transient_run_parser.add_argument('--scram-available', action='store_true', dest='scram_available', default=True, help='Scram available (default: True)')
    transient_run_parser.add_argument('--scram-delay', type=float, default=1.0, dest='scram_delay', help='Scram delay [s]')
    transient_run_parser.add_argument('--long-term', action='store_true', dest='long_term', help='Enable long-term optimizations (>1 day)')
    transient_run_parser.add_argument('--output', type=Path, help='Output file for results (JSON)')
    transient_run_parser.add_argument('--plot', action='store_true', help='Generate and display plot')
    transient_run_parser.add_argument('--plot-output', type=Path, dest='plot_output', help='Save plot to file (PNG, HTML, PDF, SVG)')
    transient_run_parser.add_argument('--plot-backend', type=str, choices=['plotly', 'matplotlib'], default='plotly', dest='plot_backend', help='Plotting backend (default: plotly)')
    transient_run_parser.set_defaults(func=transient_run)
    
    # Thermal subcommands (NEW)
    thermal_parser = subparsers.add_parser(
        'thermal',
        help='Thermal-hydraulics operations'
    )
    thermal_subparsers = thermal_parser.add_subparsers(dest='thermal_command', help='Thermal commands')
    
    # thermal lumped
    thermal_lumped_parser = thermal_subparsers.add_parser(
        'lumped',
        help='Run lumped-parameter thermal-hydraulics analysis'
    )
    thermal_lumped_parser.add_argument('--config', type=Path, help='Configuration file (JSON/YAML) with lump definitions')
    thermal_lumped_parser.add_argument('--duration', type=float, default=3600.0, help='Simulation duration [s]')
    thermal_lumped_parser.add_argument('--max-step', type=float, help='Maximum time step [s] (default: adaptive)')
    thermal_lumped_parser.add_argument('--adaptive', action='store_true', default=True, help='Use adaptive time stepping (default: True)')
    thermal_lumped_parser.add_argument('--output', type=Path, help='Output file for results (JSON)')
    thermal_lumped_parser.add_argument('--plot', action='store_true', help='Generate and display plot')
    thermal_lumped_parser.add_argument('--plot-output', type=Path, dest='plot_output', help='Save plot to file (PNG, HTML, PDF, SVG)')
    thermal_lumped_parser.add_argument('--plot-backend', type=str, choices=['plotly', 'matplotlib'], default='plotly', dest='plot_backend', help='Plotting backend (default: plotly)')
    thermal_lumped_parser.set_defaults(func=thermal_lumped)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    
    # Handle commands - func is set via set_defaults on each subparser
    if hasattr(args, 'func'):
        args.func(args)
    else:
        # Command without handler - show help
        parser.print_help()
        sys.exit(0)


if __name__ == '__main__':
    main()
