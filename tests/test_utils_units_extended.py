"""
Extended tests for smrforge.utils.units module to improve coverage.

Pint is a required dependency; these tests run when Pint is installed.
"""

import pytest
from unittest.mock import patch, Mock
import warnings

# Require Pint (required dependency)
pytest.importorskip("pint")


class TestUnitsExtended:
    """Extended tests for units module to improve coverage."""
    
    def test_check_units_incompatible_units(self):
        """Test check_units raises DimensionalityError for incompatible units."""
        from smrforge.utils.units import check_units, get_ureg
        from pint.errors import DimensionalityError
        ureg = get_ureg()
        power = 10 * ureg.megawatt
        with pytest.raises(DimensionalityError):
            check_units(power, "kelvin", "power")

    def test_check_units_with_quantity_expected_unit(self):
        """Test check_units with Quantity as expected_unit."""
        from smrforge.utils.units import check_units, get_ureg
        ureg = get_ureg()
        power = 10 * ureg.megawatt
        expected_power = 1 * ureg.megawatt
        checked = check_units(power, expected_power, "power")
        assert checked.magnitude == 10.0

    def test_check_units_plain_number_with_string_unit(self):
        """Test check_units with plain number and string unit."""
        from smrforge.utils.units import check_units
        power = check_units(10.0, "megawatt", "power")
        assert hasattr(power, "magnitude")
        assert power.magnitude == 10.0

    def test_check_units_plain_number_with_quantity_unit(self):
        """Test check_units with plain number and Quantity unit."""
        from smrforge.utils.units import check_units, get_ureg
        ureg = get_ureg()
        expected_unit = 1 * ureg.kelvin
        temp = check_units(500.0, expected_unit, "temperature")
        assert temp.magnitude == 500.0

    def test_convert_units_quantity_with_string_target(self):
        """Test convert_units with Quantity and string target."""
        from smrforge.utils.units import convert_units, get_ureg
        ureg = get_ureg()
        power_mw = 10 * ureg.megawatt
        power_w = convert_units(power_mw, "watt")
        assert power_w == 10000000.0

    def test_convert_units_quantity_with_quantity_target(self):
        """Test convert_units with Quantity and Quantity target."""
        from smrforge.utils.units import convert_units, get_ureg
        ureg = get_ureg()
        power_mw = 10 * ureg.megawatt
        target_w = 1 * ureg.watt
        power_w = convert_units(power_mw, target_w)
        assert power_w == 10000000.0

    def test_convert_units_plain_number(self):
        """Test convert_units with plain number (should return as-is)."""
        from smrforge.utils.units import convert_units
        result = convert_units(10.0, "watt")
        assert result == 10.0

    def test_convert_units_incompatible_units(self):
        """Test convert_units raises DimensionalityError for incompatible units."""
        from smrforge.utils.units import convert_units, get_ureg
        from pint.errors import DimensionalityError
        ureg = get_ureg()
        power = 10 * ureg.megawatt
        with pytest.raises(DimensionalityError):
            convert_units(power, "kelvin")

    def test_with_units_string_unit(self):
        """Test with_units with string unit."""
        from smrforge.utils.units import with_units
        power = with_units(10.0, "megawatt")
        assert power.magnitude == 10.0

    def test_with_units_quantity_unit(self):
        """Test with_units with Quantity unit."""
        from smrforge.utils.units import with_units, get_ureg
        ureg = get_ureg()
        unit = 1 * ureg.kelvin
        temp = with_units(500.0, unit)
        assert temp.magnitude == 500.0

    def test_get_ureg_singleton(self):
        """Test that get_ureg returns the same instance (singleton)."""
        from smrforge.utils.units import get_ureg
        ureg1 = get_ureg()
        ureg2 = get_ureg()
        assert ureg1 is ureg2

    def test_get_ureg_defines_reactor_units(self):
        """Test that get_ureg defines reactor-specific units."""
        from smrforge.utils.units import get_ureg
        ureg = get_ureg()
        reactivity = 1 * ureg.dollar
        assert reactivity.magnitude == 1.0
        reactivity_pcm = 100 * ureg.pcm
        assert reactivity_pcm.magnitude == 100.0

    def test_define_reactor_units_returns_registry(self):
        """Test that define_reactor_units returns the registry."""
        from smrforge.utils.units import define_reactor_units, get_ureg
        ureg1 = get_ureg()
        ureg2 = define_reactor_units()
        assert ureg1 is ureg2

    def test_check_units_with_dimensionality_check(self):
        """Test check_units accepts compatible units (returns value unchanged)."""
        from smrforge.utils.units import check_units, get_ureg
        ureg = get_ureg()
        power1 = 10 * ureg.megawatt
        power2 = check_units(power1, "kilowatt", "power")
        # check_units returns the quantity unchanged when dimensions match
        assert power2.magnitude == 10.0

    def test_check_units_raises_dimensionality_error_message(self):
        """Test that DimensionalityError includes variable name in extra_msg."""
        from smrforge.utils.units import check_units, get_ureg
        from pint.errors import DimensionalityError
        ureg = get_ureg()
        power = 10 * ureg.megawatt
        with pytest.raises(DimensionalityError) as exc_info:
            check_units(power, "kelvin", name="power")
        msg = str(exc_info.value).lower()
        assert "power" in msg or "variable" in msg

    def test_get_ureg_initializes_reactor_units(self):
        """Test that get_ureg initializes reactor-specific units on first call."""
        import smrforge.utils.units
        original_ureg = smrforge.utils.units._ureg
        smrforge.utils.units._ureg = None
        from smrforge.utils.units import get_ureg
        ureg = get_ureg()
        reactivity_dollar = 1 * ureg.dollar
        assert reactivity_dollar.magnitude == 1.0
        reactivity_pcm = 100 * ureg.pcm
        assert reactivity_pcm.magnitude == 100.0
        smrforge.utils.units._ureg = original_ureg
    
    def test_units_with_mocked_pint(self):
        """Test units module with mocked Pint to cover missing paths."""
        import sys
        from unittest.mock import MagicMock
        
        # Create mock Pint module
        mock_pint = MagicMock()
        mock_quantity = MagicMock()
        mock_registry = MagicMock()
        mock_registry_instance = MagicMock()
        
        # Setup mock registry
        mock_registry.return_value = mock_registry_instance
        mock_registry_instance.define = MagicMock()
        mock_registry_instance.megawatt = MagicMock()
        mock_registry_instance.kelvin = MagicMock()
        mock_registry_instance.watt = MagicMock()
        
        # Setup mock Quantity
        mock_quantity_instance = MagicMock()
        mock_quantity_instance.magnitude = 10.0
        mock_quantity_instance.units = MagicMock()
        mock_quantity_instance.check.return_value = True
        mock_quantity_instance.to.return_value = mock_quantity_instance
        
        mock_quantity.return_value = mock_quantity_instance
        
        # Setup mock DimensionalityError
        mock_dimensionality_error = type('DimensionalityError', (Exception,), {})
        
        mock_pint.UnitRegistry = mock_registry
        mock_pint.Quantity = mock_quantity
        mock_pint.errors = MagicMock()
        mock_pint.errors.DimensionalityError = mock_dimensionality_error
        
        # Save original
        original_pint = sys.modules.get('pint')
        original_pint_errors = sys.modules.get('pint.errors')
        
        # Mock pint module
        sys.modules['pint'] = mock_pint
        sys.modules['pint.errors'] = mock_pint.errors
        
        try:
            # Reload module to pick up mocked Pint
            import importlib
            import smrforge.utils.units
            importlib.reload(smrforge.utils.units)
            
            # Test get_ureg with mocked Pint
            smrforge.utils.units._ureg = None  # Reset
            ureg = smrforge.utils.units.get_ureg()
            assert ureg is not None
            # Verify reactor units were defined
            assert mock_registry_instance.define.call_count >= 2
            
            # Test check_units with Quantity
            mock_quantity_obj = MagicMock()
            mock_quantity_obj.check.return_value = True
            mock_quantity_obj.magnitude = 10.0
            result = smrforge.utils.units.check_units(mock_quantity_obj, "megawatt", "power")
            assert result is mock_quantity_obj
            
            # Test check_units with plain number and string unit
            result = smrforge.utils.units.check_units(10.0, "megawatt", "power")
            assert result is not None
            
            # Test check_units with plain number and Quantity unit
            mock_unit_quantity = MagicMock()
            result = smrforge.utils.units.check_units(10.0, mock_unit_quantity, "power")
            assert result is not None
            
            # Test convert_units with Quantity and string target
            mock_quantity_obj.to.return_value.magnitude = 10000000.0
            result = smrforge.utils.units.convert_units(mock_quantity_obj, "watt")
            assert result == 10000000.0
            
            # Test convert_units with Quantity and Quantity target
            mock_target_quantity = MagicMock()
            result = smrforge.utils.units.convert_units(mock_quantity_obj, mock_target_quantity)
            assert result == 10000000.0
            
            # Test convert_units with plain number
            result = smrforge.utils.units.convert_units(10.0, "watt")
            assert result == 10.0
            
            # Test with_units with string unit
            result = smrforge.utils.units.with_units(10.0, "megawatt")
            assert result is not None
            
            # Test with_units with Quantity unit
            result = smrforge.utils.units.with_units(10.0, mock_unit_quantity)
            assert result is not None
            
            # Test define_reactor_units
            result = smrforge.utils.units.define_reactor_units()
            assert result is not None
            
        finally:
            # Restore original modules
            if original_pint is not None:
                sys.modules['pint'] = original_pint
            else:
                sys.modules.pop('pint', None)
            if original_pint_errors is not None:
                sys.modules['pint.errors'] = original_pint_errors
            else:
                sys.modules.pop('pint.errors', None)
            
            # Reload module to restore original state
            import importlib
            import smrforge.utils.units
            importlib.reload(smrforge.utils.units)
    
