"""
SMRForge CLI main entry point.

Parses arguments and delegates to command handlers.
"""

import argparse
import sys
from pathlib import Path

import smrforge

from .commands.burnup import burnup_run
from .commands.config import config_init, config_set, config_show
from .commands.convert import convert_export
from .commands.data import (
    data_download,
    data_interpolate,
    data_setup,
    data_shield,
    data_validate,
)
from .commands.decay import decay_heat_calculate
from .commands.github import (
    GITHUB_ACTIONS_FEATURES,
    github_actions_configure,
    github_actions_disable,
    github_actions_enable,
    github_actions_list,
    github_actions_set,
    github_actions_status,
)
from .commands.reactor import (
    reactor_analyze,
    reactor_compare,
    reactor_create,
    reactor_list,
    template_create,
    template_modify,
    template_validate,
)
from .commands.report import report_design, report_validation
from .commands.serve import serve_dashboard
from .commands.shell import shell_interactive
from .commands.sweep import sweep_run
from .commands.thermal import thermal_lumped
from .commands.transient import transient_run
from .commands.validate import validate_benchmark, validate_design, validate_run
from .commands.visualize import (
    burnup_visualize,
    visualize_flux,
    visualize_geometry,
    visualize_tally,
)
from .commands.workflow import (
    batch_keff_run,
    workflow_atlas,
    workflow_benchmark,
    workflow_code_verify,
    workflow_design_point,
    workflow_design_study,
    workflow_doe,
    workflow_ml_export,
    workflow_multi_optimize,
    workflow_nl_design,
    workflow_optimize,
    workflow_pareto,
    workflow_regulatory_package,
    workflow_requirements_to_constraints,
    workflow_run,
    workflow_safety_report,
    workflow_scenario,
    workflow_sensitivity,
    workflow_sobol,
    workflow_surrogate,
    workflow_uq,
    workflow_variant,
)

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
        """,
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {smrforge.__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Serve command
    serve_parser = subparsers.add_parser(
        "serve", help="Launch the SMRForge web dashboard"
    )
    serve_parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address (default: 127.0.0.1)",
    )
    serve_parser.add_argument(
        "--port", type=int, default=8050, help="Port number (default: 8050)"
    )
    serve_parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    serve_parser.set_defaults(func=serve_dashboard)

    # Shell command
    shell_parser = subparsers.add_parser(
        "shell", help="Launch interactive Python shell with SMRForge pre-loaded"
    )
    shell_parser.set_defaults(func=shell_interactive)

    # Workflow subcommands
    workflow_parser = subparsers.add_parser("workflow", help="Workflow operations")
    workflow_subparsers = workflow_parser.add_subparsers(
        dest="workflow_command", help="Workflow commands"
    )

    # workflow run
    workflow_run_parser = workflow_subparsers.add_parser(
        "run", help="Run workflow from YAML file"
    )
    workflow_run_parser.add_argument("workflow", type=Path, help="Workflow YAML file")
    workflow_run_parser.set_defaults(func=workflow_run)

    # workflow batch-keff
    batch_keff_parser = workflow_subparsers.add_parser(
        "batch-keff", help="Run k-eff only on multiple reactor files in parallel"
    )
    batch_keff_parser.add_argument(
        "reactors",
        nargs="+",
        type=str,
        help="Reactor files or glob patterns (e.g. configs/*.json)",
    )
    batch_keff_parser.add_argument(
        "--no-parallel",
        action="store_true",
        dest="no_parallel",
        help="Run sequentially",
    )
    batch_keff_parser.add_argument(
        "--workers",
        type=int,
        help="Max parallel workers (default: auto; see SMRFORGE_MAX_BATCH_WORKERS)",
    )
    batch_keff_parser.add_argument(
        "--no-progress",
        action="store_true",
        dest="no_progress",
        help="Disable progress bar",
    )
    batch_keff_parser.add_argument(
        "--output", type=Path, help="Save results to JSON file"
    )
    batch_keff_parser.set_defaults(func=batch_keff_run)

    # workflow design-point
    dp_parser = workflow_subparsers.add_parser(
        "design-point", help="Steady-state design point summary"
    )
    dp_parser.add_argument(
        "--reactor", type=str, required=True, help="Reactor file or preset name"
    )
    dp_parser.add_argument("--output", type=Path, help="Save JSON")
    dp_parser.set_defaults(func=workflow_design_point)

    # workflow safety-report
    sr_parser = workflow_subparsers.add_parser(
        "safety-report", help="Coupled safety margin report"
    )
    sr_parser.add_argument(
        "--reactor", type=str, required=True, help="Reactor file or preset name"
    )
    sr_parser.add_argument("--constraints", type=Path, help="Constraint set JSON")
    sr_parser.add_argument("--output", type=Path, help="Save JSON")
    sr_parser.set_defaults(func=workflow_safety_report)

    # workflow doe
    doe_parser = workflow_subparsers.add_parser(
        "doe", help="Design of Experiments (factorial, LHS, Sobol, random)"
    )
    doe_parser.add_argument(
        "--method",
        type=str,
        choices=["factorial", "lhs", "sobol", "random"],
        default="lhs",
    )
    doe_parser.add_argument(
        "--factors",
        nargs="+",
        required=True,
        help="name:low:high or name:v1,v2,v3 for factorial",
    )
    doe_parser.add_argument(
        "--samples", type=int, default=10, help="Samples for lhs/sobol/random"
    )
    doe_parser.add_argument("--seed", type=int, help="Random seed")
    doe_parser.add_argument("--output", type=Path, help="Save JSON")
    doe_parser.set_defaults(func=workflow_doe)

    # workflow pareto
    pareto_parser = workflow_subparsers.add_parser(
        "pareto", help="Compute Pareto front from sweep results"
    )
    pareto_parser.add_argument(
        "--sweep-results", type=Path, required=True, help="Sweep results JSON"
    )
    pareto_parser.add_argument("--metric-x", type=str, default="k_eff")
    pareto_parser.add_argument(
        "--metric-y", type=str, help="Second metric (default: first other numeric)"
    )
    pareto_parser.add_argument("--output", type=Path, help="Save Pareto set JSON")
    pareto_parser.add_argument(
        "--plot", type=Path, help="Save Pareto front plot with knee point (HTML or PNG)"
    )
    pareto_parser.set_defaults(func=workflow_pareto)

    # workflow optimize
    opt_parser = workflow_subparsers.add_parser(
        "optimize", help="Design optimization (optionally constraint-aware)"
    )
    opt_parser.add_argument(
        "--reactor", type=Path, required=True, help="Base design JSON file"
    )
    opt_parser.add_argument(
        "--params", nargs="+", required=True, help="name:low:high per parameter"
    )
    opt_parser.add_argument("--objective", type=str, default="min_neg_keff")
    opt_parser.add_argument(
        "--constraints", type=Path, help="Constraint set JSON for penalty"
    )
    opt_parser.add_argument("--method", type=str, default="differential_evolution")
    opt_parser.add_argument("--max-iter", type=int, default=50)
    opt_parser.add_argument("--output", type=Path, help="Save results JSON")
    opt_parser.set_defaults(func=workflow_optimize)

    # workflow uq
    uq_parser = workflow_subparsers.add_parser(
        "uq", help="Uncertainty quantification (Monte Carlo / LHS)"
    )
    uq_parser.add_argument(
        "--reactor", type=Path, required=True, help="Base design JSON file"
    )
    uq_parser.add_argument(
        "--params",
        nargs="+",
        required=True,
        help="name:nominal:distribution[:uncertainty]",
    )
    uq_parser.add_argument("--samples", type=int, default=100)
    uq_parser.add_argument("--seed", type=int, default=42)
    uq_parser.add_argument("--output", type=Path, help="Save UQ summary JSON")
    uq_parser.set_defaults(func=workflow_uq)

    # workflow design-study
    ds_parser = workflow_subparsers.add_parser(
        "design-study", help="Run design point + safety report"
    )
    ds_parser.add_argument(
        "--reactor", type=str, required=True, help="Reactor file or preset name"
    )
    ds_parser.add_argument("--constraints", type=Path, help="Constraint set JSON")
    ds_parser.add_argument(
        "--output-dir", type=Path, default=Path("design_study_output")
    )
    ds_parser.add_argument(
        "--html", action="store_true", help="Also write design_study_report.html"
    )
    ds_parser.add_argument(
        "--plot", type=Path, help="Save safety margins bar chart (HTML or PNG)"
    )
    ds_parser.set_defaults(func=workflow_design_study)

    # workflow variant
    var_parser = workflow_subparsers.add_parser(
        "variant", help="Save design as named variant"
    )
    var_parser.add_argument(
        "--reactor", type=str, required=True, help="Reactor file or preset name"
    )
    var_parser.add_argument("--name", type=str, default="variant")
    var_parser.add_argument("--output-dir", type=Path, help="Output directory")
    var_parser.set_defaults(func=workflow_variant)

    # workflow sensitivity
    sens_parser = workflow_subparsers.add_parser(
        "sensitivity", help="Sensitivity ranking (OAT) from sweep results"
    )
    sens_parser.add_argument(
        "--sweep-results", type=Path, required=True, help="Sweep results JSON"
    )
    sens_parser.add_argument(
        "--params", nargs="+", help="Parameter names (default: from results)"
    )
    sens_parser.add_argument("--metric", type=str, default="k_eff")
    sens_parser.add_argument("--output", type=Path, help="Save ranking JSON")
    sens_parser.add_argument(
        "--plot", type=Path, help="Save sensitivity bar chart (HTML or PNG)"
    )
    sens_parser.set_defaults(func=workflow_sensitivity)

    # workflow sobol
    sobol_parser = workflow_subparsers.add_parser(
        "sobol", help="Sobol sensitivity indices from sweep results"
    )
    sobol_parser.add_argument(
        "--sweep-results", type=Path, required=True, help="Sweep results JSON"
    )
    sobol_parser.add_argument(
        "--params", nargs="+", help="Parameter names (default: from results)"
    )
    sobol_parser.add_argument("--metric", type=str, default="k_eff")
    sobol_parser.add_argument("--output", type=Path, help="Save Sobol JSON")
    sobol_parser.add_argument(
        "--plot", type=Path, help="Save Sobol indices chart (HTML or PNG)"
    )
    sobol_parser.set_defaults(func=workflow_sobol)

    # workflow scenario
    scenario_parser = workflow_subparsers.add_parser(
        "scenario", help="Scenario-based design (multiple missions)"
    )
    scenario_parser.add_argument(
        "--reactor", type=str, required=True, help="Reactor file or preset"
    )
    scenario_parser.add_argument(
        "--scenarios",
        nargs="+",
        required=True,
        help="name:path_or_preset (e.g. baseload:regulatory_limits)",
    )
    scenario_parser.add_argument("--output-dir", type=Path, help="Output directory")
    scenario_parser.add_argument(
        "--plot", type=Path, help="Save scenario comparison chart (HTML or PNG)"
    )
    scenario_parser.set_defaults(func=workflow_scenario)

    # workflow atlas
    atlas_parser = workflow_subparsers.add_parser(
        "atlas", help="Build design space atlas (catalog of presets)"
    )
    atlas_parser.add_argument("--output-dir", type=Path, default=Path("atlas_output"))
    atlas_parser.add_argument(
        "--presets", nargs="+", help="Preset names (default: all from list_presets)"
    )
    atlas_parser.add_argument(
        "--plot",
        type=Path,
        help="Save atlas scatter (power vs k_eff, colored by pass) (HTML or PNG)",
    )
    atlas_parser.set_defaults(func=workflow_atlas)

    # workflow surrogate
    sur_parser = workflow_subparsers.add_parser(
        "surrogate", help="Fit surrogate model from sweep results"
    )
    sur_parser.add_argument(
        "--sweep-results", type=Path, required=True, help="Sweep results JSON"
    )
    sur_parser.add_argument(
        "--params", nargs="+", required=True, help="Parameter names"
    )
    sur_parser.add_argument("--metric", type=str, default="k_eff")
    sur_parser.add_argument(
        "--method", type=str, choices=["rbf", "linear"], default="rbf"
    )
    sur_parser.add_argument("--output", type=Path, help="Save pickle surrogate")
    sur_parser.set_defaults(func=workflow_surrogate)

    # workflow ml-export (Pro)
    ml_export_parser = workflow_subparsers.add_parser(
        "ml-export",
        help="Export sweep results to Parquet/HDF5 for ML. Pro tier.",
    )
    ml_export_parser.add_argument(
        "--results", type=Path, required=True, help="Sweep results JSON"
    )
    ml_export_parser.add_argument(
        "--output", type=Path, help="Output Parquet or HDF5 file (default: design_points.parquet)"
    )
    ml_export_parser.set_defaults(func=workflow_ml_export)

    # workflow requirements-to-constraints
    req_parser = workflow_subparsers.add_parser(
        "requirements-to-constraints",
        help="Parse requirements YAML/JSON to ConstraintSet",
    )
    req_parser.add_argument(
        "--requirements",
        type=Path,
        required=True,
        help="Requirements YAML or JSON file",
    )
    req_parser.add_argument("--name", type=str, default="from_requirements")
    req_parser.add_argument(
        "--output", type=Path, required=True, help="Output constraint set JSON"
    )
    req_parser.set_defaults(func=workflow_requirements_to_constraints)

    # workflow nl-design (Pro): Natural-language reactor design
    nl_parser = workflow_subparsers.add_parser(
        "nl-design",
        help="Design reactor from natural language. Pro tier.",
    )
    nl_parser.add_argument(
        "--text",
        type=str,
        required=True,
        help='Design intent (e.g. "10 MW HTGR with k-eff 1.0-1.05, enrichment <20%%")',
    )
    nl_parser.add_argument("--output", type=Path, help="Save reactor spec JSON")
    nl_parser.set_defaults(func=workflow_nl_design)

    # workflow code-verify (Pro): Code-to-code verification
    cv_parser = workflow_subparsers.add_parser(
        "code-verify",
        help="Unified code-to-code verification. Pro tier.",
    )
    cv_parser.add_argument(
        "--reactor", type=str, required=True, help="Preset or reactor file"
    )
    cv_parser.add_argument(
        "--output", type=Path, default=Path("verification_output"), help="Output dir"
    )
    cv_parser.set_defaults(func=workflow_code_verify)

    # workflow regulatory-package (Pro)
    rp_parser = workflow_subparsers.add_parser(
        "regulatory-package",
        help="Generate regulatory submission package. Pro tier.",
    )
    rp_parser.add_argument(
        "--reactor", type=str, required=True, help="Preset or reactor file"
    )
    rp_parser.add_argument(
        "--output", type=Path, default=Path("regulatory_package"), help="Output dir"
    )
    rp_parser.add_argument(
        "--framework", type=str, default="NRC", help="NRC, IAEA, or ANS"
    )
    rp_parser.set_defaults(func=workflow_regulatory_package)

    # workflow benchmark (Pro): One-click benchmark reproduction
    bench_parser = workflow_subparsers.add_parser(
        "benchmark",
        help="One-click benchmark reproduction. Pro tier.",
    )
    bench_parser.add_argument(
        "--id",
        dest="benchmark_id",
        type=str,
        help="Benchmark ID (omit to list available)",
    )
    bench_parser.add_argument("--output", type=Path, help="Output directory")
    bench_parser.set_defaults(func=workflow_benchmark)

    # workflow multi-optimize (Pro): Multi-objective optimization
    mo_parser = workflow_subparsers.add_parser(
        "multi-optimize",
        help="Multi-objective design optimization. Pro tier.",
    )
    mo_parser.add_argument(
        "--reactor", type=Path, required=True, help="Base design JSON"
    )
    mo_parser.add_argument(
        "--params", nargs="+", required=True, help="name:low:high per parameter"
    )
    mo_parser.add_argument("--max-eval", type=int, default=100)
    mo_parser.add_argument("--seed", type=int)
    mo_parser.add_argument("--output", type=Path)
    mo_parser.set_defaults(func=workflow_multi_optimize)

    # Convert subcommands (Serpent, OpenMC, MCNP export)
    convert_parser = subparsers.add_parser(
        "convert",
        help="Export reactor to external code format (Serpent, OpenMC, MCNP)",
    )
    convert_subparsers = convert_parser.add_subparsers(
        dest="convert_command", help="Export format"
    )
    for fmt in ("serpent", "openmc", "mcnp"):
        p = convert_subparsers.add_parser(fmt, help=f"Export to {fmt.upper()}")
        p.add_argument(
            "--reactor",
            type=str,
            required=True,
            help="Reactor preset name or JSON file path",
        )
        p.add_argument(
            "--output",
            "-o",
            type=Path,
            required=True,
            help="Output file or directory (for OpenMC)",
        )
        if fmt == "openmc":
            p.add_argument("--particles", type=int, default=1000)
            p.add_argument("--batches", type=int, default=20)
        p.set_defaults(format=fmt, func=convert_export)

    # Reactor subcommands
    reactor_parser = subparsers.add_parser("reactor", help="Reactor operations")
    reactor_subparsers = reactor_parser.add_subparsers(
        dest="reactor_command", help="Reactor commands"
    )

    # reactor create
    create_parser = reactor_subparsers.add_parser(
        "create", help="Create a reactor from preset or configuration"
    )
    create_parser.add_argument("--preset", type=str, help="Preset design name")
    create_parser.add_argument(
        "--config", type=Path, help="Configuration file (JSON or YAML)"
    )
    create_parser.add_argument("--power", type=float, help="Thermal power [MW]")
    create_parser.add_argument("--enrichment", type=float, help="Fuel enrichment")
    create_parser.add_argument(
        "--type", type=str, help="Reactor type (htgr, pwr, bwr, fast)"
    )
    create_parser.add_argument(
        "--core-height", type=float, dest="core_height", help="Core height [cm]"
    )
    create_parser.add_argument(
        "--core-diameter", type=float, dest="core_diameter", help="Core diameter [cm]"
    )
    create_parser.add_argument(
        "--fuel-type", type=str, dest="fuel_type", help="Fuel type"
    )
    create_parser.add_argument("--output", type=Path, help="Output file")
    create_parser.add_argument(
        "--format", type=str, choices=["json", "yaml"], help="Output format"
    )
    create_parser.set_defaults(func=reactor_create)

    # reactor analyze
    analyze_parser = reactor_subparsers.add_parser(
        "analyze", help="Run analysis on a reactor"
    )
    analyze_parser.add_argument("--reactor", type=Path, help="Reactor file (JSON)")
    analyze_parser.add_argument(
        "--batch",
        nargs="+",
        type=str,
        help="Batch process multiple reactor files (glob patterns allowed)",
    )
    analyze_parser.add_argument(
        "--parallel", action="store_true", help="Process batch in parallel"
    )
    analyze_parser.add_argument(
        "--workers", type=int, default=4, help="Number of parallel workers (default: 4)"
    )
    analyze_parser.add_argument(
        "--keff", action="store_true", help="Calculate k-effective only"
    )
    analyze_parser.add_argument(
        "--neutronics", action="store_true", help="Full neutronics analysis"
    )
    analyze_parser.add_argument(
        "--burnup", action="store_true", help="Burnup calculation"
    )
    analyze_parser.add_argument(
        "--safety", action="store_true", help="Safety transient analysis"
    )
    analyze_parser.add_argument("--full", action="store_true", help="Run all analyses")
    analyze_parser.add_argument(
        "--max-iterations",
        type=int,
        dest="max_iterations",
        help="Solver max iterations",
    )
    analyze_parser.add_argument("--tolerance", type=float, help="Solver tolerance")
    analyze_parser.add_argument("--output", type=Path, help="Output file for results")
    analyze_parser.set_defaults(func=reactor_analyze)

    # reactor list
    list_parser = reactor_subparsers.add_parser(
        "list", help="List available preset reactor designs"
    )
    list_parser.add_argument(
        "--detailed", action="store_true", help="Show detailed information"
    )
    list_parser.add_argument("--type", type=str, help="Filter by reactor type")
    list_parser.set_defaults(func=reactor_list)

    # reactor compare
    compare_parser = reactor_subparsers.add_parser(
        "compare", help="Compare multiple reactor designs"
    )
    compare_parser.add_argument(
        "--presets", nargs="+", help="Preset design names to compare"
    )
    compare_parser.add_argument(
        "--reactors", nargs="+", type=Path, help="Reactor files to compare"
    )
    compare_parser.add_argument(
        "--metrics",
        nargs="+",
        help="Metrics to compare (e.g., keff,power_density,temperature_peak)",
        default=["k_eff"],
    )
    compare_parser.add_argument(
        "--output", type=Path, help="Output file for comparison (JSON or HTML)"
    )
    compare_parser.add_argument(
        "--visualize",
        action="store_true",
        help="Generate visualization (future feature)",
    )
    compare_parser.set_defaults(func=reactor_compare)

    # Data subcommands
    data_parser = subparsers.add_parser("data", help="Data management operations")
    data_subparsers = data_parser.add_subparsers(
        dest="data_command", help="Data commands"
    )

    # data setup
    setup_parser = data_subparsers.add_parser(
        "setup", help="Setup ENDF data directory (interactive)"
    )
    setup_parser.add_argument(
        "--endf-dir", type=Path, dest="endf_dir", help="ENDF directory path"
    )
    setup_parser.set_defaults(func=data_setup)

    # data download
    download_parser = data_subparsers.add_parser(
        "download", help="Download ENDF nuclear data"
    )
    download_parser.add_argument(
        "--library", type=str, default="ENDF-B-VIII.1", help="ENDF library name"
    )
    download_parser.add_argument(
        "--nuclide-set",
        type=str,
        dest="nuclide_set",
        help="Predefined nuclide set: quickstart (U235,U238,Pu239), common_smr (~30 nuclides)",
    )
    download_parser.add_argument(
        "--nuclides", nargs="+", help="Specific nuclides to download"
    )
    download_parser.add_argument("--output", type=Path, help="Output directory")
    download_parser.add_argument(
        "--max-workers", type=int, dest="max_workers", help="Parallel downloads"
    )
    download_parser.add_argument(
        "--validate", action="store_true", help="Validate downloaded files"
    )
    download_parser.add_argument(
        "--resume", action="store_true", help="Resume interrupted download"
    )
    download_parser.set_defaults(func=data_download)

    # data validate
    validate_data_parser = data_subparsers.add_parser(
        "validate", help="Validate ENDF files"
    )
    validate_data_parser.add_argument(
        "--endf-dir", type=Path, dest="endf_dir", help="ENDF directory to validate"
    )
    validate_data_parser.add_argument(
        "--files", nargs="+", type=Path, help="Specific ENDF files to validate"
    )
    validate_data_parser.add_argument(
        "--output", type=Path, help="Output file for validation report"
    )
    validate_data_parser.set_defaults(func=data_validate)

    # data interpolate (temperature interpolation)
    interpolate_parser = data_subparsers.add_parser(
        "interpolate", help="Interpolate cross-sections at different temperatures"
    )
    interpolate_parser.add_argument(
        "--nuclide", type=str, required=True, help="Nuclide (e.g., U235, Pu239)"
    )
    interpolate_parser.add_argument(
        "--reaction",
        type=str,
        required=True,
        help="Reaction type (fission, capture, total, elastic)",
    )
    interpolate_parser.add_argument(
        "--temperature", type=float, required=True, help="Target temperature [K]"
    )
    interpolate_parser.add_argument(
        "--available-temps",
        nargs="+",
        type=float,
        dest="available_temps",
        help="Available temperatures [K] (default: 293.6, 600.0, 900.0, 1200.0)",
    )
    interpolate_parser.add_argument(
        "--method",
        type=str,
        choices=["linear", "log_log", "spline"],
        default="linear",
        help="Interpolation method (default: linear)",
    )
    interpolate_parser.add_argument(
        "--endf-dir", type=Path, dest="endf_dir", help="ENDF directory path"
    )
    interpolate_parser.add_argument(
        "--output", type=Path, help="Output file (JSON or CSV)"
    )
    interpolate_parser.add_argument(
        "--plot", action="store_true", help="Plot interpolated cross-section"
    )
    interpolate_parser.add_argument(
        "--plot-output", type=Path, dest="plot_output", help="Plot output file"
    )
    interpolate_parser.set_defaults(func=data_interpolate)

    # data shield (self-shielding)
    shield_parser = data_subparsers.add_parser(
        "shield", help="Calculate self-shielded cross-sections"
    )
    shield_parser.add_argument(
        "--nuclide", type=str, required=True, help="Nuclide (e.g., U235, U238)"
    )
    shield_parser.add_argument(
        "--reaction",
        type=str,
        required=True,
        help="Reaction type (fission, capture, total, elastic)",
    )
    shield_parser.add_argument(
        "--temperature", type=float, required=True, help="Temperature [K]"
    )
    shield_parser.add_argument(
        "--sigma-0",
        type=float,
        dest="sigma_0",
        default=1.0,
        help="Background cross-section [barns] (default: 1.0)",
    )
    shield_parser.add_argument(
        "--method",
        type=str,
        choices=["bondarenko", "subgroup", "equivalence"],
        default="bondarenko",
        help="Self-shielding method (default: bondarenko)",
    )
    shield_parser.add_argument(
        "--endf-dir", type=Path, dest="endf_dir", help="ENDF directory path"
    )
    shield_parser.add_argument("--output", type=Path, help="Output file (JSON or CSV)")
    shield_parser.add_argument(
        "--plot", action="store_true", help="Plot shielded vs unshielded cross-section"
    )
    shield_parser.add_argument(
        "--plot-output", type=Path, dest="plot_output", help="Plot output file"
    )
    shield_parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare shielded and unshielded cross-sections",
    )
    shield_parser.set_defaults(func=data_shield)

    # Burnup subcommands
    burnup_parser = subparsers.add_parser("burnup", help="Burnup/depletion operations")
    burnup_subparsers = burnup_parser.add_subparsers(
        dest="burnup_command", help="Burnup commands"
    )

    # burnup run
    burnup_run_parser = burnup_subparsers.add_parser(
        "run", help="Run burnup/depletion calculation"
    )
    burnup_run_parser.add_argument(
        "--reactor", type=Path, required=True, help="Reactor file (JSON)"
    )
    burnup_run_parser.add_argument(
        "--time-steps", nargs="+", dest="time_steps", help="Time steps [days]"
    )
    burnup_run_parser.add_argument(
        "--power-density",
        type=float,
        dest="power_density",
        help="Power density [W/cm³]",
    )
    burnup_run_parser.add_argument(
        "--checkpoint-interval",
        type=float,
        dest="checkpoint_interval",
        help="Checkpoint every N days (enables checkpointing)",
    )
    burnup_run_parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        dest="checkpoint_dir",
        help="Directory for checkpoint files",
    )
    burnup_run_parser.add_argument(
        "--resume-from",
        type=Path,
        dest="resume_from",
        help="Resume from checkpoint file",
    )
    burnup_run_parser.add_argument(
        "--adaptive-tracking",
        action="store_true",
        dest="adaptive_tracking",
        help="Enable adaptive nuclide tracking",
    )
    burnup_run_parser.add_argument(
        "--nuclide-threshold",
        type=float,
        dest="nuclide_threshold",
        help="Nuclide concentration threshold",
    )
    burnup_run_parser.add_argument(
        "--output", type=Path, help="Output file for results"
    )
    burnup_run_parser.set_defaults(func=burnup_run)

    # burnup visualize
    burnup_visualize_parser = burnup_subparsers.add_parser(
        "visualize", help="Visualize burnup results"
    )
    burnup_visualize_parser.add_argument(
        "--results", type=Path, required=True, help="Burnup results file (JSON or HDF5)"
    )
    burnup_visualize_parser.add_argument(
        "--nuclides",
        nargs="+",
        help="Specific nuclides to plot (e.g., U235 U238 Pu239)",
    )
    burnup_visualize_parser.add_argument(
        "--burnup", action="store_true", help="Plot burnup over time"
    )
    burnup_visualize_parser.add_argument(
        "--keff", action="store_true", help="Plot k-eff evolution"
    )
    burnup_visualize_parser.add_argument(
        "--composition", action="store_true", help="Plot composition changes"
    )
    burnup_visualize_parser.add_argument(
        "--batch-comparison",
        action="store_true",
        help="Compare burnup across multiple fuel batches",
    )
    burnup_visualize_parser.add_argument(
        "--refueling-cycles",
        action="store_true",
        help="Visualize multi-cycle burnup evolution",
    )
    burnup_visualize_parser.add_argument(
        "--control-rod-effects",
        action="store_true",
        help="Compare burnup with/without control rods",
    )
    burnup_visualize_parser.add_argument(
        "--dashboard", action="store_true", help="Generate enhanced burnup dashboard"
    )
    burnup_visualize_parser.add_argument(
        "--batch-results",
        type=Path,
        nargs="+",
        help="Additional batch result files for comparison",
    )
    burnup_visualize_parser.add_argument(
        "--without-rods-results",
        type=Path,
        help="Results file without control rods for comparison",
    )
    burnup_visualize_parser.add_argument(
        "--output", type=Path, help="Output file for plot"
    )
    burnup_visualize_parser.add_argument(
        "--format",
        type=str,
        choices=["png", "pdf", "svg", "html"],
        default="png",
        help="Output format",
    )
    burnup_visualize_parser.add_argument(
        "--backend",
        type=str,
        choices=["plotly", "matplotlib"],
        default="plotly",
        help="Visualization backend",
    )
    burnup_visualize_parser.set_defaults(func=burnup_visualize)

    # Decay heat subcommands
    decay_parser = subparsers.add_parser("decay", help="Decay heat calculations")
    decay_subparsers = decay_parser.add_subparsers(
        dest="decay_command", help="Decay heat commands"
    )

    # decay calculate
    decay_calculate_parser = decay_subparsers.add_parser(
        "calculate", help="Calculate decay heat over time"
    )
    decay_calculate_parser.add_argument(
        "--inventory", type=Path, help="Nuclide inventory file (JSON)"
    )
    decay_calculate_parser.add_argument(
        "--nuclides",
        nargs="+",
        help="Nuclide concentrations (format: U235:1e20 Cs137:1e19)",
    )
    decay_calculate_parser.add_argument(
        "--times", nargs="+", type=float, help="Time points after shutdown [seconds]"
    )
    decay_calculate_parser.add_argument(
        "--time-range",
        nargs=3,
        type=float,
        metavar=("START", "END", "STEPS"),
        help="Time range: start end num_steps",
    )
    decay_calculate_parser.add_argument(
        "--output", type=Path, help="Output file for results (JSON)"
    )
    decay_calculate_parser.add_argument(
        "--plot", action="store_true", help="Generate decay heat plot"
    )
    decay_calculate_parser.add_argument(
        "--plot-output", type=Path, help="Output file for plot"
    )
    decay_calculate_parser.add_argument(
        "--format",
        type=str,
        choices=["png", "pdf", "svg", "html"],
        default="png",
        help="Plot format",
    )
    decay_calculate_parser.add_argument(
        "--backend",
        type=str,
        choices=["plotly", "matplotlib"],
        default="plotly",
        help="Visualization backend",
    )
    decay_calculate_parser.add_argument(
        "--endf-dir", type=Path, dest="endf_dir", help="ENDF directory for decay data"
    )
    decay_calculate_parser.set_defaults(func=decay_heat_calculate)

    # Validate subcommands
    validate_parser = subparsers.add_parser(
        "validate", help="Validation and testing operations"
    )
    validate_subparsers = validate_parser.add_subparsers(
        dest="validate_command", help="Validation commands"
    )

    # validate run
    validate_run_parser = validate_subparsers.add_parser(
        "run", help="Run validation tests"
    )
    validate_run_parser.add_argument(
        "--endf-dir", type=Path, dest="endf_dir", help="ENDF directory"
    )
    validate_run_parser.add_argument(
        "--tests", nargs="+", help="Specific test suites to run"
    )
    validate_run_parser.add_argument(
        "--benchmarks", type=Path, help="Benchmark database file"
    )
    validate_run_parser.add_argument(
        "--output", type=Path, help="Output file for results"
    )
    validate_run_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )
    validate_run_parser.set_defaults(func=validate_run)

    # validate benchmark (Community benchmark suite)
    validate_benchmark_parser = validate_subparsers.add_parser(
        "benchmark", help="Run Community benchmark cases (regression validation)"
    )
    validate_benchmark_parser.add_argument(
        "--benchmarks-file", type=Path, help="Path to community_benchmarks.json"
    )
    validate_benchmark_parser.add_argument(
        "--cases", nargs="+", help="Specific case IDs to run"
    )
    validate_benchmark_parser.add_argument(
        "--output", type=Path, help="Output Markdown report path"
    )
    validate_benchmark_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )
    validate_benchmark_parser.set_defaults(func=validate_benchmark)

    # Visualize subcommands
    visualize_parser = subparsers.add_parser(
        "visualize", help="Visualization operations"
    )
    visualize_subparsers = visualize_parser.add_subparsers(
        dest="visualize_command", help="Visualization commands"
    )

    # visualize geometry
    visualize_geom_parser = visualize_subparsers.add_parser(
        "geometry", help="Visualize reactor geometry"
    )
    visualize_geom_parser.add_argument(
        "--reactor", type=Path, required=True, help="Reactor file (JSON)"
    )
    visualize_geom_parser.add_argument(
        "--output", type=Path, help="Output file for visualization"
    )
    visualize_geom_parser.add_argument(
        "--format",
        type=str,
        choices=["png", "pdf", "svg", "html"],
        default="png",
        help="Output format",
    )
    visualize_geom_parser.add_argument(
        "--3d", dest="d3d", action="store_true", help="Generate 3D visualization"
    )
    visualize_geom_parser.add_argument(
        "--backend",
        type=str,
        choices=["plotly", "pyvista"],
        default="plotly",
        help="Visualization backend",
    )
    visualize_geom_parser.add_argument(
        "--interactive", action="store_true", help="Display interactive visualization"
    )
    visualize_geom_parser.set_defaults(func=visualize_geometry)

    # visualize flux
    visualize_flux_parser = visualize_subparsers.add_parser(
        "flux", help="Plot flux distribution"
    )
    visualize_flux_parser.add_argument(
        "--results", type=Path, required=True, help="Results file (JSON)"
    )
    visualize_flux_parser.add_argument(
        "--output", type=Path, help="Output file for plot"
    )
    visualize_flux_parser.add_argument(
        "--format",
        type=str,
        choices=["png", "pdf", "svg"],
        default="png",
        help="Output format",
    )
    visualize_flux_parser.add_argument("--group", type=int, help="Energy group index")
    visualize_flux_parser.set_defaults(func=visualize_flux)

    # visualize tally (Pro - OpenMC mesh tally)
    visualize_tally_parser = visualize_subparsers.add_parser(
        "tally",
        help="Visualize OpenMC mesh tally from statepoint. Pro tier (requires openmc).",
    )
    visualize_tally_parser.add_argument(
        "--statepoint", type=Path, required=True, help="Path to statepoint.N.h5"
    )
    visualize_tally_parser.add_argument(
        "--tally-id", type=int, help="Tally ID (default: first mesh tally)"
    )
    visualize_tally_parser.add_argument(
        "--score", type=str, help="Score type (flux, fission, etc.)"
    )
    visualize_tally_parser.add_argument(
        "--output", type=Path, help="Output file (HTML or PNG)"
    )
    visualize_tally_parser.add_argument(
        "--backend",
        type=str,
        choices=["plotly", "matplotlib", "pyvista"],
        default="plotly",
        help="Visualization backend",
    )
    visualize_tally_parser.add_argument(
        "--no-uncertainty",
        action="store_true",
        dest="no_uncertainty",
        help="Do not show uncertainty",
    )
    visualize_tally_parser.set_defaults(func=visualize_tally)

    # Sweep subcommands
    sweep_parser = subparsers.add_parser(
        "sweep", help="Parameter sweep and sensitivity analysis"
    )
    sweep_parser.add_argument(
        "--config",
        type=Path,
        help="Load sweep config from JSON or YAML file (optional; else use --params)",
    )
    sweep_parser.add_argument("--reactor", type=str, help="Reactor file or preset name")
    sweep_parser.add_argument(
        "--params",
        nargs="+",
        help="Parameter ranges (format: name:start:end:step or name:val1,val2,val3); required if no --config",
    )
    sweep_parser.add_argument(
        "--analysis",
        nargs="+",
        default=["keff"],
        help="Analysis types to run (default: keff)",
    )
    sweep_parser.add_argument(
        "--output", type=Path, help="Output directory for results"
    )
    sweep_parser.add_argument(
        "--no-parallel",
        action="store_true",
        dest="no_parallel",
        help="Disable parallel execution",
    )
    sweep_parser.add_argument("--workers", type=int, help="Number of parallel workers")
    sweep_parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from latest intermediate file in output dir",
    )
    sweep_parser.add_argument(
        "--progress", action="store_true", help="Show progress bar (Rich)"
    )
    sweep_parser.add_argument(
        "--surrogate",
        type=Path,
        help="Path to surrogate model (.onnx, .pt, .pkl) for fast evaluation (Pro)",
    )
    sweep_parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for deterministic runs",
    )
    sweep_parser.set_defaults(func=sweep_run)

    # Reactor template subcommands
    template_parser = reactor_subparsers.add_parser(
        "template", help="Template-based reactor design library"
    )
    template_subparsers = template_parser.add_subparsers(
        dest="template_command", help="Template commands"
    )

    # template create
    template_create_parser = template_subparsers.add_parser(
        "create", help="Create reactor template"
    )
    template_create_parser.add_argument(
        "--from-preset", dest="from_preset", type=str, help="Create from preset"
    )
    template_create_parser.add_argument(
        "--from-file", dest="from_file", type=str, help="Create from reactor file"
    )
    template_create_parser.add_argument("--name", type=str, help="Template name")
    template_create_parser.add_argument(
        "--description", type=str, help="Template description"
    )
    template_create_parser.add_argument("--output", type=Path, help="Output file")
    template_create_parser.add_argument(
        "--library", action="store_true", help="Save to template library"
    )
    template_create_parser.set_defaults(func=template_create)

    # template modify
    template_modify_parser = template_subparsers.add_parser(
        "modify", help="Modify reactor template"
    )
    template_modify_parser.add_argument("template", type=Path, help="Template file")
    template_modify_parser.add_argument(
        "--param", nargs="+", help="Parameters to modify (format: name=value)"
    )
    template_modify_parser.set_defaults(func=template_modify)

    # template validate
    template_validate_parser = template_subparsers.add_parser(
        "validate", help="Validate reactor template"
    )
    template_validate_parser.add_argument("template", type=Path, help="Template file")
    template_validate_parser.set_defaults(func=template_validate)

    # validate design (add to existing validate_subparsers from line 2361)
    # Note: validate_parser and validate_subparsers are already defined at line 2357-2361
    validate_design_parser = validate_subparsers.add_parser(
        "design", help="Validate reactor design against constraints"
    )
    validate_design_parser.add_argument("--reactor", type=Path, help="Reactor file")
    validate_design_parser.add_argument("--preset", type=str, help="Preset name")
    validate_design_parser.add_argument(
        "--constraints", type=Path, help="Constraint set file (JSON)"
    )
    validate_design_parser.add_argument(
        "--output", type=Path, help="Output file for validation report"
    )
    validate_design_parser.set_defaults(func=validate_design)

    # Config subcommands
    # Report subcommands (Community design summary)
    report_parser = subparsers.add_parser(
        "report",
        help="Generate design summary report (Community). For full reports see SMRForge Pro.",
    )
    report_subparsers = report_parser.add_subparsers(
        dest="report_command", help="Report commands"
    )
    report_design_parser = report_subparsers.add_parser(
        "design", help="Generate Markdown design summary from reactor analysis"
    )
    report_design_parser.add_argument(
        "--preset", type=str, help="Preset name (e.g. valar-10)"
    )
    report_design_parser.add_argument("--reactor", type=Path, help="Reactor JSON file")
    report_design_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("design_report.md"),
        help="Output Markdown file",
    )
    report_design_parser.set_defaults(func=report_design)

    # report validation (Pro)
    report_validation_parser = report_subparsers.add_parser(
        "validation",
        help="Generate surrogate validation report (pred vs ref). Pro tier.",
    )
    report_validation_parser.add_argument(
        "--predictions", type=Path, required=True, help="Predictions file (.txt, .npy, .csv)"
    )
    report_validation_parser.add_argument(
        "--reference", type=Path, required=True, help="Reference values file"
    )
    report_validation_parser.add_argument(
        "--output", type=Path, default=Path("validation_report.json"), help="Output JSON"
    )
    report_validation_parser.add_argument(
        "--metric", type=str, default="output", help="Metric name for report"
    )
    report_validation_parser.add_argument(
        "--pdf", action="store_true", help="Also save PDF report"
    )
    report_validation_parser.set_defaults(func=report_validation)

    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_subparsers = config_parser.add_subparsers(
        dest="config_command", help="Config commands"
    )

    # config show
    config_show_parser = config_subparsers.add_parser(
        "show", help="Show current configuration"
    )
    config_show_parser.add_argument(
        "--key",
        type=str,
        help="Show specific configuration key (e.g., endf.default_directory)",
    )
    config_show_parser.set_defaults(func=config_show)

    # config set
    config_set_parser = config_subparsers.add_parser(
        "set", help="Set configuration value"
    )
    config_set_parser.add_argument(
        "key", type=str, help="Configuration key (e.g., endf.default_directory)"
    )
    config_set_parser.add_argument("value", type=str, help="Configuration value")
    config_set_parser.set_defaults(func=config_set)

    # config init
    config_init_parser = config_subparsers.add_parser(
        "init", help="Initialize configuration file"
    )
    config_init_parser.add_argument(
        "--template",
        type=str,
        choices=["default", "production", "development"],
        default="default",
        help="Configuration template",
    )
    config_init_parser.add_argument(
        "--force", action="store_true", help="Overwrite existing configuration file"
    )
    config_init_parser.set_defaults(func=config_init)

    # GitHub Actions subcommands
    github_parser = subparsers.add_parser(
        "github",
        help="GitHub Actions management: enable/disable workflows and select which features run",
    )
    github_parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        metavar="DIR",
        help="Repository root (default: current directory)",
    )
    github_subparsers = github_parser.add_subparsers(
        dest="github_command", help="GitHub Actions commands"
    )

    # github actions status
    github_status_parser = github_subparsers.add_parser(
        "status", help="Show GitHub Actions status (global and per-feature)"
    )
    github_status_parser.add_argument(
        "--output", type=Path, help="Output file for status (JSON)"
    )
    github_status_parser.set_defaults(func=github_actions_status)

    # github actions list
    github_list_parser = github_subparsers.add_parser(
        "list", help="List available workflow features and whether they run"
    )
    github_list_parser.set_defaults(func=github_actions_list)

    # github actions configure (interactive or with flags)
    github_configure_parser = github_subparsers.add_parser(
        "configure",
        help="Select which features run in GitHub Actions (interactive or use --ci/--docs/... on|off)",
    )
    _feat_ids = [f["id"] for f in GITHUB_ACTIONS_FEATURES]
    github_configure_parser.add_argument(
        "--ci",
        choices=["on", "off"],
        default=None,
        help="CI workflow (tests, lint, build)",
    )
    github_configure_parser.add_argument(
        "--ci-quick",
        dest="ci_quick",
        choices=["on", "off"],
        default=None,
        help="Quick CI (single Python, no coverage)",
    )
    github_configure_parser.add_argument(
        "--docs", choices=["on", "off"], default=None, help="Docs build and deploy"
    )
    github_configure_parser.add_argument(
        "--performance",
        choices=["on", "off"],
        default=None,
        help="Performance benchmarks",
    )
    github_configure_parser.add_argument(
        "--security",
        choices=["on", "off"],
        default=None,
        help="Security audit workflow",
    )
    github_configure_parser.add_argument(
        "--release",
        choices=["on", "off"],
        default=None,
        help="Release to PyPI on version tags",
    )
    github_configure_parser.add_argument(
        "--nightly",
        choices=["on", "off"],
        default=None,
        help="Scheduled nightly full run",
    )
    github_configure_parser.add_argument(
        "--docker",
        choices=["on", "off"],
        default=None,
        help="Build and push Docker image",
    )
    github_configure_parser.add_argument(
        "--dependabot",
        choices=["on", "off"],
        default=None,
        help="Run CI on Dependabot PRs",
    )
    github_configure_parser.add_argument(
        "--stale", choices=["on", "off"], default=None, help="Stale issue/PR management"
    )
    github_configure_parser.set_defaults(func=github_actions_configure)

    # github actions set <feature> on|off
    github_set_parser = github_subparsers.add_parser(
        "set", help="Set one feature on or off"
    )
    github_set_parser.add_argument("feature", choices=_feat_ids, help="Feature ID")
    github_set_parser.add_argument(
        "value", choices=["on", "off"], help="Enable or disable"
    )
    github_set_parser.set_defaults(func=github_actions_set)

    # github actions enable
    github_enable_parser = github_subparsers.add_parser(
        "enable", help="Enable GitHub Actions workflows (global master switch)"
    )
    github_enable_parser.set_defaults(func=github_actions_enable)

    # github actions disable
    github_disable_parser = github_subparsers.add_parser(
        "disable", help="Disable GitHub Actions workflows (global master switch)"
    )
    github_disable_parser.set_defaults(func=github_actions_disable)

    # Transient subcommands (NEW)
    transient_parser = subparsers.add_parser(
        "transient", help="Transient analysis operations"
    )
    transient_subparsers = transient_parser.add_subparsers(
        dest="transient_command", help="Transient commands"
    )

    # transient run
    transient_run_parser = transient_subparsers.add_parser(
        "run", help="Run transient analysis"
    )
    transient_run_parser.add_argument(
        "--power", type=float, required=True, help="Initial reactor power [W]"
    )
    transient_run_parser.add_argument(
        "--temperature", type=float, required=True, help="Initial temperature [K]"
    )
    transient_run_parser.add_argument(
        "--type",
        type=str,
        choices=[
            "reactivity_insertion",
            "reactivity_step",
            "power_change",
            "decay_heat",
        ],
        default="reactivity_insertion",
        help="Transient type",
    )
    transient_run_parser.add_argument(
        "--reactivity",
        type=float,
        help="Reactivity inserted [dk/k] (for reactivity_insertion/step)",
    )
    transient_run_parser.add_argument(
        "--duration", type=float, default=100.0, help="Simulation duration [s]"
    )
    transient_run_parser.add_argument(
        "--scram-available",
        action="store_true",
        dest="scram_available",
        default=True,
        help="Scram available (default: True)",
    )
    transient_run_parser.add_argument(
        "--scram-delay",
        type=float,
        default=1.0,
        dest="scram_delay",
        help="Scram delay [s]",
    )
    transient_run_parser.add_argument(
        "--long-term",
        action="store_true",
        dest="long_term",
        help="Enable long-term optimizations (>1 day)",
    )
    transient_run_parser.add_argument(
        "--output", type=Path, help="Output file for results (JSON)"
    )
    transient_run_parser.add_argument(
        "--plot", action="store_true", help="Generate and display plot"
    )
    transient_run_parser.add_argument(
        "--plot-output",
        type=Path,
        dest="plot_output",
        help="Save plot to file (PNG, HTML, PDF, SVG)",
    )
    transient_run_parser.add_argument(
        "--plot-backend",
        type=str,
        choices=["plotly", "matplotlib"],
        default="plotly",
        dest="plot_backend",
        help="Plotting backend (default: plotly)",
    )
    transient_run_parser.set_defaults(func=transient_run)

    # Thermal subcommands (NEW)
    thermal_parser = subparsers.add_parser(
        "thermal", help="Thermal-hydraulics operations"
    )
    thermal_subparsers = thermal_parser.add_subparsers(
        dest="thermal_command", help="Thermal commands"
    )

    # thermal lumped
    thermal_lumped_parser = thermal_subparsers.add_parser(
        "lumped", help="Run lumped-parameter thermal-hydraulics analysis"
    )
    thermal_lumped_parser.add_argument(
        "--config",
        type=Path,
        help="Configuration file (JSON/YAML) with lump definitions",
    )
    thermal_lumped_parser.add_argument(
        "--duration", type=float, default=3600.0, help="Simulation duration [s]"
    )
    thermal_lumped_parser.add_argument(
        "--max-step", type=float, help="Maximum time step [s] (default: adaptive)"
    )
    thermal_lumped_parser.add_argument(
        "--adaptive",
        action="store_true",
        default=True,
        help="Use adaptive time stepping (default: True)",
    )
    thermal_lumped_parser.add_argument(
        "--output", type=Path, help="Output file for results (JSON)"
    )
    thermal_lumped_parser.add_argument(
        "--plot", action="store_true", help="Generate and display plot"
    )
    thermal_lumped_parser.add_argument(
        "--plot-output",
        type=Path,
        dest="plot_output",
        help="Save plot to file (PNG, HTML, PDF, SVG)",
    )
    thermal_lumped_parser.add_argument(
        "--plot-backend",
        type=str,
        choices=["plotly", "matplotlib"],
        default="plotly",
        dest="plot_backend",
        help="Plotting backend (default: plotly)",
    )
    thermal_lumped_parser.set_defaults(func=thermal_lumped)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()  # pragma: no cover
        sys.exit(0)  # pragma: no cover

    # Handle commands - func is set via set_defaults on each subparser
    if hasattr(args, "func"):
        args.func(args)
    else:  # pragma: no cover
        # Command without handler - show help
        parser.print_help()  # pragma: no cover
        sys.exit(0)  # pragma: no cover


if __name__ == "__main__":
    main()
