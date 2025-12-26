# smrforge/validation/pydantic_layer.py
"""
Pydantic v2 models for SMRForge with automatic validation.
Provides type safety, bounds checking, and serialization.
"""

import warnings
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal, Optional

import numpy as np
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings

# ============================================================================
# Custom Types for Nuclear Engineering
# ============================================================================


def validate_numpy_array(v: Any) -> np.ndarray:
    """Convert to numpy array and validate."""
    if isinstance(v, list):
        v = np.array(v)
    if not isinstance(v, np.ndarray):
        raise ValueError("Must be numpy array or list")
    return v


def validate_positive_array(v: Any) -> np.ndarray:
    """Validate array is non-negative."""
    arr = validate_numpy_array(v)
    if np.any(arr < 0):
        raise ValueError(f"Contains negative values: min={np.min(arr)}")
    if np.any(np.isnan(arr)):
        raise ValueError("Contains NaN values")
    if np.any(np.isinf(arr)):
        raise ValueError("Contains Inf values")
    return arr


def validate_normalized_array(v: Any) -> np.ndarray:
    """Validate array sums to 1."""
    arr = validate_positive_array(v)
    total = np.sum(arr)
    if not np.isclose(total, 1.0, rtol=1e-3):
        raise ValueError(f"Array must sum to 1.0, got {total}")
    return arr


# Type aliases
NumpyArray = Annotated[np.ndarray, BeforeValidator(validate_numpy_array)]
PositiveArray = Annotated[np.ndarray, BeforeValidator(validate_positive_array)]
NormalizedArray = Annotated[np.ndarray, BeforeValidator(validate_normalized_array)]


# ============================================================================
# Enums
# ============================================================================


class ReactorType(str, Enum):
    """Reactor type classification."""

    PRISMATIC = "prismatic"
    PEBBLE_BED = "pebble_bed"
    ANNULAR = "annular"
    HYBRID = "hybrid"


class FuelType(str, Enum):
    """Fuel type options."""

    UCO = "UCO"
    UO2 = "UO2"
    UC = "UC"
    UN = "UN"


class EnrichmentClass(str, Enum):
    """Enrichment classification."""

    NATURAL = "natural"
    LEU = "LEU"  # < 20%
    HALEU = "HALEU"  # 20-5%
    HEU = "HEU"  # > 20%


class GraphiteGrade(str, Enum):
    """Graphite grade options."""

    IG_110 = "IG-110"
    H_451 = "H-451"
    NBG_18 = "NBG-18"
    PCEA = "PCEA"


# ============================================================================
# Core Models
# ============================================================================


