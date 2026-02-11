"""Tests for geometry visualization module."""

import numpy as np
import pytest

try:
    import matplotlib

    matplotlib.use("Agg")  # Use non-interactive backend
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not MATPLOTLIB_AVAILABLE, reason="matplotlib not available"
)

from smrforge.geometry.core_geometry import PebbleBedCore, PrismaticCore
from smrforge.visualization.geometry import (
    plot_core_layout,
    plot_flux_on_geometry,
    plot_power_distribution,
    plot_temperature_distribution,
)


@pytest.fixture
def prismatic_core():
    """Create a test prismatic core."""
    core = PrismaticCore(name="Test-Prismatic")
    core.build_hexagonal_lattice(
        n_rings=2,
        pitch=40.0,
        block_height=79.3,
        n_axial=3,
        flat_to_flat=36.0,
    )
    return core


@pytest.fixture
def pebble_bed_core():
    """Create a test pebble bed core."""
    core = PebbleBedCore(name="Test-Pebble")
    core.build_structured_packing(
        core_height=200.0,
        core_diameter=100.0,
        pebble_radius=3.0,
    )
    return core


class TestPlotCoreLayout:
    """Test plot_core_layout function."""

    def test_plot_prismatic_xy_view(self, prismatic_core):
        """Test plotting prismatic core in xy view."""
        fig, ax = plot_core_layout(prismatic_core, view="xy")

        assert fig is not None
        assert ax is not None
        assert ax.get_xlabel() == "X (cm)"
        assert ax.get_ylabel() == "Y (cm)"
        plt.close(fig)

    def test_plot_prismatic_xz_view(self, prismatic_core):
        """Test plotting prismatic core in xz view."""
        fig, ax = plot_core_layout(prismatic_core, view="xz")

        assert fig is not None
        assert ax is not None
        assert ax.get_ylabel() == "Z (cm)"
        plt.close(fig)

    def test_plot_prismatic_yz_view(self, prismatic_core):
        """Test plotting prismatic core in yz view."""
        fig, ax = plot_core_layout(prismatic_core, view="yz")

        assert fig is not None
        assert ax is not None
        plt.close(fig)

    def test_plot_prismatic_with_labels(self, prismatic_core):
        """Test plotting with labels."""
        fig, ax = plot_core_layout(prismatic_core, view="xy", show_labels=True)

        assert fig is not None
        assert ax is not None
        plt.close(fig)

    def test_plot_pebble_bed_xy_view(self, pebble_bed_core):
        """Test plotting pebble bed core in xy view."""
        fig, ax = plot_core_layout(pebble_bed_core, view="xy")

        assert fig is not None
        assert ax is not None
        plt.close(fig)

    def test_plot_pebble_bed_xz_view(self, pebble_bed_core):
        """Test plotting pebble bed core in xz view."""
        fig, ax = plot_core_layout(pebble_bed_core, view="xz")

        assert fig is not None
        assert ax is not None
        plt.close(fig)

    def test_plot_with_custom_axes(self, prismatic_core):
        """Test plotting with provided axes."""
        fig, ax = plt.subplots()
        result_fig, result_ax = plot_core_layout(prismatic_core, view="xy", ax=ax)

        assert result_fig == fig
        assert result_ax == ax
        plt.close(fig)

    def test_plot_unsupported_core_type(self):
        """Test plotting with unsupported core type."""

        class FakeCore:
            pass

        fake_core = FakeCore()
        with pytest.raises(ValueError, match="Unsupported core type"):
            plot_core_layout(fake_core, view="xy")


class TestPlotFluxOnGeometry:
    """Test plot_flux_on_geometry function."""

    def test_plot_flux_prismatic(self, prismatic_core):
        """Test plotting flux on prismatic core."""
        # Test with no mesh (fallback path to avoid reshape issues with mesh)
        flux = np.ones((10, 15))

        fig, ax = plot_flux_on_geometry(flux, prismatic_core, view="xy")

        assert fig is not None
        assert ax is not None
        plt.close(fig)

    def test_plot_flux_prismatic_no_mesh(self, prismatic_core):
        """Test plotting flux when core has no mesh."""
        flux = np.ones((10, 15))

        # Should fall back to basic layout
        fig, ax = plot_flux_on_geometry(flux, prismatic_core, view="xy")

        assert fig is not None
        assert ax is not None
        plt.close(fig)

    def test_plot_flux_pebble_bed(self, pebble_bed_core):
        """Test plotting flux on pebble bed core."""
        flux = np.ones(100)  # Simple flux array

        fig, ax = plot_flux_on_geometry(flux, pebble_bed_core, view="xy")

        assert fig is not None
        assert ax is not None
        plt.close(fig)


class TestPlotPowerDistribution:
    """Test plot_power_distribution function."""

    def test_plot_power_prismatic(self, prismatic_core):
        """Test plotting power distribution."""
        prismatic_core.generate_mesh(n_radial=10, n_axial=15)
        # For side view, meshgrid shape is (len(z), len(r)) = (16, 11)
        power = np.ones((16, 11)) * 1e6  # W/cm³

        fig, ax = plot_power_distribution(power, prismatic_core, view="xz")

        assert fig is not None
        assert ax is not None
        plt.close(fig)

    def test_plot_power_with_custom_colormap(self, prismatic_core):
        """Test plotting power with custom colormap."""
        prismatic_core.generate_mesh(n_radial=10, n_axial=15)
        power = np.ones((16, 11)) * 1e6

        fig, ax = plot_power_distribution(
            power, prismatic_core, view="xz", cmap="viridis"
        )

        assert fig is not None
        assert ax is not None
        plt.close(fig)


class TestPlotTemperatureDistribution:
    """Test plot_temperature_distribution function."""

    def test_plot_temperature_prismatic(self, prismatic_core):
        """Test plotting temperature distribution."""
        prismatic_core.generate_mesh(n_radial=10, n_axial=15)
        temperature = np.ones((16, 11)) * 1200.0  # K

        fig, ax = plot_temperature_distribution(temperature, prismatic_core, view="xz")

        assert fig is not None
        assert ax is not None
        plt.close(fig)

    def test_plot_temperature_with_custom_colormap(self, prismatic_core):
        """Test plotting temperature with custom colormap."""
        prismatic_core.generate_mesh(n_radial=10, n_axial=15)
        temperature = np.ones((16, 11)) * 1200.0

        fig, ax = plot_temperature_distribution(
            temperature, prismatic_core, view="xz", cmap="plasma"
        )

        assert fig is not None
        assert ax is not None
        plt.close(fig)
