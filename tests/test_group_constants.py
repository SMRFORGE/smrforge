"""
Tests for group constant generation.
"""

import numpy as np
import pytest

from smrforge.geometry import PrismaticCore
from smrforge.neutronics import MultiGroupDiffusion
from smrforge.neutronics.group_constants import (
    FewGroupConstants,
    GroupConstantGenerator,
)
from smrforge.validation.models import CrossSectionData, SolverOptions


@pytest.fixture
def simple_diffusion_solver():
    """Create a minimal diffusion solver with solved flux."""
    core = PrismaticCore(name="Test")
    core.core_height = 100
    core.core_diameter = 50
    core.reflector_thickness = 5
    core.generate_mesh(n_radial=6, n_axial=10)
    ng = 4
    ss = np.ones((2, ng, ng)) * 0.05
    np.fill_diagonal(ss[0], 0.4)
    np.fill_diagonal(ss[1], 0.28)
    xs = CrossSectionData(
        n_groups=ng,
        n_materials=2,
        sigma_t=[[0.5, 0.6, 0.7, 0.8], [0.3, 0.4, 0.5, 0.6]],
        sigma_a=[[0.05, 0.06, 0.07, 0.08], [0.01, 0.02, 0.03, 0.04]],
        sigma_f=[[0.04, 0.045, 0.05, 0.055], [0, 0, 0, 0]],
        nu_sigma_f=[[0.1, 0.11, 0.12, 0.13], [0, 0, 0, 0]],
        sigma_s=ss,
        chi=[[1, 0, 0, 0], [1, 0, 0, 0]],
        D=[[1.0, 1.2, 1.4, 1.6], [1.5, 1.7, 1.9, 2.1]],
    )
    opt = SolverOptions(max_iterations=50, tolerance=1e-4)
    diff = MultiGroupDiffusion(core, xs, opt)
    diff.solve_steady_state()
    return diff


class TestGroupConstantGenerator:
    """Tests for GroupConstantGenerator."""

    def test_collapse_to_few_groups(self):
        """collapse_to_few_groups produces valid FewGroupConstants."""
        sigma_t = np.ones((2, 8)) * 0.5
        sigma_a = np.ones((2, 8)) * 0.1
        sigma_f = np.ones((2, 8)) * 0.04
        nu_sigma_f = np.ones((2, 8)) * 0.1
        sigma_s = np.ones((2, 8, 8)) * 0.05
        chi = np.eye(8)
        D = np.ones((2, 8)) * 1.0
        gen = GroupConstantGenerator(
            sigma_t, sigma_a, sigma_f, nu_sigma_f, sigma_s, chi, D, 8
        )
        flux = np.ones((10, 8))
        fg = gen.collapse_to_few_groups(flux, [0, 4, 8])
        assert isinstance(fg, FewGroupConstants)
        assert fg.n_groups == 2
        assert fg.sigma_t.shape == (2, 2)
        assert fg.sigma_s.shape == (2, 2, 2)

    def test_from_diffusion_solver(self, simple_diffusion_solver):
        """from_diffusion_solver extracts and collapses from solver."""
        gen, fg = GroupConstantGenerator.from_diffusion_solver(
            simple_diffusion_solver, [0, 2, 4]
        )
        assert isinstance(gen, GroupConstantGenerator)
        assert isinstance(fg, FewGroupConstants)
        assert fg.n_groups == 2
        assert fg.sigma_t.shape[0] == 2

    def test_from_diffusion_solver_no_flux_raises(self, simple_diffusion_solver):
        """from_diffusion_solver raises when solver flux is None."""
        simple_diffusion_solver.flux = None
        with pytest.raises(ValueError, match="solved flux"):
            GroupConstantGenerator.from_diffusion_solver(
                simple_diffusion_solver, [0, 2]
            )

    def test_export_to_file(self, tmp_path):
        """export_to_file writes JSON and npz."""
        sigma_t = np.ones((1, 4)) * 0.5
        gen = GroupConstantGenerator(
            sigma_t, sigma_t * 0.2, sigma_t * 0.1, sigma_t * 0.1,
            np.ones((1, 4, 4)) * 0.1, np.eye(4), np.ones((1, 4)), 4
        )
        fg = gen.collapse_to_few_groups(np.ones((5, 4)), [0, 2, 4])
        gen.export_to_file(fg, tmp_path / "fg.json", format="json")
        assert (tmp_path / "fg.json").exists()
        gen.export_to_file(fg, tmp_path / "fg.npz", format="npz")
        assert (tmp_path / "fg.npz").exists()
