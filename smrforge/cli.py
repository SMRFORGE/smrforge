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


def _print_success(message: str):
    """Print success message with styling if rich is available."""
    if _RICH_AVAILABLE:
        console.print(f"[bold green]✓[/bold green] {message}")
    else:
        print(f"✓ {message}")


def _print_error(message: str):
    """Print error message with styling if rich is available."""
    if _RICH_AVAILABLE:
        console.print(f"[bold red]✗[/bold red] {message}")
    else:
        print(f"✗ {message}")


def _print_info(message: str):
    """Print info message with styling if rich is available."""
    if _RICH_AVAILABLE:
        console.print(f"[blue]ℹ[/blue] {message}")
    else:
        print(f"ℹ {message}")


def _print_warning(message: str):
    """Print warning message with styling if rich is available."""
    if _RICH_AVAILABLE:
        console.print(f"[bold yellow]⚠[/bold yellow] {message}")
    else:
        print(f"⚠ {message}")


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
                    'reactor_type': str(reactor.spec.reactor_type) if hasattr(reactor, 'spec') else None,
                    'fuel_type': str(reactor.spec.fuel_type) if hasattr(reactor, 'spec') else None,
                    'core_height': reactor.spec.core_height if hasattr(reactor, 'spec') else None,
                    'core_diameter': reactor.spec.core_diameter if hasattr(reactor, 'spec') else None,
                }
                with open(output_path, 'w') as f:
                    json.dump(reactor_dict, f, indent=2)
                _print_success(f"Saved reactor to {output_path} (JSON format)")
            elif output_format in ['yaml', 'yml']:
                if not _YAML_AVAILABLE:
                    _print_error("YAML support not available. Install PyYAML: pip install pyyaml")
                    sys.exit(1)
                reactor_dict = {
                    'name': reactor.spec.name if hasattr(reactor, 'spec') else 'reactor',
                    'power_mw': reactor.spec.power_thermal / 1e6 if hasattr(reactor, 'spec') else None,
                    'enrichment': reactor.spec.enrichment if hasattr(reactor, 'spec') else None,
                    'reactor_type': str(reactor.spec.reactor_type) if hasattr(reactor, 'spec') else None,
                    'fuel_type': str(reactor.spec.fuel_type) if hasattr(reactor, 'spec') else None,
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
        
        # Check for batch mode
        if args.batch:
            # Batch processing mode - placeholder for future implementation
            _print_error("Batch processing is not yet fully implemented")
            _print_info("For batch processing, use the Python API or process files individually")
            _print_info("Example: for f in *.json; do smrforge reactor analyze --reactor $f; done")
            sys.exit(1)
        
        # Single file mode
        if not args.reactor:
            _print_error("Must specify --reactor FILE or --batch PATTERN")
            sys.exit(1)
        
        # Load reactor
        if not args.reactor.exists():
            _print_error(f"Reactor file not found: {args.reactor}")
            sys.exit(1)
        
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
                json.dump(results, f, indent=2)
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
                print(json.dumps(results, indent=2))
        
    except ImportError as e:
        _print_error(f"Failed to import SMRForge modules: {e}")
        sys.exit(1)
    except Exception as e:
        _print_error(f"Failed to analyze reactor: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _reactor_analyze_batch(args):
    """Run batch analysis on multiple reactors."""
    try:
        from smrforge.convenience import create_reactor
        import json
        
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
        
        # Save results
        batch_results = {
            'processed': len(all_results),
            'failed': len(errors),
            'results': {str(k): v for k, v in all_results.items()},
            'errors': {str(k): v for k, v in errors.items()} if errors else {}
        }
        
        # Save summary
        summary_file = output_dir / 'batch_results.json'
        with open(summary_file, 'w') as f:
            json.dump(batch_results, f, indent=2)
        _print_success(f"Batch results saved to {summary_file}")
        
        # Save individual results
        for reactor_file, result in all_results.items():
            result_file = output_dir / f"{reactor_file.stem}_results.json"
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2)
        
        # Display summary
        if _RICH_AVAILABLE:
            table = Table(title="Batch Analysis Summary")
            table.add_column("Reactor", style="cyan")
            table.add_column("k-eff", style="green")
            table.add_column("Status", style="yellow")
            
            for reactor_file, result in all_results.items():
                k_eff = result.get('k_eff', 'N/A')
                table.add_row(reactor_file.name, str(k_eff), "✓ Success")
            
            for reactor_file, error in errors.items():
                error_msg = error[:50] + "..." if len(error) > 50 else error
                table.add_row(reactor_file.name, "N/A", f"✗ Error: {error_msg}")
            
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
                    json.dump(comparison, f, indent=2, default=str)
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
                    json.dump(report, f, indent=2)
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
            
            with open(args.reactor) as f:
                reactor_data = json.load(f)
            
            reactor = create_reactor(**reactor_data)
        else:
            _print_error("Must specify --reactor FILE")
            sys.exit(1)
        
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
                json.dump(options_dict, f, indent=2)
            _print_success(f"Burnup options saved to {output_path}")
        
    except ImportError as e:
        _print_error(f"Failed to import burnup modules: {e}")
        sys.exit(1)
    except Exception as e:
        _print_error(f"Failed to run burnup calculation: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


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
                    os.environ['LOCAL_ENDF_DIR'] = endf_str
                    cmd.extend(['--endf-dir', endf_str])
                except (TypeError, AttributeError):
                    # Handle Mock objects or other non-Path types
                    endf_str = str(args.endf_dir)
                    os.environ['LOCAL_ENDF_DIR'] = endf_str
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
        
        if args.output:
            cmd.extend(['--output', str(args.output)])
        
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
    except Exception as e:
        _print_error(f"Failed to visualize geometry: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


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
        
    except ImportError as e:
        _print_error(f"Failed to import visualization modules: {e}")
        sys.exit(1)
    except Exception as e:
        _print_error(f"Failed to visualize burnup results: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
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


def config_init(args):
    """Initialize configuration file."""
    try:
        if not _YAML_AVAILABLE:
            _print_error("PyYAML not available. Install PyYAML: pip install pyyaml")
            sys.exit(1)
        
        config_dir = Path.home() / ".smrforge"
        config_file = config_dir / "config.yaml"
        
        if config_file.exists() and not args.force:
            _print_error(f"Configuration file already exists: {config_file}")
            _print_info("Use --force to overwrite existing configuration")
            sys.exit(1)
        
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
                        'reactor_type': str(reactor.spec.reactor_type) if hasattr(reactor, 'spec') else 'unknown',
                    }
                    
                    with open(output_path, 'w') as f:
                        if output_path.suffix.lower() in ['.yaml', '.yml']:
                            yaml.safe_dump(reactor_dict, f)
                        else:
                            json.dump(reactor_dict, f, indent=2)
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
                        json.dump(results, f, indent=2)
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
        
        # Parse parameters
        parameters = {}
        if args.params:
            for param_spec in args.params:
                # Format: name:start:end:step or name:val1,val2,val3
                parts = param_spec.split(':')
                if len(parts) == 4:
                    name, start, end, step = parts
                    parameters[name] = (float(start), float(end), float(step))
                elif len(parts) == 2:
                    name, values_str = parts
                    values = [float(v) for v in values_str.split(',')]
                    parameters[name] = values
        
        # Get reactor template
        reactor_template = None
        if args.reactor:
            if Path(args.reactor).exists():
                import json
                with open(args.reactor) as f:
                    reactor_template = json.load(f)
            else:
                reactor_template = {"name": args.reactor}  # Try as preset
        
        # Create sweep config
        config = SweepConfig(
            parameters=parameters,
            analysis_types=args.analysis or ["keff"],
            reactor_template=reactor_template,
            output_dir=Path(args.output) if args.output else Path("sweep_results"),
            parallel=not args.no_parallel,
            max_workers=args.workers
        )
        
        # Run sweep
        sweep = ParameterSweep(config)
        results = sweep.run()
        
        # Save results
        output_file = Path(args.output) / "sweep_results.json" if args.output else Path("sweep_results/sweep_results.json")
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
                json.dump(output_data, f, indent=2)
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
                json.dump(output_data, f, indent=2)
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
                json.dump(report, f, indent=2)
            _print_success(f"Validation report saved to {args.output}")
        
    except Exception as e:
        _print_error(f"Failed to validate design: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


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
    burnup_visualize_parser.add_argument('--output', type=Path, help='Output file for plot')
    burnup_visualize_parser.add_argument('--format', type=str, choices=['png', 'pdf', 'svg', 'html'], default='png', help='Output format')
    burnup_visualize_parser.set_defaults(func=burnup_visualize)
    
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
    sweep_parser.add_argument('--reactor', type=str, help='Reactor file or preset name')
    sweep_parser.add_argument('--params', nargs='+', required=True, 
                            help='Parameter ranges (format: name:start:end:step or name:val1,val2,val3)')
    sweep_parser.add_argument('--analysis', nargs='+', default=['keff'], 
                            help='Analysis types to run (default: keff)')
    sweep_parser.add_argument('--output', type=Path, help='Output directory for results')
    sweep_parser.add_argument('--no-parallel', action='store_true', dest='no_parallel',
                            help='Disable parallel execution')
    sweep_parser.add_argument('--workers', type=int, help='Number of parallel workers')
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
