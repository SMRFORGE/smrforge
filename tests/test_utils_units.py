"""
Tests for smrforge.utils.units module.

Pint is a required dependency; tests that need Pint run when it is installed.
"""

from unittest.mock import Mock, patch

import pytest

# Require Pint so Pint-using tests run (required dependency)
pytest.importorskip("pint")


class TestUnitsModule:
    """Test units module."""

    def test_pint_available_flag(self):
        """Test that _PINT_AVAILABLE flag exists."""
        from smrforge.utils import units

        assert hasattr(units, "_PINT_AVAILABLE")
        assert isinstance(units._PINT_AVAILABLE, bool)

    def test_get_ureg_with_pint(self):
        """Test get_ureg when Pint is available."""
        from smrforge.utils.units import get_ureg

        ureg = get_ureg()
        assert ureg is not None
        power = 10 * ureg.megawatt
        assert power.magnitude == 10

    def test_get_ureg_without_pint(self):
        """Test get_ureg when Pint is not available."""
        with patch("smrforge.utils.units._PINT_AVAILABLE", False):
            from smrforge.utils.units import get_ureg

            with pytest.raises(ImportError, match="Pint is required"):
                get_ureg()

    def test_check_units_without_pint(self, capfd):
        """Test check_units when Pint is not available."""
        with patch("smrforge.utils.units._PINT_AVAILABLE", False):
            from smrforge.utils.units import check_units

            result = check_units(10.0, "megawatt", "power")
            assert result == 10.0
        out, err = capfd.readouterr()
        assert "pint" in (out + err).lower()

    def test_check_units_with_pint(self):
        """Test check_units when Pint is available."""
        from smrforge.utils.units import check_units, get_ureg

        ureg = get_ureg()
        power = check_units(10.0, "megawatt", "power")
        assert power.magnitude == 10.0
        temp = 500 * ureg.kelvin
        checked_temp = check_units(temp, ureg.kelvin, "temperature")
        assert checked_temp.magnitude == 500.0

    def test_convert_units_without_pint(self):
        """Test convert_units when Pint is not available."""
        with patch("smrforge.utils.units._PINT_AVAILABLE", False):
            from smrforge.utils.units import convert_units

            result = convert_units(10.0, "watt")
            assert result == 10.0

    def test_convert_units_with_pint(self):
        """Test convert_units when Pint is available."""
        from smrforge.utils.units import convert_units, get_ureg

        ureg = get_ureg()
        power_mw = 10 * ureg.megawatt
        power_w = convert_units(power_mw, "watt")
        assert power_w == 10000000.0

    def test_with_units_without_pint(self, capfd):
        """Test with_units when Pint is not available."""
        with patch("smrforge.utils.units._PINT_AVAILABLE", False):
            from smrforge.utils.units import with_units

            result = with_units(10.0, "megawatt")
            assert result == 10.0
        out, err = capfd.readouterr()
        assert "pint" in (out + err).lower()

    def test_with_units_with_pint(self):
        """Test with_units when Pint is available."""
        from smrforge.utils.units import with_units

        power = with_units(10.0, "megawatt")
        assert hasattr(power, "magnitude")
        assert power.magnitude == 10.0
        assert str(power.units) == "megawatt"

    def test_define_reactor_units(self):
        """Test define_reactor_units."""
        from smrforge.utils.units import define_reactor_units, get_ureg

        ureg = define_reactor_units()
        assert ureg is not None
        reactivity = 0.001 * ureg.dollar
        assert reactivity.magnitude == 0.001

    def test_fallback_registry_quantity_methods(self):
        """
        Cover the Pint-less fallback registry code paths:
        - `_FallbackQuantity.to` / `.check`
        - `_FallbackUnit.__rmul__` exception fallback (non-numeric)
        """
        import smrforge.utils.units as u

        ureg = u._get_fallback_ureg()

        q = 2 * ureg.dollar
        assert q.magnitude == 2.0
        assert q.to("anything") is q
        assert q.check("anything") is True

        # Non-numeric multiplication should fall back to magnitude=0.0
        q2 = "x" * ureg.pcm
        assert q2.magnitude == 0.0

    def test_units_module_pint_available_paths_via_fake_pint(self):
        """
        Cover Pint-available branches even when Pint isn't installed by injecting
        a tiny fake `pint` module and reloading `smrforge.utils.units`.
        """
        import importlib
        import sys
        from types import ModuleType

        import smrforge.utils.units as units

        # Create a minimal fake Pint implementation.
        pint = ModuleType("pint")
        pint_errors = ModuleType("pint.errors")

        class FakeDimensionalityError(Exception):
            pass

        class FakeQuantity:
            def __init__(self, magnitude: float, unit: "FakeUnit"):
                self.magnitude = float(magnitude)
                self.units = unit

            def to(self, _target_quantity: object):
                return self

            def check(self, _dimensionality: object) -> bool:
                return True

        class FakeUnit:
            def __init__(self, name: str):
                self.name = name
                self.dimensionality = f"dim:{name}"
                self.units = self

            def __rmul__(self, other: object):
                return FakeQuantity(float(other), self)

        class FakeUnitRegistry:
            def __init__(self):
                self.defined = []

            def define(self, spec: str):
                self.defined.append(spec)

            def __call__(self, unit_name: str):
                return FakeUnit(str(unit_name))

        pint.UnitRegistry = FakeUnitRegistry  # type: ignore[attr-defined]
        pint.Quantity = FakeQuantity  # type: ignore[attr-defined]
        pint_errors.DimensionalityError = FakeDimensionalityError  # type: ignore[attr-defined]

        # Reload units with fake pint present, then restore.
        orig_pint = sys.modules.get("pint")
        orig_pint_errors = sys.modules.get("pint.errors")
        try:
            sys.modules["pint"] = pint
            sys.modules["pint.errors"] = pint_errors

            importlib.reload(units)
            assert units._PINT_AVAILABLE is True

            ureg = units.get_ureg()
            assert ureg is units.get_ureg()  # singleton

            # Quantity path (is_quantity=True)
            q = 5.0 * ureg("kelvin")
            out_q = units.check_units(q, "kelvin", name="temp")
            assert out_q is q

            # Plain number with string expected_unit
            out_num = units.check_units(10.0, "megawatt", name="power")
            assert hasattr(out_num, "magnitude")

            # Plain number with unit object expected_unit (else branch)
            unit_obj = ureg("watt")
            out_num2 = units.check_units(3.0, unit_obj, name="p")
            assert hasattr(out_num2, "magnitude")

            # convert_units quantity path
            assert units.convert_units(q, "kelvin") == 5.0

            # with_units else branch
            w = units.with_units(7.0, unit_obj)
            assert getattr(w, "magnitude", None) == 7.0
        finally:
            # Restore original pint modules (or remove our fakes), then reload units back.
            if orig_pint is None:
                sys.modules.pop("pint", None)
            else:
                sys.modules["pint"] = orig_pint

            if orig_pint_errors is None:
                sys.modules.pop("pint.errors", None)
            else:
                sys.modules["pint.errors"] = orig_pint_errors

            importlib.reload(units)


