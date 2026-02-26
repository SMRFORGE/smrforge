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
            _print_info(
                "NOTE: Interactive setup is recommended. Use without --endf-dir for interactive mode."
            )
            # For now, call interactive setup
            setup_endf_data_interactive()
        else:
            # Interactive setup
            setup_endf_data_interactive()

    except ImportError as e:
        _print_error(f"Failed to import ENDF setup module: {e}")  # pragma: no cover
        sys.exit(1)  # pragma: no cover
    except Exception as e:
        _print_error(f"Failed to setup ENDF data: {e}")
        if args.verbose if hasattr(args, "verbose") else False:
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)




def data_download(args):
    """Download ENDF nuclear data."""
    try:
        from smrforge.data_downloader import download_endf_data

        kwargs = {}
        if args.library:
            kwargs["library"] = args.library
        if args.nuclide_set:
            kwargs["nuclide_set"] = args.nuclide_set
        if args.nuclides:
            kwargs["isotopes"] = args.nuclides
        if args.output:
            kwargs["output_dir"] = str(args.output)
        if args.max_workers:
            kwargs["max_workers"] = args.max_workers
        if args.validate:
            kwargs["validate"] = True
        if args.resume:
            kwargs["resume"] = True

        _print_info(f"Downloading ENDF data...")
        _print_info(f"  Library: {kwargs.get('library', 'ENDF-B-VIII.1')}")

        stats = download_endf_data(**kwargs)

        if _RICH_AVAILABLE:
            table = Table(title="Download Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Downloaded", str(stats.get("downloaded", 0)))
            table.add_row("Skipped", str(stats.get("skipped", 0)))
            table.add_row("Failed", str(stats.get("failed", 0)))
            table.add_row("Output Directory", str(stats.get("output_dir", "N/A")))
            console.print(table)
        else:  # pragma: no cover
            print(f"\n✓ Download complete:")  # pragma: no cover
            print(
                f"  Downloaded: {stats.get('downloaded', 0)} files"
            )  # pragma: no cover
            print(f"  Skipped: {stats.get('skipped', 0)} files")  # pragma: no cover
            print(f"  Failed: {stats.get('failed', 0)} files")  # pragma: no cover
            print(f"  Output: {stats.get('output_dir', 'N/A')}")  # pragma: no cover

    except ImportError as e:  # pragma: no cover
        _print_error(f"Data downloader not available: {e}")  # pragma: no cover
        print(
            "Install required dependencies or use manual ENDF setup"
        )  # pragma: no cover
        sys.exit(1)  # pragma: no cover
    except Exception as e:  # pragma: no cover
        _print_error(f"Failed to download data: {e}")  # pragma: no cover
        if args.verbose if hasattr(args, "verbose") else False:  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover




