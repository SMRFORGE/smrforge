"""
Tests for DAGMC/CAD geometry import.
"""

from pathlib import Path
from unittest.mock import patch

import pytest


class TestDAGMCImport:
    """Tests for dagmc_import module."""

    def test_dagmc_available_returns_bool(self):
        """dagmc_available returns a boolean."""
        from smrforge.geometry.dagmc_import import dagmc_available

        result = dagmc_available()
        assert isinstance(result, bool)

    def test_import_dagmc_returns_none_when_unavailable(self):
        """import_dagmc_geometry returns None when DAGMC not available."""
        from smrforge.geometry.dagmc_import import import_dagmc_geometry

        with patch("smrforge.geometry.dagmc_import.dagmc_available", return_value=False):
            result = import_dagmc_geometry(Path("/nonexistent/file.h5m"))
            assert result is None

    def test_import_dagmc_returns_none_for_missing_file(self):
        """import_dagmc_geometry returns None when file does not exist."""
        from smrforge.geometry.dagmc_import import import_dagmc_geometry

        with patch("smrforge.geometry.dagmc_import.dagmc_available", return_value=True):
            result = import_dagmc_geometry(Path("/nonexistent/dagmc.h5m"))
            assert result is None

    def test_import_dagmc_with_mock_bbox(self, tmp_path):
        """import_dagmc_geometry returns PrismaticCore when bbox extracted."""
        from smrforge.geometry.dagmc_import import import_dagmc_geometry

        h5m = tmp_path / "test.h5m"
        h5m.write_bytes(b"dummy")
        with patch("smrforge.geometry.dagmc_import.dagmc_available", return_value=True):
            with patch(
                "smrforge.geometry.dagmc_import._get_bbox_from_h5m",
                return_value=((0, 0, 0), (10, 10, 100)),
            ):
                result = import_dagmc_geometry(h5m, n_radial=4, n_axial=4)
        assert result is not None
        assert hasattr(result, "core_height")
        assert hasattr(result, "core_diameter")
        assert result.core_height == 100
        # Bbox (0,0,0)-(10,10,100): r_max = sqrt(10^2+10^2) = sqrt(200)
        assert abs(result.core_diameter - 2 * (200**0.5)) < 0.1

    def test_import_dagmc_fallback_when_bbox_fails(self, tmp_path):
        """import_dagmc_geometry uses placeholder when bbox extraction fails."""
        from smrforge.geometry.dagmc_import import import_dagmc_geometry

        h5m = tmp_path / "test.h5m"
        h5m.write_bytes(b"dummy")
        with patch("smrforge.geometry.dagmc_import.dagmc_available", return_value=True):
            with patch(
                "smrforge.geometry.dagmc_import._get_bbox_from_h5m",
                return_value=None,
            ):
                result = import_dagmc_geometry(h5m)
        assert result is not None
        assert result.core_height == 100.0
        assert result.core_diameter == 50.0

    def test_voxelize_nonexistent_returns_none(self):
        """voxelize_h5m_to_mesh returns None for nonexistent file."""
        from smrforge.geometry.dagmc_import import voxelize_h5m_to_mesh

        result = voxelize_h5m_to_mesh(Path("/nonexistent/file.h5m"))
        assert result is None

    def test_voxelize_with_mock_bbox(self, tmp_path):
        """voxelize_h5m_to_mesh returns tuple when bbox available."""
        from smrforge.geometry.dagmc_import import voxelize_h5m_to_mesh

        h5m = tmp_path / "test.h5m"
        h5m.write_bytes(b"dummy")
        with patch(
            "smrforge.geometry.dagmc_import._get_bbox_from_h5m",
            return_value=((0, 0, 0), (10, 10, 100)),
        ):
            result = voxelize_h5m_to_mesh(h5m, nx=5, ny=5, nz=10)
        assert result is not None
        xc, yc, zc, mat = result
        assert len(xc) == 5
        assert len(yc) == 5
        assert len(zc) == 10
        assert mat.shape == (5, 5, 10)