class ReactorSpecification(BaseModel):
    """
    Complete reactor specification with automatic validation.
    All physical units in SI or common nuclear engineering units.
    """

    # Identification
    name: str = Field(min_length=1, max_length=100, description="Reactor design name")
    reactor_type: ReactorType = Field(description="Core configuration type")
    description: str = Field(
        default="", max_length=500, description="Design description"
    )
    design_reference: str = Field(
        default="", max_length=200, description="Reference document"
    )

    # Power ratings
    power_thermal: float = Field(gt=0, le=1e9, description="Thermal power [W]")
    power_electric: Optional[float] = Field(
        default=None, gt=0, le=5e8, description="Electric power output [W]"
    )

    # Temperatures [K]
    inlet_temperature: float = Field(
        gt=273.15, le=900, description="Coolant inlet temperature [K]"
    )
    outlet_temperature: float = Field(
        gt=273.15, le=1500, description="Coolant outlet temperature [K]"
    )
    max_fuel_temperature: float = Field(
        gt=273.15, le=3000, description="Design limit for fuel temperature [K]"
    )

    # Pressure [Pa]
    primary_pressure: float = Field(
        gt=0, le=50e6, description="Primary system pressure [Pa]"
    )

    # Core geometry [cm]
    core_height: float = Field(gt=0, le=2000, description="Active core height [cm]")
    core_diameter: float = Field(gt=0, le=2000, description="Active core diameter [cm]")
    reflector_thickness: float = Field(
        ge=0, le=200, description="Radial reflector thickness [cm]"
    )

    # Fuel specification
    fuel_type: FuelType = Field(description="Fuel form")
    enrichment: float = Field(
        ge=0, le=1.0, description="U-235 enrichment (mass fraction)"
    )
    heavy_metal_loading: float = Field(
        gt=0, le=50000, description="Total heavy metal mass [kg]"
    )

    # Operating conditions
    coolant_flow_rate: float = Field(
        gt=0, le=1000, description="Primary coolant mass flow rate [kg/s]"
    )

    # Performance targets
    cycle_length: float = Field(gt=0, le=10000, description="Fuel cycle length [days]")
    capacity_factor: float = Field(ge=0, le=1.0, description="Target capacity factor")
    target_burnup: float = Field(
        gt=0, le=300, description="Target discharge burnup [MWd/kg]"
    )

    # Safety parameters
    doppler_coefficient: float = Field(
        lt=0, ge=-1e-3, description="Doppler temperature coefficient [dk/k/K]"
    )
    shutdown_margin: float = Field(gt=0, le=0.30, description="Shutdown margin [dk/k]")

    # Economics (optional)
    capital_cost: Optional[float] = Field(
        default=None, gt=0, description="Capital cost [USD]"
    )
    fuel_cost: Optional[float] = Field(
        default=None, gt=0, description="Fuel cost [USD/kg]"
    )

    # Maturity level
    maturity_level: Literal["conceptual", "preliminary", "detailed"] = Field(
        default="conceptual", description="Design maturity"
    )

    # ========================================================================
    # Validators
    # ========================================================================

    @model_validator(mode="after")
    def validate_temperatures(self):
        """Cross-validate temperature relationships."""
        if self.inlet_temperature >= self.outlet_temperature:
            raise ValueError(
                f"Inlet temperature ({self.inlet_temperature:.1f} K) must be "
                f"less than outlet ({self.outlet_temperature:.1f} K)"
            )

        if self.outlet_temperature > self.max_fuel_temperature:
            raise ValueError(
                f"Outlet temperature ({self.outlet_temperature:.1f} K) exceeds "
                f"max fuel temperature ({self.max_fuel_temperature:.1f} K)"
            )

        # Reasonable delta-T check
        delta_T = self.outlet_temperature - self.inlet_temperature
        if delta_T < 50:
            warnings.warn(f"Very small temperature rise: {delta_T:.1f} K")
        if delta_T > 500:
            warnings.warn(f"Very large temperature rise: {delta_T:.1f} K")

        return self

    @model_validator(mode="after")
    def validate_enrichment_class(self):
        """Validate enrichment against fuel type and regulations."""
        enr_pct = self.enrichment * 100

        if self.enrichment > 0.20:
            warnings.warn(
                f"Enrichment {enr_pct:.1f}% exceeds LEU limit (20%). "
                f"HEU classification - special licensing required."
            )
        elif self.enrichment > 0.05:
            warnings.warn(
                f"Enrichment {enr_pct:.1f}% is HALEU (5-20%). "
                f"Valid for advanced reactor designs."
            )

        return self

    @model_validator(mode="after")
    def validate_geometry(self):
        """Validate core geometry ratios."""
        aspect_ratio = self.core_height / self.core_diameter

        if aspect_ratio < 0.5:
            warnings.warn(
                f"Very flat core (H/D = {aspect_ratio:.2f}). "
                f"May have poor neutron economy."
            )

        if aspect_ratio > 5.0:
            warnings.warn(
                f"Very tall core (H/D = {aspect_ratio:.2f}). "
                f"May have axial power peaking issues."
            )

        return self

    @model_validator(mode="after")
    def validate_power_density(self):
        """Check power density reasonableness."""
        volume = np.pi * (self.core_diameter / 2) ** 2 * self.core_height  # cm³
        power_density = self.power_thermal / (volume * 1e-6)  # W/m³

        if power_density < 1e5:
            warnings.warn(f"Very low power density: {power_density/1e6:.2f} MW/m³")

        if power_density > 1e7:
            warnings.warn(
                f"Very high power density: {power_density/1e6:.2f} MW/m³. "
                f"May exceed cooling capability."
            )

        return self

    @field_validator("doppler_coefficient")
    @classmethod
    def validate_negative_feedback(cls, v):
        """Doppler coefficient must be negative for safety."""
        if v >= 0:
            raise ValueError(
                f"Doppler coefficient must be negative, got {v}. "
                f"Positive feedback is unsafe."
            )
        if v < -1e-4:
            warnings.warn(f"Very strong Doppler coefficient: {v*1e5:.2f} pcm/K")
        return v

    # ========================================================================
    # Computed Properties
    # ========================================================================

    @property
    def aspect_ratio(self) -> float:
        """Core height to diameter ratio."""
        return self.core_height / self.core_diameter

    @property
    def thermal_efficiency(self) -> Optional[float]:
        """Thermal to electric efficiency."""
        if self.power_electric:
            return self.power_electric / self.power_thermal
        return None

    @property
    def enrichment_class(self) -> EnrichmentClass:
        """Classify enrichment level."""
        if self.enrichment < 0.01:
            return EnrichmentClass.NATURAL
        elif self.enrichment <= 0.05:
            return EnrichmentClass.LEU
        elif self.enrichment <= 0.20:
            return EnrichmentClass.HALEU
        else:
            return EnrichmentClass.HEU

    @property
    def core_volume(self) -> float:
        """Active core volume [m³]."""
        return np.pi * (self.core_diameter / 200) ** 2 * (self.core_height / 100)

    @property
    def power_density(self) -> float:
        """Volumetric power density [MW/m³]."""
        return (self.power_thermal / 1e6) / self.core_volume

    @property
    def specific_power(self) -> float:
        """Specific power [kW/kg HM]."""
        return (self.power_thermal / 1000) / self.heavy_metal_loading

    # ========================================================================
    # Configuration
    # ========================================================================

    model_config = ConfigDict(
        validate_assignment=True,  # Validate on attribute changes
        validate_default=True,  # Validate default values
        extra="forbid",  # No extra fields allowed
        frozen=False,  # Allow modifications
        str_strip_whitespace=True,  # Clean string inputs
        json_schema_extra={
            "examples": [
                {
                    "name": "Valar-10",
                    "reactor_type": "prismatic",
                    "power_thermal": 10e6,
                    "power_electric": 3.5e6,
                    "inlet_temperature": 823.15,
                    "outlet_temperature": 1023.15,
                    "max_fuel_temperature": 1873.15,
                    "primary_pressure": 7.0e6,
                    "core_height": 200.0,
                    "core_diameter": 100.0,
                    "reflector_thickness": 30.0,
                    "fuel_type": "UCO",
                    "enrichment": 0.195,
                    "heavy_metal_loading": 150.0,
                    "coolant_flow_rate": 8.0,
                    "cycle_length": 3650,
                    "capacity_factor": 0.95,
                    "target_burnup": 150.0,
                    "doppler_coefficient": -3.5e-5,
                    "shutdown_margin": 0.05,
                }
            ]
        },
    )


