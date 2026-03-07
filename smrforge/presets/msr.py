"""
Molten Salt Reactor (MSR) SMR preset designs.

Provides preset support for liquid-fuel and thermal MSR concepts, using
PrismaticCore as a simplified cylindrical diffusion-ready geometry.
For full MSR geometry (MSRSMRCore, salt channels, graphite blocks), use
smrforge.geometry.create_liquid_fuel_msr_core() or create_thermal_msr_core().
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from ..geometry import PrismaticCore
from ..validation.models import (
    CrossSectionData,
    FuelType,
    ReactorSpecification,
    ReactorType,
)


def _make_msr_thermal_2g_xs() -> CrossSectionData:
    """
    Create a simple 2-group thermal MSR cross section set.

    Material 0: fuel salt (U in FLiBe)
    Material 1: graphite reflector
    """
    return CrossSectionData(
        n_groups=2,
        n_materials=2,
        sigma_t=np.array(
            [
                [0.35, 0.85],  # fuel salt
                [0.22, 0.65],  # graphite
            ]
        ),
        sigma_a=np.array(
            [
                [0.010, 0.12],  # fuel salt absorption
                [0.001, 0.008],  # graphite absorption
            ]
        ),
        sigma_f=np.array(
            [
                [0.006, 0.09],  # fuel salt fission
                [0.0, 0.0],  # no fission in graphite
            ]
        ),
        nu_sigma_f=np.array(
            [
                [0.015, 0.225],  # nu~2.5 * sigma_f
                [0.0, 0.0],
            ]
        ),
        sigma_s=np.array(
            [
                [[0.34, 0.01], [0.0, 0.74]],  # fuel salt scattering
                [[0.22, 0.00], [0.0, 0.64]],  # graphite scattering
            ]
        ),
        chi=np.array(
            [
                [1.0, 0.0],  # fission spectrum
                [0.0, 0.0],
            ]
        ),
        D=np.array(
            [
                [1.4, 0.55],  # fuel salt diffusion
                [1.2, 0.5],  # graphite diffusion
            ]
        ),
    )


class LiquidFuelMSR:
    """Liquid-fuel MSR SMR preset (simplified PrismaticCore geometry)."""

    def __init__(self):
        self.spec = ReactorSpecification(
            name="Liquid-Fuel-MSR",
            reactor_type=ReactorType.PRISMATIC,
            description="Representative liquid-fuel molten salt reactor SMR",
            design_reference="Conceptual MSR parameters (FLiBe, thermal spectrum)",
            maturity_level="conceptual",
            power_thermal=225e6,  # 225 MWth
            power_electric=100e6,  # 100 MWe (~44% with Brayton)
            inlet_temperature=823.15,  # 550°C (schema max 900K; MSR-typical)
            outlet_temperature=1023.15,  # 750°C
            max_fuel_temperature=1200.0 + 273.15,  # 1200°C
            primary_pressure=0.5e6,  # 0.5 MPa (low pressure)
            core_height=400.0,
            core_diameter=300.0,
            reflector_thickness=50.0,
            fuel_type=FuelType.UO2,  # U fluorides in practice; UO2 for schema
            enrichment=0.20,  # HALEU typical for MSR
            heavy_metal_loading=5000.0,
            coolant_flow_rate=900.0,  # salt circulation [kg/s] (schema max 1000)
            cycle_length=3650,  # long-life core
            capacity_factor=0.92,
            target_burnup=80.0,
            doppler_coefficient=-2.0e-5,
            shutdown_margin=0.05,
        )
        self.core: Optional[PrismaticCore] = None

    def build_core(self) -> PrismaticCore:
        """Build PrismaticCore (cylindrical approximation) for diffusion solver."""
        self.core = PrismaticCore(name=self.spec.name)
        self.core.core_height = self.spec.core_height
        self.core.core_diameter = self.spec.core_diameter
        self.core.reflector_thickness = self.spec.reflector_thickness
        n_radial = max(20, int(self.spec.core_diameter / 15))
        n_axial = max(15, int(self.spec.core_height / 25))
        self.core.generate_mesh(n_radial=n_radial, n_axial=n_axial)
        return self.core

    def get_cross_sections(self) -> CrossSectionData:
        return _make_msr_thermal_2g_xs()