def data_validate(args):
    """Validate ENDF files."""
    try:
        from smrforge.core.reactor_core import NuclearDataCache, scan_endf_directory

        if args.endf_dir:
            endf_dir = Path(args.endf_dir)
            if not endf_dir.exists():
                _print_error(
                    f"ENDF directory not found: {endf_dir}"
                )  # pragma: no cover
                sys.exit(1)  # pragma: no cover

            _print_info(f"Scanning ENDF directory: {endf_dir}")

            # Scan directory
            scan_results = scan_endf_directory(endf_dir)

            # Validate files
            total_files = scan_results.get("total_files", 0)
            valid_files = scan_results.get("valid_files", 0)
            nuclides = scan_results.get("nuclides", [])

            if _RICH_AVAILABLE:
                table = Table(title="ENDF Validation Results")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                table.add_row("Total Files", str(total_files))
                table.add_row("Valid Files", str(valid_files))
                table.add_row("Invalid Files", str(total_files - valid_files))
                table.add_row("Unique Nuclides", str(len(nuclides)))
                table.add_row(
                    "Directory Structure",
                    scan_results.get("directory_structure", "unknown"),
                )
                console.print(table)

                if nuclides:
                    console.print(
                        f"\n[bold]Sample nuclides found:[/bold] {', '.join(nuclides[:10])}"
                    )
                    if len(nuclides) > 10:
                        console.print(
                            f"[dim]... and {len(nuclides) - 10} more[/dim]"
                        )  # pragma: no cover
            else:  # pragma: no cover
                print(f"\nENDF Validation Results:")  # pragma: no cover
                print(f"  Total Files: {total_files}")  # pragma: no cover
                print(f"  Valid Files: {valid_files}")  # pragma: no cover
                print(
                    f"  Invalid Files: {total_files - valid_files}"
                )  # pragma: no cover
                print(f"  Unique Nuclides: {len(nuclides)}")  # pragma: no cover
                print(
                    f"  Directory Structure: {scan_results.get('directory_structure', 'unknown')}"
                )  # pragma: no cover
                if nuclides:  # pragma: no cover
                    print(
                        f"\nSample nuclides: {', '.join(nuclides[:10])}"
                    )  # pragma: no cover

            # Save report if output specified
            if args.output:
                report = {  # pragma: no cover
                    "validation_date": str(Path.cwd()),  # pragma: no cover
                    "endf_directory": str(endf_dir),  # pragma: no cover
                    "results": scan_results,  # pragma: no cover
                }  # pragma: no cover
                with open(args.output, "w") as f:  # pragma: no cover
                    json.dump(_to_jsonable(report), f, indent=2)  # pragma: no cover
                _print_success(
                    f"Validation report saved to {args.output}"
                )  # pragma: no cover

        elif args.files:
            # Validate specific files
            valid_count = 0
            invalid_count = 0

            for file_path in args.files:
                file_path = Path(file_path)
                if not file_path.exists():
                    _print_error(f"File not found: {file_path}")  # pragma: no cover
                    invalid_count += 1  # pragma: no cover
                    continue  # pragma: no cover

                is_valid = NuclearDataCache._validate_endf_file(file_path)
                if is_valid:
                    valid_count += 1
                    _print_success(f"{file_path.name}: Valid")
                else:
                    invalid_count += 1  # pragma: no cover
                    _print_error(f"{file_path.name}: Invalid")  # pragma: no cover

            if _RICH_AVAILABLE:
                console.print(
                    f"\n[bold]Summary:[/bold] {valid_count} valid, {invalid_count} invalid"
                )  # pragma: no cover
            else:  # pragma: no cover
                print(f"\nSummary: {valid_count} valid, {invalid_count} invalid")
        else:  # pragma: no cover
            _print_error("Must specify --endf-dir or --files")
            sys.exit(1)

    except ImportError as e:  # pragma: no cover
        _print_error(f"Failed to import validation modules: {e}")  # pragma: no cover
        sys.exit(1)  # pragma: no cover
    except Exception as e:  # pragma: no cover
        _print_error(f"Failed to validate ENDF files: {e}")  # pragma: no cover
        if args.verbose if hasattr(args, "verbose") else False:  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover




