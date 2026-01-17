"""
SMRForge - Small Modular Reactor Design and Analysis Toolkit
============================================================
A comprehensive toolkit for nuclear reactor design, analysis, and optimization.

Main modules:
- core: Reactor components and materials (✅ Stable)
- neutronics: Reactor physics and neutron transport (✅ Stable)
- thermal: Thermal-hydraulics analysis (🟡 Experimental - API may change)
- safety: Safety analysis and transients (🟡 Experimental - API may change)
- uncertainty: Uncertainty quantification (🟡 Experimental - API may change)
- visualization: Plotting tools (✅ Stable)
- fuel: Fuel performance modeling (❌ Not implemented)
- optimization: Design optimization (❌ Not implemented)
- io: Input/output utilities (❌ Not implemented)
- control: Control systems (✅ Implemented - PID, load-following)
- mechanics: Structural mechanics (✅ Implemented - fuel rod mechanics)
- economics: Cost modeling (✅ Implemented - capital, operating, LCOE)

⚠️ Feature Status: See FEATURE_STATUS.md for detailed status of each module.
"""

# Import version from dedicated module
from smrforge.__version__ import __version__, __version_info__, get_version

__author__ = "SMRForge Development Team"

# Core imports
from smrforge.core import constants

# Expose key classes at package level
try:
    from smrforge.neutronics.solver import MultiGroupDiffusion
    from smrforge.neutronics import NeutronicsSolver  # Alias defined in neutronics/__init__.py

    _NEUTRONICS_AVAILABLE = True
except ImportError as e:
    import warnings

    warnings.warn(f"Could not import neutronics solver: {e}", ImportWarning)
    _NEUTRONICS_AVAILABLE = False

try:
    from smrforge.thermal import ThermalHydraulics  # Alias for ChannelThermalHydraulics
    from smrforge.thermal import (
        ChannelGeometry,
        ChannelThermalHydraulics,
        FlowRegime,
        FluidProperties,
    )

    _THERMAL_AVAILABLE = True
except ImportError as e:
    import warnings

    warnings.warn(f"Could not import thermal hydraulics: {e}", ImportWarning)
    _THERMAL_AVAILABLE = False

# Convenience functions and classes for easy usage
try:
    # Try importing from convenience package (which re-exports from convenience.py file)
    try:
        from smrforge.convenience import (  # Factory functions; High-level class
            SimpleReactor,
            analyze_preset,
            compare_designs,
            create_reactor,
            get_preset,
            list_presets,
            quick_keff,
        )
        _CONVENIENCE_AVAILABLE = True
    except (ImportError, AttributeError) as e1:
        # Fallback: import directly from convenience.py file module as a package submodule
        # This properly handles relative imports by loading it as part of smrforge package
        import importlib
        import sys
        from pathlib import Path
        
        # Use importlib to import convenience.py as smrforge.convenience_file module
        # This allows relative imports to work correctly
        convenience_file = Path(__file__).parent / "convenience.py"
        if convenience_file.exists():
            # Import as a proper package submodule using importlib
            # This makes relative imports work
            package_name = __name__  # Should be 'smrforge'
            module_name = f"{package_name}.convenience_file"
            
            # Use importlib to load the module as a package member
            loader = importlib.machinery.SourceFileLoader(module_name, str(convenience_file))
            spec = importlib.util.spec_from_loader(module_name, loader)
            convenience_mod = importlib.util.module_from_spec(spec)
            
            # Set __package__ to make relative imports work
            convenience_mod.__package__ = package_name
            convenience_mod.__name__ = module_name
            
            # Add parent to sys.modules so relative imports resolve correctly
            sys.modules[module_name] = convenience_mod
            
            try:
                spec.loader.exec_module(convenience_mod)
                
                SimpleReactor = convenience_mod.SimpleReactor
                analyze_preset = convenience_mod.analyze_preset
                compare_designs = convenience_mod.compare_designs
                create_reactor = convenience_mod.create_reactor
                get_preset = convenience_mod.get_preset
                list_presets = convenience_mod.list_presets
                quick_keff = convenience_mod.quick_keff
                _CONVENIENCE_AVAILABLE = True
            except Exception as e2:
                # If that fails, raise the original error
                raise e1 from e2
        else:
            raise ImportError(f"Could not find convenience.py file: {convenience_file}")

except ImportError as e:
    import warnings

    warnings.warn(
        f"Could not import convenience functions: {e}\n"
        f"Some features may not be available. Please check your installation.",
        ImportWarning,
    )
    _CONVENIENCE_AVAILABLE = False

# Additional convenience utilities
try:
    from smrforge.convenience_utils import (
        create_simple_core,
        create_simple_solver,
        create_simple_xs_data,
        create_simple_burnup_solver,
        create_nuclide_list,
        get_nuclide,
        get_material,
        list_materials,
        quick_burnup_calculation,
        quick_decay_heat,
        quick_keff_calculation,
        quick_mesh_extraction,
        quick_plot_core,
        quick_plot_mesh,
        run_complete_analysis,
    )

    _CONVENIENCE_UTILS_AVAILABLE = True
except ImportError as e:
    _CONVENIENCE_UTILS_AVAILABLE = False
    # Don't warn - these are optional convenience functions

# Transient convenience functions (optional - requires safety module)
try:
    from smrforge.convenience.transients import (
        quick_transient,
        reactivity_insertion,
        decay_heat_removal,
    )

    _TRANSIENT_CONVENIENCE_AVAILABLE = True