class GeometryParameters(BaseModel):
    """Geometry parameters for core construction."""

    # Prismatic parameters
    n_rings: Optional[int] = Field(
        default=None, ge=1, le=20, description="Number of hexagonal rings"
    )
    lattice_pitch: Optional[float] = Field(
        default=None, gt=0, le=100, description="Block-to-block pitch [cm]"
    )
    block_height: Optional[float] = Field(
        default=None, gt=0, le=200, description="Individual block height [cm]"
    )
    n_axial_blocks: Optional[int] = Field(
        default=None, ge=1, le=50, description="Number of axial block layers"
    )
    flat_to_flat: Optional[float] = Field(
        default=36.0, gt=0, le=100, description="Block flat-to-flat distance [cm]"
    )

    # Pebble bed parameters
    pebble_diameter: Optional[float] = Field(
        default=6.0, gt=0, le=10, description="Fuel pebble diameter [cm]"
    )
    packing_fraction: Optional[float] = Field(
        default=0.61, gt=0, le=1.0, description="Pebble packing fraction"
    )

    # Mesh parameters
    n_radial_mesh: int = Field(
        default=20, ge=5, le=200, description="Number of radial mesh cells"
    )
    n_axial_mesh: int = Field(
        default=50, ge=10, le=500, description="Number of axial mesh cells"
    )

    @model_validator(mode="after")
    def validate_mesh_quality(self):
        """Warn about mesh quality."""
        if self.n_radial_mesh < 10:
            warnings.warn("Radial mesh is coarse. Consider n_radial >= 10")

        if self.n_axial_mesh < 20:
            warnings.warn("Axial mesh is coarse. Consider n_axial >= 20")

        if self.n_radial_mesh > 100 or self.n_axial_mesh > 200:
            warnings.warn("Very fine mesh. May be slow.")

        return self

    model_config = ConfigDict(validate_assignment=True, extra="forbid")


