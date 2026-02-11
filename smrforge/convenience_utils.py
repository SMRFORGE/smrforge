"""
Additional convenience utilities for SMRForge.

Provides helper functions and methods for common operations across
geometry, neutronics, burnup, visualization, and nuclear data.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

# Import core modules
try:
    from .burnup.solver import BurnupOptions, BurnupSolver
    from .core.reactor_core import NuclearDataCache, Nuclide
    from .decay_heat.calculator import DecayHeatCalculator
    from .gamma_transport.solver import GammaTransportOptions, GammaTransportSolver
    from .geometry.core_geometry import PebbleBedCore, PrismaticCore
    from .geometry.mesh_extraction import (
        extract_core_surface_mesh,
        extract_core_volume_mesh,
        extract_material_boundaries,
    )
    from .neutronics.solver import MultiGroupDiffusion
    from .validation.models import CrossSectionData, SolverOptions

    _CORE_AVAILABLE = True
except ImportError:
    _CORE_AVAILABLE = False

# Import visualization (optional)
try:
    from .visualization.geometry import plot_core_layout
    from .visualization.mesh_3d import export_mesh_to_vtk, plot_mesh3d_plotly

    _VIZ_AVAILABLE = True
except ImportError:
    _VIZ_AVAILABLE = False


# ============================================================================
# Geometry Convenience Functions
# ============================================================================


def create_simple_core(
    name: str = "SimpleCore",
    n_rings: int = 3,
    pitch: float = 40.0,
    block_height: float = 80.0,
    n_axial: int = 2,
    n_radial: int = 15,
    n_axial_mesh: int = 20,
) -> PrismaticCore:
    """
    Create a simple prismatic core with sensible defaults.

    Args:
        name: Core name
        n_rings: Number of hexagonal rings
        pitch: Block-to-block pitch [cm]
        block_height: Block height [cm]
        n_axial: Number of axial blocks
        n_radial: Number of radial mesh points
        n_axial_mesh: Number of axial mesh points

    Returns:
        PrismaticCore instance with mesh generated

    Example:
        >>> core = create_simple_core(n_rings=3, pitch=40.0)
        >>> print(f"Core has {len(core.blocks)} blocks")
    """
    if not _CORE_AVAILABLE:
        raise ImportError("Geometry module not available")

    core = PrismaticCore(name=name)
    core.build_hexagonal_lattice(
        n_rings=n_rings,
        pitch=pitch,
        block_height=block_height,
        n_axial=n_axial,
        flat_to_flat=36.0,
    )
    core.generate_mesh(n_radial=n_radial, n_axial=n_axial_mesh)
    return core


def quick_mesh_extraction(
    core: Union[PrismaticCore, PebbleBedCore],
    mesh_type: str = "volume",
    include_channels: bool = False,
) -> "Mesh3D":
    """
    Quick mesh extraction from core geometry.

    Args:
        core: PrismaticCore or PebbleBedCore instance
        mesh_type: Type of mesh - "volume" or "surface"
        include_channels: Whether to include fuel/coolant channels

    Returns:
        Mesh3D instance

    Example:
        >>> core = create_simple_core()
        >>> mesh = quick_mesh_extraction(core, mesh_type="volume")
        >>> print(f"Mesh has {mesh.n_vertices} vertices")
    """
    if not _CORE_AVAILABLE:
        raise ImportError("Geometry module not available")

    if mesh_type == "volume":
        return extract_core_volume_mesh(core, include_channels=include_channels)
    elif mesh_type == "surface":
        return extract_core_surface_mesh(core)
    else:
        raise ValueError(f"Unknown mesh_type: {mesh_type}. Use 'volume' or 'surface'")


# ============================================================================
# Neutronics Convenience Functions
# ============================================================================


def create_simple_solver(
    core: Optional[PrismaticCore] = None,
    xs_data: Optional[CrossSectionData] = None,
    n_groups: int = 2,
    max_iterations: int = 1000,
    tolerance: float = 1e-6,
    verbose: bool = False,
    skip_validation: bool = True,
) -> MultiGroupDiffusion:
    """
    Create a neutronics solver with sensible defaults.

    Args:
        core: PrismaticCore instance (creates simple core if None)
        xs_data: CrossSectionData (creates simple 2-group if None)
        n_groups: Number of energy groups (if creating xs_data)
        max_iterations: Maximum solver iterations
        tolerance: Solver tolerance
        verbose: Whether to print solver progress

    Returns:
        MultiGroupDiffusion solver instance

    Example:
        >>> solver = create_simple_solver()
        >>> k_eff, flux = solver.solve_steady_state()
    """
    if not _CORE_AVAILABLE:
        raise ImportError("Neutronics module not available")

    if core is None:
        core = create_simple_core()

    if xs_data is None:
        xs_data = create_simple_xs_data(n_groups=n_groups)

    options = SolverOptions(
        max_iterations=max_iterations,
        tolerance=tolerance,
        verbose=verbose,
        skip_solution_validation=skip_validation,
    )

    return MultiGroupDiffusion(core, xs_data, options)


def create_simple_xs_data(
    n_groups: int = 2,
    n_materials: int = 2,
    k_eff_target: float = 1.0,
) -> CrossSectionData:
    """
    Create simple cross-section data with sensible defaults.

    Args:
        n_groups: Number of energy groups
        n_materials: Number of materials (fuel and reflector)
        k_eff_target: Target k-eff (adjusts cross-sections)

    Returns:
        CrossSectionData instance

    Example:
        >>> xs = create_simple_xs_data(n_groups=2)
        >>> print(f"Cross-sections: {xs.n_groups} groups, {xs.n_materials} materials")
    """
    if not _CORE_AVAILABLE:
        raise ImportError("Validation module not available")

    # Base 2-group cross-sections (typical HTGR values)
    if n_groups == 2:
        # Adjust nu_sigma_f to target k_eff
        nu_sigma_f_scale = k_eff_target

        return CrossSectionData(
            n_groups=2,
            n_materials=n_materials,
            sigma_t=np.array(
                [
                    [0.30, 0.90],  # Fuel
                    [0.28, 0.75],  # Reflector
                ]
            )[:n_materials],
            sigma_a=np.array(
                [
                    [0.008, 0.12],  # Fuel
                    [0.002, 0.025],  # Reflector
                ]
            )[:n_materials],
            sigma_f=np.array(
                [
                    [0.006, 0.10],  # Fuel
                    [0.0, 0.0],  # Reflector
                ]
            )[:n_materials],
            nu_sigma_f=np.array(
                [
                    [0.008 * nu_sigma_f_scale, 0.10 * nu_sigma_f_scale],  # Fuel
                    [0.0, 0.0],  # Reflector
                ]
            )[:n_materials],
            sigma_s=np.array(
                [
                    [[0.29, 0.01], [0.0, 0.78]],  # Fuel scattering
                    [[0.28, 0.0], [0.0, 0.73]],  # Reflector scattering
                ]
            )[:n_materials],
            chi=np.array(
                [
                    [1.0, 0.0],  # Fuel fission spectrum
                    [0.0, 0.0],  # Reflector
                ]
            )[:n_materials],
            D=np.array(
                [
                    [1.0, 0.4],  # Fuel diffusion
                    [1.2, 0.5],  # Reflector diffusion
                ]
            )[:n_materials],
        )
    else:
        # For other group structures, create placeholder
        # In practice, users should provide real cross-sections
        raise ValueError(
            f"Simple cross-sections only available for 2 groups. "
            f"Requested {n_groups} groups. Provide xs_data directly."
        )


def quick_keff_calculation(
    core: Optional[PrismaticCore] = None,
    xs_data: Optional[CrossSectionData] = None,
    skip_validation: bool = True,
    **solver_kwargs,
) -> Tuple[float, np.ndarray]:
    """
    Quick k-eff calculation with minimal setup.

    Args:
        core: PrismaticCore instance (creates if None)
        xs_data: CrossSectionData (creates if None)
        skip_validation: Whether to skip solution validation (default: True for convenience)
        **solver_kwargs: Additional arguments for solver creation

    Returns:
        Tuple of (k_eff, flux)

    Example:
        >>> k_eff, flux = quick_keff_calculation()
        >>> print(f"k-eff = {k_eff:.6f}")
    """
    # Add skip_validation to solver options if not provided
    if "options" not in solver_kwargs:
        solver_kwargs.setdefault("verbose", False)

    solver = create_simple_solver(core=core, xs_data=xs_data, **solver_kwargs)

    # Create options with skip_validation if needed
    if skip_validation:
        options = SolverOptions(
            max_iterations=solver_kwargs.get("max_iterations", 1000),
            tolerance=solver_kwargs.get("tolerance", 1e-6),
            verbose=solver_kwargs.get("verbose", False),
            skip_solution_validation=True,
        )
        # Update solver options
        solver.options = options

    return solver.solve_steady_state()


# ============================================================================
# Burnup Convenience Functions
# ============================================================================


def create_simple_burnup_solver(
    neutronics_solver: Optional[MultiGroupDiffusion] = None,
    time_steps_days: Optional[List[float]] = None,
    power_density: float = 1e6,
    initial_enrichment: float = 0.195,
    cache: Optional[NuclearDataCache] = None,
) -> BurnupSolver:
    """
    Create a burnup solver with sensible defaults.

    Args:
        neutronics_solver: MultiGroupDiffusion solver (creates if None)
        time_steps_days: List of time points **[days]** (default: [0, 365, 730]).
                         **Note:** Parameter name is explicitly `time_steps_days` to make
                         the unit clear. This is passed to `BurnupOptions.time_steps` which
                         also uses days. For consistency, see `BurnupOptions` documentation.
        power_density: Power density **[W/cm³]** (default: 1e6 W/cm³ = 1 MW/cm³)
        initial_enrichment: Initial U-235 enrichment (fraction, default: 0.195 = 19.5%)
        cache: NuclearDataCache instance (creates if None)

    Returns:
        BurnupSolver instance

    Example:
        >>> # Create with default time steps (0, 1 year, 2 years in days)
        >>> burnup = create_simple_burnup_solver()
        >>> inventory = burnup.solve()

        >>> # Create with custom time steps (in days)
        >>> burnup = create_simple_burnup_solver(
        ...     time_steps_days=[0, 90, 180, 365, 730],  # 0, 3, 6, 12, 24 months
        ...     power_density=1e6  # 1 MW/cm³
        ... )
    """
    if not _CORE_AVAILABLE:
        raise ImportError("Burnup module not available")

    if neutronics_solver is None:
        neutronics_solver = create_simple_solver()

    if time_steps_days is None:
        time_steps_days = [0.0, 365.0, 730.0]  # 0, 1 year, 2 years

    if cache is None:
        cache = NuclearDataCache()

    options = BurnupOptions(
        time_steps=time_steps_days,
        power_density=power_density,
        initial_enrichment=initial_enrichment,
    )

    return BurnupSolver(neutronics_solver, options, cache=cache)


def quick_burnup_calculation(
    time_days: float = 365.0,
    power_density: float = 1e6,
    initial_enrichment: float = 0.195,
    **kwargs,
) -> "NuclideInventory":
    """
    Quick burnup calculation for a single time point.

    Args:
        time_days: Burnup time [days]
        power_density: Power density [W/cm³]
        initial_enrichment: Initial U-235 enrichment
        **kwargs: Additional arguments for solver creation

    Returns:
        NuclideInventory instance

    Example:
        >>> inventory = quick_burnup_calculation(time_days=365.0)
        >>> u235 = Nuclide(Z=92, A=235)
        >>> conc = inventory.get_concentration(u235)
    """
    burnup_solver = create_simple_burnup_solver(
        time_steps_days=[0.0, time_days],
        power_density=power_density,
        initial_enrichment=initial_enrichment,
        **kwargs,
    )
    return burnup_solver.solve()


# ============================================================================
# Nuclear Data Convenience Functions
# ============================================================================


def get_nuclide(name: str) -> Nuclide:
    """
    Get Nuclide instance from name string.

    Args:
        name: Nuclide name (e.g., "U235", "Pu239", "Cs137")

    Returns:
        Nuclide instance

    Example:
        >>> u235 = get_nuclide("U235")
        >>> print(u235.zam)  # 922350
    """
    if not _CORE_AVAILABLE:
        raise ImportError("Core module not available")

    # Parse nuclide name (simple implementation)
    # Format: "U235", "Pu239m1", "Cs137"
    name = name.strip()

    # Common nuclide mapping
    nuclide_map = {
        "U235": Nuclide(Z=92, A=235),
        "U238": Nuclide(Z=92, A=238),
        "Pu239": Nuclide(Z=94, A=239),
        "Pu240": Nuclide(Z=94, A=240),
        "Pu241": Nuclide(Z=94, A=241),
        "Cs137": Nuclide(Z=55, A=137),
        "Sr90": Nuclide(Z=38, A=90),
        "Xe135": Nuclide(Z=54, A=135),
        "I135": Nuclide(Z=53, A=135),
        "Nd144": Nuclide(Z=60, A=144),
        "Ba140": Nuclide(Z=56, A=140),
    }

    if name in nuclide_map:
        return nuclide_map[name]

    # Try to parse (simple implementation)
    # This is a basic parser - could be enhanced
    import re

    match = re.match(r"([A-Za-z]+)(\d+)(m\d+)?", name)
    if match:
        element = match.group(1)
        A = int(match.group(2))
        m = int(match.group(3)[1:]) if match.group(3) else 0

        # Element to Z mapping (common elements)
        element_map = {
            "H": 1,
            "He": 2,
            "Li": 3,
            "Be": 4,
            "B": 5,
            "C": 6,
            "N": 7,
            "O": 8,
            "F": 9,
            "Ne": 10,
            "Na": 11,
            "Mg": 12,
            "Al": 13,
            "Si": 14,
            "P": 15,
            "S": 16,
            "Cl": 17,
            "Ar": 18,
            "K": 19,
            "Ca": 20,
            "Fe": 26,
            "Ni": 28,
            "Cu": 29,
            "Zn": 30,
            "Sr": 38,
            "I": 53,
            "Xe": 54,
            "Cs": 55,
            "Ba": 56,
            "La": 57,
            "Ce": 58,
            "Pr": 59,
            "Nd": 60,
            "Pm": 61,
            "Sm": 62,
            "Eu": 63,
            "Gd": 64,
            "U": 92,
            "Np": 93,
            "Pu": 94,
            "Am": 95,
            "Cm": 96,
        }

        if element in element_map:
            return Nuclide(Z=element_map[element], A=A, m=m)

    raise ValueError(f"Could not parse nuclide name: {name}")


def create_nuclide_list(names: List[str]) -> List[Nuclide]:
    """
    Create list of Nuclide instances from name strings.

    Args:
        names: List of nuclide names

    Returns:
        List of Nuclide instances

    Example:
        >>> nuclides = create_nuclide_list(["U235", "U238", "Pu239"])
        >>> print(f"Created {len(nuclides)} nuclides")
    """
    return [get_nuclide(name) for name in names]


# ============================================================================
# Decay Heat Convenience Functions
# ============================================================================


def quick_decay_heat(
    nuclides: Dict[str, float],
    time_seconds: float = 86400.0,
    cache: Optional[NuclearDataCache] = None,
) -> float:
    """
    Quick decay heat calculation for a nuclide inventory.

    Args:
        nuclides: Dictionary mapping nuclide names to concentrations [atoms/cm³]
        time_seconds: Time after shutdown [seconds]
        cache: NuclearDataCache instance (creates if None)

    Returns:
        Decay heat [W]

    Example:
        >>> heat = quick_decay_heat({"U235": 1e20, "Cs137": 1e19}, time_seconds=86400)
        >>> print(f"Decay heat: {heat:.2e} W")
    """
    if not _CORE_AVAILABLE:
        raise ImportError("Decay heat module not available")

    if cache is None:
        cache = NuclearDataCache()

    calculator = DecayHeatCalculator(cache=cache)

    # Convert nuclide names to Nuclide instances
    concentrations = {get_nuclide(name): conc for name, conc in nuclides.items()}

    times = np.array([0.0, time_seconds])
    result = calculator.calculate_decay_heat(concentrations, times)

    return result.get_decay_heat_at_time(time_seconds)


# ============================================================================
# Visualization Convenience Functions
# ============================================================================


def quick_plot_core(
    core: Union[PrismaticCore, PebbleBedCore],
    view: str = "xy",
    show: bool = True,
    **kwargs,
):
    """
    Quick plot of core layout.

    Args:
        core: PrismaticCore or PebbleBedCore instance
        view: View direction - "xy", "xz", or "yz"
        show: Whether to display plot
        **kwargs: Additional arguments for plot_core_layout

    Example:
        >>> core = create_simple_core()
        >>> quick_plot_core(core, view="xy")
    """
    if not _VIZ_AVAILABLE:
        raise ImportError(
            "Visualization module not available. Install with: pip install smrforge[viz]"
        )

    fig, ax = plot_core_layout(core, view=view, **kwargs)
    if show:
        import matplotlib.pyplot as plt

        plt.show()
    return fig, ax


def quick_plot_mesh(
    mesh: "Mesh3D",
    color_by: Optional[str] = None,
    show: bool = True,
    **kwargs,
):
    """
    Quick 3D mesh plot.

    Args:
        mesh: Mesh3D instance
        color_by: Field to color by (e.g., "material", "flux")
        show: Whether to display plot
        **kwargs: Additional arguments for plot_mesh3d_plotly

    Example:
        >>> core = create_simple_core()
        >>> mesh = quick_mesh_extraction(core)
        >>> quick_plot_mesh(mesh, color_by="material")
    """
    if not _VIZ_AVAILABLE:
        raise ImportError(
            "Visualization module not available. Install with: pip install smrforge[viz]"
        )

    fig = plot_mesh3d_plotly(mesh, color_by=color_by, **kwargs)
    if show:
        fig.show()
    return fig


# ============================================================================
# Material Convenience Functions
# ============================================================================


def get_material(name: str) -> Any:
    """
    Get material from MaterialDatabase by name.

    Args:
        name: Material name (e.g., "graphite_IG-110", "helium", "triso_uco")

    Returns:
        Material instance

    Example:
        >>> graphite = get_material("graphite_IG-110")
        >>> k = graphite.thermal_conductivity(1200.0)
    """
    if not _CORE_AVAILABLE:
        raise ImportError("Materials module not available")

    from .core.materials_database import MaterialDatabase

    db = MaterialDatabase()
    return db.get(name)


def list_materials(category: Optional[str] = None) -> List[str]:
    """
    List available materials, optionally filtered by category.

    Args:
        category: Optional category filter ("moderator", "coolant", "fuel", "structural")

    Returns:
        List of material names

    Example:
        >>> materials = list_materials(category="moderator")
        >>> print(materials)  # ['graphite_IG-110', 'graphite_H-451', ...]
    """
    if not _CORE_AVAILABLE:
        raise ImportError("Materials module not available")

    from .core.materials_database import MaterialDatabase

    db = MaterialDatabase()
    return db.list_materials(category=category)


# ============================================================================
# Class Extension Convenience Methods
# ============================================================================
# These add convenience methods to existing classes via monkey-patching
# (only if not already present)


def _add_convenience_methods() -> None:
    """Add convenience methods to existing classes."""
    if not _CORE_AVAILABLE:
        return

    # Add convenience method to PrismaticCore
    if hasattr(PrismaticCore, "quick_setup"):
        return  # Already added

    def quick_setup(
        self,
        n_rings: int = 3,
        pitch: float = 40.0,
        block_height: float = 80.0,
        n_axial: int = 2,
        n_radial: int = 15,
        n_axial_mesh: int = 20,
    ) -> None:
        """
        Quick setup of core geometry and mesh.

        Args:
            n_rings: Number of hexagonal rings
            pitch: Block-to-block pitch [cm]
            block_height: Block height [cm]
            n_axial: Number of axial blocks
            n_radial: Number of radial mesh points
            n_axial_mesh: Number of axial mesh points

        Example:
            >>> core = PrismaticCore("MyCore")
            >>> core.quick_setup(n_rings=3, pitch=40.0)
        """
        self.build_hexagonal_lattice(
            n_rings=n_rings,
            pitch=pitch,
            block_height=block_height,
            n_axial=n_axial,
            flat_to_flat=36.0,
        )
        self.generate_mesh(n_radial=n_radial, n_axial=n_axial_mesh)

    PrismaticCore.quick_setup = quick_setup

    # Add convenience method to MultiGroupDiffusion
    if hasattr(MultiGroupDiffusion, "quick_solve"):
        return  # Already added

    def quick_solve(
        self, return_power: bool = False
    ) -> Union[float, Tuple[float, np.ndarray], Dict]:
        """
        Quick solve for k-eff, optionally returning flux and power.

        Args:
            return_power: Whether to return power distribution

        Returns:
            If return_power=False: k_eff
            If return_power=True: (k_eff, flux, power) or dict with all results

        Example:
            >>> solver = create_simple_solver()
            >>> k_eff = solver.quick_solve()
            >>> results = solver.quick_solve(return_power=True)
        """
        k_eff, flux = self.solve_steady_state()

        if return_power:
            # Try to get power (requires power_thermal attribute)
            if hasattr(self, "geometry") and hasattr(self.geometry, "spec"):
                power_thermal = getattr(self.geometry.spec, "power_thermal", 10e6)
            else:
                power_thermal = 10e6  # Default 10 MW

            power = self.compute_power_distribution(power_thermal)
            return {
                "k_eff": k_eff,
                "flux": flux,
                "power": power,
                "peak_flux": np.max(flux),
                "peak_power": np.max(power),
            }
        return k_eff

    MultiGroupDiffusion.quick_solve = quick_solve


# Auto-add convenience methods on import
_add_convenience_methods()


# ============================================================================
# Complete Workflow Convenience Functions
# ============================================================================


def run_complete_analysis(
    core: Optional[PrismaticCore] = None,
    xs_data: Optional[CrossSectionData] = None,
    power_mw: float = 10.0,
    include_burnup: bool = False,
    burnup_time_days: float = 365.0,
) -> Dict:
    """
    Run complete reactor analysis workflow.

    Args:
        core: PrismaticCore instance (creates if None)
        xs_data: CrossSectionData (creates if None)
        power_mw: Thermal power [MW]
        include_burnup: Whether to include burnup calculation
        burnup_time_days: Burnup time [days] if include_burnup=True

    Returns:
        Dictionary with analysis results

    Example:
        >>> results = run_complete_analysis(power_mw=10.0)
        >>> print(f"k-eff: {results['k_eff']:.6f}")
        >>> print(f"Peak flux: {results['peak_flux']:.2e}")
    """
    if not _CORE_AVAILABLE:
        raise ImportError("Core modules not available")

    # Create solver
    solver = create_simple_solver(core=core, xs_data=xs_data)

    # Solve neutronics
    k_eff, flux = solver.solve_steady_state()

    # Compute power distribution
    power = solver.compute_power_distribution(power_mw * 1e6)

    results = {
        "k_eff": k_eff,
        "flux": flux,
        "power_distribution": power,
        "peak_flux": np.max(flux),
        "peak_power_density": np.max(power),
        "avg_power_density": np.mean(power),
    }

    # Add burnup if requested
    if include_burnup:
        burnup_solver = create_simple_burnup_solver(
            neutronics_solver=solver,
            time_steps_days=[0.0, burnup_time_days],
        )
        inventory = burnup_solver.solve()
        results["burnup_inventory"] = inventory
        results["burnup_time_days"] = burnup_time_days

    return results
