"""
Extended tests for smrforge.utils.units module to improve coverage.
"""

import pytest
from unittest.mock import patch, Mock
import warnings


class TestUnitsExtended:
    """Extended tests for units module to improve coverage."""
    
    def test_check_units_incompatible_units(self):
        """Test check_units raises DimensionalityError for incompatible units."""
        try:
            from smrforge.utils.units import check_units, get_ureg
            from pint.errors import DimensionalityError
            ureg = get_ureg()
            
            power = 10 * ureg.megawatt
            # Try to check power against temperature - should raise error
            with pytest.raises(DimensionalityError):
                check_units(power, "kelvin", "power")
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_check_units_with_quantity_expected_unit(self):
        """Test check_units with Quantity as expected_unit."""
        try:
            from smrforge.utils.units import check_units, get_ureg
            ureg = get_ureg()
            
            power = 10 * ureg.megawatt
            expected_power = 1 * ureg.megawatt  # Quantity as expected_unit
            checked = check_units(power, expected_power, "power")
            assert checked.magnitude == 10.0
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_check_units_plain_number_with_string_unit(self):
        """Test check_units with plain number and string unit."""
        try:
            from smrforge.utils.units import check_units, _PINT_AVAILABLE
            power = check_units(10.0, "megawatt", "power")
            if _PINT_AVAILABLE:
                assert hasattr(power, 'magnitude')
                assert power.magnitude == 10.0
            else:
                # When Pint not available, returns value as-is
                assert power == 10.0
        except ImportError:
            pytest.skip("Cannot import units module")
    
    def test_check_units_plain_number_with_quantity_unit(self):
        """Test check_units with plain number and Quantity unit."""
        try:
            from smrforge.utils.units import check_units, get_ureg
            ureg = get_ureg()
            expected_unit = 1 * ureg.kelvin
            temp = check_units(500.0, expected_unit, "temperature")
            assert hasattr(temp, 'magnitude')
            assert temp.magnitude == 500.0
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_convert_units_quantity_with_string_target(self):
        """Test convert_units with Quantity and string target."""
        try:
            from smrforge.utils.units import convert_units, get_ureg
            ureg = get_ureg()
            
            power_mw = 10 * ureg.megawatt
            power_w = convert_units(power_mw, "watt")
            assert power_w == 10000000.0
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_convert_units_quantity_with_quantity_target(self):
        """Test convert_units with Quantity and Quantity target."""
        try:
            from smrforge.utils.units import convert_units, get_ureg
            ureg = get_ureg()
            
            power_mw = 10 * ureg.megawatt
            target_w = 1 * ureg.watt
            power_w = convert_units(power_mw, target_w)
            assert power_w == 10000000.0
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_convert_units_plain_number(self):
        """Test convert_units with plain number (should return as-is)."""
        try:
            from smrforge.utils.units import convert_units
            result = convert_units(10.0, "watt")
            assert result == 10.0
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_convert_units_incompatible_units(self):
        """Test convert_units raises DimensionalityError for incompatible units."""
        try:
            from smrforge.utils.units import convert_units, get_ureg
            from pint.errors import DimensionalityError
            ureg = get_ureg()
            
            power = 10 * ureg.megawatt
            # Try to convert power to temperature - should raise error
            with pytest.raises(DimensionalityError):
                convert_units(power, "kelvin")
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
            unit = 1 * ureg.kelvin
            temp = with_units(500.0, unit)
            if hasattr(temp, 'magnitude'):
                assert temp.magnitude == 500.0
            else:
                assert temp == 500.0
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_get_ureg_singleton(self):
        """Test that get_ureg returns the same instance (singleton)."""
        try:
            from smrforge.utils.units import get_ureg
            ureg1 = get_ureg()
            ureg2 = get_ureg()
            assert ureg1 is ureg2  # Should be the same instance
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_get_ureg_defines_reactor_units(self):
        """Test that get_ureg defines reactor-specific units."""
        try:
            from smrforge.utils.units import get_ureg
            ureg = get_ureg()
            
            # Test dollar unit (reactivity)
            reactivity = 1 * ureg.dollar
            assert reactivity.magnitude == 1.0
            
            # Test pcm unit (reactivity)
            reactivity_pcm = 100 * ureg.pcm
            assert reactivity_pcm.magnitude == 100.0
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_define_reactor_units_returns_registry(self):
        """Test that define_reactor_units returns the registry."""
        try:
            from smrforge.utils.units import define_reactor_units, get_ureg
            ureg1 = get_ureg()
            ureg2 = define_reactor_units()
            # Should return the same registry instance
            assert ureg1 is ureg2
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_check_units_with_dimensionality_check(self):
        """Test check_units properly checks dimensionality."""
        try:
            from smrforge.utils.units import check_units, get_ureg
            ureg = get_ureg()
            
            # Compatible units (both power)
            power1 = 10 * ureg.megawatt
            power2 = check_units(power1, "kilowatt", "power")
            # Should convert and be compatible
            assert power2.magnitude == 10000.0
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_check_units_raises_dimensionality_error_message(self):
        """Test that DimensionalityError includes variable name."""
        try:
            from smrforge.utils.units import check_units, get_ureg
            from pint.errors import DimensionalityError
            ureg = get_ureg()
            
            power = 10 * ureg.megawatt
            with pytest.raises(DimensionalityError) as exc_info:
                check_units(power, "kelvin", "power")
            # Error should mention the variable name
            assert "power" in str(exc_info.value).lower() or "name" in str(exc_info.value).lower()
        except ImportError:
            pytest.skip("Pint not available")
    
    def test_get_ureg_initializes_reactor_units(self):
        """Test that get_ureg initializes reactor-specific units on first call."""
        try:
            # Reset the global registry to test initialization
            import smrforge.utils.units
            original_ureg = smrforge.utils.units._ureg
            smrforge.utils.units._ureg = None  # Reset to trigger initialization
            
            from smrforge.utils.units import get_ureg
            ureg = get_ureg()
            
            # Test that reactor units are defined (lines 52-53)
            reactivity_dollar = 1 * ureg.dollar
            assert reactivity_dollar.magnitude == 1.0
            
            reactivity_pcm = 100 * ureg.pcm
            assert reactivity_pcm.magnitude == 100.0
            
            # Restore original
            smrforge.utils.units._ureg = original_ureg
        except ImportError:
            pytest.skip("Pint not available")
    
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
        
        # Create a mock Quantity class (not just a function) so isinstance() works
        mock_quantity_class = type('Quantity', (object,), {})
        # Make it callable like the original
        def quantity_constructor(*args, **kwargs):
            return mock_quantity_instance
        mock_quantity_class.__call__ = staticmethod(quantity_constructor)
        
        mock_pint.UnitRegistry = mock_registry
        mock_pint.Quantity = mock_quantity_class  # Use class, not MagicMock
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
            # Create an instance that is actually an instance of the mocked Quantity class
            mock_quantity_obj = mock_quantity_class()
            mock_quantity_obj.check = MagicMock(return_value=True)
            mock_quantity_obj.magnitude = 10.0
            mock_quantity_obj.units = MagicMock()
            mock_quantity_obj.to = MagicMock()  # Add 'to' method for later test
            result = smrforge.utils.units.check_units(mock_quantity_obj, "megawatt", "power")
            # Should return the same object when it's already a Quantity
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
    
