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
- fuel_cycle: Fuel cycle optimization and long-term simulation (✅ Implemented - optimization, material aging)

⚠️ Feature Status: See docs/status/feature-status.md for detailed status of each module.
"""

# Import version from dedicated module
from smrforge.__version__ import __version__, __version_info__, get_version

__author__ = "SMRForge Development Team"

# Core imports
from smrforge.core import constants

# Expose key classes at package level
try:
    from smrforge.neutronics import (  # Alias defined in neutronics/__init__.py
        NeutronicsSolver,
    )
    from smrforge.neutronics.solver import MultiGroupDiffusion

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
    from smrforge.convenience import (  # Factory functions; High-level class
        SimpleReactor,
        analyze_preset,
        compare_designs,
        create_reactor,
        get_constraint_set,
        get_default_output_dir,
        get_design_point,
        get_example_path,
        get_preset,
        list_constraint_sets,
        list_examples,
        list_fuel_types,
        list_nuclides,
        list_presets,
        list_reactor_types,
        list_sweepable_params,
        load_reactor,
        quick_economics,
        quick_keff,
        quick_optimize,
        quick_sweep,
        quick_uq,
        quick_validate,
        save_variant,
    )

    _CONVENIENCE_AVAILABLE = True
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
        create_nuclide_list,
        create_simple_burnup_solver,
        create_simple_core,
        create_simple_solver,
        create_simple_xs_data,
        get_material,
        get_nuclide,
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
        decay_heat_removal,
        quick_transient,
        reactivity_insertion,
    )

    _TRANSIENT_CONVENIENCE_AVAILABLE = True
except ImportError as e:
    _TRANSIENT_CONVENIENCE_AVAILABLE = False
    # Don't warn - safety module may not be available

# Data downloader (optional - requires requests)
try:
    from smrforge.data_downloader import (
        COMMON_SMR_NUCLIDES,
        download_endf_data,
        download_preprocessed_library,
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
            "load_reactor",
            "quick_validate",
            "quick_sweep",
            "quick_economics",
            "quick_optimize",
            "quick_uq",
            "list_presets",
            "list_reactor_types",
            "list_fuel_types",
            "list_constraint_sets",
            "get_constraint_set",
            "get_example_path",
            "list_examples",
            "list_nuclides",
            "list_sweepable_params",
            "get_default_output_dir",
            "get_preset",
            "quick_keff",
            "analyze_preset",
            "compare_designs",
            "get_design_point",
            "save_variant",
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
    from smrforge.gamma_transport import GammaTransportOptions, GammaTransportSolver

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

# Keep `smrforge.utils` attribute in sync with `sys.modules`.
# Some tests delete/reload `smrforge` and/or `smrforge.utils` directly, which can
# leave a stale `smrforge.utils` attribute pointing at a module object that is
# no longer the canonical `sys.modules["smrforge.utils"]`.
from ._import_compat import canonical_import, delete_global  # noqa: E402


def __getattr__(name: str):
    """
    Lazy accessors for submodules that may be deleted/reloaded in tests.

    Important: `import package.submodule` does **not** reliably overwrite an
    existing `package.submodule` attribute, even if `sys.modules` has the
    canonical module. Several tests delete `sys.modules[...]` entries, leading
    to stale attributes and `importlib.reload(package.submodule)` failures.
    """
    if name == "utils":
        return canonical_import("smrforge.utils")
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Ensure we don't keep a stale cached `utils` attribute.
delete_global(globals(), "utils")

# Help system (always available)
try:
    from smrforge.help import help, help_topics, system_info

    __all__.extend(["help", "system_info", "help_topics"])
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

# Fuel cycle optimization and long-term simulation (optional)
try:
    from smrforge.fuel_cycle import (
        FuelCycleOptimizer,
        LongTermThermalCoupling,
        MaterialAging,
        RefuelingStrategyOptimizer,
    )

    __all__.extend(
        [
            "FuelCycleOptimizer",
            "RefuelingStrategyOptimizer",
            "LongTermThermalCoupling",
            "MaterialAging",
        ]
    )
    _FUEL_CYCLE_AVAILABLE = True
except ImportError as e:
    _FUEL_CYCLE_AVAILABLE = False
    # Don't warn - fuel_cycle module may not be available

# Advanced two-phase flow models (optional - requires thermal module)
try:
    from smrforge.thermal.two_phase_advanced import (
        BoilingHeatTransfer,
        DriftFluxModel,
        TwoFluidModel,
        TwoPhaseThermalHydraulics,
    )
    from smrforge.thermal.two_phase_integration import (
        integrate_two_phase_with_thermal_hydraulics,
    )

    __all__.extend(
        [
            "DriftFluxModel",
            "TwoFluidModel",
            "BoilingHeatTransfer",
            "TwoPhaseThermalHydraulics",
            "integrate_two_phase_with_thermal_hydraulics",
        ]
    )
    _TWO_PHASE_ADVANCED_AVAILABLE = True
except ImportError as e:
    _TWO_PHASE_ADVANCED_AVAILABLE = False
    # Don't warn - two-phase advanced module may not be available

# Photon and gamma production parsers (always available)
try:
    from smrforge.core.gamma_production_parser import (
        ENDFGammaProductionParser,
        GammaProductionData,
        GammaProductionSpectrum,
    )
    from smrforge.core.photon_parser import ENDFPhotonParser, PhotonCrossSection

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
