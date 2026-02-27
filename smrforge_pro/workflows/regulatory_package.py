"""
Regulatory package: NRC/IAEA submission - inputs, outputs, traceability matrix, margins.

Pro tier - one-click submission-ready package.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.workflows.regulatory_package")


def generate_regulatory_package(
    reactor: Any,
    output_dir: Any,
    preset: str = "10_CFR_50",
    include_traceability: bool = True,
) -> Dict[str, Any]:
    """
    Generate NRC/IAEA submission package: inputs, outputs, traceability matrix, margins.

    Args:
        reactor: Reactor instance
        output_dir: Output directory for package
        preset: Traceability preset (10_CFR_50, IAEA_SSR_2_1, ANS_5_1)
        include_traceability: Include requirements-to-design traceability matrix

    Returns:
        Package manifest (paths, summary)
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    manifest: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "preset": preset,
        "files": [],
    }

    from smrforge.convenience import get_design_point

    point = get_design_point(reactor)
    design_path = out / "design_summary.json"
    design_path.write_text(json.dumps(point, indent=2), encoding="utf-8")
    manifest["files"].append(str(design_path.name))

    from smrforge.validation.safety_report import safety_margin_report

    report = safety_margin_report(reactor)
    safety_path = out / "safety_report.json"
    safety_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    manifest["files"].append(str(safety_path.name))

    if include_traceability:
        try:
            from smrforge_pro.reporting.regulatory import generate_traceability_matrix

            matrix = generate_traceability_matrix(reactor, preset=preset)
            trace_path = out / "traceability_matrix.json"
            trace_path.write_text(json.dumps(matrix, indent=2), encoding="utf-8")
            manifest["files"].append(str(trace_path.name))
        except ImportError:
            manifest["traceability"] = "smrforge_pro.reporting.regulatory not available"
        except Exception as e:
            manifest["traceability"] = f"Error: {e}"

    manifest["summary"] = {
        "k_eff": point.get("k_eff"),
        "passed": report.passed,
    }

    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return manifest
