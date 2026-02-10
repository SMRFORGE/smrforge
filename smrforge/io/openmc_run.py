"""
OpenMC runner and statepoint parser for SMRForge.

Runs OpenMC as a subprocess and parses statepoint HDF5 for k-eff and tally results.
Requires OpenMC to be installed and on PATH (or OPENMC_EXECUTABLE).
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..utils.logging import get_logger

logger = get_logger("smrforge.io.openmc_run")


def run_openmc(
    work_dir: Union[str, Path],
    executable: Optional[str] = None,
    timeout: Optional[float] = None,
    env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess:
    """
    Run OpenMC in the given directory.

    Args:
        work_dir: Directory containing geometry.xml, materials.xml, settings.xml
        executable: OpenMC executable path (default: 'openmc' from PATH)
        timeout: Timeout in seconds (None = no limit)
        env: Optional environment overrides (e.g. OPENMC_CROSS_SECTIONS)

    Returns:
        CompletedProcess with returncode, stdout, stderr

    Raises:
        FileNotFoundError: If executable not found
        subprocess.TimeoutExpired: If timeout exceeded
    """
    work_dir = Path(work_dir)
    if not (work_dir / "geometry.xml").exists():
        raise FileNotFoundError(f"geometry.xml not found in {work_dir}")

    cmd = executable or "openmc"
    run_env = dict(__import__("os").environ)
    if env:
        run_env.update(env)

    logger.info("Running OpenMC in %s", work_dir)
    result = subprocess.run(
        [cmd],
        cwd=str(work_dir),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=run_env,
    )

    if result.returncode != 0:
        logger.warning(
            "OpenMC exited with code %d: %s", result.returncode, result.stderr[:500]
        )

    return result


def parse_statepoint(statepoint_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Parse OpenMC statepoint HDF5 for k-eff and tallies.

    Args:
        statepoint_path: Path to statepoint.N.h5

    Returns:
        Dict with 'k_eff', 'k_eff_std', 'batches', and optionally 'tallies'.

    Raises:
        FileNotFoundError: If statepoint not found
        ImportError: If h5py not available
    """
    statepoint_path = Path(statepoint_path)
    if not statepoint_path.exists():
        raise FileNotFoundError(f"Statepoint not found: {statepoint_path}")

    try:
        import h5py
    except ImportError as e:
        raise ImportError(
            "h5py required to parse OpenMC statepoint. pip install h5py"
        ) from e

    result: Dict[str, Any] = {}

    with h5py.File(statepoint_path, "r") as f:
        if "k_combined" in f:
            k = f["k_combined"][()]
            if hasattr(k, "__len__") and len(k) >= 2:
                result["k_eff"] = float(k[0])
                result["k_eff_std"] = float(k[1])
            else:
                result["k_eff"] = float(k)

        if "k_generation" in f:
            kg = f["k_generation"][()]
            result["batches"] = int(kg.shape[0]) if hasattr(kg, "shape") else 0

        # Parse tallies if present
        if "tallies" in f:
            tallies = {}
            for key in f["tallies"].keys():
                try:
                    tid = int(key)
                    t = f["tallies"][key]
                    tallies[tid] = {
                        "mean": (
                            t["mean"][()].tolist()
                            if hasattr(t["mean"], "__iter__")
                            else float(t["mean"][()])
                        ),
                        "std_dev": (
                            t["std_dev"][()].tolist()
                            if hasattr(t["std_dev"], "__iter__")
                            else float(t["std_dev"][()])
                        ),
                    }
                except (KeyError, TypeError):
                    pass
            result["tallies"] = tallies

    return result


def run_and_parse(
    work_dir: Union[str, Path],
    executable: Optional[str] = None,
    timeout: Optional[float] = None,
    statepoint_glob: str = "statepoint.*.h5",
) -> Dict[str, Any]:
    """
    Run OpenMC and parse the latest statepoint.

    Args:
        work_dir: Directory with OpenMC input files
        executable: OpenMC executable (default: 'openmc')
        timeout: Run timeout in seconds
        statepoint_glob: Glob pattern for statepoint files

    Returns:
        Dict with 'returncode', 'stdout', 'stderr', and if successful
        'k_eff', 'k_eff_std', 'batches', 'tallies'.
    """
    work_dir = Path(work_dir)
    proc = run_openmc(work_dir, executable=executable, timeout=timeout)

    out: Dict[str, Any] = {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }

    if proc.returncode == 0:
        statepoints = sorted(work_dir.glob(statepoint_glob))
        if statepoints:
            latest = statepoints[-1]
            try:
                parsed = parse_statepoint(latest)
                out.update(parsed)
            except Exception as e:
                logger.warning("Could not parse statepoint %s: %s", latest, e)

    return out