def data_interpolate(args):
    """Interpolate cross-sections at different temperatures."""
    try:
        from smrforge.convenience_utils import get_nuclide
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide
        from smrforge.core.temperature_interpolation import (
            InterpolationMethod,
            interpolate_cross_section_temperature,
        )

        # Parse nuclide
        nuclide = get_nuclide(args.nuclide)
        if nuclide is None:
            _print_error(f"Invalid nuclide: {args.nuclide}")
            sys.exit(1)

        # Parse interpolation method
        method_map = {
            "linear": InterpolationMethod.LINEAR,
            "log_log": InterpolationMethod.LOG_LOG,
            "spline": InterpolationMethod.SPLINE,
        }
        method = method_map[args.method]

        # Setup cache
        cache = NuclearDataCache()
        if args.endf_dir:
            cache.local_endf_dir = Path(args.endf_dir)  # pragma: no cover

        # Get available temperatures
        available_temps = args.available_temps
        if available_temps is None:
            available_temps = np.array([293.6, 600.0, 900.0, 1200.0])
        else:
            available_temps = np.array(available_temps)  # pragma: no cover

        _print_info(
            f"Interpolating {nuclide.name} {args.reaction} cross-section at {args.temperature:.1f} K"
        )
        _print_info(f"Using {args.method} interpolation method")

        # Interpolate
        energy, xs = interpolate_cross_section_temperature(
            cache=cache,
            nuclide=nuclide,
            reaction=args.reaction,
            target_temperature=args.temperature,
            available_temperatures=available_temps,
            method=method,
        )

        # Display results
        if _RICH_AVAILABLE:
            table = Table(
                title=f"{nuclide.name} {args.reaction} Cross-Section at {args.temperature:.1f} K"
            )  # pragma: no cover
            table.add_column("Energy [eV]", style="cyan")  # pragma: no cover
            table.add_column("Cross-Section [barn]", style="green")  # pragma: no cover

            # Show sample points
            n_points = min(20, len(energy))  # pragma: no cover
            indices = np.linspace(
                0, len(energy) - 1, n_points, dtype=int
            )  # pragma: no cover
            for idx in indices:  # pragma: no cover
                table.add_row(
                    f"{energy[idx]:.2e}", f"{xs[idx]:.6e}"
                )  # pragma: no cover

            console.print(table)  # pragma: no cover
            console.print(
                f"\n[bold]Total points:[/bold] {len(energy)}"
            )  # pragma: no cover
            console.print(
                f"[bold]Energy range:[/bold] {energy[0]:.2e} - {energy[-1]:.2e} eV"
            )  # pragma: no cover
            console.print(
                f"[bold]XS range:[/bold] {np.min(xs):.6e} - {np.max(xs):.6e} barn"
            )  # pragma: no cover
        else:  # pragma: no cover
            print(
                f"\n{nuclide.name} {args.reaction} Cross-Section at {args.temperature:.1f} K"
            )
            print(f"  Total points: {len(energy)}")
            print(f"  Energy range: {energy[0]:.2e} - {energy[-1]:.2e} eV")
            print(f"  XS range: {np.min(xs):.6e} - {np.max(xs):.6e} barn")

        # Save output
        if args.output:
            output_path = Path(args.output)
            if output_path.suffix.lower() == ".csv":
                import csv  # pragma: no cover

                with open(output_path, "w", newline="") as f:  # pragma: no cover
                    writer = csv.writer(f)  # pragma: no cover
                    writer.writerow(
                        ["Energy [eV]", "Cross-Section [barn]"]
                    )  # pragma: no cover
                    for e, x in zip(energy, xs):  # pragma: no cover
                        writer.writerow([e, x])  # pragma: no cover
            else:
                # JSON format
                data = {
                    "nuclide": nuclide.name,
                    "reaction": args.reaction,
                    "temperature": args.temperature,
                    "method": args.method,
                    "energy": energy.tolist(),
                    "cross_section": xs.tolist(),
                }
                with open(output_path, "w") as f:
                    json.dump(_to_jsonable(data), f, indent=2)
            _print_success(f"Results saved to {args.output}")

        # Plot if requested
        if args.plot or args.plot_output:
            try:  # pragma: no cover
                import matplotlib.pyplot as plt  # pragma: no cover

                plt.figure(figsize=(10, 6))  # pragma: no cover
                plt.loglog(
                    energy,
                    xs,
                    "b-",
                    linewidth=2,
                    label=f"{nuclide.name} {args.reaction}",
                )  # pragma: no cover
                plt.xlabel("Energy [eV]")  # pragma: no cover
                plt.ylabel("Cross-Section [barn]")  # pragma: no cover
                plt.title(
                    f"{nuclide.name} {args.reaction} at {args.temperature:.1f} K ({args.method} interpolation)"
                )  # pragma: no cover
                plt.grid(True, alpha=0.3)  # pragma: no cover
                plt.legend()  # pragma: no cover

                if args.plot_output:  # pragma: no cover
                    plt.savefig(
                        args.plot_output, dpi=150, bbox_inches="tight"
                    )  # pragma: no cover
                    _print_success(
                        f"Plot saved to {args.plot_output}"
                    )  # pragma: no cover
                else:  # pragma: no cover
                    plt.show()  # pragma: no cover
            except ImportError:  # pragma: no cover
                _print_warning(
                    "Matplotlib not available for plotting"
                )  # pragma: no cover

    except Exception as e:
        _print_error(f"Failed to interpolate cross-section: {e}")  # pragma: no cover
        if args.verbose if hasattr(args, "verbose") else False:  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover




