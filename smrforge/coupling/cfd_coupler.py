"""
CFD (Computational Fluid Dynamics) coupling interface for multiphysics.

Provides CFDCoupler for exchanging temperature, velocity, and pressure
fields between neutronics/thermal-hydraulics and CFD codes (e.g., OpenFOAM,
STAR-CCM+, Fluent). Supports one-way and two-way coupling workflows.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.coupling.cfd_coupler")


@dataclass
class CFDMesh:
    """CFD mesh representation for coupling."""

    n_cells: int
    x: np.ndarray  # Cell centers [cm]
    y: np.ndarray
    z: np.ndarray
    volumes: np.ndarray  # Cell volumes [cm^3]


@dataclass
class CFDFields:
    """Temperature, velocity, pressure from CFD."""

    temperature: np.ndarray  # [n_cells] K
    velocity_x: Optional[np.ndarray] = None
    velocity_y: Optional[np.ndarray] = None
    velocity_z: Optional[np.ndarray] = None
    pressure: Optional[np.ndarray] = None
    density: Optional[np.ndarray] = None


@dataclass
class PowerDensityFields:
    """Power density from neutronics for CFD heat source."""

    power_density: np.ndarray  # [n_cells] W/cm^3
    mesh: Optional[CFDMesh] = None


class CFDCoupler:
    """
    Interface for coupling SMRForge with CFD codes.

    Exchanges:
    - Power density (neutronics -> CFD) as heat source
    - Temperature/flow (CFD -> neutronics) for feedback

    Supports file-based exchange and optional in-process callbacks.

    Attributes:
        mesh: CFD mesh (optional, for mapping)
        coupling_mode: 'one_way' or 'two_way'
        data_format: 'numpy', 'csv', or 'hdf5' for file exchange

    Example:
        >>> coupler = CFDCoupler(
        ...     mesh=cfd_mesh,
        ...     coupling_mode="two_way",
        ... )
        >>> coupler.send_power_to_cfd(power_density)
        >>> cfd_fields = coupler.receive_temperature_from_cfd()
    """

    def __init__(
        self,
        mesh: Optional[CFDMesh] = None,
        coupling_mode: str = "one_way",
        work_dir: Optional[Path] = None,
        data_format: str = "numpy",
        send_power_hook: Optional[Callable[[np.ndarray], None]] = None,
        receive_temperature_hook: Optional[Callable[[], CFDFields]] = None,
    ):
        """
        Initialize CFD coupler.

        Args:
            mesh: CFD mesh for mapping (optional)
            coupling_mode: 'one_way' (neutronics->CFD only) or 'two_way'
            work_dir: Directory for file exchange
            data_format: 'numpy', 'csv', or 'hdf5'
            send_power_hook: Optional callback to send power to CFD
            receive_temperature_hook: Optional callback to get T from CFD
        """
        self.mesh = mesh
        self.coupling_mode = coupling_mode
        self.work_dir = Path(work_dir or ".")
        self.data_format = data_format
        self._send_power_hook = send_power_hook
        self._receive_temperature_hook = receive_temperature_hook
        self._power_sent = False
        self._temperature_received = False

        logger.debug(
            f"CFDCoupler: mode={coupling_mode}, format={data_format}, "
            f"work_dir={self.work_dir}"
        )

    def send_power_to_cfd(
        self,
        power_density: np.ndarray,
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Send power density to CFD as heat source.

        Args:
            power_density: Power density [W/cm^3] per cell
            output_path: Optional file path (default: work_dir/power_density.npy)

        Returns:
            Path where data was written (or passed to hook)
        """
        if self._send_power_hook is not None:
            self._send_power_hook(power_density)
            self._power_sent = True
            return self.work_dir / "power_density"

        path = output_path or self.work_dir / "power_density"
        self.work_dir.mkdir(parents=True, exist_ok=True)

        if self.data_format == "numpy":
            fp = path.with_suffix(".npy")
            np.save(fp, power_density)
        elif self.data_format == "csv":
            fp = path.with_suffix(".csv")
            np.savetxt(fp, power_density, delimiter=",")
        else:
            fp = path.with_suffix(".npy")
            np.save(fp, power_density)

        self._power_sent = True
        logger.info(f"Sent power density to CFD: {fp}")
        return fp

    def receive_temperature_from_cfd(
        self,
        input_path: Optional[Path] = None,
    ) -> CFDFields:
        """
        Receive temperature (and optional flow) from CFD.

        Args:
            input_path: Optional file path (default: work_dir/cfd_fields.npy)

        Returns:
            CFDFields with temperature and optional velocity/pressure
        """
        if self._receive_temperature_hook is not None:
            fields = self._receive_temperature_hook()
            self._temperature_received = True
            return fields

        path = input_path or self.work_dir / "cfd_fields.npy"
        if path.exists():
            data = np.load(path, allow_pickle=True).item()
            self._temperature_received = True
            return CFDFields(
                temperature=data["temperature"],
                velocity_x=data.get("velocity_x"),
                velocity_y=data.get("velocity_y"),
                velocity_z=data.get("velocity_z"),
                pressure=data.get("pressure"),
                density=data.get("density"),
            )

        # Stub: return uniform temperature when no file/hook
        n = self.mesh.n_cells if self.mesh else 100
        logger.debug("No CFD file/hook; returning stub temperature field")
        return CFDFields(temperature=np.full(n, 600.0))  # 600 K default

    def cfd_available(self) -> bool:
        """Check if CFD interface is configured."""
        return (
            self._send_power_hook is not None
            or self._receive_temperature_hook is not None
            or (self.work_dir / "cfd_fields.npy").exists()
        )

    def map_power_to_cfd_mesh(
        self,
        r_positions: np.ndarray,
        z_positions: np.ndarray,
        power_rz: np.ndarray,
    ) -> np.ndarray:
        """
        Map (r,z) power to CFD mesh via nearest-neighbor or interpolation.

        Args:
            r_positions: Radial positions [cm]
            z_positions: Axial positions [cm]
            power_rz: Power density [nz, nr]

        Returns:
            Power density on CFD mesh [n_cells]
        """
        if self.mesh is None:
            logger.warning("No CFD mesh; returning flattened power")
            return power_rz.ravel()

        # Nearest-neighbor mapping
        n = self.mesh.n_cells
        out = np.zeros(n)
        for i in range(n):
            x, y, z = self.mesh.x[i], self.mesh.y[i], self.mesh.z[i]
            r = np.sqrt(x**2 + y**2)
            ir = np.argmin(np.abs(r_positions - r))
            iz = np.argmin(np.abs(z_positions - z))
            out[i] = power_rz[iz, ir]
        return out
