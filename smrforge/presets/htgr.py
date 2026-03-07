# smrforge/presets/htgr.py
"""
Reference HTGR designs using Pydantic validation.
All designs are automatically validated on construction.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from ..core.materials_database import MaterialDatabase
from ..geometry import PebbleBedCore, PrismaticCore

# Import Pydantic models
from ..validation.models import (
    CrossSectionData,
    FuelType,
    GeometryParameters,
    GraphiteGrade,
    MaterialComposition,
    ReactorSpecification,
    ReactorType,
)

try:
    # LWR SMR presets live in a separate module, but are registered here so the
    # existing preset discovery API continues to work.
    from .smr_lwr import BWRX300, CAREM32MWe, NuScalePWR77MWe, SMART100MWe

    _LWR_PRESETS_AVAILABLE = True
except Exception:
    _LWR_PRESETS_AVAILABLE = False

try:
    from .msr import LiquidFuelMSR

    _MSR_PRESETS_AVAILABLE = True
except Exception:
    _MSR_PRESETS_AVAILABLE = False

    class LiquidFuelMSR:  # type: ignore[no-redef]
        pass


class ValarAtomicsReactor:
    """
    Valar Atomics-inspired 10 MWth micro-reactor design.
    Now uses Pydantic for automatic validation.
    """

    def __init__(self):
        # Use Pydantic model - automatic validation!
        self.spec = ReactorSpecification(
            # Identification
            name="Valar-10",
            reactor_type=ReactorType.PRISMATIC,
            description="Compact HTGR for remote power and industrial heat",
            design_reference="Valar Atomics public specifications (2024)",
            maturity_level="conceptual",
            # Power ratings [W]
            power_thermal=10e6,  # 10 MWth
            power_electric=3.5e6,  # 3.5 MWe (35% efficiency)
            # Temperatures [K]
            inlet_temperature=550.0 + 273.15,  # 550°C
            outlet_temperature=750.0 + 273.15,  # 750°C
            max_fuel_temperature=1600.0 + 273.15,  # 1600°C
            # Pressure [Pa]
            primary_pressure=7.0e6,  # 7 MPa
            # Compact core design [cm]
            core_height=200.0,  # 2 m
            core_diameter=100.0,  # 1 m
            reflector_thickness=30.0,
            # TRISO-UCO fuel
            fuel_type=FuelType.UCO,
            enrichment=0.195,  # 19.5% HALEU
            heavy_metal_loading=150.0,  # kg
            # Operating conditions
            coolant_flow_rate=8.0,  # kg/s
            # Long life core
            cycle_length=3650,  # 10 years without refueling
            capacity_factor=0.95,
            target_burnup=150.0,  # MWd/kg (deep burn)
            # Safety parameters
            doppler_coefficient=-3.5e-5,  # Strong negative
            shutdown_margin=0.05,  # 5% dk/k
        )

        # Geometry parameters (also Pydantic validated)
        self.geometry_params = GeometryParameters(
            n_rings=2,  # Small core: 2 rings
            lattice_pitch=38.0,  # cm
            block_height=50.0,  # cm per block
            n_axial_blocks=4,  # Total 200 cm height
            flat_to_flat=36.0,  # cm
            n_radial_mesh=15,
            n_axial_mesh=20,
        )

        self.core: Optional[PrismaticCore] = None
        self.materials = MaterialDatabase()

    def build_core(self) -> PrismaticCore:
        """Build the core geometry using validated parameters."""
        self.core = PrismaticCore(name=self.spec.name)

        # Use validated geometry parameters
        self.core.build_hexagonal_lattice(
            n_rings=self.geometry_params.n_rings,
            pitch=self.geometry_params.lattice_pitch,
            block_height=self.geometry_params.block_height,
            n_axial=self.geometry_params.n_axial_blocks,
            flat_to_flat=self.geometry_params.flat_to_flat,
        )

        # Generate mesh with validated parameters
        self.core.generate_mesh(
            n_radial=self.geometry_params.n_radial_mesh,
            n_axial=self.geometry_params.n_axial_mesh,
        )

        return self.core

    def get_cross_sections(self) -> CrossSectionData:
        """Generate validated cross sections."""
        n_groups = 8
        n_materials = 2

        # Create cross section data (will be validated by Pydantic)
        xs_data = CrossSectionData(
            n_groups=n_groups,
            n_materials=n_materials,
            sigma_t=np.array(
                [
                    [0.28, 0.32, 0.35, 0.38, 0.50, 0.70, 0.85, 0.95],  # Fuel
                    [0.25, 0.27, 0.30, 0.32, 0.40, 0.55, 0.65, 0.75],  # Reflector
                ]
            ),
            sigma_a=np.array(
                [
                    [0.005, 0.008, 0.015, 0.025, 0.045, 0.080, 0.12, 0.15],
                    [0.001, 0.002, 0.003, 0.005, 0.008, 0.012, 0.018, 0.025],
                ]
            ),
            sigma_f=np.array(
                [
                    [0.004, 0.007, 0.012, 0.020, 0.035, 0.065, 0.10, 0.13],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                ]
            ),
            nu_sigma_f=np.array(
                [
                    [0.010, 0.017, 0.030, 0.050, 0.088, 0.163, 0.25, 0.33],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                ]
            ),
            sigma_s=self._create_scattering_matrix(n_groups, n_materials),
            chi=np.array(
                [
                    [0.60, 0.30, 0.08, 0.015, 0.004, 0.001, 0.0, 0.0],
                    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                ]
            ),
            D=np.array(
                [
                    [1.2, 1.0, 0.8, 0.6, 0.5, 0.4, 0.35, 0.30],
                    [1.5, 1.3, 1.1, 0.9, 0.7, 0.6, 0.50, 0.45],
                ]
            ),
        )

        # Pydantic automatically validates:
        # - All arrays are positive
        # - sigma_f <= sigma_a <= sigma_t
        # - chi sums to 1
        # - Shapes are consistent

        return xs_data

    def _create_scattering_matrix(self, n_groups: int, n_materials: int) -> np.ndarray:
        """Create downscattering matrix."""
        sigma_s = np.zeros((n_materials, n_groups, n_groups))

        for m in range(n_materials):
            for g_from in range(n_groups):
                sigma_s[m, g_from, g_from] = 0.25
                if g_from < n_groups - 1:
                    sigma_s[m, g_from, g_from + 1] = 0.03
                if g_from < n_groups - 2:
                    sigma_s[m, g_from, g_from + 2] = 0.005

        return sigma_s

    def to_json(self, filepath: Path):
        """Save design to JSON with validation."""
        with open(filepath, "w") as f:
            f.write(self.spec.model_dump_json(indent=2))

    @classmethod
    def from_json(cls, filepath: Path):
        """Load design from JSON with automatic validation."""
        with open(filepath) as f:
            spec = ReactorSpecification.model_validate_json(f.read())

        reactor = cls.__new__(cls)
        reactor.spec = spec
        reactor.materials = MaterialDatabase()
        reactor.core = None
        return reactor


class GTMHR350:
    """GT-MHR 350 MWth with Pydantic validation."""

    def __init__(self):
        self.spec = ReactorSpecification(
            name="GT-MHR-350",
            reactor_type=ReactorType.PRISMATIC,
            description="Large HTGR for baseload electricity",
            design_reference="GA GT-MHR Preliminary Safety Analysis (1996)",
            maturity_level="detailed",
            power_thermal=350e6,  # 350 MWth
            power_electric=165e6,  # 165 MWe (47% with Brayton cycle)
            inlet_temperature=490.0 + 273.15,
            outlet_temperature=850.0 + 273.15,
            max_fuel_temperature=1600.0 + 273.15,
            primary_pressure=7.0e6,
            core_height=793.0,
            core_diameter=450.0,
            reflector_thickness=100.0,
            fuel_type=FuelType.UCO,
            enrichment=0.155,  # 15.5%
            heavy_metal_loading=5000.0,
            coolant_flow_rate=320.0,
            cycle_length=425,  # 18 month cycle
            capacity_factor=0.92,
            target_burnup=90.0,
            doppler_coefficient=-2.8e-5,
            shutdown_margin=0.10,
        )

        self.geometry_params = GeometryParameters(
            n_rings=6,  # Large array
            lattice_pitch=40.0,
            block_height=79.3,
            n_axial_blocks=10,
            flat_to_flat=36.0,
            n_radial_mesh=30,
            n_axial_mesh=50,
        )

    def build_core(self) -> PrismaticCore:
        """Build GT-MHR core."""
        core = PrismaticCore(name=self.spec.name)

        core.build_hexagonal_lattice(
            n_rings=self.geometry_params.n_rings,
            pitch=self.geometry_params.lattice_pitch,
            block_height=self.geometry_params.block_height,
            n_axial=self.geometry_params.n_axial_blocks,
            flat_to_flat=self.geometry_params.flat_to_flat,
        )

        core.reflector_thickness = self.spec.reflector_thickness
        core.generate_mesh(
            n_radial=self.geometry_params.n_radial_mesh,
            n_axial=self.geometry_params.n_axial_mesh,
        )

        return core


class HTRPM200:
    """HTR-PM 200 MWth pebble bed with Pydantic validation."""

    def __init__(self):
        self.spec = ReactorSpecification(
            name="HTR-PM-200",
            reactor_type=ReactorType.PEBBLE_BED,
            description="Modular pebble bed with continuous refueling",
            design_reference="HTR-PM Final Safety Analysis Report (2018)",
            maturity_level="detailed",
            power_thermal=200e6,
            power_electric=90e6,  # 45% efficiency
            inlet_temperature=250.0 + 273.15,
            outlet_temperature=750.0 + 273.15,
            max_fuel_temperature=1620.0 + 273.15,
            primary_pressure=7.0e6,
            core_height=1100.0,
            core_diameter=300.0,
            reflector_thickness=100.0,
            fuel_type=FuelType.UO2,
            enrichment=0.085,  # 8.5% LEU
            heavy_metal_loading=3600.0,
            coolant_flow_rate=96.0,
            cycle_length=10000,  # Continuous refueling
            capacity_factor=0.92,
            target_burnup=90.0,
            doppler_coefficient=-2.5e-5,
            shutdown_margin=0.08,
        )

        self.geometry_params = GeometryParameters(
            pebble_diameter=6.0,
            packing_fraction=0.61,
            n_radial_mesh=25,
            n_axial_mesh=70,
        )

    def build_core(self) -> PebbleBedCore:
        """Build pebble bed core."""
        core = PebbleBedCore(name=self.spec.name)

        core.build_structured_packing(
            core_height=self.spec.core_height,
            core_diameter=self.spec.core_diameter,
            pebble_radius=self.geometry_params.pebble_diameter / 2,
        )

        return core


class MicroHTGR:
    """1 MWth micro-HTGR with Pydantic validation."""

    def __init__(self):
        self.spec = ReactorSpecification(
            name="Micro-HTGR-1",
            reactor_type=ReactorType.PRISMATIC,
            description="Transportable micro-reactor for remote power",
            design_reference="Conceptual design",
            maturity_level="conceptual",
            power_thermal=1e6,  # 1 MWth
            power_electric=0.35e6,  # 350 kWe
            inlet_temperature=500.0 + 273.15,
            outlet_temperature=800.0 + 273.15,
            max_fuel_temperature=1600.0 + 273.15,
            primary_pressure=5.0e6,
            core_height=100.0,
            core_diameter=50.0,
            reflector_thickness=20.0,
            fuel_type=FuelType.UCO,
            enrichment=0.195,  # HALEU
            heavy_metal_loading=30.0,
            coolant_flow_rate=1.5,
            cycle_length=3650,  # 10 years
            capacity_factor=0.90,
            target_burnup=200.0,
            doppler_coefficient=-4.0e-5,  # Very strong
            shutdown_margin=0.08,
        )

        self.geometry_params = GeometryParameters(
            n_rings=1,  # Very compact
            lattice_pitch=35.0,
            block_height=50.0,
            n_axial_blocks=2,
            n_radial_mesh=12,
            n_axial_mesh=15,
        )


class DesignLibrary:
    """
    Central library of validated reference designs.
    All designs use Pydantic for automatic validation.
    """

    def __init__(self):
        self.designs: Dict[str, ReactorSpecification] = {}
        self._load_designs()

    def _load_designs(self):
        """Load all reference designs (with automatic validation)."""
        # Each design is validated on construction
        valar = ValarAtomicsReactor()
        gtmhr = GTMHR350()
        htrpm = HTRPM200()
        micro = MicroHTGR()

        self.designs["valar-10"] = valar.spec
        self.designs["gt-mhr-350"] = gtmhr.spec
        self.designs["htr-pm-200"] = htrpm.spec
        self.designs["micro-htgr-1"] = micro.spec

        if _LWR_PRESETS_AVAILABLE:
            nuscale = NuScalePWR77MWe()
            smart = SMART100MWe()
            carem = CAREM32MWe()
            bwrx = BWRX300()

            self.designs["nuscale-77mwe"] = nuscale.spec
            self.designs["smart-100mwe"] = smart.spec
            self.designs["carem-32mwe"] = carem.spec
            self.designs["bwrx-300"] = bwrx.spec

        if _MSR_PRESETS_AVAILABLE:
            msr = LiquidFuelMSR()
            self.designs["msr-liquid"] = msr.spec

    def get_design(self, name: str) -> ReactorSpecification:
        """Retrieve a validated design by name."""
        if name not in self.designs:
            raise KeyError(
                f"Design '{name}' not found. Available: {list(self.designs.keys())}"
            )
        return self.designs[name]

    def list_designs(self) -> List[str]:
        """List all available designs."""
        return list(self.designs.keys())

    def compare_designs(self, design_names: List[str]) -> None:
        """Print comparison table of validated designs."""
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="Reactor Design Comparison")

        table.add_column("Parameter", style="cyan")
        for name in design_names:
            table.add_column(name, justify="right")

        # Use Pydantic properties for comparison
        params = [
            ("Type", lambda s: s.reactor_type.value),
            ("Power (MWth)", lambda s: s.power_thermal / 1e6),
            (
                "Power (MWe)",
                lambda s: s.power_electric / 1e6 if s.power_electric else None,
            ),
            (
                "Efficiency (%)",
                lambda s: s.thermal_efficiency * 100 if s.thermal_efficiency else None,
            ),
            ("Height (m)", lambda s: s.core_height / 100),
            ("Diameter (m)", lambda s: s.core_diameter / 100),
            ("Aspect Ratio", lambda s: s.aspect_ratio),
            ("Enrichment (%)", lambda s: s.enrichment * 100),
            ("Enr. Class", lambda s: s.enrichment_class.value),
            ("Inlet T (°C)", lambda s: s.inlet_temperature - 273.15),
            ("Outlet T (°C)", lambda s: s.outlet_temperature - 273.15),
            ("Pressure (MPa)", lambda s: s.primary_pressure / 1e6),
            ("Cycle (days)", lambda s: s.cycle_length),
            ("Burnup (MWd/kg)", lambda s: s.target_burnup),
            ("Power Density (MW/m³)", lambda s: s.power_density),
        ]

        for label, accessor in params:
            row = [label]
            for name in design_names:
                design = self.designs[name]
                value = accessor(design)
                if value is None:
                    row.append("N/A")
                elif isinstance(value, float):
                    row.append(f"{value:.2f}")
                else:
                    row.append(str(value))
            table.add_row(*row)

        console.print(table)

    def export_design(self, name: str, filepath: Path):
        """Export validated design to JSON."""
        design = self.get_design(name)

        with open(filepath, "w") as f:
            f.write(design.model_dump_json(indent=2))

    def import_design(self, filepath: Path, name: str):
        """Import and validate design from JSON."""
        with open(filepath) as f:
            design = ReactorSpecification.model_validate_json(f.read())

        self.designs[name] = design
        return design

    def validate_all_designs(self) -> bool:
        """Validate all designs (for testing)."""
        from rich.console import Console

        console = Console()

        all_valid = True
        for name, spec in self.designs.items():
            try:
                # Re-validate (Pydantic validates on construction, but good to check)
                ReactorSpecification.model_validate(spec.model_dump())
                console.print(f"[green][OK][/green] {name}: Valid")
            except Exception as e:
                console.print(f"[red][FAIL][/red] {name}: {e}")
                all_valid = False

        return all_valid


if __name__ == "__main__":
    from rich.console import Console

    console = Console()

    console.print("[bold cyan]Updated HTGR Reference Design Library[/bold cyan]\n")

    # Load library (all designs validated automatically)
    library = DesignLibrary()

    console.print(f"Available designs: {', '.join(library.list_designs())}\n")

    # Compare designs using Pydantic computed properties
    library.compare_designs(["valar-10", "gt-mhr-350", "htr-pm-200", "micro-htgr-1"])

    # Build Valar reactor with validation
    console.print("\n[bold]Building Valar-10 Core...[/bold]")
    valar = ValarAtomicsReactor()

    # Spec is already validated!
    console.print(f"   Name: {valar.spec.name}")
    console.print(f"   Type: {valar.spec.reactor_type.value}")
    console.print(f"   Power density: {valar.spec.power_density:.2f} MW/m³")
    console.print(f"   Enrichment class: {valar.spec.enrichment_class.value}")
    console.print(f"   Efficiency: {valar.spec.thermal_efficiency * 100:.1f}%")

    core = valar.build_core()
    console.print(f"   Core built: {len(core.blocks)} blocks")

    # Export validated design
    output_dir = Path("./validated_designs")
    output_dir.mkdir(exist_ok=True)
    valar.to_json(output_dir / "valar-10.json")

    # Validate all
    console.print("\n[bold]Validating all designs...[/bold]")
    if library.validate_all_designs():
        console.print("\n[bold green]All designs validated successfully![/bold green]")

    console.print(f"\n[bold]Design exported to: {output_dir / 'valar-10.json'}[/bold]")