def data_shield(args):
    """Calculate self-shielded cross-sections."""
    try:
        from smrforge.convenience_utils import get_nuclide
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide
        from smrforge.core.self_shielding_integration import (
            get_cross_section_with_self_shielding,
        )

        # Parse nuclide
        nuclide = get_nuclide(args.nuclide)
        if nuclide is None:
            _print_error(f"Invalid nuclide: {args.nuclide}")
            sys.exit(1)

        # Setup cache
        cache = NuclearDataCache()
        if args.endf_dir:
            cache.local_endf_dir = Path(args.endf_dir)  # pragma: no cover

        _print_info(
            f"Calculating self-shielded {nuclide.name} {args.reaction} cross-section"
        )
        _print_info(
            f"Method: {args.method}, Temperature: {args.temperature:.1f} K, σ₀: {args.sigma_0:.2f} barn"
        )

        # Get shielded cross-section
        energy_shielded, xs_shielded = get_cross_section_with_self_shielding(
            cache=cache,
            nuclide=nuclide,
            reaction=args.reaction,
            temperature=args.temperature,
            sigma_0=args.sigma_0,
            method=args.method,
            enable_self_shielding=True,
        )

        # Get unshielded for comparison if requested
        if args.compare or args.plot:
            energy_unshielded, xs_unshielded = (
                get_cross_section_with_self_shielding(  # pragma: no cover
                    cache=cache,
                    nuclide=nuclide,
                    reaction=args.reaction,
                    temperature=args.temperature,
                    sigma_0=args.sigma_0,
                    method=args.method,
                    enable_self_shielding=False,
                )
            )

        # Display results
        if _RICH_AVAILABLE:
            table = Table(
                title=f"{nuclide.name} {args.reaction} Self-Shielded Cross-Section"
            )  # pragma: no cover
            table.add_column("Energy [eV]", style="cyan")  # pragma: no cover
            table.add_column("Shielded XS [barn]", style="green")  # pragma: no cover
            if args.compare:  # pragma: no cover
                table.add_column(
                    "Unshielded XS [barn]", style="yellow"
                )  # pragma: no cover
                table.add_column(
                    "Shielding Factor", style="magenta"
                )  # pragma: no cover

            # Show sample points
            n_points = min(20, len(energy_shielded))  # pragma: no cover
            indices = np.linspace(
                0, len(energy_shielded) - 1, n_points, dtype=int
            )  # pragma: no cover
            for idx in indices:  # pragma: no cover
                row = [
                    f"{energy_shielded[idx]:.2e}",
                    f"{xs_shielded[idx]:.6e}",
                ]  # pragma: no cover
                if args.compare:  # pragma: no cover
                    unshielded_val = np.interp(
                        energy_shielded[idx], energy_unshielded, xs_unshielded
                    )  # pragma: no cover
                    shielding_factor = (
                        xs_shielded[idx] / unshielded_val if unshielded_val > 0 else 1.0
                    )  # pragma: no cover
                    row.append(f"{unshielded_val:.6e}")  # pragma: no cover
                    row.append(f"{shielding_factor:.4f}")  # pragma: no cover
                table.add_row(*row)  # pragma: no cover

            console.print(table)  # pragma: no cover
            console.print(
                f"\n[bold]Total points:[/bold] {len(energy_shielded)}"
            )  # pragma: no cover
            console.print(
                f"[bold]Energy range:[/bold] {energy_shielded[0]:.2e} - {energy_shielded[-1]:.2e} eV"
            )  # pragma: no cover
            console.print(
                f"[bold]Shielded XS range:[/bold] {np.min(xs_shielded):.6e} - {np.max(xs_shielded):.6e} barn"
            )  # pragma: no cover
            if args.compare:  # pragma: no cover
                avg_shielding = (
                    np.mean(xs_shielded) / np.mean(xs_unshielded)
                    if np.mean(xs_unshielded) > 0
                    else 1.0
                )  # pragma: no cover
                console.print(
                    f"[bold]Average shielding factor:[/bold] {avg_shielding:.4f}"
                )  # pragma: no cover
        else:  # pragma: no cover
            print(f"\n{nuclide.name} {args.reaction} Self-Shielded Cross-Section")
            print(f"  Total points: {len(energy_shielded)}")
            print(
                f"  Energy range: {energy_shielded[0]:.2e} - {energy_shielded[-1]:.2e} eV"
            )
            print(
                f"  Shielded XS range: {np.min(xs_shielded):.6e} - {np.max(xs_shielded):.6e} barn"
            )

        # Save output
        if args.output:
            output_path = Path(args.output)
            if output_path.suffix.lower() == ".csv":
                import csv  # pragma: no cover

                with open(output_path, "w", newline="") as f:  # pragma: no cover
                    writer = csv.writer(f)  # pragma: no cover
                    if args.compare:  # pragma: no cover
                        writer.writerow(
                            [
                                "Energy [eV]",
                                "Shielded XS [barn]",
                                "Unshielded XS [barn]",
                                "Shielding Factor",
                            ]
                        )  # pragma: no cover
                        for e, xs_s, xs_u in zip(
                            energy_shielded,
                            xs_shielded,  # pragma: no cover
                            np.interp(
                                energy_shielded, energy_unshielded, xs_unshielded
                            ),
                        ):  # pragma: no cover
                            factor = (
                                xs_s / xs_u if xs_u > 0 else 1.0
                            )  # pragma: no cover
                            writer.writerow([e, xs_s, xs_u, factor])  # pragma: no cover
                    else:  # pragma: no cover
                        writer.writerow(
                            ["Energy [eV]", "Cross-Section [barn]"]
                        )  # pragma: no cover
                        for e, x in zip(
                            energy_shielded, xs_shielded
                        ):  # pragma: no cover
                            writer.writerow([e, x])  # pragma: no cover
            else:
                # JSON format
                data = {
                    "nuclide": nuclide.name,
                    "reaction": args.reaction,
                    "temperature": args.temperature,
                    "sigma_0": args.sigma_0,
                    "method": args.method,
                    "energy": energy_shielded.tolist(),
                    "cross_section_shielded": xs_shielded.tolist(),
                }
                if args.compare:
                    data["cross_section_unshielded"] = (
                        xs_unshielded.tolist()
                    )  # pragma: no cover
                    data["shielding_factors"] = (
                        xs_shielded / xs_unshielded
                    ).tolist()  # pragma: no cover
                with open(output_path, "w") as f:
                    json.dump(_to_jsonable(data), f, indent=2)
            _print_success(f"Results saved to {args.output}")

        # Plot if requested
        if args.plot or args.plot_output:
            try:  # pragma: no cover
                import matplotlib.pyplot as plt  # pragma: no cover

                plt.figure(figsize=(10, 6))  # pragma: no cover
                plt.loglog(
                    energy_shielded,
                    xs_shielded,
                    "b-",
                    linewidth=2,  # pragma: no cover
                    label=f"{nuclide.name} {args.reaction} (shielded)",
                )  # pragma: no cover
                if args.compare:  # pragma: no cover
                    plt.loglog(
                        energy_unshielded,
                        xs_unshielded,
                        "r--",
                        linewidth=2,  # pragma: no cover
                        label=f"{nuclide.name} {args.reaction} (unshielded)",
                    )  # pragma: no cover
                plt.xlabel("Energy [eV]")  # pragma: no cover
                plt.ylabel("Cross-Section [barn]")  # pragma: no cover
                plt.title(
                    f"{nuclide.name} {args.reaction} Self-Shielding\n"  # pragma: no cover
                    f"T={args.temperature:.1f} K, σ₀={args.sigma_0:.2f} barn, Method={args.method}"
                )  # pragma: no cover
                plt.grid(True, alpha=0.3)  # pragma: no cover
                plt.legend()  # pragma: no cover

                if args.plot_output:  # pragma: no cover
                    plt.savefig(
                        args.plot_output, dpi=150, bbox_inches="tight"
                    )  # pragma: no cover
                    _print_success(
                        f"Plot saved to {args.plot_output}"
                    )  # pragma: no cover
                else:  # pragma: no cover
                    plt.show()  # pragma: no cover
            except ImportError:  # pragma: no cover
                _print_warning(
                    "Matplotlib not available for plotting"
                )  # pragma: no cover

    except Exception as e:
        _print_error(
            f"Failed to calculate self-shielded cross-section: {e}"
        )  # pragma: no cover
        if args.verbose if hasattr(args, "verbose") else False:  # pragma: no cover
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)  # pragma: no cover