class TestUnitsEdgeCases:
    """Edge case tests for units.py to improve coverage to 60%+."""

    def test_check_units_quantity_with_string_unit(self):
        """Test check_units with Quantity and string expected_unit."""
        from smrforge.utils.units import check_units, get_ureg

        ureg = get_ureg()
        temp = 500 * ureg.kelvin
        checked = check_units(temp, "kelvin", "temperature")
        assert checked.magnitude == 500.0

    def test_check_units_quantity_with_quantity_unit(self):
        """Test check_units with Quantity and Quantity expected_unit."""
        from smrforge.utils.units import check_units, get_ureg

        ureg = get_ureg()
        temp = 500 * ureg.kelvin
        checked = check_units(temp, ureg.kelvin, "temperature")
        assert checked.magnitude == 500.0

    def test_check_units_quantity_wrong_dimension(self):
        """Test check_units with Quantity having wrong dimensions."""
        from pint.errors import DimensionalityError

        from smrforge.utils.units import check_units, get_ureg

        ureg = get_ureg()
        power = 10 * ureg.megawatt
        with pytest.raises(DimensionalityError):
            check_units(power, "kelvin", "temperature")

    def test_check_units_plain_number_with_string_unit(self):
        """Test check_units with plain number and string expected_unit."""
        from smrforge.utils.units import check_units

        result = check_units(10.0, "megawatt", "power")
        assert hasattr(result, "magnitude") or isinstance(result, float)

    def test_check_units_plain_number_with_quantity_unit(self):
        """Test check_units with plain number and Quantity expected_unit."""
        from smrforge.utils.units import check_units, get_ureg

        ureg = get_ureg()
        result = check_units(10.0, ureg.megawatt, "power")
        assert hasattr(result, "magnitude") or isinstance(result, float)

    def test_convert_units_quantity_with_string_target(self):
        """Test convert_units with Quantity and string target_unit."""
        from smrforge.utils.units import convert_units, get_ureg

        ureg = get_ureg()
        power_mw = 10 * ureg.megawatt
        power_w = convert_units(power_mw, "watt")
        assert power_w == 10000000.0

    def test_convert_units_quantity_with_quantity_target(self):
        """Test convert_units with Quantity and Quantity target_unit."""
        from smrforge.utils.units import convert_units, get_ureg

        ureg = get_ureg()
        power_mw = 10 * ureg.megawatt
        power_w = convert_units(power_mw, ureg.watt)
        assert power_w == 10000000.0

    def test_convert_units_plain_number(self):
        """Test convert_units with plain number (no conversion)."""
        from smrforge.utils.units import convert_units

        result = convert_units(10.0, "watt")
        assert result == 10.0

    def test_with_units_string_unit(self):
        """Test with_units with string unit."""
        from smrforge.utils.units import with_units

        power = with_units(10.0, "megawatt")
        assert hasattr(power, "magnitude")
        assert power.magnitude == 10.0

    def test_with_units_quantity_unit(self):
        """Test with_units with Quantity unit."""
        from smrforge.utils.units import get_ureg, with_units

        ureg = get_ureg()
        power = with_units(10.0, ureg.megawatt)
        assert power.magnitude == 10.0

    def test_get_ureg_singleton(self):
        """Test that get_ureg returns same instance (singleton)."""
        from smrforge.utils.units import get_ureg

        ureg1 = get_ureg()
        ureg2 = get_ureg()
        assert ureg1 is ureg2

    def test_define_reactor_units_reactivity_units(self):
        """Test that reactor units (dollar, pcm) are defined."""
        from smrforge.utils.units import define_reactor_units

        ureg = define_reactor_units()
        reactivity_dollar = 0.001 * ureg.dollar
        assert reactivity_dollar.magnitude == 0.001
        reactivity_pcm = 100 * ureg.pcm
        assert reactivity_pcm.magnitude == 100
