from types import SimpleNamespace

import numpy as np
import pytest


def test_materials_database_helium_density_func():
    from smrforge.core.materials_database import HeliumCoolant

    he = HeliumCoolant()
    rho = he.density_func(500.0, P=1.0e6)
    assert rho == pytest.approx(1.0e6 / (2077.0 * 500.0))


def test_cost_modeling_present_value_annuity_zero_discount_rate():
    from smrforge.economics.cost_modeling import LCOECalculator

    calc = LCOECalculator(capital_cost=1.0, power_electric=1.0, discount_rate=0.07)
    pv = calc._present_value_annuity(annual_value=10.0, years=3.0, discount_rate=0.0)
    assert pv == 30.0


def test_assembly_manager_shuffle_batch_only_sets_fresh_to_batch1():
    from smrforge.geometry.assembly import (
        Assembly,
        AssemblyManager,
        Point3D,
        RefuelingPattern,
    )

    mgr = AssemblyManager()
    mgr.add_assembly(Assembly(id=1, position=Point3D(0.0, 0.0, 0.0), batch=0))

    pattern = RefuelingPattern(name="one-batch", n_batches=1, batch_fractions=[1.0])
    mgr.shuffle_assemblies(pattern, shuffle_type="batch_only", apply_positions=False)

    assert mgr.assemblies[0].batch == 1


def test_control_rods_bank_worth_profile_but_no_inserted_length_uses_linear():
    from smrforge.geometry.control_rods import ControlRodBank

    bank = ControlRodBank(
        id=1,
        name="bank",
        rods=[],
        insertion=0.25,
        max_worth=0.05,
        worth_profile=lambda x: x,
    )
    # worth_profile branch, but inserted_len/bank_length are 0 -> linear fallback
    assert bank.total_worth() == pytest.approx(0.05 * (1.0 - 0.25))


def test_compact_smr_core_unknown_shape_raises():
    from smrforge.geometry.smr_compact_core import CompactSMRCore

    core = CompactSMRCore()
    with pytest.raises(ValueError):
        core.build_compact_core(n_assemblies=17, core_shape="not-a-shape")


def test_burnup_fuel_management_integration_flux_distribution_early_returns():
    from smrforge.burnup.fuel_management_integration import BurnupFuelManagerIntegration

    dummy_fuel_manager = SimpleNamespace(assemblies=[SimpleNamespace(id=1, batch=1)])
    integ = BurnupFuelManagerIntegration(dummy_fuel_manager)

    # No solver attached
    assert integ._get_assembly_flux_distribution() == {}

    # Solver attached but flux is None
    integ._neutronics_solver = SimpleNamespace(flux=None)
    assert integ._get_assembly_flux_distribution() == {}


def test_adaptive_sampling_resample_uniform_when_all_importances_zero(monkeypatch):
    from smrforge.neutronics.adaptive_sampling import AdaptiveMonteCarloSolver

    class DummySourceBank:
        def __init__(self):
            self.size = 1
            self.cleared = False
            self.added = 0

        def clear(self):
            self.cleared = True

        def add_particle(self, **kwargs):
            self.added += 1

    class DummyFissionBank:
        def __init__(self):
            self.size = 1
            self.position = np.array([[0.0, 0.0, 0.0]])

    class DummyMCSolver:
        def __init__(self):
            self.n_particles = 1
            self.fission_bank = DummyFissionBank()
            self.source_bank = DummySourceBank()

    class ZeroImportanceMap:
        def get_sampling_probability(self, z, r):
            return 0.0

    # Patch the imported sampling helpers to deterministic outputs.
    import smrforge.neutronics.monte_carlo_optimized as mco

    monkeypatch.setattr(mco, "sample_isotropic_direction", lambda _: (0.0, 0.0, 1.0))
    monkeypatch.setattr(mco, "sample_fission_spectrum", lambda: 1.0)

    mc = DummyMCSolver()
    solver = AdaptiveMonteCarloSolver(mc_solver=mc)
    solver.importance_map = ZeroImportanceMap()

    solver._resample_source_importance()
    assert mc.source_bank.cleared is True
    assert mc.source_bank.added == 1


def test_hybrid_solver_flux_gradient_identification_accepts_2d_flux():
    from smrforge.neutronics.hybrid_solver import HybridSolver

    class DummyGeom:
        n_axial = 3
        n_radial = 3
        core_diameter = 100.0
        r_reflector = 100.0

    class DummyDiffusion:
        geometry = DummyGeom()

    class DummyMC:
        pass

    hs = HybridSolver(diffusion_solver=DummyDiffusion(), mc_solver=DummyMC())
    flux_2d = np.ones((DummyGeom.n_axial, DummyGeom.n_radial))
    part = hs._identify_complex_regions_from_flux(flux_2d)
    assert part.diffusion_mask.shape == (DummyGeom.n_axial, DummyGeom.n_radial)
