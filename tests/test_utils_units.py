"""
Tests for smrforge.utils.units module.
"""

import pytest
from unittest.mock import patch, Mock


class TestUnitsModule:
    """Test units module."""
    
    def test_pint_available_flag(self):
        """Test that _PINT_AVAILABLE flag exists."""
        from smrforge.utils import units
        assert hasattr(units, '_PINT_AVAILABLE')
        assert isinstance(units._PINT_AVAILABLE, bool)
    
    def test_get_ureg_with_pint(self):
        """Test get_ureg when Pint is available."""
        try:
            from smrforge.utils.units import get_ureg
            ureg = get_ureg()
            assert ureg is not None
            # Test that we can use it
            power = 10 * ureg.megawatt
            assert power.magnitude == 10
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_get_ureg_without_pint(self):
        """Test get_ureg when Pint is not available."""
        with patch('smrforge.utils.units._PINT_AVAILABLE', False):
            from smrforge.utils.units import get_ureg
            with pytest.raises(ImportError, match="Pint is required"):
                get_ureg()
    
    def test_check_units_without_pint(self):
        """Test check_units when Pint is not available."""
        with patch('smrforge.utils.units._PINT_AVAILABLE', False):
            from smrforge.utils.units import check_units
            import warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = check_units(10.0, "megawatt", "power")
                assert result == 10.0
                assert len(w) == 1
                assert "Pint not installed" in str(w[0].message)
    
    def test_check_units_with_pint(self):
        """Test check_units when Pint is available."""
        try:
            from smrforge.utils.units import check_units, get_ureg
            ureg = get_ureg()
            # Test with plain number
            power = check_units(10.0, "megawatt", "power")
            assert power.magnitude == 10.0
            # Test with Quantity
            temp = 500 * ureg.kelvin
            checked_temp = check_units(temp, ureg.kelvin, "temperature")
            assert checked_temp.magnitude == 500.0
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_convert_units_without_pint(self):
        """Test convert_units when Pint is not available."""
        with patch('smrforge.utils.units._PINT_AVAILABLE', False):
            from smrforge.utils.units import convert_units
            result = convert_units(10.0, "watt")
            assert result == 10.0
    
    def test_convert_units_with_pint(self):
        """Test convert_units when Pint is available."""
        try:
            from smrforge.utils.units import convert_units, get_ureg
            ureg = get_ureg()
            power_mw = 10 * ureg.megawatt
            power_w = convert_units(power_mw, "watt")
            assert power_w == 10000000.0
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_with_units_without_pint(self):
        """Test with_units when Pint is not available."""
        with patch('smrforge.utils.units._PINT_AVAILABLE', False):
            from smrforge.utils.units import with_units
            import warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = with_units(10.0, "megawatt")
                assert result == 10.0
                assert len(w) == 1
                assert "Pint not installed" in str(w[0].message)
    
    def test_with_units_with_pint(self):
        """Test with_units when Pint is available."""
        try:
            from smrforge.utils.units import with_units
            power = with_units(10.0, "megawatt")
            # Check if it's a Quantity (Pint available) or float (Pint not available)
            if hasattr(power, 'magnitude'):
                assert power.magnitude == 10.0
                assert str(power.units) == "megawatt"
            else:
                # Pint not actually available despite try block
                assert power == 10.0
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_define_reactor_units(self):
        """Test define_reactor_units."""
        try:
            from smrforge.utils.units import define_reactor_units, get_ureg
            ureg = define_reactor_units()
            assert ureg is not None
            # Test reactor-specific units
            reactivity = 0.001 * ureg.dollar
            assert reactivity.magnitude == 0.001
        except ImportError:
            pytest.skip("Pint not available")


