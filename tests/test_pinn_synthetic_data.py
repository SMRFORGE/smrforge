"""
Tests for PINN MVP synthetic data generator.

Standalone: Only requires numpy. No torch or smrforge_pro.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Import from examples
examples_dir = Path(__file__).resolve().parent.parent / "examples"
sys.path.insert(0, str(examples_dir))
try:
    from pinn_mvp_synthetic_data import generate_synthetic_pinn_data
finally:
    sys.path.pop(0)


class TestPinnSyntheticData:
    """Tests for generate_synthetic_pinn_data."""

    def test_generates_valid_shapes(self):
        """Output x and y have correct shapes."""
        x, y = generate_synthetic_pinn_data(n_samples=50, seed=42)
        assert x.shape == (50, 5), "x should be (50, 5)"
        assert y.shape == (50, 3), "y should be (50, 3) with k_eff, flux, temp"

    def test_reproducible_with_seed(self):
        """Same seed produces same data."""
        x1, y1 = generate_synthetic_pinn_data(n_samples=20, seed=123)
        x2, y2 = generate_synthetic_pinn_data(n_samples=20, seed=123)
        np.testing.assert_array_equal(x1, x2)
        np.testing.assert_array_equal(y1, y2)

    def test_different_seeds_differ(self):
        """Different seeds produce different data."""
        x1, _ = generate_synthetic_pinn_data(n_samples=20, seed=1)
        x2, _ = generate_synthetic_pinn_data(n_samples=20, seed=2)
        assert not np.allclose(x1, x2)

    def test_param_ranges_respected(self):
        """Generated x values stay within param ranges."""
        param_ranges = {
            "enrichment": (5.0, 20.0),
            "moderator_density": (0.1, 0.9),
            "core_height": (1.0, 2.0),
            "fuel_radius": (0.4, 0.8),
            "cr_position": (0.0, 1.0),
        }
        x, y = generate_synthetic_pinn_data(
            n_samples=100, seed=42, param_ranges=param_ranges
        )
        lows = np.array([param_ranges[n][0] for n in param_ranges])
        highs = np.array([param_ranges[n][1] for n in param_ranges])
        assert np.all(x >= lows - 1e-6)
        assert np.all(x <= highs + 1e-6)

    def test_output_physical_plausibility(self):
        """k_eff, flux, temp in plausible ranges."""
        _, y = generate_synthetic_pinn_data(n_samples=50, seed=42)
        k_eff = y[:, 0]
        max_flux = y[:, 1]
        avg_temp = y[:, 2]
        assert np.all(k_eff > 0.5) and np.all(k_eff < 1.5)
        assert np.all(max_flux > 0)
        assert np.all(avg_temp > 0)


def test_synthetic_data_script_runs(tmp_path):
    """Run the script from command line and verify output NPZ."""
    import subprocess

    project_root = Path(__file__).resolve().parent.parent
    script_path = project_root / "examples" / "pinn_mvp_synthetic_data.py"
    out_file = tmp_path / "pinn_dataset.npz"
    result = subprocess.run(
        [sys.executable, str(script_path), "--output", str(out_file), "-n", "25"],
        capture_output=True,
        text=True,
        cwd=project_root,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert out_file.exists()
    data = np.load(out_file, allow_pickle=True)
    assert "x" in data and "y" in data
    assert data["x"].shape == (25, 5)
    assert data["y"].shape == (25, 3)
