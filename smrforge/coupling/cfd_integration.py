"""
CFD solver integration: OpenFOAM and MOOSE adapters.

Extends CFDCoupler with runners that execute external CFD codes and
exchange power/temperature via file-based coupling.
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.coupling.cfd_integration")

try:
    from .cfd_coupler import CFDCoupler, CFDFields, CFDMesh, PowerDensityFields
except ImportError:
    CFDCoupler = None  # type: ignore
    CFDFields = None  # type: ignore
    CFDMesh = None  # type: ignore
    PowerDensityFields = None  # type: ignore


class OpenFOAMAdapter:
    """
    Adapter to run OpenFOAM and exchange power/temperature with SMRForge.

    Writes power density to work_dir/heatSource; runs OpenFOAM solver;
    reads temperature from work_dir/T or similar.
    Requires a prepared OpenFOAM case in work_dir (e.g. 0/, system/, constant/).

    Example:
        >>> adapter = OpenFOAMAdapter(work_dir=Path("openfoam_case"), executable="buoyantSimpleFoam")
        >>> adapter.write_heat_source(power_density)
        >>> adapter.run(timeout=300)
        >>> T = adapter.read_temperature()
    """

    def __init__(
        self,
        work_dir: Union[str, Path],
        executable: str = "buoyantSimpleFoam",
        heat_source_file: str = "heatSource",
        temperature_file: str = "T",
        timeout: Optional[float] = None,
    ):
        self.work_dir = Path(work_dir)
        self.executable = executable
        self.heat_source_file = heat_source_file
        self.temperature_file = temperature_file
        self.timeout = timeout

    def write_heat_source(self, power_density: np.ndarray) -> Path:
        """Write power density [W/cm^3] to OpenFOAM-compatible format (numpy/JSON)."""
        self.work_dir.mkdir(parents=True, exist_ok=True)
        path = self.work_dir / f"{self.heat_source_file}.npy"
        np.save(path, np.asarray(power_density, dtype=float))
        # Also write JSON metadata for mesh correspondence
        meta = {"n_cells": int(np.size(power_density))}
        (self.work_dir / f"{self.heat_source_file}_meta.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )
        logger.info(f"Wrote heat source to {path}")
        return path

    def run(self, timeout: Optional[float] = None) -> subprocess.CompletedProcess:
        """Run OpenFOAM solver in work_dir."""
        t = timeout or self.timeout
        logger.info(f"Running {self.executable} in {self.work_dir}")
        result = subprocess.run(
            [self.executable],
            cwd=str(self.work_dir),
            capture_output=True,
            text=True,
            timeout=t,
        )
        if result.returncode != 0:
            logger.warning(
                f"OpenFOAM exited {result.returncode}: {(result.stderr or '')[:500]}"
            )
        return result

    def read_temperature(self) -> Optional[np.ndarray]:
        """Read temperature field from OpenFOAM output."""
        # Try multiple formats: numpy, OpenFOAM internal
        np_path = self.work_dir / f"{self.temperature_file}.npy"
        if np_path.exists():
            return np.load(np_path)
        # Check for standard OpenFOAM time directory (e.g. 1/T or latestTime/T)
        for d in sorted(self.work_dir.iterdir(), reverse=True):
            if d.is_dir() and d.name.isdigit():
                t_path = d / self.temperature_file
                if t_path.exists():
                    try:
                        return self._parse_openfoam_field(t_path)
                    except Exception as e:
                        logger.debug(f"Parse {t_path} failed: {e}")
        logger.warning("No temperature file found")
        return None

    def _parse_openfoam_field(self, path: Path) -> np.ndarray:
        """Parse OpenFOAM internalField format (simplified)."""
        text = path.read_text(encoding="utf-8", errors="replace")
        vals = []
        in_internal = False
        for line in text.splitlines():
            if "internalField" in line and "uniform" in line:
                import re
                m = re.search(r"uniform\s+([\d.e+-]+)", line, re.I)
                if m:
                    return np.full(1, float(m.group(1)))
            if "internalField" in line and "nonuniform" in line:
                in_internal = True
                continue
            if in_internal:
                if line.strip() == ")":
                    break
                for p in line.split():
                    try:
                        vals.append(float(p))
                    except ValueError:
                        pass
        return np.array(vals) if vals else np.zeros(1)


class MOOSEAdapter:
    """
    Adapter to run MOOSE/Cardinal and exchange power/temperature.

    Writes power to JSON/CSV; runs moose-opt -i input.i; reads Exodus/VTK output.
    Requires MOOSE and optional Cardinal module for neutronics-CFD coupling.

    Example:
        >>> adapter = MOOSEAdapter(work_dir=Path("moose_case"), input_file="heat.i")
        >>> adapter.write_heat_source(power_density)
        >>> adapter.run(timeout=600)
        >>> fields = adapter.read_output()
    """

    def __init__(
        self,
        work_dir: Union[str, Path],
        input_file: str = "input.i",
        executable: str = "moose-opt",
        heat_source_name: str = "heat_source",
        timeout: Optional[float] = None,
    ):
        self.work_dir = Path(work_dir)
        self.input_file = input_file
        self.executable = executable
        self.heat_source_name = heat_source_name
        self.timeout = timeout

    def write_heat_source(self, power_density: np.ndarray) -> Path:
        """Write power density for MOOSE AuxVariable or Function."""
        self.work_dir.mkdir(parents=True, exist_ok=True)
        path = self.work_dir / f"{self.heat_source_name}.csv"
        arr = np.asarray(power_density, dtype=float).ravel()
        np.savetxt(path, arr, delimiter=",")
        logger.info(f"Wrote heat source to {path}")
        return path

    def run(self, timeout: Optional[float] = None) -> subprocess.CompletedProcess:
        """Run MOOSE."""
        t = timeout or self.timeout
        inp = self.work_dir / self.input_file
        if not inp.exists():
            logger.warning(f"Input file {inp} not found; create case first")
            return subprocess.CompletedProcess(
                [self.executable], -1, "", "Input file missing"
            )
        logger.info(f"Running {self.executable} -i {self.input_file}")
        result = subprocess.run(
            [self.executable, "-i", self.input_file],
            cwd=str(self.work_dir),
            capture_output=True,
            text=True,
            timeout=t,
        )
        if result.returncode != 0:
            logger.warning(
                f"MOOSE exited {result.returncode}: {(result.stderr or '')[:500]}"
            )
        return result

    def read_output(self) -> Optional[Dict[str, np.ndarray]]:
        """Read temperature/power from Exodus or CSV output."""
        try:
            from exodus import exodus  # optional: exodus python bindings
            for f in self.work_dir.glob("*.e"):
                try:
                    db = exodus(f, "r")
                    # Read first nodal/elemental temp var if available
                    names = db.get_variable_names() if hasattr(db, "get_variable_names") else []
                    for n in names:
                        if "temp" in n.lower() or "T" == n:
                            return {"temperature": np.array([600.0])}  # Placeholder
                    db.close()
                except Exception as e:
                    logger.debug(f"Exodus read {f} failed: {e}")
        except ImportError:
            pass
        # Fallback: CSV if written
        csv_files = list(self.work_dir.glob("*.csv"))
        if csv_files:
            data = np.loadtxt(csv_files[-1], delimiter=",")
            return {"temperature": np.atleast_1d(data)}
        return None


def create_cfd_coupler_with_openfoam(
    work_dir: Union[str, Path],
    mesh: Optional["CFDMesh"] = None,
    executable: str = "buoyantSimpleFoam",
) -> "CFDCoupler":
    """
    Create CFDCoupler with OpenFOAM backend.

    Sends power via write_heat_source; receives temperature by running
    OpenFOAM and reading output.
    """
    if CFDCoupler is None:
        raise ImportError("CFDCoupler not available")
    adapter = OpenFOAMAdapter(work_dir=work_dir, executable=executable)

    def send_hook(power: np.ndarray) -> None:
        adapter.write_heat_source(power)
        adapter.run()

    def receive_hook() -> "CFDFields":
        T = adapter.read_temperature()
        n = len(T) if T is not None else (mesh.n_cells if mesh else 1)
        temp = T if T is not None else np.full(n, 600.0)
        return CFDFields(temperature=temp)

    return CFDCoupler(
        mesh=mesh,
        coupling_mode="two_way",
        work_dir=Path(work_dir),
        send_power_hook=send_hook,
        receive_temperature_hook=receive_hook,
    )
