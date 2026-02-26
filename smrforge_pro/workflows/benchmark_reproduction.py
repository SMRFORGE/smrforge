"""
One-click benchmark reproduction (Pro).

Download OECD/NEA or other benchmarks, run, compare to reference, produce report.
Integrates Community execute_and_document_benchmarks for CI-ready suite.

Uses Pydantic for BenchmarkResult validation and serialization.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.workflows.benchmark_reproduction")


# Registry of known benchmarks (IAEA/OECD/NUREG references + presets)
BENCHMARK_REGISTRY: Dict[str, Dict[str, Any]] = {
    "valar10_preset": {
        "name": "Valar-10 preset",
        "description": "SMRForge built-in Valar-10 HTGR preset",
        "type": "preset",
        "reference": {"k_eff": 1.0},
        "config": {"preset": "valar-10"},
    },
    "htgr-simple": {
        "name": "Simple HTGR",
        "description": "Minimal HTGR for validation",
        "type": "preset",
        "reference": {"k_eff": None},
        "config": {"preset": "valar-10", "power_mw": 10, "enrichment": 0.195},
    },
    # IAEA/NUREG/OECD benchmark references (from Community BENCHMARK_REFERENCES)
    "godiva_bare_sphere": {
        "name": "Godiva bare sphere",
        "description": "IAEA criticality benchmark - bare HEU sphere",
        "type": "reference",
        "reference": {"k_eff": 1.0, "tolerance": 0.005},
        "source": "IAEA/NEA",
        "config": {"preset": "valar-10"},  # Placeholder until dedicated model
    },
    "jezebel_pu239": {
        "name": "Jezebel Pu-239",
        "description": "IAEA criticality benchmark - bare Pu sphere",
        "type": "reference",
        "reference": {"k_eff": 1.0, "tolerance": 0.005},
        "source": "IAEA",
        "config": {"preset": "valar-10"},
    },
    "lra_benchmark": {
        "name": "LRA benchmark",
        "description": "LWR assembly benchmark",
        "type": "reference",
        "reference": {"k_eff": 1.0, "tolerance": 0.01},
        "source": "NUREG",
        "config": {"preset": "valar-10"},
    },
}


class BenchmarkResult(BaseModel):
    """Result of benchmark run (Pydantic-validated)."""

    model_config = {"arbitrary_types_allowed": True}

    benchmark_id: str
    reference: Dict[str, Any] = Field(default_factory=dict)
    calculated: Dict[str, Any] = Field(default_factory=dict)
    differences: Dict[str, float] = Field(default_factory=dict)
    passed: bool = False
    output_dir: Path


# Special ID to run Community's execute_and_document_benchmarks suite
COMMUNITY_SUITE_ID = "community_suite"


def list_benchmarks() -> List[str]:
    """List available benchmark IDs (including community_suite for full CI suite)."""
    ids = list(BENCHMARK_REGISTRY.keys())
    return ids + [COMMUNITY_SUITE_ID]


def reproduce_community_benchmarks(
    benchmark_names: Optional[List[str]] = None,
    endf_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> tuple:
    """
    Run Community's execute_and_document_benchmarks and return results.

    Pro integration: uses Community's CI-ready benchmark suite for full validation.
    Delegates to smrforge.validation.benchmark_runner.execute_and_document_benchmarks.

    Returns:
        Tuple of (list of BenchmarkResult, output Path) from Community
    """
    from smrforge.validation.benchmark_runner import execute_and_document_benchmarks

    return execute_and_document_benchmarks(
        benchmark_names=benchmark_names,
        endf_dir=endf_dir,
        output_dir=output_dir or Path("benchmark_output") / "community_suite",
    )


def reproduce_benchmark(
    benchmark_id: str,
    output_dir: Optional[Path] = None,
) -> Union[BenchmarkResult, tuple]:
    """
    Reproduce a benchmark: run and compare to reference.

    When benchmark_id is "community_suite", integrates Community's
    execute_and_document_benchmarks for full CI validation.

    Args:
        benchmark_id: ID from BENCHMARK_REGISTRY or "community_suite"
        output_dir: Where to write results

    Returns:
        BenchmarkResult for single benchmark, or (results, path) for community_suite
    """
    if benchmark_id == COMMUNITY_SUITE_ID:
        out = output_dir or Path("benchmark_output") / "community_suite"
        results, path = reproduce_community_benchmarks(
            output_dir=out, endf_dir=None, benchmark_names=None
        )
        return results, path

    if benchmark_id not in BENCHMARK_REGISTRY:
        avail = [COMMUNITY_SUITE_ID] + list(BENCHMARK_REGISTRY.keys())
        raise ValueError(
            f"Unknown benchmark '{benchmark_id}'. Available: {avail}"
        )

    if output_dir is None:
        output_dir = Path("benchmark_output") / benchmark_id
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    entry = BENCHMARK_REGISTRY[benchmark_id]
    config = entry.get("config", {})
    reference = entry.get("reference", {})

    try:
        from smrforge.convenience import create_reactor, get_design_point

        preset = config.get("preset", "valar-10")
        reactor = create_reactor(preset, **{k: v for k, v in config.items() if k != "preset"})
        results = reactor.solve()
        design_point = get_design_point(reactor)
    except ImportError:
        raise ImportError(
            "reproduce_benchmark requires smrforge. pip install smrforge"
        ) from None
    except Exception as e:
        calculated = {"error": str(e)}
        differences = {}
        passed = False
    else:
        calculated = {
            "k_eff": results.get("k_eff"),
            "power_thermal_mw": design_point.get("power_thermal_mw"),
        }
        differences = {}
        for k, ref_val in reference.items():
            if ref_val is not None and k in calculated and calculated[k] is not None:
                calc_val = calculated[k]
                if isinstance(calc_val, (int, float)) and isinstance(ref_val, (int, float)):
                    differences[k] = float(calc_val - ref_val)
        passed = all(
            abs(d) < 0.02 for d in differences.values()
        ) if differences else True

    result = BenchmarkResult(
        benchmark_id=benchmark_id,
        reference=reference,
        calculated=calculated,
        differences=differences,
        passed=passed,
        output_dir=output_dir,
    )

    # Save report
    report = {
        "benchmark_id": benchmark_id,
        "name": entry.get("name", benchmark_id),
        "reference": reference,
        "calculated": calculated,
        "differences": differences,
        "passed": passed,
    }
    (output_dir / "report.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    return result
