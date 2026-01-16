"""
Tests for unit checking utilities using Pint.
"""

import numpy as np
import pytest

# Test if Pint is available
try:
    from pint import UnitRegistry, Quantity
    from pint.errors import DimensionalityError
    _PINT_AVAILABLE = True
except ImportError:
    _PINT_AVAILABLE = False


@pytest.mark.skipif(not _PINT_AVAILABLE, reason="Pint not installed")
class TestUnitRegistry:
    """Test unit registry functionality."""

    def test_get_ureg(self):
        """Test getting unit registry."""
        from smrforge.utils.units import get_ureg
        
        ureg = get_ureg()
        assert ureg is not None
        assert isinstance(ureg, UnitRegistry)

    def test_reactor_units_defined(self):
        """Test that reactor-specific units are defined."""
        from smrforge.utils.units import get_ureg
        
        ureg = get_ureg()
        
        # Test dollar unit (reactivity cents)
        dollar = ureg.dollar
        assert dollar is not None
        
        # Test pcm unit (per cent mille)
        pcm = ureg.pcm
        assert pcm is not None


@pytest.mark.skipif(not _PINT_AVAILABLE, reason="Pint not installed")
class TestUnitChecking:
    """Test unit checking functions."""

    def test_check_units_with_quantity(self):
        """Test checking units with Pint Quantity."""
        from smrforge.utils.units import check_units, get_ureg
        
        ureg = get_ureg()
        
        power = 10.0 * ureg.megawatt
        checked = check_units(power, "megawatt", "power")
        assert checked.magnitude == 10.0
        assert checked.units == ureg.megawatt

    def test_check_units_with_plain_number(self):
        """Test checking units with plain number."""
        from smrforge.utils.units import check_units
        
        power = check_units(10.0, "megawatt", "power")
        assert power.magnitude == 10.0

    def test_check_units_dimensionality_error(self):
        """Test that wrong units raise error."""
        from smrforge.utils.units import check_units, get_ureg
        from pint.errors import DimensionalityError
        
        ureg = get_ureg()
        
        power = 10.0 * ureg.megawatt
        with pytest.raises(DimensionalityError):
            check_units(power, "kelvin", "power")  # Wrong dimension

    def test_convert_units(self):
        """Test unit conversion."""
        from smrforge.utils.units import convert_units, get_ureg
        
        ureg = get_ureg()
        
        power_mw = 10.0 * ureg.megawatt
        power_w = convert_units(power_mw, "watt")
        assert abs(power_w - 10e6) < 1.0

    def test_with_units(self):
        """Test attaching units to plain numbers."""
        from smrforge.utils.units import with_units, get_ureg
        
        ureg = get_ureg()
        
        power = with_units(10.0, "megawatt")
        assert power.magnitude == 10.0
        assert power.units == ureg.megawatt

    def test_reactivity_units(self):
        """Test reactivity units (dollar, pcm)."""
        from smrforge.utils.units import with_units, get_ureg
        
        ureg = get_ureg()
        
        reactivity_dollar = with_units(0.01, "dollar")
        assert reactivity_dollar.magnitude == 0.01
        
        reactivity_pcm = with_units(100.0, "pcm")
        assert reactivity_pcm.magnitude == 100.0


@pytest.mark.skipif(_PINT_AVAILABLE, reason="Pint is installed - test backwards compatibility")
class TestBackwardsCompatibility:
    """Test backwards compatibility when Pint is not available."""

    def test_get_ureg_raises_import_error(self):
        """Test that get_ureg raises ImportError when Pint not available."""
        from smrforge.utils.units import get_ureg
        
        with pytest.raises(ImportError):
            get_ureg()

    def test_functions_without_pint(self):
        """Test that functions degrade gracefully without Pint."""
        from smrforge.utils.units import check_units, convert_units, with_units
        import warnings
        
        # These should warn but not crash
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            value = check_units(10.0, "megawatt", "power")
            assert len(w) == 1  # Should have issued a warning
            assert value == 10.0  # Should return original value
        
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            converted = convert_units(10.0, "watt")
            assert converted == 10.0
        
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            with_units_value = with_units(10.0, "megawatt")
            assert with_units_value == 10.0
