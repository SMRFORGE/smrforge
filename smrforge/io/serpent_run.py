"""
Serpent runner and result parser for SMRForge.

Runs Serpent 2 as a subprocess and parses _res.m output for k-eff and related results.
Enables round-trip analysis: export (Pro) -> run Serpent -> parse results -> use in SMRForge.

Requires Serpent 2 to be installed and on PATH (or SERPENT_EXECUTABLE).
"""

import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..utils.logging import get_logger

logger = get_logger("smrforge.io.serpent_run")

# Serpent result variable names for k-eff (prefer IMP_KEFF as implicit estimator)
_KEFF_VARS = ["IMP_KEFF", "ANA_KEFF", "ABS_KEFF", "COL_KEFF"]


def run_serpent(
    work_dir: Union[str, Path],
    input_file: Union[str, Path],
    executable: Optional[str] = None,
    timeout: Optional[float] = None,
    env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess:
    """
    Run Serpent 2 in the given directory.

    Args:
        work_dir: Directory containing the input file
        input_file: Serpent input file (e.g. model.sss, model.serp)
        executable: Serpent executable (default: 'sss2' from PATH)
        timeout: Timeout in seconds (None = no limit)
        env: Optional environment overrides

    Returns:
        CompletedProcess with returncode, stdout, stderr

    Raises:
        FileNotFoundError: If input file or executable not found
        subprocess.TimeoutExpired: If timeout exceeded
    """
    work_dir = Path(work_dir)
    input_path = work_dir / input_file if not Path(input_file).is_absolute() else Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Serpent input file not found: {input_path}")

    cmd = executable or "sss2"
    run_env = dict(__import__("os").environ)
    if env:
        run_env.update(env)

    logger.info("Running Serpent in %s: %s", work_dir, input_path.name)
    result = subprocess.run(
        [cmd, str(input_path.name)],
        cwd=str(work_dir),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=run_env,
    )

    if result.returncode != 0:
        logger.warning(
            "Serpent exited with code %d: %s",
            result.returncode,
            (result.stderr or "")[:500],
        )

    return result


def _parse_res_array(line: str) -> Optional[List[float]]:
    """Extract numeric array from line like 'VAR (idx, [1:2]) = [ 1.04 0.001 ];'"""
    match = re.search(r"=\s*\[\s*([\d.Ee+\-\s]+)\s*\]", line)
    if not match:
        return None
    parts = match.group(1).split()
    values: List[float] = []
    for p in parts:
        try:
            values.append(float(p))
        except ValueError:
            pass
    return values if values else None


def parse_res_file(res_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Parse Serpent _res.m file for k-eff and related results.

    Args:
        res_path: Path to [input]_res.m

    Returns:
        Dict with 'k_eff', 'k_eff_std', and optionally 'cycles', 'burnup', etc.

    Raises:
        FileNotFoundError: If res file not found
    """
    res_path = Path(res_path)
    if not res_path.exists():
        raise FileNotFoundError(f"Serpent result file not found: {res_path}")

    result: Dict[str, Any] = {}

    with open(res_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line_stripped = line.strip()
            for var in _KEFF_VARS:
                if line_stripped.startswith(f"{var} "):
                    values = _parse_res_array(line_stripped)
                    if values and len(values) >= 1:
                        result["k_eff"] = float(values[0])
                        if len(values) >= 2:
                            # Second value is relative statistical error
                            rel_err = float(values[1])
                            result["k_eff_std"] = result["k_eff"] * rel_err
                        result["k_eff_source"] = var
                        break
            if "k_eff" in result:
                break

            # Optionally capture cycles
            if line_stripped.startswith("CYCLES ") and "cycles" not in result:
                values = _parse_res_array(line_stripped)
                if values:
                    result["cycles"] = int(values[0])

    return result


def run_and_parse(
    work_dir: Union[str, Path],
    input_file: Union[str, Path],
    executable: Optional[str] = None,
    timeout: Optional[float] = None,
    res_glob: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run Serpent and parse the _res.m result file.

    Args:
        work_dir: Directory with Serpent input
        input_file: Input file name (e.g. model.sss)
        executable: Serpent executable (default: 'sss2')
        timeout: Run timeout in seconds
        res_glob: Glob for result file (default: [input_base]_res.m)

    Returns:
        Dict with 'returncode', 'stdout', 'stderr', and if successful
        'k_eff', 'k_eff_std', 'cycles', etc.
    """
    work_dir = Path(work_dir)
    input_path = Path(input_file)
    base = input_path.stem
    proc = run_serpent(
        work_dir, input_file, executable=executable, timeout=timeout
    )

    out: Dict[str, Any] = {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }

    if proc.returncode == 0:
        pattern = res_glob or f"{base}_res.m"
        res_files = sorted(work_dir.glob(pattern))
        if res_files:
            latest = res_files[-1]
            try:
                parsed = parse_res_file(latest)
                out.update(parsed)
            except Exception as e:
                logger.warning("Could not parse Serpent result %s: %s", latest, e)

    return out
