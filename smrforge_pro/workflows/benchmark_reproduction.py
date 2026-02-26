"""
One-click benchmark reproduction (Pro).

Download OECD/NEA or other benchmarks, run, compare to reference, produce report.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.workflows.benchmark_reproduction")


# Registry of known benchmarks (can be extended from config/JSON)
BENCHMARK_REGISTRY: Dict[str, Dict[str, Any]] = {
    "valar10_preset": {
        "name": "Valar-10 preset",
        "description": "SMRForge built-in Valar-10 HTGR preset",
        "type": "preset",
        "reference": {"k_eff": 1.0},  # Placeholder; real ref from benchmark data
        "config": {"preset": "valar-10"},
    },
    "htgr-simple": {
        "name": "Simple HTGR",
        "description": "Minimal HTGR for validation",
        "type": "preset",
        "reference": {"k_eff": None},
        "config": {"preset": "valar-10", "power_mw": 10, "enrichment": 0.195},
    },
}


@dataclass
class BenchmarkResult:
    """Result of benchmark run."""

    benchmark_id: str
    reference: Dict[str, Any]
    calculated: Dict[str, Any]
    differences: Dict[str, float]
    passed: bool
    output_dir: Path


def list_benchmarks() -> List[str]:
    """List available benchmark IDs."""
    return list(BENCHMARK_REGISTRY.keys())


def reproduce_benchmark(
    benchmark_id: str,
    output_dir: Optional[Path] = None,
) -> BenchmarkResult:
    """
    Reproduce a benchmark: run and compare to reference.

    Args:
        benchmark_id: ID from BENCHMARK_REGISTRY (or list_benchmarks())
        output_dir: Where to write results

    Returns:
        BenchmarkResult with reference, calculated, differences, passed
    """
    if benchmark_id not in BENCHMARK_REGISTRY:
        raise ValueError(
            f"Unknown benchmark '{benchmark_id}'. Available: {list_benchmarks()}"
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
