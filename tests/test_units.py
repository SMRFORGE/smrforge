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

    def test_define_reactor_units(self):
        """Test define_reactor_units function."""
        from smrforge.utils.units import define_reactor_units
        
        ureg = define_reactor_units()
        assert ureg is not None
        # Verify reactor units are defined
        assert hasattr(ureg, 'dollar')
        assert hasattr(ureg, 'pcm')


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

    def test_check_units_with_quantity_expected_unit(self):
        """Test check_units with Quantity as expected_unit."""
        from smrforge.utils.units import check_units, get_ureg
        
        ureg = get_ureg()
        
        power = 10.0 * ureg.megawatt
        checked = check_units(power, ureg.megawatt, "power")
        assert checked.magnitude == 10.0

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

    def test_convert_units_with_quantity_target_str(self):
        """Test convert_units with Quantity and string target."""
        from smrforge.utils.units import convert_units, get_ureg
        
        ureg = get_ureg()
        
        power_mw = 10.0 * ureg.megawatt
        power_w = convert_units(power_mw, "watt")
        assert abs(power_w - 10e6) < 1.0

    def test_convert_units_with_quantity_target_quantity(self):
        """Test convert_units with Quantity and Quantity target."""
        from smrforge.utils.units import convert_units, get_ureg
        
        ureg = get_ureg()
        
        power_mw = 10.0 * ureg.megawatt
        power_w = convert_units(power_mw, ureg.watt)
        assert abs(power_w - 10e6) < 1.0

    def test_convert_units_plain_number(self):
        """Test convert_units with plain number."""
        from smrforge.utils.units import convert_units
        
        result = convert_units(10.0, "watt")
        assert result == 10.0

    def test_with_units_string_unit(self):
        """Test with_units with string unit."""
        from smrforge.utils.units import with_units, get_ureg
        
        ureg = get_ureg()
        
        power = with_units(10.0, "megawatt")
        assert power.magnitude == 10.0
        assert power.units == ureg.megawatt

    def test_with_units_quantity_unit(self):
        """Test with_units with Quantity unit."""
        from smrforge.utils.units import with_units, get_ureg
        
        ureg = get_ureg()
        
        power = with_units(10.0, ureg.megawatt)
        assert power.magnitude == 10.0
        assert power.units == ureg.megawatt


@pytest.mark.skipif(not _PINT_AVAILABLE, reason="Pint not installed")
class TestUnitsEdgeCases:
    """Edge case tests for unit utilities."""
    
    def test_check_units_plain_number_string_unit(self):
        """Test check_units with plain number and string unit."""
        from smrforge.utils.units import check_units
        
        power = check_units(10.0, "megawatt", "power")
        assert power.magnitude == 10.0
    
    def test_check_units_plain_number_quantity_unit(self):
        """Test check_units with plain number and Quantity unit."""
        from smrforge.utils.units import check_units, get_ureg
        
        ureg = get_ureg()
        power = check_units(10.0, ureg.megawatt, "power")
        assert power.magnitude == 10.0
    
    def test_check_units_compatible_units(self):
        """Test check_units with compatible but different units."""
        from smrforge.utils.units import check_units, get_ureg
        
        ureg = get_ureg()
        
        # Watt and megawatt are compatible
        power_w = 10e6 * ureg.watt
        checked = check_units(power_w, "megawatt", "power")
        assert checked.magnitude == 10.0
    
    def test_convert_units_incompatible_units(self):
        """Test convert_units with incompatible units raises error."""
        from smrforge.utils.units import convert_units, get_ureg
        from pint.errors import DimensionalityError
        
        ureg = get_ureg()
        
        power = 10.0 * ureg.megawatt
        with pytest.raises(DimensionalityError):
            convert_units(power, "kelvin")  # Incompatible dimensions
    
    def test_with_units_zero_value(self):
        """Test with_units with zero value."""
        from smrforge.utils.units import with_units, get_ureg
        
        ureg = get_ureg()
        
        power = with_units(0.0, "megawatt")
        assert power.magnitude == 0.0
        assert power.units == ureg.megawatt
    
    def test_with_units_negative_value(self):
        """Test with_units with negative value."""
        from smrforge.utils.units import with_units, get_ureg
        
        ureg = get_ureg()
        
        temp = with_units(-100.0, "kelvin")
        assert temp.magnitude == -100.0
        assert temp.units == ureg.kelvin
    
    def test_convert_units_quantity_to_same_unit(self):
        """Test converting Quantity to same unit."""
        from smrforge.utils.units import convert_units, get_ureg
        
        ureg = get_ureg()
        
        power = 10.0 * ureg.megawatt
        result = convert_units(power, "megawatt")
        assert abs(result - 10.0) < 1e-10
    
    def test_get_ureg_singleton(self):
        """Test that get_ureg returns same instance (singleton)."""
        from smrforge.utils.units import get_ureg
        
        ureg1 = get_ureg()
        ureg2 = get_ureg()
        
        # Should be same instance
        assert ureg1 is ureg2
    
    def test_check_units_name_parameter(self):
        """Test that name parameter is used in error messages."""
        from smrforge.utils.units import check_units, get_ureg
        from pint.errors import DimensionalityError
        
        ureg = get_ureg()
        
        power = 10.0 * ureg.megawatt
        try:
            check_units(power, "kelvin", name="my_power")
        except DimensionalityError as e:
            # Error message should mention the name
            assert "my_power" in str(e) or "power" in str(e).lower()
    
    def test_convert_units_float_result(self):
        """Test that convert_units always returns float."""
        from smrforge.utils.units import convert_units, get_ureg
        
        ureg = get_ureg()
        
        power = 10.0 * ureg.megawatt
        result = convert_units(power, "watt")
        
        assert isinstance(result, float)
        assert not isinstance(result, int)
    
    def test_with_units_int_value(self):
        """Test with_units with integer value."""
        from smrforge.utils.units import with_units, get_ureg
        
        ureg = get_ureg()
        
        power = with_units(10, "megawatt")  # Integer
        assert power.magnitude == 10.0  # Should be converted to float
        assert power.units == ureg.megawatt
    
    def test_reactor_units_dollar_conversion(self):
        """Test dollar unit conversion."""
        from smrforge.utils.units import with_units, convert_units, get_ureg
        
        ureg = get_ureg()
        
        # Dollar is defined as 0.01 * dimensionless
        reactivity = with_units(1.0, "dollar")
        assert reactivity.magnitude == 1.0
        
        # Should be able to convert to dimensionless
        dimless = convert_units(reactivity, "dimensionless")
        assert abs(dimless - 0.01) < 1e-10
    
    def test_reactor_units_pcm_conversion(self):
        """Test pcm unit conversion."""
        from smrforge.utils.units import with_units, convert_units, get_ureg
        
        ureg = get_ureg()
        
        # PCM is defined as 0.0001 * dimensionless
        reactivity = with_units(100.0, "pcm")
        assert reactivity.magnitude == 100.0
        
        # Should be able to convert to dimensionless
        dimless = convert_units(reactivity, "dimensionless")
        assert abs(dimless - 0.01) < 1e-10  # 100 pcm = 0.01


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

    def test_define_reactor_units(self):
        """Test define_reactor_units function raises ImportError when Pint not available."""
        from smrforge.utils.units import define_reactor_units
        
        # When Pint is not available, this should raise ImportError
        with pytest.raises(ImportError, match="Pint is required"):
            define_reactor_units()
