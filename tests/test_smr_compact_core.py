"""
Tests for SMR compact core layouts.

Tests reduced assembly counts, compact reflectors, and SMR-specific arrangements.
"""

import pytest
import numpy as np

try:
    from smrforge.geometry.smr_compact_core import (
        CompactReflector,
        CompactSMRCore,
        create_mpower_compact_core,
        create_nuscale_compact_core,
    )
    from smrforge.geometry.core_geometry import Point3D

    _SMR_COMPACT_CORE_AVAILABLE = True
except ImportError:
    _SMR_COMPACT_CORE_AVAILABLE = False


@pytest.mark.skipif(
    not _SMR_COMPACT_CORE_AVAILABLE,
    reason="SMR compact core not available",
)
class TestCompactReflector:
    """Tests for CompactReflector class."""

    def test_reflector_creation(self):
        """Test creating compact reflector."""
        reflector = CompactReflector(
            id=1,
            position=Point3D(0, 0, 0),
            inner_radius=100.0,  # cm
            outer_radius=110.0,  # cm
            height=365.76,  # cm
            material="water",
        )

        assert reflector.id == 1
        assert reflector.inner_radius == 100.0
        assert reflector.outer_radius == 110.0
        assert reflector.thickness == 10.0
        assert reflector.material == "water"

    def test_reflector_volume(self):
        """Test reflector volume calculation."""
        reflector = CompactReflector(
            id=1,
            position=Point3D(0, 0, 0),
            inner_radius=100.0,
            outer_radius=110.0,
            height=365.76,
        )

        volume = reflector.volume()
        expected = np.pi * (110.0**2 - 100.0**2) * 365.76

        assert volume == pytest.approx(expected)

    def test_reflector_thickness_calculation(self):
        """Test automatic thickness calculation."""
        reflector = CompactReflector(
            id=1,
            position=Point3D(0, 0, 0),
            inner_radius=100.0,
            outer_radius=110.0,
            height=365.76,
            thickness=0.0,  # Should be calculated
        )

        assert reflector.thickness == 10.0


@pytest.mark.skipif(
    not _SMR_COMPACT_CORE_AVAILABLE,
    reason="SMR compact core not available",
)
class TestCompactSMRCore:
    """Tests for CompactSMRCore class."""

    def test_core_creation(self):
        """Test creating compact SMR core."""
        core = CompactSMRCore(name="Test-Compact-Core")

        assert core.name == "Test-Compact-Core"
        assert core.is_compact is True
        assert core.reflector_thickness == 10.0

    def test_build_compact_core_square(self):
        """Test building compact square core."""
        core = CompactSMRCore()

        core.build_compact_core(
            n_assemblies=37,
            assembly_pitch=21.5,
            core_shape="square",
        )

        assert len(core.assemblies) > 0
        assert core.reflector is not None
        assert core.reflector_thickness > 0

    def test_build_compact_core_circular(self):
        """Test building compact circular core."""
        core = CompactSMRCore()

        core.build_compact_core(
            n_assemblies=37,
            assembly_pitch=21.5,
            core_shape="circular",
        )

        assert len(core.assemblies) > 0
        assert core.reflector is not None

    def test_build_compact_core_hexagonal(self):
        """Test building compact hexagonal core."""
        core = CompactSMRCore()

        core.build_compact_core(
            n_assemblies=37,
            assembly_pitch=21.5,
            core_shape="hexagonal",
        )

        assert len(core.assemblies) > 0

    def test_calculate_square_arrangement(self):
        """Test square arrangement calculation."""
        core = CompactSMRCore()

        n_x, n_y = core._calculate_square_arrangement(37)
        assert n_x * n_y >= 37  # Should fit all assemblies

        n_x, n_y = core._calculate_square_arrangement(17)
        assert n_x * n_y >= 17

    def test_get_assembly_count_by_batch(self):
        """Test getting assembly count by batch."""
        core = CompactSMRCore()

        core.build_compact_core(
            n_assemblies=37,
            assembly_pitch=21.5,
        )

        # Assign some batches
        for i, assembly in enumerate(core.assemblies):
            assembly.batch = (i % 3) + 1

        batch_counts = core.get_assembly_count_by_batch()

        assert len(batch_counts) > 0
        assert sum(batch_counts.values()) == len(core.assemblies)

    def test_get_compact_core_metrics(self):
        """Test getting compact core metrics."""
        core = CompactSMRCore()

        core.build_compact_core(
            n_assemblies=37,
            assembly_pitch=21.5,
            reflector_thickness=10.0,
        )

        metrics = core.get_compact_core_metrics()

        assert "n_assemblies" in metrics
        assert "core_diameter" in metrics
        assert "reflector_thickness" in metrics
        assert "assembly_density" in metrics
        assert "compactness_ratio" in metrics

        assert metrics["n_assemblies"] == 37
        assert metrics["reflector_thickness"] == 10.0
        assert metrics["assembly_density"] > 0


@pytest.mark.skipif(
    not _SMR_COMPACT_CORE_AVAILABLE,
    reason="SMR compact core not available",
)
class TestPresetCores:
    """Tests for preset compact core functions."""

    def test_create_nuscale_compact_core(self):
        """Test creating NuScale-style compact core."""
        core = create_nuscale_compact_core()

        assert core.name == "NuScale-Compact"
        assert len(core.assemblies) == 37
        assert core.reflector is not None

    def test_create_mpower_compact_core(self):
        """Test creating mPower-style compact core."""
        core = create_mpower_compact_core()

        assert core.name == "mPower-Compact"
        assert len(core.assemblies) == 69
        assert core.reflector is not None