except ImportError as e:
    _TRANSIENT_CONVENIENCE_AVAILABLE = False
    # Don't warn - safety module may not be available

# Data downloader (optional - requires requests)
try:
    from smrforge.data_downloader import (
        download_endf_data,
        download_preprocessed_library,
        COMMON_SMR_NUCLIDES,
    )
    _DATA_DOWNLOADER_AVAILABLE = True
except ImportError as e:
    _DATA_DOWNLOADER_AVAILABLE = False
    # Don't warn - requests/tqdm may not be installed

__all__ = [
    "__version__",
    "__version_info__",
    "get_version",
    "__author__",
    "constants",
]

# Add solver exports if available
if _NEUTRONICS_AVAILABLE:
    __all__.extend(["NeutronicsSolver", "MultiGroupDiffusion"])

# Add thermal exports if available
if _THERMAL_AVAILABLE:
    __all__.extend(
        [
            "ThermalHydraulics",
            "ChannelThermalHydraulics",
            "ChannelGeometry",
            "FluidProperties",
            "FlowRegime",
        ]
    )

# Add convenience exports if available
if _CONVENIENCE_AVAILABLE:
    __all__.extend(
        [
            "create_reactor",
            "list_presets",
            "get_preset",
            "quick_keff",
            "analyze_preset",
            "compare_designs",
            "SimpleReactor",
        ]
    )

# Add data downloader if available
if _DATA_DOWNLOADER_AVAILABLE:
    __all__.extend(
        [
            "download_endf_data",
            "download_preprocessed_library",
            "COMMON_SMR_NUCLIDES",
        ]
    )

# Add convenience utilities if available
if _CONVENIENCE_UTILS_AVAILABLE:
    __all__.extend(
        [
            "create_simple_core",
            "create_simple_solver",
            "create_simple_xs_data",
            "create_simple_burnup_solver",
            "create_nuclide_list",
            "get_nuclide",
            "get_material",
            "list_materials",
            "quick_burnup_calculation",
            "quick_decay_heat",
            "quick_keff_calculation",
            "quick_mesh_extraction",
            "quick_plot_core",
            "quick_plot_mesh",
            "run_complete_analysis",
        ]
    )

# Add transient convenience functions if available
if _TRANSIENT_CONVENIENCE_AVAILABLE:
    __all__.extend(
        [
            "quick_transient",
            "reactivity_insertion",
            "decay_heat_removal",
        ]
    )

# Decay heat and gamma transport (always available)
try:
    from smrforge.decay_heat import DecayHeatCalculator, DecayHeatResult
    from smrforge.gamma_transport import GammaTransportSolver, GammaTransportOptions

    __all__.extend(
        [
            "DecayHeatCalculator",
            "DecayHeatResult",
            "GammaTransportSolver",
            "GammaTransportOptions",
        ]
    )
except ImportError:
    pass

# Help system (always available)
try:
    from smrforge.help import help

    __all__.append("help")
except ImportError:
    pass

# GUI/Dashboard (optional - requires dash)
try:
    from smrforge.gui import create_app, run_server

    __all__.extend(["create_app", "run_server"])
    _GUI_AVAILABLE = True
except ImportError:
    _GUI_AVAILABLE = False
    # Don't warn - dash is optional

# Control systems (optional - requires control module)
try:
    from smrforge.control import (
        LoadFollowingController,
        PIDController,
        ReactorController,
    )
    from smrforge.control.integration import (
        create_controlled_reactivity,
        create_load_following_reactivity,
    )

    __all__.extend(
        [
            "PIDController",
            "ReactorController",
            "LoadFollowingController",
            "create_controlled_reactivity",
            "create_load_following_reactivity",
        ]
    )
    _CONTROL_AVAILABLE = True
except ImportError as e:
    _CONTROL_AVAILABLE = False
    # Don't warn - control module may not be available

# Structural mechanics (optional - requires mechanics module)
try:
    from smrforge.mechanics import (
        FuelRodMechanics,
        FuelSwelling,
        PelletCladdingInteraction,
        StressStrain,
        ThermalExpansion,
    )

    __all__.extend(
        [
            "FuelRodMechanics",
            "ThermalExpansion",
            "StressStrain",
            "PelletCladdingInteraction",
            "FuelSwelling",
        ]
    )
    _MECHANICS_AVAILABLE = True
except ImportError as e:
    _MECHANICS_AVAILABLE = False
    # Don't warn - mechanics module may not be available

# Economics (optional - requires economics module)
try:
    from smrforge.economics import (
        CapitalCostEstimator,
        CostBreakdown,
        LCOECalculator,
        OperatingCostEstimator,
    )

    __all__.extend(
        [
            "CapitalCostEstimator",
            "OperatingCostEstimator",
            "LCOECalculator",
            "CostBreakdown",
        ]
    )
    _ECONOMICS_AVAILABLE = True
except ImportError as e:
    _ECONOMICS_AVAILABLE = False
    # Don't warn - economics module may not be available

# Photon and gamma production parsers (always available)
try:
    from smrforge.core.photon_parser import ENDFPhotonParser, PhotonCrossSection
    from smrforge.core.gamma_production_parser import (
        ENDFGammaProductionParser,
        GammaProductionData,
        GammaProductionSpectrum,
    )

    __all__.extend(
        [
            "ENDFPhotonParser",
            "PhotonCrossSection",
            "ENDFGammaProductionParser",
            "GammaProductionData",
            "GammaProductionSpectrum",
        ]
    )
except ImportError:
    pass
