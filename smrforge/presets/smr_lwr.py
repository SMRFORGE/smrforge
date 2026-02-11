"""
Light Water Reactor (LWR) SMR preset designs.

These presets intentionally focus on *specification + simple neutronics-ready
geometry*, so they can be used via the existing high-level convenience API
(`smrforge.create_reactor(...)`) and the CLI preset flow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from ..validation.models import (
    CrossSectionData,
    FuelType,
    ReactorSpecification,
    ReactorType,
)


@dataclass
class CylindricalDiffusionCore:
    """
    Minimal cylindrical core model compatible with `MultiGroupDiffusion`.

    The solver requires:
    - `core_diameter` [cm]
    - `core_height` [cm]
    - `radial_mesh` [cm]
    - `axial_mesh` [cm]

    We also include an optional `reflector_thickness` used only to extend the
    mesh beyond the active core so material 1 can represent a reflector region.
    """

    name: str
    core_height: float
    core_diameter: float
    reflector_thickness: float = 0.0
    radial_mesh: np.ndarray = field(init=False)
    axial_mesh: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        self.build_mesh()

    def build_mesh(
        self, n_radial: int = 30, n_axial: int = 50
    ) -> "CylindricalDiffusionCore":
        r_max = self.core_diameter / 2 + max(0.0, self.reflector_thickness)
        self.radial_mesh = np.linspace(0.0, r_max, n_radial + 1)
        self.axial_mesh = np.linspace(0.0, self.core_height, n_axial + 1)
        return self

    # Alias used by some examples/geometry classes
    generate_mesh = build_mesh


def _make_lwr_2g_xs() -> CrossSectionData:
    """
    Create a simple 2-group LWR-style cross section set.

    Material 0: fuel region
    Material 1: moderator/reflector region (water)
    """

    return CrossSectionData(
        n_groups=2,
        n_materials=2,
        sigma_t=np.array(
            [
                [0.30, 0.90],  # fuel
                [0.25, 0.75],  # water/reflector
            ]
        ),
        sigma_a=np.array(
            [
                [0.012, 0.14],  # fuel absorption
                [0.001, 0.015],  # water absorption
            ]
        ),
        sigma_f=np.array(
            [
                [0.007, 0.11],  # fuel fission
                [0.0, 0.0],  # no fission in water
            ]
        ),
        nu_sigma_f=np.array(
            [
                [0.0175, 0.275],  # nu~2.5 * sigma_f
                [0.0, 0.0],
            ]
        ),
        sigma_s=np.array(
            [
                [[0.28, 0.01], [0.0, 0.76]],  # fuel scattering (downscatter)
                [[0.24, 0.00], [0.0, 0.73]],  # water scattering
            ]
        ),
        chi=np.array(
            [
                [1.0, 0.0],  # fission spectrum (fast)
                [0.0, 0.0],  # non-fissioning material
            ]
        ),
        D=np.array(
            [
                [1.5, 0.6],  # fuel diffusion
                [1.8, 0.7],  # moderator diffusion
            ]
        ),
    )


class NuScalePWR77MWe:
    """NuScale-style integral PWR SMR (representative parameters)."""

    def __init__(self):
        self.spec = ReactorSpecification(
            name="NuScale-77MWe",
            reactor_type=ReactorType.PWR_SMR,
            description="Representative integral PWR SMR module (NuScale-class)",
            design_reference="Representative public NuScale-class parameters",
            maturity_level="preliminary",
            power_thermal=250e6,
            power_electric=77e6,
            inlet_temperature=290.0 + 273.15,
            outlet_temperature=325.0 + 273.15,
            max_fuel_temperature=1200.0 + 273.15,
            primary_pressure=12.8e6,
            core_height=200.0,
            core_diameter=200.0,
            reflector_thickness=30.0,
            fuel_type=FuelType.UO2,
            enrichment=0.0495,
            heavy_metal_loading=12000.0,
            coolant_flow_rate=800.0,
            cycle_length=730.0,
            capacity_factor=0.95,
            target_burnup=50.0,
            doppler_coefficient=-2.5e-5,
            shutdown_margin=0.06,
        )
        self.core: Optional[CylindricalDiffusionCore] = None

    def build_core(self) -> CylindricalDiffusionCore:
        self.core = CylindricalDiffusionCore(
            name=self.spec.name,
            core_height=self.spec.core_height,
            core_diameter=self.spec.core_diameter,
            reflector_thickness=self.spec.reflector_thickness,
        )
        return self.core

    def get_cross_sections(self) -> CrossSectionData:
        return _make_lwr_2g_xs()


class SMART100MWe:
    """SMART-class integral PWR SMR (representative parameters)."""

    def __init__(self):
        self.spec = ReactorSpecification(
            name="SMART-100MWe",
            reactor_type=ReactorType.PWR_SMR,
            description="Representative SMART-class integral PWR SMR",
            design_reference="Representative public SMART-class parameters",
            maturity_level="preliminary",
            power_thermal=330e6,
            power_electric=100e6,
            inlet_temperature=295.0 + 273.15,
            outlet_temperature=330.0 + 273.15,
            max_fuel_temperature=1200.0 + 273.15,
            primary_pressure=15.0e6,
            core_height=240.0,
            core_diameter=220.0,
            reflector_thickness=35.0,
            fuel_type=FuelType.UO2,
            enrichment=0.0495,
            heavy_metal_loading=15000.0,
            coolant_flow_rate=900.0,
            cycle_length=540.0,
            capacity_factor=0.92,
            target_burnup=45.0,
            doppler_coefficient=-2.5e-5,
            shutdown_margin=0.06,
        )
        self.core: Optional[CylindricalDiffusionCore] = None

    def build_core(self) -> CylindricalDiffusionCore:
        self.core = CylindricalDiffusionCore(
            name=self.spec.name,
            core_height=self.spec.core_height,
            core_diameter=self.spec.core_diameter,
            reflector_thickness=self.spec.reflector_thickness,
        )
        return self.core

    def get_cross_sections(self) -> CrossSectionData:
        return _make_lwr_2g_xs()


class CAREM32MWe:
    """CAREM-class integral PWR SMR (representative parameters)."""

    def __init__(self):
        self.spec = ReactorSpecification(
            name="CAREM-32MWe",
            reactor_type=ReactorType.PWR_SMR,
            description="Representative CAREM-class integral PWR SMR",
            design_reference="Representative public CAREM-class parameters",
            maturity_level="preliminary",
            power_thermal=100e6,
            power_electric=32e6,
            inlet_temperature=280.0 + 273.15,
            outlet_temperature=315.0 + 273.15,
            max_fuel_temperature=1200.0 + 273.15,
            primary_pressure=12.0e6,
            core_height=140.0,
            core_diameter=160.0,
            reflector_thickness=25.0,
            fuel_type=FuelType.UO2,
            enrichment=0.035,
            heavy_metal_loading=6000.0,
            coolant_flow_rate=300.0,
            cycle_length=365.0,
            capacity_factor=0.90,
            target_burnup=35.0,
            doppler_coefficient=-2.5e-5,
            shutdown_margin=0.06,
        )
        self.core: Optional[CylindricalDiffusionCore] = None

    def build_core(self) -> CylindricalDiffusionCore:
        self.core = CylindricalDiffusionCore(
            name=self.spec.name,
            core_height=self.spec.core_height,
            core_diameter=self.spec.core_diameter,
            reflector_thickness=self.spec.reflector_thickness,
        )
        return self.core

    def get_cross_sections(self) -> CrossSectionData:
        return _make_lwr_2g_xs()


class BWRX300:
    """BWRX-300-class BWR SMR (representative parameters)."""

    def __init__(self):
        self.spec = ReactorSpecification(
            name="BWRX-300",
            reactor_type=ReactorType.BWR_SMR,
            description="Representative BWR SMR (BWRX-300 class)",
            design_reference="Representative public BWRX-300-class parameters",
            maturity_level="preliminary",
            power_thermal=870e6,
            power_electric=300e6,
            inlet_temperature=270.0 + 273.15,
            outlet_temperature=285.0 + 273.15,
            max_fuel_temperature=1200.0 + 273.15,
            primary_pressure=7.2e6,
            core_height=365.0,
            core_diameter=400.0,
            reflector_thickness=50.0,
            fuel_type=FuelType.UO2,
            enrichment=0.045,
            heavy_metal_loading=25000.0,
            coolant_flow_rate=1000.0,
            cycle_length=720.0,
            capacity_factor=0.92,
            target_burnup=50.0,
            doppler_coefficient=-2.5e-5,
            shutdown_margin=0.08,
        )
        self.core: Optional[CylindricalDiffusionCore] = None

    def build_core(self) -> CylindricalDiffusionCore:
        self.core = CylindricalDiffusionCore(
            name=self.spec.name,
            core_height=self.spec.core_height,
            core_diameter=self.spec.core_diameter,
            reflector_thickness=self.spec.reflector_thickness,
        )
        return self.core

    def get_cross_sections(self) -> CrossSectionData:
        return _make_lwr_2g_xs()
