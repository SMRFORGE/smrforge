"""
MCNP runner and result parser for SMRForge.

Runs MCNP as a subprocess and parses output for k-eff and related results.
Enables round-trip analysis: export (Pro) -> run MCNP -> parse results -> use in SMRForge.

Requires MCNP to be installed and on PATH (or MCNP_EXECUTABLE).
"""

import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..utils.logging import get_logger

logger = get_logger("smrforge.io.mcnp_run")

# MCNP k-eff pattern: "colony result" or "best estimate" k-eff
_KEFF_PATTERNS = [
    re.compile(r"collision\s+estimator\s+.*?k\s*eff\s*=\s*([\d.]+)\s+\(?\s*([\d.]+)\s*\)?", re.I | re.S),
    re.compile(r"best\s+estimate.*?([\d.]+)\s+\(?\s*([\d.]+)\s*\)?", re.I | re.S),
    re.compile(r"keff\s*=\s*([\d.]+)\s+([\d.]+)", re.I),
]


def run_mcnp(
    work_dir: Union[str, Path],
    input_file: Union[str, Path],
    executable: Optional[str] = None,
    timeout: Optional[float] = None,
    env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess:
    """
    Run MCNP in the given directory.

    Args:
        work_dir: Directory containing the input file
        input_file: MCNP input file (e.g. model.inp, model.mcnp)
        executable: MCNP executable (default: 'mcnp6' or 'mcnp' from PATH)
        timeout: Timeout in seconds (None = no limit)
        env: Optional environment overrides

    Returns:
        CompletedProcess with returncode, stdout, stderr
    """
    work_dir = Path(work_dir)
    input_path = (
        work_dir / input_file
        if not Path(input_file).is_absolute()
        else Path(input_file)
    )
    if not input_path.exists():
        raise FileNotFoundError(f"MCNP input file not found: {input_path}")

    cmd = executable or "mcnp6"
    run_env = dict(__import__("os").environ)
    if env:
        run_env.update(env)

    # MCNP typically: mcnp6 i=model.inp
    logger.info("Running MCNP in %s: %s", work_dir, input_path.name)
    result = subprocess.run(
        [cmd, "i=" + input_path.name],
        cwd=str(work_dir),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=run_env,
    )

    if result.returncode != 0:
        logger.warning(
            "MCNP exited with code %d: %s",
            result.returncode,
            (result.stderr or "")[:500],
        )

    return result


def parse_mcnp_output(output_text: str) -> Dict[str, Any]:
    """
    Parse MCNP stdout/stderr for k-eff and uncertainty.

    MCNP output format varies; this looks for common patterns.

    Args:
        output_text: Combined stdout + stderr from MCNP run

    Returns:
        Dict with 'k_eff', 'k_eff_std' if found
    """
    result: Dict[str, Any] = {}
    text = output_text or ""

    # Look for "best estimate" block
    best_match = re.search(
        r"best\s+estimate\s+of\s+the\s+combined\s+(\w+)\s+and\s+(\w+).*?([\d.]+)\s+\(?\s*([\d.]+)\s*\)?",
        text,
        re.I | re.DOTALL,
    )
    if best_match:
        try:
            result["k_eff"] = float(best_match.group(3))
            result["k_eff_std"] = float(best_match.group(4))
            return result
        except (ValueError, IndexError):
            pass

    # Simpler: keff = value (uncertainty)
    for pat in _KEFF_PATTERNS:
        m = pat.search(text)
        if m:
            try:
                result["k_eff"] = float(m.group(1))
                if len(m.groups()) >= 2:
                    result["k_eff_std"] = float(m.group(2))
                return result
            except (ValueError, IndexError):
                continue

    return result


def run_and_parse(
    work_dir: Union[str, Path],
    input_file: Union[str, Path],
    executable: Optional[str] = None,
    timeout: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Run MCNP and parse output for k-eff.

    Args:
        work_dir: Directory with MCNP input
        input_file: Input file name (e.g. model.inp)
        executable: MCNP executable (default: mcnp6)
        timeout: Run timeout in seconds

    Returns:
        Dict with 'returncode', 'stdout', 'stderr', and if successful
        'k_eff', 'k_eff_std'
    """
    work_dir = Path(work_dir)
    proc = run_mcnp(work_dir, input_file, executable=executable, timeout=timeout)

    out: Dict[str, Any] = {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }

    if proc.returncode == 0 or proc.stdout:
        parsed = parse_mcnp_output((proc.stdout or "") + (proc.stderr or ""))
        out.update(parsed)

    return out
