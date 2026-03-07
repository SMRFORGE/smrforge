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
    _exit_pro_required,
    _print_error,
    _print_info,
    _print_success,
    _print_warning,
    _require_path,
    _save_workflow_plot,
    _to_jsonable,
    console,
    rprint,
    yaml,
    Panel,
    Table,
)


def report_design(args):
    """Generate design summary report from reactor analysis."""
    try:
        import smrforge as smr
        from smrforge.reporting import generate_markdown_report

        if args.preset:
            results = smr.analyze_preset(args.preset)
            title = f"Design Summary: {args.preset}"
        elif args.reactor and args.reactor.exists():
            reactor = smr.SimpleReactor.load(args.reactor)
            results = reactor.solve()
            title = f"Design Summary: {args.reactor.stem}"
        else:
            _exit_error("Specify --preset or --reactor.")
        out = Path(args.output) if args.output else Path("design_report.md")
        generate_markdown_report(results, title=title, output_path=out)
        _print_success(f"Report saved to {out}")
    except Exception as e:
        _exit_error(f"Report generation failed: {e}")


def report_validation(args):
    """Generate surrogate validation report (pred vs ref). Pro tier only."""
    try:
        from smrforge_pro.ai.validation_report import (
            generate_validation_report,
            SurrogateValidationReport,
        )
    except ImportError:
        _exit_pro_required("Validation report")
    import numpy as np

    pred_path = _require_path(
        args, "predictions", "--predictions and --reference files required"
    )
    ref_path = _require_path(
        args, "reference", "--predictions and --reference files required"
    )
    output = Path(getattr(args, "output", None) or "validation_report.json")
    if pred_path.suffix == ".npy":
        pred = np.load(pred_path)
    else:
        pred = np.loadtxt(
            pred_path, delimiter="," if pred_path.suffix == ".csv" else None
        )
    if ref_path.suffix == ".npy":
        ref = np.load(ref_path)
    else:
        ref = np.loadtxt(ref_path, delimiter="," if ref_path.suffix == ".csv" else None)
    pred = np.asarray(pred).flatten()
    ref = np.asarray(ref).flatten()
    report = generate_validation_report(
        pred, ref, metric_name=getattr(args, "metric", "output")
    )
    report.save_json(output)

    # Rich table: validation metrics summary (with plain fallback)
    if _RICH_AVAILABLE and Table is not None and console is not None:
        table = Table(title="Validation Report")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        table.add_row("Metric", report.metric_name)
        table.add_row("Samples", str(report.n_samples))
        table.add_row("MAE", f"{report.mae:.6f}")
        table.add_row("RMSE", f"{report.rmse:.6f}")
        table.add_row("Max Error", f"{report.max_err:.6f}")
        console.print(table)
    else:
        print("\nValidation metrics:")
        print(f"  Metric: {report.metric_name}")
        print(f"  Samples: {report.n_samples}")
        print(f"  MAE: {report.mae:.6f}")
        print(f"  RMSE: {report.rmse:.6f}")
        print(f"  Max Error: {report.max_err:.6f}")

    if getattr(args, "pdf", False):
        pdf_path = output.with_suffix(".pdf")
        report.save_pdf(pdf_path)
        _print_success(f"Reports saved to {output} and {pdf_path}")
    else:
        _print_success(f"Report saved to {output}")