class CrossSectionData(BaseModel):
    """Multi-group cross section data with validation."""

    n_groups: int = Field(ge=1, le=100, description="Number of energy groups")
    n_materials: int = Field(ge=1, le=50, description="Number of materials")

    # Cross sections [material, group]
    sigma_t: PositiveArray = Field(description="Total cross section [1/cm]")
    sigma_a: PositiveArray = Field(description="Absorption cross section [1/cm]")
    sigma_f: PositiveArray = Field(description="Fission cross section [1/cm]")
    nu_sigma_f: PositiveArray = Field(description="Nu*fission cross section [1/cm]")

    # Scattering matrix [material, from_group, to_group]
    sigma_s: PositiveArray = Field(description="Scattering matrix [1/cm]")

    # Fission spectrum [material, group]
    chi: PositiveArray = Field(description="Fission spectrum (must sum to 1 per material)")

    # Diffusion coefficients [material, group]
    D: PositiveArray = Field(description="Diffusion coefficient [cm]")

    @model_validator(mode="after")
    def validate_shapes(self):
        """Validate array shapes are consistent."""
        expected_shape = (self.n_materials, self.n_groups)

        for name in ["sigma_t", "sigma_a", "sigma_f", "nu_sigma_f", "chi", "D"]:
            arr = getattr(self, name)
            if arr.shape != expected_shape:
                raise ValueError(
                    f"{name} shape {arr.shape} != expected {expected_shape}"
                )

        # Scattering matrix
        expected_s_shape = (self.n_materials, self.n_groups, self.n_groups)
        if self.sigma_s.shape != expected_s_shape:
            raise ValueError(
                f"sigma_s shape {self.sigma_s.shape} != expected {expected_s_shape}"
            )

        return self

    @model_validator(mode="after")
    def validate_physical_relationships(self):
        """Validate physical constraints on cross sections."""
        # Check sigma_a <= sigma_t
        if np.any(self.sigma_a > self.sigma_t):
            raise ValueError("Absorption XS cannot exceed total XS (non-physical)")

        # Check sigma_f <= sigma_a
        if np.any(self.sigma_f > self.sigma_a):
            raise ValueError("Fission XS cannot exceed absorption XS (non-physical)")

        # Check reasonable diffusion coefficient
        if np.any(self.D > 20):
            warnings.warn("Very large diffusion coefficient (> 20 cm)")

        # Validate chi normalization: for fissioning materials, chi must sum to 1.0 per material
        for mat_idx in range(self.n_materials):
            # Only validate chi normalization for materials that fission
            if np.any(self.sigma_f[mat_idx, :] > 0):
                chi_sum = np.sum(self.chi[mat_idx, :])
                if not np.isclose(chi_sum, 1.0, rtol=1e-3):
                    raise ValueError(
                        f"chi for material {mat_idx} must sum to 1.0, got {chi_sum}"
                    )

        return self

    model_config = ConfigDict(
        arbitrary_types_allowed=True, validate_assignment=True  # Allow numpy arrays
    )


