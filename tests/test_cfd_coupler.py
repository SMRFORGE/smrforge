"""Tests for CFD coupler interface."""

import numpy as np
import pytest

from smrforge.coupling.cfd_coupler import (
    CFDCoupler,
    CFDFields,
    CFDMesh,
    PowerDensityFields,
)


class TestCFDCoupler:
    """Tests for CFDCoupler."""

    def test_coupler_init(self, tmp_path):
        """Test CFDCoupler initialization."""
        coupler = CFDCoupler(work_dir=tmp_path)
        assert coupler.work_dir == tmp_path

    def test_send_power_to_cfd(self, tmp_path):
        """Test sending power to CFD."""
        coupler = CFDCoupler(work_dir=tmp_path)
        power = np.ones(100) * 1e6
        path = coupler.send_power_to_cfd(power)
        assert path.exists() or path.with_suffix(".npy").exists()

    def test_receive_temperature_stub(self, tmp_path):
        """Test receiving temperature (stub when no file)."""
        coupler = CFDCoupler(work_dir=tmp_path)
        fields = coupler.receive_temperature_from_cfd()
        assert isinstance(fields, CFDFields)
        assert fields.temperature.size > 0

    def test_cfd_mesh(self):
        """Test CFDMesh dataclass."""
        mesh = CFDMesh(
            n_cells=10,
            x=np.zeros(10),
            y=np.zeros(10),
            z=np.linspace(0, 100, 10),
            volumes=np.ones(10) * 100,
        )
        assert mesh.n_cells == 10