class TestUnitsEdgeCases:
    """Edge case tests for units.py to improve coverage to 60%+."""
    
    def test_check_units_quantity_with_string_unit(self):
        """Test check_units with Quantity and string expected_unit."""
        try:
            from smrforge.utils.units import check_units, get_ureg
            ureg = get_ureg()
            
            temp = 500 * ureg.kelvin
            checked = check_units(temp, "kelvin", "temperature")
            
            assert checked.magnitude == 500.0
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_check_units_quantity_with_quantity_unit(self):
        """Test check_units with Quantity and Quantity expected_unit."""
        try:
            from smrforge.utils.units import check_units, get_ureg
            ureg = get_ureg()
            
            temp = 500 * ureg.kelvin
            checked = check_units(temp, ureg.kelvin, "temperature")
            
            assert checked.magnitude == 500.0
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_check_units_quantity_wrong_dimension(self):
        """Test check_units with Quantity having wrong dimensions."""
        try:
            from smrforge.utils.units import check_units, get_ureg
            from pint.errors import DimensionalityError
            ureg = get_ureg()
            
            power = 10 * ureg.megawatt
            with pytest.raises(DimensionalityError):
                check_units(power, "kelvin", "temperature")
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_check_units_plain_number_with_string_unit(self):
        """Test check_units with plain number and string expected_unit."""
        try:
            from smrforge.utils.units import check_units
            result = check_units(10.0, "megawatt", "power")
            
            assert hasattr(result, 'magnitude') or isinstance(result, float)
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_check_units_plain_number_with_quantity_unit(self):
        """Test check_units with plain number and Quantity expected_unit."""
        try:
            from smrforge.utils.units import check_units, get_ureg
            ureg = get_ureg()
            
            result = check_units(10.0, ureg.megawatt, "power")
            
            assert hasattr(result, 'magnitude') or isinstance(result, float)
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_convert_units_quantity_with_string_target(self):
        """Test convert_units with Quantity and string target_unit."""
        try:
            from smrforge.utils.units import convert_units, get_ureg
            ureg = get_ureg()
            
            power_mw = 10 * ureg.megawatt
            power_w = convert_units(power_mw, "watt")
            
            assert power_w == 10000000.0
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_convert_units_quantity_with_quantity_target(self):
        """Test convert_units with Quantity and Quantity target_unit."""
        try:
            from smrforge.utils.units import convert_units, get_ureg
            ureg = get_ureg()
            
            power_mw = 10 * ureg.megawatt
            power_w = convert_units(power_mw, ureg.watt)
            
            assert power_w == 10000000.0
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_convert_units_plain_number(self):
        """Test convert_units with plain number (no conversion)."""
        try:
            from smrforge.utils.units import convert_units
            result = convert_units(10.0, "watt")
            
            assert result == 10.0
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_with_units_string_unit(self):
        """Test with_units with string unit."""
        try:
            from smrforge.utils.units import with_units
            power = with_units(10.0, "megawatt")
            
            if hasattr(power, 'magnitude'):
                assert power.magnitude == 10.0
            else:
                assert power == 10.0
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_with_units_quantity_unit(self):
        """Test with_units with Quantity unit."""
        try:
            from smrforge.utils.units import with_units, get_ureg
            ureg = get_ureg()
            
            power = with_units(10.0, ureg.megawatt)
            
            if hasattr(power, 'magnitude'):
                assert power.magnitude == 10.0
            else:
                assert power == 10.0
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_get_ureg_singleton(self):
        """Test that get_ureg returns same instance (singleton)."""
        try:
            from smrforge.utils.units import get_ureg
            ureg1 = get_ureg()
            ureg2 = get_ureg()
            
            assert ureg1 is ureg2
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_define_reactor_units_reactivity_units(self):
        """Test that reactor units (dollar, pcm) are defined."""
        try:
            from smrforge.utils.units import define_reactor_units, get_ureg
            ureg = define_reactor_units()
            
            # Test dollar unit
            reactivity_dollar = 0.001 * ureg.dollar
            assert reactivity_dollar.magnitude == 0.001
            
            # Test pcm unit
            reactivity_pcm = 100 * ureg.pcm
            assert reactivity_pcm.magnitude == 100
        except ImportError:
            pytest.skip("Pint not available")