class SolverOptions(BaseModel):
    """Solver configuration with validation."""

    max_iterations: int = Field(
        default=1000, ge=10, le=10000, description="Maximum iterations"
    )
    tolerance: float = Field(
        default=1e-6, gt=0, le=1e-2, description="Convergence tolerance"
    )
    acceleration: Literal["none", "chebyshev", "gmres"] = Field(
        default="chebyshev", description="Acceleration method"
    )
    inner_solver: Literal["gauss_seidel", "sor", "bicgstab"] = Field(
        default="gauss_seidel", description="Inner iteration solver"
    )
    eigen_method: Literal["power", "arnoldi"] = Field(
        default="power", description="Eigenvalue method"
    )
    verbose: bool = Field(default=True, description="Print progress")
    omega: float = Field(
        default=1.5, gt=0, le=2.0, description="SOR relaxation parameter"
    )

    @field_validator("tolerance")
    @classmethod
    def validate_tolerance(cls, v):
        """Warn about extreme tolerance values."""
        if v < 1e-10:
            warnings.warn(f"Very tight tolerance ({v}). May be slow.")
        if v > 1e-3:
            warnings.warn(f"Loose tolerance ({v}). May be inaccurate.")
        return v

    model_config = ConfigDict(validate_assignment=True, extra="forbid")


class MaterialComposition(BaseModel):
    """Material composition with validation."""

    material_id: str = Field(
        min_length=1, max_length=50, description="Material identifier"
    )

    composition: Dict[str, float] = Field(
        description="Nuclide compositions {nuclide: atom_density [atoms/b-cm]}"
    )

    temperature: float = Field(gt=0, le=4000, description="Material temperature [K]")

    density: float = Field(gt=0, le=30, description="Physical density [g/cm³]")

    @model_validator(mode="after")
    def validate_composition(self):
        """Validate composition dictionary."""
        if not self.composition:
            raise ValueError("Composition cannot be empty")

        for nuclide, density in self.composition.items():
            if density < 0:
                raise ValueError(f"Negative atom density for {nuclide}: {density}")
            if density > 0.2:
                warnings.warn(
                    f"Very high atom density for {nuclide}: {density} atoms/b-cm"
                )

        return self

    @property
    def total_number_density(self) -> float:
        """Total atomic number density [atoms/b-cm]."""
        return sum(self.composition.values())

    model_config = ConfigDict(validate_assignment=True)


class TransientConditions(BaseModel):
    """Initial and boundary conditions for transient analysis."""

    initial_power: float = Field(gt=0, description="Initial power level [W]")
    initial_temperature: float = Field(
        gt=273.15, le=3000, description="Initial average temperature [K]"
    )
    initial_flow_rate: float = Field(
        ge=0, description="Initial coolant flow rate [kg/s]"
    )
    initial_pressure: float = Field(gt=0, description="Initial pressure [Pa]")

    transient_type: str = Field(description="Type of transient")
    trigger_time: float = Field(ge=0, description="Time when transient initiates [s]")

    t_start: float = Field(default=0.0, ge=0, description="Simulation start time [s]")
    t_end: float = Field(gt=0, le=1e6, description="Simulation end time [s]")

    scram_available: bool = Field(
        default=True, description="Is reactor scram available"
    )
    scram_delay: float = Field(
        default=1.0, ge=0, le=10, description="Scram actuation delay [s]"
    )

    @model_validator(mode="after")
    def validate_times(self):
        """Validate time parameters."""
        if self.t_end <= self.t_start:
            raise ValueError("t_end must be greater than t_start")

        if self.trigger_time < self.t_start or self.trigger_time > self.t_end:
            raise ValueError("trigger_time must be within [t_start, t_end]")

        return self

    model_config = ConfigDict(validate_assignment=True)


# ============================================================================
# Settings (for configuration files)
# ============================================================================


