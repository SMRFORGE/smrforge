"""
Tests for __init__.py module imports.

These tests verify that module imports work correctly, including
graceful handling when optional dependencies are missing.
"""

import pytest
import sys
from unittest.mock import patch


class TestCoreInit:
    """Test smrforge/core/__init__.py."""
    
    def test_import_core_constants(self):
        """Test importing constants from core."""
        from smrforge.core import constants
        assert constants is not None
    
    def test_import_core_materials_database(self):
        """Test importing materials_database from core."""
        from smrforge.core import materials_database
        assert materials_database is not None
    
    def test_import_core_reactor_core(self):
        """Test importing reactor_core components."""
        from smrforge.core import NuclearDataCache, Nuclide, Library
        assert NuclearDataCache is not None
        assert Nuclide is not None
        assert Library is not None
    
    def test_import_core_endf_parser(self):
        """Test importing ENDF parser components."""
        from smrforge.core import ENDFEvaluation, ENDFCompatibility, ReactionData
        assert ENDFEvaluation is not None
        assert ENDFCompatibility is not None
        assert ReactionData is not None
    
    def test_import_core_resonance_selfshield(self):
        """Test importing resonance self-shielding components."""
        from smrforge.core import (
            ResonanceSelfShielding,
            BondarenkoMethod,
            SubgroupMethod,
            EquivalenceTheory,
        )
        assert ResonanceSelfShielding is not None
        assert BondarenkoMethod is not None
    
    def test_core_init_all_attributes(self):
        """Test that __all__ is properly populated."""
        import smrforge.core as core_module
        assert hasattr(core_module, '__all__')
        assert 'constants' in core_module.__all__
        assert 'materials_database' in core_module.__all__


class TestNeutronicsInit:
    """Test smrforge/neutronics/__init__.py."""
    
    def test_import_neutronics_solver(self):
        """Test importing neutronics solver."""
        from smrforge.neutronics import NeutronicsSolver, MultiGroupDiffusion
        assert NeutronicsSolver is not None
        assert MultiGroupDiffusion is not None
        assert NeutronicsSolver == MultiGroupDiffusion  # Should be aliased
    
    def test_import_neutronics_monte_carlo(self):
        """Test importing Monte Carlo solver."""
        from smrforge.neutronics import MonteCarlo, MonteCarloSolver
        assert MonteCarlo is not None
        assert MonteCarloSolver is not None
        assert MonteCarlo == MonteCarloSolver  # Should be aliased
    
    def test_import_neutronics_transport(self):
        """Test importing transport solver."""
        from smrforge.neutronics import Transport
        assert Transport is not None
    
    def test_neutronics_init_all_attributes(self):
        """Test that __all__ is properly populated."""
        import smrforge.neutronics as neutronics_module
        assert hasattr(neutronics_module, '__all__')
        assert 'NeutronicsSolver' in neutronics_module.__all__
        assert 'MultiGroupDiffusion' in neutronics_module.__all__


class TestThermalInit:
    """Test smrforge/thermal/__init__.py."""
    
    def test_import_thermal_hydraulics(self):
        """Test importing thermal hydraulics."""
        from smrforge.thermal import ThermalHydraulics, ChannelThermalHydraulics
        assert ThermalHydraulics is not None
        assert ChannelThermalHydraulics is not None
        assert ThermalHydraulics == ChannelThermalHydraulics  # Should be aliased
    
    def test_import_thermal_components(self):
        """Test importing thermal components."""
        from smrforge.thermal import (
            ChannelGeometry,
            FluidProperties,
            FlowRegime,
        )
        assert ChannelGeometry is not None
        assert FluidProperties is not None
        assert FlowRegime is not None
    
    def test_thermal_init_all_attributes(self):
        """Test that __all__ is properly populated."""
        import smrforge.thermal as thermal_module
        assert hasattr(thermal_module, '__all__')
        assert 'ThermalHydraulics' in thermal_module.__all__
        assert 'ChannelThermalHydraulics' in thermal_module.__all__


class TestGeometryInit:
    """Test smrforge/geometry/__init__.py."""
    
    def test_import_geometry_core(self):
        """Test importing core geometry classes."""
        from smrforge.geometry import PrismaticCore, PebbleBedCore, CoreType, LatticeType
        assert PrismaticCore is not None
        assert PebbleBedCore is not None
        assert CoreType is not None
        assert LatticeType is not None
    
    def test_import_geometry_control_rods(self):
        """Test importing control rod components."""
        from smrforge.geometry import (
            ControlRod,
            ControlRodBank,
            ControlRodSystem,
            ControlRodType,
            BankPriority,
            ControlRodSequence,
            ScramEvent,
        )
        assert ControlRod is not None
        assert ControlRodBank is not None
        assert ControlRodSystem is not None
    
    def test_import_geometry_assembly(self):
        """Test importing assembly components."""
        from smrforge.geometry import (
            Assembly,
            AssemblyManager,
            FuelBatch,
            RefuelingEvent,
            RefuelingPattern,
        )
        assert Assembly is not None
        assert AssemblyManager is not None
    
    def test_import_geometry_mesh_3d(self):
        """Test importing 3D mesh components."""
        from smrforge.geometry import (
            Mesh3D,
            Surface,
            combine_meshes,
            extract_cylinder_mesh,
            extract_hexagonal_prism_mesh,
            extract_sphere_mesh,
        )
        assert Mesh3D is not None
        assert Surface is not None
        assert combine_meshes is not None
    
    def test_import_geometry_validation(self):
        """Test importing geometry validation."""
        from smrforge.geometry import (
            ValidationReport,
            Gap,
            validate_geometry_completeness,
            check_gaps_and_boundaries,
            validate_material_connectivity,
        )
        assert ValidationReport is not None
        assert Gap is not None
    
    def test_geometry_init_all_attributes(self):
        """Test that __all__ is properly populated."""
        import smrforge.geometry as geometry_module
        assert hasattr(geometry_module, '__all__')
        assert 'PrismaticCore' in geometry_module.__all__
        assert 'PebbleBedCore' in geometry_module.__all__


