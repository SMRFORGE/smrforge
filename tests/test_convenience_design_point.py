"""
Tests for get_design_point and save_variant (convenience API).
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from smrforge.convenience import get_design_point, save_variant


def test_get_design_point_basic():
    """get_design_point returns power_thermal_mw, k_eff from reactor.solve()."""
    reactor = Mock()
    reactor.solve.return_value = {"power_thermal_mw": 50.0, "k_eff": 1.02}
    reactor.spec.power_thermal = 50e6
    point = get_design_point(reactor)
    assert point["power_thermal_mw"] == 50.0
    assert point["k_eff"] == 1.02
    reactor.solve.assert_called_once()


def test_get_design_point_with_power_distribution():
    """get_design_point includes max/mean power density and peak factor when present."""
    reactor = Mock()
    reactor.solve.return_value = {
        "power_thermal_mw": 10.0,
        "k_eff": 1.0,
        "power_distribution": [1.0, 2.0, 3.0],
    }
    reactor.spec.power_thermal = 10e6
    point = get_design_point(reactor)
    assert point["max_power_density"] == 3.0
    assert point["mean_power_density"] == 2.0
    assert point["power_peak_factor"] == pytest.approx(3.0 / 2.0)


def test_save_variant_creates_file(tmp_path):
    """save_variant writes design_<name>.json and returns path."""
    reactor = Mock()
    reactor.save = Mock()
    path = save_variant(reactor, "my_variant", output_dir=str(tmp_path))
    assert path == tmp_path / "design_my_variant.json"
    reactor.save.assert_called_once_with(path)


def test_save_variant_sanitizes_name(tmp_path):
    """save_variant sanitizes variant name for filename."""
    reactor = Mock()
    reactor.save = Mock()
    path = save_variant(reactor, "v1.2-beta", output_dir=str(tmp_path))
    assert path.name == "design_v1.2-beta.json"
    reactor.save.assert_called_once()
