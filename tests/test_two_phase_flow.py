"""
Tests for two-phase flow support.

Tests advanced two-phase flow calculations for BWR SMRs.
"""

import numpy as np
import pytest

try:
    from smrforge.geometry.core_geometry import Point3D
    from smrforge.geometry.two_phase_flow import (
        TwoPhaseFlowRegion,
        create_bwr_two_phase_region,
    )

    _TWO_PHASE_FLOW_AVAILABLE = True
except ImportError:
    _TWO_PHASE_FLOW_AVAILABLE = False


@pytest.mark.skipif(
    not _TWO_PHASE_FLOW_AVAILABLE,
    reason="Two-phase flow not available",
)
class TestTwoPhaseFlowRegion:
    """Tests for TwoPhaseFlowRegion class."""

    def test_region_creation(self):
        """Test creating two-phase flow region."""
        region = TwoPhaseFlowRegion(
            id=1,
            position=Point3D(0, 0, 0),
            flow_area=100.0,  # cm²
            height=365.76,  # cm
            pressure=7.0e6,  # Pa
            mass_flow_rate=10.0,  # kg/s
        )

        assert region.id == 1
        assert region.flow_area == 100.0
        assert region.pressure == 7.0e6

    def test_calculate_void_fraction_from_quality(self):
        """Test void fraction calculation from quality."""
        region = TwoPhaseFlowRegion(
            id=1,
            position=Point3D(0, 0, 0),
            flow_area=100.0,
            height=365.76,
            quality=0.5,  # 50% steam
        )

        void_fraction = region.calculate_void_fraction_from_quality()

        assert 0.0 <= void_fraction <= 1.0
        assert void_fraction > 0.5  # Void fraction > quality (vapor less dense)

    def test_calculate_quality_from_void_fraction(self):
        """Test quality calculation from void fraction."""
        region = TwoPhaseFlowRegion(
            id=1,
            position=Point3D(0, 0, 0),
            flow_area=100.0,
            height=365.76,
            void_fraction=0.8,  # 80% vapor by volume
        )

        quality = region.calculate_quality_from_void_fraction()

        assert 0.0 <= quality <= 1.0
        assert quality < 0.8  # Quality < void fraction (vapor less dense)

    def test_determine_flow_regime(self):
        """Test flow regime determination."""
        # Bubbly flow
        region = TwoPhaseFlowRegion(
            id=1,
            position=Point3D(0, 0, 0),
            flow_area=100.0,
            height=365.76,
            void_fraction=0.2,
        )
        assert region.determine_flow_regime() == "bubbly"

        # Slug flow
        region.void_fraction = 0.4
        assert region.determine_flow_regime() == "slug"

        # Churn flow
        region.void_fraction = 0.6
        assert region.determine_flow_regime() == "churn"

        # Annular flow
        region.void_fraction = 0.8
        assert region.determine_flow_regime() == "annular"

        # Mist flow
        region.void_fraction = 0.98
        assert region.determine_flow_regime() == "mist"

    def test_void_fraction_quality_edges(self):
        """Test void fraction at quality 0 and 1."""
        region = TwoPhaseFlowRegion(
            id=1,
            position=Point3D(0, 0, 0),
            flow_area=100.0,
            height=365.76,
            quality=0.0,
        )
        assert region.calculate_void_fraction_from_quality() == 0.0
        region.quality = 1.0
        assert region.calculate_void_fraction_from_quality() == 1.0

    def test_quality_void_fraction_edges(self):
        """Test quality at void fraction 0 and 1."""
        region = TwoPhaseFlowRegion(
            id=1,
            position=Point3D(0, 0, 0),
            flow_area=100.0,
            height=365.76,
            void_fraction=0.0,
        )
        assert region.calculate_quality_from_void_fraction() == 0.0
        region.void_fraction = 1.0
        assert region.calculate_quality_from_void_fraction() == 1.0

    def test_saturation_cache_hit(self):
        """Test that second call uses saturation cache."""
        region = TwoPhaseFlowRegion(
            id=1,
            position=Point3D(0, 0, 0),
            flow_area=100.0,
            height=365.76,
            pressure=7.0e6,
            quality=0.5,
        )
        v1 = region.calculate_void_fraction_from_quality()
        v2 = region.calculate_void_fraction_from_quality()
        assert v1 == v2
        assert 0.0 <= v1 <= 1.0

    def test_void_fraction_when_saturation_invalid(self):
        """Test void fraction returns 0 when saturation densities invalid (rho_l or rho_v <= 0)."""
        from unittest.mock import patch

        region = TwoPhaseFlowRegion(
            id=1,
            position=Point3D(0, 0, 0),
            flow_area=100.0,
            height=365.76,
            pressure=7.0e6,
            quality=0.5,
        )
        with patch.object(
            region, "_get_saturation_densities", return_value=(0.0, 36.0)
        ):
            assert region.calculate_void_fraction_from_quality() == 0.0
        with patch.object(
            region, "_get_saturation_densities", return_value=(740.0, 0.0)
        ):
            assert region.calculate_void_fraction_from_quality() == 0.0

    def test_quality_when_saturation_invalid(self):
        """Test quality returns 0 when saturation densities invalid."""
        from unittest.mock import patch

        region = TwoPhaseFlowRegion(
            id=1,
            position=Point3D(0, 0, 0),
            flow_area=100.0,
            height=365.76,
            void_fraction=0.5,
        )
        with patch.object(
            region, "_get_saturation_densities", return_value=(0.0, 36.0)
        ):
            assert region.calculate_quality_from_void_fraction() == 0.0
        with patch.object(
            region, "_get_saturation_densities", return_value=(740.0, 0.0)
        ):
            assert region.calculate_quality_from_void_fraction() == 0.0

    def test_calculate_pressure_drop(self):
        """Test pressure drop calculation."""
        region = TwoPhaseFlowRegion(
            id=1,
            position=Point3D(0, 0, 0),
            flow_area=100.0,  # cm²
            height=365.76,  # cm
            mass_flow_rate=10.0,  # kg/s
            void_fraction=0.5,
            quality=0.3,
        )

        dp = region.calculate_pressure_drop()

        assert dp > 0
        assert dp < 1e6  # Reasonable pressure drop [Pa]

    def test_update_from_heat_addition(self):
        """Test updating properties from heat addition."""
        region = TwoPhaseFlowRegion(
            id=1,
            position=Point3D(0, 0, 0),
            flow_area=100.0,
            height=365.76,
            mass_flow_rate=10.0,  # kg/s
            quality=0.0,  # Subcooled inlet
        )

        # Add heat (enough to create some quality)
        heat_added = 1e6  # W
        result = region.update_from_heat_addition(heat_added, inlet_quality=0.0)

        assert "quality" in result
        assert "void_fraction" in result
        assert "flow_regime" in result
        assert result["quality"] > 0.0


@pytest.mark.skipif(
    not _TWO_PHASE_FLOW_AVAILABLE,
    reason="Two-phase flow not available",
)
class TestPresetFunctions:
    """Tests for preset two-phase flow functions."""

    def test_create_bwr_two_phase_region(self):
        """Test creating BWR two-phase region."""
        region = create_bwr_two_phase_region(
            id=1,
            position=Point3D(0, 0, 0),
            flow_area=100.0,
            height=365.76,
            mass_flow_rate=10.0,
        )

        assert region.id == 1
        assert region.pressure == 7.0e6  # Typical BWR pressure
        assert region.mass_flow_rate == 10.0
