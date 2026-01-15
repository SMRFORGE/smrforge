"""
Convenience functions for easy SMRForge usage.
Provides one-liners and simplified APIs for common tasks.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np

from .geometry.core_geometry import PrismaticCore
from .neutronics.solver import MultiGroupDiffusion

# Core imports - these are required for convenience functions to work
# If they fail, the convenience module cannot be imported (by design)
from .validation.models import (
    CrossSectionData,
    FuelType,
    ReactorSpecification,
    ReactorType,
    SolverOptions,
)

# Import presets (handle case where they might not be available)
try:
    from .presets.htgr import (
        GTMHR350,
        HTRPM200,
        DesignLibrary,
        MicroHTGR,
        ValarAtomicsReactor,
    )

    _PRESETS_AVAILABLE = True
except ImportError:
    _PRESETS_AVAILABLE = False

    # Define dummy classes for type hints
    class DesignLibrary:
        pass

    class ValarAtomicsReactor:
        pass

    class GTMHR350:
        pass

    class HTRPM200:
        pass

    class MicroHTGR:
        pass


# Global design library instance
_design_library: Optional[DesignLibrary] = None


def _get_library() -> DesignLibrary:
    """Lazy-load design library."""
    global _design_library
    if not _PRESETS_AVAILABLE:
        raise ImportError(
            "Preset designs not available. Install required dependencies."
        )
    if _design_library is None:
        _design_library = DesignLibrary()
    return _design_library


def list_presets() -> List[str]:
    """
    List all available preset reactor designs.

    Returns:
        List of preset design names as strings.

    Raises:
        ImportError: If preset designs module is not available.

    Example:
        >>> import smrforge as smr
        >>> designs = smr.list_presets()
        >>> print(designs)
        ['valar-10', 'gt-mhr-350', 'htr-pm-200', 'micro-htgr-1']
        
        >>> # Iterate over available presets
        >>> for design in smr.list_presets():
        ...     print(f"Available design: {design}")
    """
    return _get_library().list_designs()


def get_preset(name: str) -> ReactorSpecification:
    """
    Get a preset reactor design specification.

    Args:
        name: Name of preset design (use list_presets() to see available).

    Returns:
        ReactorSpecification object containing reactor design parameters.

    Raises:
        ImportError: If preset designs module is not available.
        ValueError: If the specified preset name is not found.

    Example:
        >>> spec = smr.get_preset("valar-10")
        >>> print(f"Power: {spec.power_thermal/1e6:.1f} MWth")
        >>> print(f"Fuel: {spec.fuel_type}")
        >>> print(f"Enrichment: {spec.enrichment:.2f}%")
        
        >>> # Check if preset exists before getting it
        >>> if "valar-10" in smr.list_presets():
        ...     spec = smr.get_preset("valar-10")
    """
    return _get_library().get_design(name)


def create_reactor(
    name: Optional[str] = None,
    power_mw: Optional[float] = None,
    core_height: Optional[float] = None,
    core_diameter: Optional[float] = None,
    enrichment: Optional[float] = None,
    **kwargs,
) -> "SimpleReactor":
    """
    Create a reactor with sensible defaults.

    Either provide a preset name, or custom parameters. This is the main entry
    point for creating reactor models in SMRForge.

    Args:
        name: Preset design name (e.g., "valar-10") or None for custom designs.
              Use list_presets() to see available presets.
        power_mw: Thermal power in MW (for custom designs only).
        core_height: Core height in cm (for custom designs only).
        core_diameter: Core diameter in cm (for custom designs only).
        enrichment: Fuel enrichment (0-1, for custom designs only).
        **kwargs: Additional parameters for custom designs (passed to SimpleReactor).

    Returns:
        SimpleReactor object with easy-to-use methods for analysis.

    Raises:
        ImportError: If preset designs module is not available.
        ValueError: If the specified preset name is not found or parameters are invalid.

    Examples:
        # Use preset design
        >>> reactor = smr.create_reactor("valar-10")
        >>> k_eff = reactor.solve_keff()

        # Create custom design
        >>> reactor = smr.create_reactor(
        ...     power_mw=10,
        ...     core_height=200,
        ...     core_diameter=100,
        ...     enrichment=0.195
        ... )
        >>> results = reactor.solve()
    """
    if name:
        # Use preset
        preset_class = {
            "valar-10": ValarAtomicsReactor,
            "gt-mhr-350": GTMHR350,
            "htr-pm-200": HTRPM200,
            "micro-htgr-1": MicroHTGR,
        }.get(name)

        if preset_class is None:
            raise ValueError(f"Unknown preset '{name}'. Available: {list_presets()}")

        preset = preset_class()
        return SimpleReactor.from_preset(preset)
    else:
        # Create custom reactor
        return SimpleReactor(
            power_mw=power_mw or 10.0,
            core_height=core_height or 200.0,
            core_diameter=core_diameter or 100.0,
            enrichment=enrichment or 0.195,
            **kwargs,
        )


def quick_keff(
    power_mw: float = 10.0,
    enrichment: float = 0.195,
    core_height: float = 200.0,
    core_diameter: float = 100.0,
    **kwargs,
) -> float:
    """
    Quick one-liner to get k-eff for a simple reactor.

    This is a convenience function that creates a reactor and solves for k-eff
    in a single call. Useful for quick calculations or parameter sweeps.

    Args:
        power_mw: Thermal power in MW (default: 10.0).
        enrichment: Fuel enrichment (0-1, default: 0.195 = 19.5%).
        core_height: Core height in cm (default: 200.0).
        core_diameter: Core diameter in cm (default: 100.0).
        **kwargs: Additional reactor parameters passed to create_reactor().

    Returns:
        k-eff value as a float.

    Raises:
        ImportError: If required modules are not available.
        RuntimeError: If solver fails to converge.

    Example:
        >>> import smrforge as smr
        >>> k = smr.quick_keff(power_mw=10, enrichment=0.195)
        >>> print(f"k-eff = {k:.6f}")
        
        >>> # Parameter sweep
        >>> enrichments = [0.10, 0.15, 0.20, 0.25]
        >>> for enr in enrichments:
        ...     k = smr.quick_keff(enrichment=enr)
        ...     print(f"Enrichment {enr:.2f}: k-eff = {k:.6f}")
    """
    reactor = create_reactor(
        power_mw=power_mw,
        enrichment=enrichment,
        core_height=core_height,
        core_diameter=core_diameter,
        **kwargs,
    )
    return reactor.solve_keff()


def analyze_preset(design_name: str) -> Dict:
    """
    Analyze a preset design with one line.

    Creates a reactor from a preset design and runs a full analysis,
    returning all results in a dictionary. This is the simplest way
    to analyze a preset reactor design.

    Args:
        design_name: Name of preset design (use list_presets() to see available).

    Returns:
        Dictionary with analysis results containing:
            - k_eff: Effective multiplication factor
            - flux: Neutron flux distribution
            - power: Power distribution
            - Other solver-specific results

    Raises:
        ImportError: If preset designs module is not available.
        ValueError: If the specified preset name is not found.
        RuntimeError: If solver fails to converge.

    Example:
        >>> results = smr.analyze_preset("valar-10")
        >>> print(f"k-eff: {results['k_eff']:.6f}")
        >>> print(f"Power peak: {results['power'].max():.2f} W/cm³")
        
        >>> # Compare multiple presets
        >>> for design in ["valar-10", "htr-pm-200"]:
        ...     results = smr.analyze_preset(design)
        ...     print(f"{design}: k-eff = {results['k_eff']:.6f}")
    """
    reactor = create_reactor(design_name)
    return reactor.solve()


def compare_designs(design_names: List[str]) -> Dict[str, Dict]:
    """
    Compare multiple designs side-by-side.

    Analyzes multiple preset designs and returns their results in a
    dictionary for easy comparison. Useful for design trade studies.

    Args:
        design_names: List of preset design names to compare.

    Returns:
        Dictionary mapping design names to their analysis results.
        Each value is a dictionary with k_eff, flux, power, etc.

    Raises:
        ImportError: If preset designs module is not available.
        ValueError: If any specified preset name is not found.
        RuntimeError: If solver fails to converge for any design.

    Example:
        >>> results = smr.compare_designs(["valar-10", "htr-pm-200"])
        >>> for name, data in results.items():
        ...     print(f"{name}: k-eff = {data['k_eff']:.6f}")
        
        >>> # Extract specific metrics
        >>> k_effs = {name: r['k_eff'] for name, r in results.items()}
        >>> print(f"Best k-eff: {max(k_effs, key=k_effs.get)}")
    """
    results = {}
    for name in design_names:
        try:
            results[name] = analyze_preset(name)
        except Exception as e:
            results[name] = {"error": str(e)}
    return results


class SimpleReactor:
    """
    High-level reactor wrapper for easy usage.
    Hides complexity and provides simple methods.
    """

    def __init__(
        self,
        power_mw: float = 10.0,
        core_height: float = 200.0,
        core_diameter: float = 100.0,
        enrichment: float = 0.195,
        reactor_type: ReactorType = ReactorType.PRISMATIC,
        fuel_type: FuelType = FuelType.UCO,
        **kwargs,
    ):
        """
        Create a simple reactor with sensible defaults.

        Args:
            power_mw: Thermal power in MW
            core_height: Core height in cm
            core_diameter: Core diameter in cm
            enrichment: Fuel enrichment (0-1)
            reactor_type: Type of reactor
            fuel_type: Type of fuel
            **kwargs: Additional parameters passed to ReactorSpecification
        """
        # Create specification with defaults for all required fields
        # Calculate heavy metal loading from power (rough estimate: ~10-15 kg/MWth)
        estimated_hm_loading = kwargs.get("heavy_metal_loading", power_mw * 15.0)

        self.spec = ReactorSpecification(
            name=kwargs.get("name", "Custom-Reactor"),
            reactor_type=reactor_type,
            power_thermal=power_mw * 1e6,  # Convert to W
            core_height=core_height,
            core_diameter=core_diameter,
            enrichment=enrichment,
            fuel_type=fuel_type,
            inlet_temperature=kwargs.get("inlet_temperature", 823.15),  # 550°C
            outlet_temperature=kwargs.get("outlet_temperature", 1023.15),  # 750°C
            max_fuel_temperature=kwargs.get("max_fuel_temperature", 1873.15),  # 1600°C
            primary_pressure=kwargs.get("primary_pressure", 7.0e6),
            reflector_thickness=kwargs.get("reflector_thickness", 30.0),  # 30 cm
            heavy_metal_loading=estimated_hm_loading,
            coolant_flow_rate=kwargs.get(
                "coolant_flow_rate", power_mw * 0.8
            ),  # ~0.8 kg/s per MW
            cycle_length=kwargs.get("cycle_length", 3650),  # 10 years
            capacity_factor=kwargs.get("capacity_factor", 0.95),
            target_burnup=kwargs.get("target_burnup", 150.0),  # MWd/kg
            doppler_coefficient=kwargs.get(
                "doppler_coefficient", -3.5e-5
            ),  # pcm/K typical for HTGR
            shutdown_margin=kwargs.get("shutdown_margin", 0.05),  # 5% shutdown margin
            **{
                k: v
                for k, v in kwargs.items()
                if k
                not in [
                    "name",
                    "inlet_temperature",
                    "outlet_temperature",
                    "primary_pressure",
                    "max_fuel_temperature",
                    "reflector_thickness",
                    "heavy_metal_loading",
                    "coolant_flow_rate",
                    "cycle_length",
                    "capacity_factor",
                    "target_burnup",
                    "doppler_coefficient",
                    "shutdown_margin",
                ]
            },
        )

        # Will be created lazily
        self._core: Optional[PrismaticCore] = None
        self._xs_data: Optional[CrossSectionData] = None
        self._solver: Optional[MultiGroupDiffusion] = None

    @classmethod
    def from_preset(cls, preset_reactor) -> "SimpleReactor":
        """
        Create SimpleReactor from a preset reactor object.

        Args:
            preset_reactor: Instance of ValarAtomicsReactor, GTMHR350, etc.

        Returns:
            SimpleReactor instance
        """
        instance = cls.__new__(cls)
        instance.spec = preset_reactor.spec
        instance._core = None
        instance._xs_data = None
        instance._solver = None
        instance._preset = preset_reactor  # Keep reference for methods
        return instance

    def _get_core(self) -> PrismaticCore:
        """Get or create core geometry."""
        if self._core is None:
            if hasattr(self, "_preset"):
                # Use preset's build method
                self._core = self._preset.build_core()
            else:
                # Build simple core
                self._core = PrismaticCore(name=self.spec.name)
                # Estimate geometry parameters
                n_rings = max(2, int(self.spec.core_diameter / 80))
                self._core.build_hexagonal_lattice(
                    n_rings=n_rings,
                    pitch=40.0,
                    block_height=self.spec.core_height / 4,
                    n_axial=4,
                    flat_to_flat=36.0,
                )
                self._core.generate_mesh(n_radial=15, n_axial=20)
        return self._core

    def _get_xs_data(self) -> CrossSectionData:
        """Get or create cross section data."""
        if self._xs_data is None:
            if hasattr(self, "_preset"):
                # Use preset's cross sections
                self._xs_data = self._preset.get_cross_sections()
            else:
                # Create simple 2-group cross sections
                self._xs_data = self._create_simple_xs()
        return self._xs_data

    def _create_simple_xs(self) -> CrossSectionData:
        """Create simple 2-group cross sections for quick analysis."""
        # Simplified 2-group cross sections (typical HTGR values)
        # Adjusted to produce k_eff ~ 1.0 for criticality
        return CrossSectionData(
            n_groups=2,
            n_materials=2,  # Fuel and reflector
            sigma_t=np.array(
                [
                    [0.30, 0.90],  # Fuel
                    [0.28, 0.75],  # Reflector
                ]
            ),
            sigma_a=np.array(
                [
                    [0.008, 0.12],  # Fuel
                    [0.002, 0.025],  # Reflector
                ]
            ),
            sigma_f=np.array(
                [
                    [0.006, 0.10],  # Fuel
                    [0.0, 0.0],  # Reflector
                ]
            ),
            nu_sigma_f=np.array(
                [
                    [0.008, 0.10],  # Fuel (adjusted for near-critical reactor)
                    [0.0, 0.0],  # Reflector
                ]
            ),
            sigma_s=np.array(
                [
                    [[0.29, 0.01], [0.0, 0.78]],  # Fuel scattering
                    [[0.28, 0.0], [0.0, 0.73]],  # Reflector scattering
                ]
            ),
            chi=np.array(
                [
                    [1.0, 0.0],  # Fuel fission spectrum (all fast, normalized)
                    [0.0, 0.0],  # Reflector (no fission)
                ]
            ),
            D=np.array(
                [
                    [1.0, 0.4],  # Diffusion coefficients
                    [1.2, 0.5],
                ]
            ),
        )

    def _get_solver(self) -> MultiGroupDiffusion:
        """Get or create solver."""
        if self._solver is None:
            options = SolverOptions(max_iterations=1000, tolerance=1e-6, verbose=False)
            self._solver = MultiGroupDiffusion(
                self._get_core(), self._get_xs_data(), options
            )
        return self._solver

    def solve_keff(self) -> float:
        """
        Solve for k-eff (one-liner!).

        Returns:
            k-eff value

        Example:
            >>> reactor = smr.create_reactor("valar-10")
            >>> k = reactor.solve_keff()
            >>> print(f"k-eff = {k:.6f}")
        """
        solver = self._get_solver()
        try:
            k_eff, _ = solver.solve_steady_state()
            return k_eff
        except ValueError as e:
            # If validation fails but k_eff was computed, return it anyway
            # This allows convenience functions to work with approximate cross sections
            if hasattr(solver, "k_eff") and solver.k_eff is not None:
                import warnings

                warnings.warn(
                    f"Solution validation failed, but returning k_eff = {solver.k_eff:.6f}. "
                    f"Error: {e}",
                    UserWarning,
                )
                return solver.k_eff
            raise

    def solve(self) -> Dict:
        """
        Run complete analysis (one-liner!).

        Returns:
            Dictionary with results:
            - k_eff: Effective multiplication factor
            - flux: Neutron flux distribution
            - power: Power distribution (if available)

        Example:
            >>> reactor = smr.create_reactor("valar-10")
            >>> results = reactor.solve()
            >>> print(f"k-eff: {results['k_eff']:.6f}")
        """
        solver = self._get_solver()
        k_eff, flux = solver.solve_steady_state()

        results = {
            "k_eff": k_eff,
            "flux": flux,
            "name": self.spec.name,
            "power_thermal_mw": self.spec.power_thermal / 1e6,
        }

        # Add power distribution if available
        try:
            power = solver.compute_power_distribution(self.spec.power_thermal)
            results["power_distribution"] = power
        except Exception:
            pass

        return results

    def save(self, filepath: Union[str, Path]):
        """
        Save reactor specification to JSON file.

        Args:
            filepath: Path to save file

        Example:
            >>> reactor = smr.create_reactor("valar-10")
            >>> reactor.save("my_reactor.json")
        """
        filepath = Path(filepath)
        with open(filepath, "w") as f:
            f.write(self.spec.model_dump_json(indent=2))

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "SimpleReactor":
        """
        Load reactor specification from JSON file.

        Args:
            filepath: Path to JSON file

        Returns:
            SimpleReactor instance

        Example:
            >>> reactor = smr.SimpleReactor.load("my_reactor.json")
        """
        filepath = Path(filepath)
        with open(filepath) as f:
            spec = ReactorSpecification.model_validate_json(f.read())

        instance = cls.__new__(cls)
        instance.spec = spec
        instance._core = None
        instance._xs_data = None
        instance._solver = None
        return instance
