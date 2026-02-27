"""Tests for CFD integration (OpenFOAMAdapter, MOOSEAdapter)."""

import numpy as np
import pytest

pytest.importorskip("smrforge")


class TestOpenFOAMAdapter:
    """Tests for OpenFOAMAdapter."""

    def test_adapter_import(self):
        """OpenFOAMAdapter is importable."""
        from smrforge.coupling.cfd_integration import OpenFOAMAdapter

        assert OpenFOAMAdapter is not None

    def test_write_heat_source(self, tmp_path):
        """Write heat source creates .npy file."""
        from smrforge.coupling.cfd_integration import OpenFOAMAdapter

        adapter = OpenFOAMAdapter(work_dir=tmp_path)
        power = np.array([1.0, 2.0, 3.0])
        path = adapter.write_heat_source(power)
        assert path.exists()
        loaded = np.load(path)
        np.testing.assert_array_almost_equal(loaded, power)

    def test_read_temperature_no_file(self, tmp_path):
        """read_temperature returns None when no output file."""
        from smrforge.coupling.cfd_integration import OpenFOAMAdapter

        adapter = OpenFOAMAdapter(work_dir=tmp_path)
        assert adapter.read_temperature() is None


class TestMOOSEAdapter:
    """Tests for MOOSEAdapter."""

    def test_adapter_import(self):
        """MOOSEAdapter is importable."""
        from smrforge.coupling.cfd_integration import MOOSEAdapter

        assert MOOSEAdapter is not None

    def test_write_heat_source(self, tmp_path):
        """Write heat source creates CSV file."""
        from smrforge.coupling.cfd_integration import MOOSEAdapter

        adapter = MOOSEAdapter(work_dir=tmp_path)
        power = np.array([1.0, 2.0])
        path = adapter.write_heat_source(power)
        assert path.exists()
        data = np.loadtxt(path, delimiter=",")
        assert len(data) == 2
