"""
SMRForge CLI

Command-line interface for SMRForge, including dashboard launcher.
All features remain available via Python API and CLI.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

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
        from smrforge.convenience import create_reactor, list_presets
        from smrforge.validation.models import ReactorSpecification
        
        # Check if preset is provided
        if args.preset:
            if args.preset not in list_presets():
                _print_error(f"Preset '{args.preset}' not found.")
                print(f"\nAvailable presets: {', '.join(list_presets())}")
                sys.exit(1)
            
            reactor = create_reactor(args.preset)
            _print_success(f"Created reactor from preset: {args.preset}")
            
        # Check if config file is provided
        elif args.config:
            if not args.config.exists():
                _print_error(f"Config file not found: {args.config}")
                sys.exit(1)
            
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
        
        # Load reactor
        if args.reactor:
            if not args.reactor.exists():
                _print_error(f"Reactor file not found: {args.reactor}")
                sys.exit(1)
            
            with open(args.reactor) as f:
                reactor_data = json.load(f)
            
            # Create reactor from data
            reactor = create_reactor(**reactor_data)
        else:
            _print_error("Must specify --reactor FILE")
            sys.exit(1)
        
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
    """Compare multiple reactor designs."""
    try:
        import smrforge as smr
        from smrforge.convenience import create_reactor, compare_designs
        import json
        
        if args.presets:
            # Compare presets
            comparison = compare_designs(args.presets)
        elif args.reactors:
            # Compare reactor files
            reactors = []
            for reactor_file in args.reactors:
                if not reactor_file.exists():
                    _print_error(f"Reactor file not found: {reactor_file}")
                    sys.exit(1)
                with open(reactor_file) as f:
                    reactor_data = json.load(f)
                reactors.append(create_reactor(**reactor_data))
            # Comparison logic would need to be implemented
            _print_error("Comparing reactor files not yet implemented")
            print("Use --presets for preset comparison")
            sys.exit(1)
        else:
            _print_error("Must specify --presets or --reactors")
            sys.exit(1)
        
        # Display comparison
        if _RICH_AVAILABLE:
            console.print("\n[bold cyan]Design Comparison[/bold cyan]")
            console.print(json.dumps(comparison, indent=2, default=str))
        else:
            print("\nDesign Comparison:")
            print("=" * 70)
            print(json.dumps(comparison, indent=2, default=str))
        
        # Save if output specified
        if args.output:
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
        
        # Create burnup options
        burnup_options = BurnupOptions(
            time_steps=time_steps,
            power_density=args.power_density or 1e6,
            adaptive_tracking=args.adaptive_tracking,
            nuclide_threshold=args.nuclide_threshold or 1e15,
        )
        
        _print_info(f"Running burnup calculation...")
        _print_info(f"  Time steps: {time_steps} days")
        _print_info(f"  Power density: {burnup_options.power_density:.2e} W/cm³")
        _print_info(f"  Adaptive tracking: {burnup_options.adaptive_tracking}")
        
        _print_info("\nNOTE: Burnup calculation requires geometry and cross-section data.")
        _print_info("For full burnup calculations, use the Python API:")
        print("  from smrforge.burnup import BurnupSolver, BurnupOptions")
        print("  burnup = BurnupSolver(neutronics_solver, burnup_options)")
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
    """Run validation tests."""
    try:
        import subprocess
        from pathlib import Path
        
        # Build pytest command
        cmd = ['pytest', 'tests/test_validation_comprehensive.py', '-v']
        
        if args.endf_dir:
            import os
            os.environ['LOCAL_ENDF_DIR'] = str(args.endf_dir)
        
        if args.tests:
            # Filter to specific test classes (would need more sophisticated parsing)
            _print_info(f"NOTE: --tests filter not yet fully implemented")
        
        if args.benchmarks:
            _print_info(f"NOTE: Benchmark comparison requires Python API integration")
        
        if args.verbose:
            cmd.append('-v')
        else:
            cmd.append('-q')
        
        _print_info("Running validation tests...")
        _print_info(f"Command: {' '.join(cmd)}")
        
        # Run pytest
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            _print_success("Validation tests passed")
        else:
            _print_error("Validation tests failed")
            sys.exit(result.returncode)
        
        # Generate report if requested
        if args.output:
            _print_info(f"\nNOTE: Report generation requires:")
            print(f"  python scripts/generate_validation_report.py --results results.json")
        
    except FileNotFoundError:
        _print_error("pytest not found. Install pytest: pip install pytest")
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
    analyze_parser.add_argument('--reactor', type=Path, required=True, help='Reactor file (JSON)')
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
    compare_parser.add_argument('--metrics', nargs='+', help='Metrics to compare')
    compare_parser.add_argument('--output', type=Path, help='Output file for comparison')
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
    burnup_run_parser.add_argument('--adaptive-tracking', action='store_true', dest='adaptive_tracking', help='Enable adaptive nuclide tracking')
    burnup_run_parser.add_argument('--nuclide-threshold', type=float, dest='nuclide_threshold', help='Nuclide concentration threshold')
    burnup_run_parser.add_argument('--output', type=Path, help='Output file for results')
    burnup_run_parser.set_defaults(func=burnup_run)
    
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
