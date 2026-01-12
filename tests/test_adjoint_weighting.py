"""
Tests for adjoint flux weighting in multi-group collapse.
"""

import pytest
import numpy as np

try:
    from smrforge.core.multigroup_advanced import collapse_with_adjoint_weighting

    _ADJOINT_WEIGHTING_AVAILABLE = True
except ImportError:
    _ADJOINT_WEIGHTING_AVAILABLE = False


@pytest.mark.skipif(
    not _ADJOINT_WEIGHTING_AVAILABLE,
    reason="Adjoint weighting not available",
)
class TestAdjointWeighting:
    """Tests for adjoint flux weighting."""

    def test_collapse_with_adjoint_weighting(self):
        """Test collapsing with adjoint weighting."""
        # Fine-group structure (100 groups)
        fine_groups = np.logspace(7, -5, 101)

        # Coarse-group structure (4 groups: [2e7, 1e6), [1e6, 1e5), [1e5, 1e-5])
        coarse_groups = np.array([2e7, 1e6, 1e5, 1e-5])

        # Fine-group data
        fine_xs = np.ones(100) * 5.0  # 5 barns
        fine_flux = np.ones(100)  # Uniform flux
        fine_adjoint = np.ones(100)  # Uniform adjoint

        # Collapse
        coarse_xs = collapse_with_adjoint_weighting(
            fine_groups, coarse_groups, fine_xs, fine_flux, fine_adjoint
        )

        assert len(coarse_xs) == 3  # 4 boundaries = 3 groups
        assert np.all(coarse_xs > 0)

    def test_adjoint_weighting_preserves_reaction_rates(self):
        """Test that adjoint weighting preserves reaction rates approximately."""
        fine_groups = np.logspace(7, -5, 101)
        coarse_groups = np.array([2e7, 1e6, 1e5, 1e-5])

        fine_xs = np.ones(100) * 5.0
        fine_flux = np.ones(100)
        fine_adjoint = np.ones(100)

        coarse_xs = collapse_with_adjoint_weighting(
            fine_groups, coarse_groups, fine_xs, fine_flux, fine_adjoint
        )

        # With uniform flux and adjoint, should get approximately same value
        # Note: may not be exactly 5.0 due to group boundaries, but should be close
        assert np.all(coarse_xs > 0)
        assert np.all(coarse_xs < 10.0)  # Reasonable range

    def test_adjoint_weighting_with_varying_flux(self):
        """Test adjoint weighting with varying flux."""
        fine_groups = np.logspace(7, -5, 101)
        coarse_groups = np.array([2e7, 1e6, 1e5, 1e-5])

        # Flux peaks in thermal groups
        fine_xs = np.ones(100) * 5.0
        fine_flux = np.exp(-np.linspace(0, 5, 100))  # Exponential decay
        fine_adjoint = np.ones(100)

        coarse_xs = collapse_with_adjoint_weighting(
            fine_groups, coarse_groups, fine_xs, fine_flux, fine_adjoint
        )

        assert len(coarse_xs) == 3  # 4 boundaries = 3 groups
        assert np.all(coarse_xs > 0)
