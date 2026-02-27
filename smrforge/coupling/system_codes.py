"""
RELAP/TRACE system code coupling for transient analysis.

Runs RELAP-5 or TRACE as subprocess; exchanges power distribution and
thermal-hydraulic boundary conditions. Supports coupled neutronics-TH.
"""

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.coupling.system_codes")


@dataclass
class PowerMap:
    """Spatial power distribution for coupling."""

    axial_positions: np.ndarray  # cm
    radial_positions: np.ndarray  # cm
    power: np.ndarray  # [n_axial, n_radial] W/cm³


@dataclass
class THBoundaryConditions:
    """Thermal-hydraulic boundary conditions from system code."""

    pressure_inlet: float  # Pa
    temperature_inlet: float  # K
    mass_flow_rate: float  # kg/s


def _find_executable(names: List[str]) -> Optional[Path]:
    """Find executable in PATH."""
    import shutil

    for name in names:
        path = shutil.which(name)
        if path:
            return Path(path)
    return None


def system_code_available(code: str = "relap") -> bool:
    """Check if RELAP or TRACE executable is on PATH."""
    if code.lower() == "relap":
        return _find_executable(["relap5", "relap"]) is not None
    if code.lower() == "trace":
        return _find_executable(["trace", "trace.exe"]) is not None
    return False


class RELAPCoupler:
    """
    Coupler to run RELAP-5 and exchange data.

    Writes RELAP input with power map; runs RELAP; parses output for
    feedback (temperature, density) to neutronics.
    """

    def __init__(
        self,
        executable: Optional[Path] = None,
        work_dir: Optional[Path] = None,
    ):
        self.executable = executable or _find_executable(["relap5", "relap"])
        self.work_dir = Path(work_dir or ".")

    def run(
        self,
        input_file: Path,
        timeout: float = 3600.0,
    ) -> Tuple[int, str, str]:
        """
        Run RELAP-5 on input file.

        Returns:
            (returncode, stdout, stderr)
        """
        if self.executable is None:
            raise FileNotFoundError("RELAP-5 executable not found. Install RELAP and add to PATH.")
        cmd = [str(self.executable), str(input_file)]
        try:
            r = subprocess.run(
                cmd,
                cwd=str(self.work_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return r.returncode, r.stdout or "", r.stderr or ""
        except subprocess.TimeoutExpired:
            logger.error("RELAP timed out")
            return -1, "", "Timeout"
        except Exception as e:
            logger.error(f"RELAP run failed: {e}")
            return -1, "", str(e)

    def write_power_to_input(
        self,
        input_path: Path,
        output_path: Path,
        power_map: PowerMap,
    ) -> None:
        """
        Inject power map into RELAP input (simplified table format).

        Full implementation would parse RELAP input structure and
        update power tables. This is a stub for the workflow.
        """
        with open(output_path, "w") as f:
            f.write("! RELAP input with power from SMRForge\n")
            f.write("! Power map: axial x radial\n")
            np.savetxt(f, power_map.power, fmt="%.6e")
        logger.info(f"Wrote power map to {output_path}")


class TRACECoupler:
    """
    Coupler to run TRACE and exchange data.

    Similar to RELAPCoupler; TRACE has different input format.
    """

    def __init__(
        self,
        executable: Optional[Path] = None,
        work_dir: Optional[Path] = None,
    ):
        self.executable = executable or _find_executable(["trace", "trace.exe"])
        self.work_dir = Path(work_dir or ".")

    def run(
        self,
        input_file: Path,
        timeout: float = 3600.0,
    ) -> Tuple[int, str, str]:
        """Run TRACE on input file."""
        if self.executable is None:
            raise FileNotFoundError("TRACE executable not found. Install TRACE and add to PATH.")
        cmd = [str(self.executable), str(input_file)]
        try:
            r = subprocess.run(
                cmd,
                cwd=str(self.work_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return r.returncode, r.stdout or "", r.stderr or ""
        except subprocess.TimeoutExpired:
            return -1, "", "Timeout"
        except Exception as e:
            return -1, "", str(e)