class TestUncertaintyInit:
    """Test smrforge/uncertainty/__init__.py."""
    
    def test_import_uncertainty(self):
        """Test importing uncertainty module."""
        from smrforge.uncertainty import uq
        assert uq is not None


class TestMainInit:
    """Test smrforge/__init__.py."""
    
    def test_import_version(self):
        """Test importing version information."""
        from smrforge import __version__, __version_info__, get_version
        assert __version__ is not None
        assert __version_info__ is not None
        assert callable(get_version)
    
    def test_import_constants(self):
        """Test importing constants."""
        from smrforge import constants
        assert constants is not None
    
    def test_import_neutronics_from_main(self):
        """Test importing neutronics from main package."""
        from smrforge import NeutronicsSolver, MultiGroupDiffusion
        assert NeutronicsSolver is not None
        assert MultiGroupDiffusion is not None
    
    def test_import_thermal_from_main(self):
        """Test importing thermal from main package."""
        from smrforge import ThermalHydraulics, ChannelThermalHydraulics
        assert ThermalHydraulics is not None
        assert ChannelThermalHydraulics is not None
    
    def test_import_convenience_from_main(self):
        """Test importing convenience functions from main package."""
        from smrforge import (
            create_reactor,
            list_presets,
            get_preset,
            quick_keff,
            SimpleReactor,
        )
        assert create_reactor is not None
        assert list_presets is not None
        assert get_preset is not None
        assert quick_keff is not None
        assert SimpleReactor is not None
    
    def test_import_decay_heat_from_main(self):
        """Test importing decay heat from main package."""
        from smrforge import DecayHeatCalculator, DecayHeatResult
        assert DecayHeatCalculator is not None
        assert DecayHeatResult is not None
    
    def test_import_gamma_transport_from_main(self):
        """Test importing gamma transport from main package."""
        from smrforge import GammaTransportSolver, GammaTransportOptions
        assert GammaTransportSolver is not None
        assert GammaTransportOptions is not None
    
    def test_import_help_from_main(self):
        """Test importing help from main package."""
        from smrforge import help
        assert callable(help)
    
    def test_main_init_all_attributes(self):
        """Test that __all__ is properly populated."""
        import smrforge as main_module
        assert hasattr(main_module, '__all__')
        assert '__version__' in main_module.__all__
        assert '__version_info__' in main_module.__all__
        assert 'constants' in main_module.__all__


class TestInitImportErrors:
    """Test __init__.py files handle import errors gracefully."""
    
    def test_core_init_import_error_reactor_core(self):
        """Test core __init__ handles reactor_core import error."""
        with patch.dict(sys.modules, {'smrforge.core.reactor_core': None}):
            # Reload module to trigger import error
            import importlib
            import smrforge.core as core_module
            importlib.reload(core_module)
            
            # Should still work without reactor_core
            assert hasattr(core_module, '__all__')
    
    def test_neutronics_init_import_error_solver(self):
        """Test neutronics __init__ handles solver import error."""
        with patch.dict(sys.modules, {'smrforge.neutronics.solver': None}):
            import importlib
            import smrforge.neutronics as neutronics_module
            importlib.reload(neutronics_module)
            
            # Should handle error gracefully
            assert hasattr(neutronics_module, '__all__')
    
    def test_thermal_init_import_error(self):
        """Test thermal __init__ handles import error."""
        with patch.dict(sys.modules, {'smrforge.thermal.hydraulics': None}):
            import importlib
            import smrforge.thermal as thermal_module
            importlib.reload(thermal_module)
            
            # Should handle error gracefully
            assert hasattr(thermal_module, '__all__')
    
    def test_geometry_init_import_error(self):
        """Test geometry __init__ handles import error."""
        with patch.dict(sys.modules, {'smrforge.geometry.core_geometry': None}):
            import importlib
            import smrforge.geometry as geometry_module
            importlib.reload(geometry_module)
            
            # Should handle error gracefully
            assert hasattr(geometry_module, '__all__')
    
    def test_main_init_import_error(self):
        """Test main __init__ handles import error."""
        with patch.dict(sys.modules, {'smrforge.neutronics.solver': None}):
            import importlib
            import smrforge as main_module
            importlib.reload(main_module)
            
            # Should handle error gracefully
            assert hasattr(main_module, '__all__')
            assert '__version__' in main_module.__all__  # Should still have version