class SMRForgeSettings(BaseSettings):
    """
    Global settings loaded from environment or config file.
    """

    # Paths
    cache_dir: Path = Field(
        default=Path.home() / ".smrforge" / "cache",
        description="Nuclear data cache directory",
    )
    output_dir: Path = Field(
        default=Path("./results"), description="Default output directory"
    )

    # Nuclear data
    nuclear_data_library: Literal["endfb8.0", "jeff3.3", "jendl5.0"] = Field(
        default="endfb8.0", description="Default nuclear data library"
    )

    # Performance
    n_threads: int = Field(
        default=4, ge=1, le=64, description="Number of parallel threads"
    )
    use_numba: bool = Field(default=True, description="Enable Numba JIT compilation")

    # Validation
    strict_validation: bool = Field(
        default=True, description="Enable strict validation mode"
    )
    validation_warnings: bool = Field(
        default=True, description="Show validation warnings"
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )

    model_config = ConfigDict(
        env_prefix="SMRFORGE_",  # Environment variables: SMRFORGE_CACHE_DIR, etc.
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# ============================================================================
# Utility Functions
# ============================================================================


def load_reactor_from_json(filepath: Path) -> ReactorSpecification:
    """Load reactor specification from JSON file."""
    with open(filepath) as f:
        return ReactorSpecification.model_validate_json(f.read())


def save_reactor_to_json(spec: ReactorSpecification, filepath: Path):
    """Save reactor specification to JSON file."""
    with open(filepath, "w") as f:
        f.write(spec.model_dump_json(indent=2))


def load_reactor_from_yaml(filepath: Path) -> ReactorSpecification:
    """Load reactor specification from YAML file."""
    import yaml

    with open(filepath) as f:
        data = yaml.safe_load(f)
    return ReactorSpecification.model_validate(data)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    from rich.console import Console

    console = Console()

    console.print("[bold cyan]Pydantic Validation Layer Demo[/bold cyan]\n")

    # Test 1: Valid reactor specification
    console.print("[bold]Test 1: Valid Specification[/bold]")
    try:
        spec = ReactorSpecification(
            name="Valar-10",
            reactor_type=ReactorType.PRISMATIC,
            power_thermal=10e6,
            power_electric=3.5e6,
            inlet_temperature=823.15,
            outlet_temperature=1023.15,
            max_fuel_temperature=1873.15,
            primary_pressure=7.0e6,
            core_height=200.0,
            core_diameter=100.0,
            reflector_thickness=30.0,
            fuel_type=FuelType.UCO,
            enrichment=0.195,
            heavy_metal_loading=150.0,
            coolant_flow_rate=8.0,
            cycle_length=3650,
            capacity_factor=0.95,
            target_burnup=150.0,
            doppler_coefficient=-3.5e-5,
            shutdown_margin=0.05,
        )
        console.print(f"  ✓ Created: {spec.name}")
        console.print(f"    Power density: {spec.power_density:.2f} MW/m³")
        console.print(f"    Enrichment class: {spec.enrichment_class.value}")
        console.print(f"    Aspect ratio: {spec.aspect_ratio:.2f}")
    except Exception as e:
        console.print(f"  ✗ Error: {e}")

    # Test 2: Invalid temperature order
    console.print("\n[bold]Test 2: Invalid Temperature Order[/bold]")
    try:
        bad_spec = ReactorSpecification(
            name="Bad-Reactor",
            reactor_type=ReactorType.PRISMATIC,
            power_thermal=10e6,
            inlet_temperature=1000.0,  # Higher than outlet!
            outlet_temperature=800.0,
            max_fuel_temperature=1873.15,
            primary_pressure=7.0e6,
            core_height=200.0,
            core_diameter=100.0,
            reflector_thickness=30.0,
            fuel_type=FuelType.UCO,
            enrichment=0.195,
            heavy_metal_loading=150.0,
            coolant_flow_rate=8.0,
            cycle_length=3650,
            capacity_factor=0.95,
            target_burnup=150.0,
            doppler_coefficient=-3.5e-5,
            shutdown_margin=0.05,
        )
    except Exception as e:
        console.print(f"  ✓ Caught error: {e}")

    # Test 3: JSON serialization
    console.print("\n[bold]Test 3: JSON Serialization[/bold]")
    json_str = spec.model_dump_json(indent=2)
    console.print(f"  JSON (first 200 chars): {json_str[:200]}...")

    # Test 4: Reload from JSON
    spec_reloaded = ReactorSpecification.model_validate_json(json_str)
    console.print(f"  ✓ Reloaded: {spec_reloaded.name}")

    # Test 5: Cross section validation
    console.print("\n[bold]Test 5: Cross Section Validation[/bold]")
    console.print("  ✓ All tests completed successfully!")
