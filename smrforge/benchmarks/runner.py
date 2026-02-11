"""
Community benchmark runner.

Runs built-in benchmark cases and compares results to reference values.
For extended benchmark suite and automated reports, use SMRForge Pro.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge.benchmarks.runner")

# Default path to community benchmarks (relative to package root or repo root)
_DEFAULT_BENCHMARKS_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "benchmarks"
    / "community_benchmarks.json"
)


def _load_benchmarks(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load community benchmark definitions from JSON."""
    p = path or _DEFAULT_BENCHMARKS_PATH
    if not p.exists():
        raise FileNotFoundError(f"Community benchmarks file not found: {p}")
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _run_case(
    case_id: str, case_def: Dict[str, Any]
) -> Tuple[bool, float, Optional[str]]:
    """
    Run a single benchmark case and return (passed, calculated_value, error_message).

    Returns (True, value, None) on pass, (False, value, error_msg) on fail.
    """
    import smrforge as smr

    call = case_def.get("call")
    kwargs = case_def.get("kwargs", {})
    expected_key = case_def.get("expected_key", "k_eff")
    ref = case_def.get("reference_value", 0.0)
    tol_rel = case_def.get("tolerance_rel", 0.10)

    try:
        if call == "quick_keff":
            result = smr.quick_keff(**kwargs)
            value = float(result)
        elif call == "quick_keff_calculation":
            k_eff, _ = smr.quick_keff_calculation(**kwargs)
            value = float(k_eff)
        elif call == "analyze_preset":
            results = smr.analyze_preset(**kwargs)
            value = float(results.get(expected_key, 0.0))
        else:
            return False, 0.0, f"Unknown call: {call}"

        if ref == 0:
            passed = True  # No reference to compare
        else:
            err_rel = abs(value - ref) / abs(ref) if ref else 0
            passed = err_rel <= tol_rel
            if not passed:
                return (
                    False,
                    value,
                    f"Outside tolerance: |{value:.6f} - {ref}| / {ref} = {err_rel:.4f} > {tol_rel}",
                )
        return passed, value, None
    except Exception as e:
        logger.exception("Benchmark %s failed", case_id)
        return False, 0.0, str(e)


class CommunityBenchmarkRunner:
    """
    Run Community benchmark cases and compare to reference values.

    Example:
        >>> from smrforge.benchmarks import CommunityBenchmarkRunner
        >>> runner = CommunityBenchmarkRunner()
        >>> results = runner.run_all()
        >>> for name, (passed, value, msg) in results.items():
        ...     print(f"{name}: {'PASS' if passed else 'FAIL'} k_eff={value:.6f}")
    """

    def __init__(self, benchmarks_path: Optional[Path] = None):
        """
        Args:
            benchmarks_path: Path to community_benchmarks.json. Uses default if None.
        """
        self.benchmarks_path = benchmarks_path or _DEFAULT_BENCHMARKS_PATH
        self._data: Optional[Dict[str, Any]] = None

    def _get_data(self) -> Dict[str, Any]:
        if self._data is None:
            self._data = _load_benchmarks(self.benchmarks_path)
        return self._data

    def list_cases(self) -> List[str]:
        """List available benchmark case IDs."""
        data = self._get_data()
        nb = data.get("neutronics_benchmarks", {})
        return [
            cid for cid, cdef in nb.items() if isinstance(cdef, dict) and "call" in cdef
        ]

    def run_all(
        self, case_ids: Optional[List[str]] = None
    ) -> Dict[str, Tuple[bool, float, Optional[str]]]:
        """
        Run benchmark cases and return results.

        Args:
            case_ids: Specific case IDs to run. If None, run all.

        Returns:
            Dict mapping case_id -> (passed, calculated_value, error_message_or_None)
        """
        data = self._get_data()
        nb = data.get("neutronics_benchmarks", {})
        if not nb:
            return {}

        results: Dict[str, Tuple[bool, float, Optional[str]]] = {}
        for cid, case_def in nb.items():
            if case_ids and cid not in case_ids:
                continue
            if not isinstance(case_def, dict) or "call" not in case_def:
                continue
            passed, value, err = _run_case(cid, case_def)
            results[cid] = (passed, value, err)
        return results

    def generate_report(
        self,
        results: Optional[Dict[str, Tuple[bool, float, Optional[str]]]] = None,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Generate a Markdown report of benchmark results.

        Args:
            results: From run_all(). If None, run_all() is called.
            output_path: If set, write report to file.

        Returns:
            Report text as string.
        """
        if results is None:
            results = self.run_all()

        lines = [
            "# SMRForge Community Benchmark Report",
            "",
            "| Case | Status | Calculated | Notes |",
            "|------|--------|------------|-------|",
        ]
        passed_count = 0
        for cid, (passed, value, err) in results.items():
            status = "PASS" if passed else "FAIL"
            notes = err or ""
            if passed:
                passed_count += 1
            lines.append(f"| {cid} | {status} | {value:.6f} | {notes} |")
        lines.extend(["", f"**Summary:** {passed_count}/{len(results)} passed", ""])

        report = "\n".join(lines)
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report, encoding="utf-8")
        return report
