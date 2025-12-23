"""
Comprehensive tests for thermal-hydraulics module
"""

import pytest
import numpy as np


class TestThermalImports:
    """Test thermal module imports."""
    
    def test_thermal_module_import(self):
        """Test that thermal module can be imported."""
        from smrforge import thermal
        assert thermal is not None
    
    def test_channel_thermal_hydraulics_import(self):
        """Test that ChannelThermalHydraulics can be imported."""
        try:
            from smrforge.thermal.hydraulics import ChannelThermalHydraulics
            assert ChannelThermalHydraulics is not None
        except ImportError:
            pytest.skip("ChannelThermalHydraulics not available")
    
    def test_channel_geometry_import(self):
        """Test that ChannelGeometry can be imported."""
        try:
            from smrforge.thermal.hydraulics import ChannelGeometry
            assert ChannelGeometry is not None
        except ImportError:
            pytest.skip("ChannelGeometry not available")


class TestChannelGeometry:
    """Test ChannelGeometry class."""
    
    def test_channel_geometry_creation(self):
        """Test creating a ChannelGeometry instance."""
        try:
            from smrforge.thermal.hydraulics import ChannelGeometry
            
            geometry = ChannelGeometry(
                length=400.0,  # cm
                diameter=1.0,  # cm
                flow_area=np.pi * (0.5)**2,  # cm²
                heated_perimeter=np.pi * 1.0  # cm
            )
            
            assert geometry.length == 400.0
            assert geometry.diameter == 1.0
            assert geometry.flow_area > 0
            assert geometry.heated_perimeter > 0
        except ImportError:
            pytest.skip("ChannelGeometry not available")
    
    def test_channel_geometry_hydraulic_diameter(self):
        """Test hydraulic diameter calculation."""
        try:
            from smrforge.thermal.hydraulics import ChannelGeometry
            
            flow_area = np.pi * (0.5)**2  # cm²
            heated_perimeter = np.pi * 1.0  # cm
            
            geometry = ChannelGeometry(
                length=400.0,
                diameter=1.0,
                flow_area=flow_area,
                heated_perimeter=heated_perimeter
            )
            
            D_h = geometry.hydraulic_diameter
            expected = 4 * flow_area / heated_perimeter
            assert np.isclose(D_h, expected)
            assert np.isclose(D_h, 1.0)  # For circular channel
        except ImportError:
            pytest.skip("ChannelGeometry not available")


class TestChannelThermalHydraulics:
    """Test ChannelThermalHydraulics class."""
    
    def test_thermal_hydraulics_creation(self):
        """Test creating a ChannelThermalHydraulics instance."""
        try:
            from smrforge.thermal.hydraulics import (
                ChannelThermalHydraulics,
                ChannelGeometry
            )
            
            geometry = ChannelGeometry(
                length=400.0,  # cm
                diameter=1.0,  # cm
                flow_area=np.pi * (0.5)**2,  # cm²
                heated_perimeter=np.pi * 1.0  # cm
            )
            
            inlet_conditions = {
                'temperature': 823.15,  # K (550°C)
                'pressure': 7.0e6,  # Pa (7 MPa)
                'mass_flow_rate': 0.1  # kg/s
            }
            
            th = ChannelThermalHydraulics(
                geometry=geometry,
                inlet_conditions=inlet_conditions
            )
            
            assert th.geom == geometry
            assert th.T_in == 823.15
            assert th.P_in == 7.0e6
            assert th.mdot == 0.1
        except ImportError:
            pytest.skip("ChannelThermalHydraulics not available")
    
    def test_set_power_profile(self):
        """Test setting power profile."""
        try:
            from smrforge.thermal.hydraulics import (
                ChannelThermalHydraulics,
                ChannelGeometry
            )
            
            geometry = ChannelGeometry(
                length=400.0,
                diameter=1.0,
                flow_area=np.pi * (0.5)**2,
                heated_perimeter=np.pi * 1.0
            )
            
            inlet_conditions = {
                'temperature': 823.15,
                'pressure': 7.0e6,
                'mass_flow_rate': 0.1
            }
            
            th = ChannelThermalHydraulics(
                geometry=geometry,
                inlet_conditions=inlet_conditions
            )
            
            # Create power profile
            power_profile = np.ones(len(th.z)) * 1000.0  # W/cm
            
            th.set_power_profile(power_profile)
            
            assert len(th.q_linear) == len(th.z)
            assert np.all(th.q_linear == power_profile)
        except ImportError:
            pytest.skip("ChannelThermalHydraulics not available")
