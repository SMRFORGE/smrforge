"""
Additional coverage for convenience_utils and related modules.

Targets remaining uncovered lines to reach 90% project coverage:
- convenience_utils: ImportError paths (_CORE_AVAILABLE, _VIZ_AVAILABLE),
  create_simple_burnup_solver/get_material/list_materials when core unavailable,
  quick_plot_core/quick_plot_mesh when viz unavailable, show=True branches,
  quick_solve return_power with/without geometry.spec.power_thermal.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestConvenienceUtilsImportErrorPaths:
    """Cover convenience_utils ImportError and optional branches."""

    def test_create_simple_burnup_solver_core_unavailable(self):
        """create_simple_burnup_solver raises when _CORE_AVAILABLE is False."""
        import smrforge.convenience_utils as cu
        with patch.object(cu, "_CORE_AVAILABLE", False):
            with pytest.raises(ImportError, match="Burnup module not available"):
                cu.create_simple_burnup_solver()

    def test_get_material_core_unavailable(self):
        """get_material raises when _CORE_AVAILABLE is False."""
        import smrforge.convenience_utils as cu
        with patch.object(cu, "_CORE_AVAILABLE", False):
            with pytest.raises(ImportError, match="Materials module not available"):
                cu.get_material("graphite_IG-110")

    def test_list_materials_core_unavailable(self):
        """list_materials raises when _CORE_AVAILABLE is False."""
        import smrforge.convenience_utils as cu
        with patch.object(cu, "_CORE_AVAILABLE", False):
            with pytest.raises(ImportError, match="Materials module not available"):
                cu.list_materials()

    def test_quick_plot_core_viz_unavailable(self):
        """quick_plot_core raises when _VIZ_AVAILABLE is False."""
        import smrforge.convenience_utils as cu
        core = Mock()
        with patch.object(cu, "_VIZ_AVAILABLE", False):
            with pytest.raises(ImportError, match="Visualization module not available"):
                cu.quick_plot_core(core)

    def test_quick_plot_mesh_viz_unavailable(self):
        """quick_plot_mesh raises when _VIZ_AVAILABLE is False."""
        import smrforge.convenience_utils as cu
        mesh = Mock()
        with patch.object(cu, "_VIZ_AVAILABLE", False):
            with pytest.raises(ImportError, match="Visualization module not available"):
                cu.quick_plot_mesh(mesh)

    def test_quick_plot_core_show_true_calls_plt_show(self):
        """quick_plot_core with show=True calls plt.show()."""
        import smrforge.convenience_utils as cu
        if not getattr(cu, "_VIZ_AVAILABLE", False):
            pytest.skip("Visualization not available")
        core = Mock()
        with patch("matplotlib.pyplot.show") as mock_show:
            with patch.object(cu, "plot_core_layout", return_value=(Mock(), Mock())):
                cu.quick_plot_core(core, show=True)
                mock_show.assert_called_once()

    def test_quick_plot_mesh_show_true_calls_fig_show(self):
        """quick_plot_mesh with show=True calls fig.show()."""
        import smrforge.convenience_utils as cu
        if not getattr(cu, "_VIZ_AVAILABLE", False):
            pytest.skip("Visualization not available")
        mesh = Mock()
        mock_fig = Mock()
        with patch.object(cu, "plot_mesh3d_plotly", return_value=mock_fig):
            cu.quick_plot_mesh(mesh, show=True)
            mock_fig.show.assert_called_once()


class TestConvenienceUtilsQuickSolveReturnPower:
    """Cover quick_solve return_power branches in _add_convenience_methods."""

    def test_quick_solve_return_power_with_geometry_spec_power_thermal(self):
        """quick_solve(return_power=True) uses geometry.spec.power_thermal when present."""
        import numpy as np
        import smrforge.convenience_utils as cu
        if not getattr(cu, "_CORE_AVAILABLE", False):
            pytest.skip("Core not available")
        cu._add_convenience_methods()
        from smrforge.neutronics.solver import MultiGroupDiffusion
        quick_solve = getattr(MultiGroupDiffusion, "quick_solve", None)
        if quick_solve is None:
            pytest.skip("quick_solve not patched")
        solver = Mock()
        solver.solve_steady_state.return_value = (1.0, np.ones(10))
        solver.compute_power_distribution.return_value = np.ones(10) * 0.1
        solver.geometry = Mock()
        solver.geometry.spec = Mock()
        solver.geometry.spec.power_thermal = 15e6
        out = quick_solve(solver, return_power=True)
        assert isinstance(out, dict)
        assert "k_eff" in out and "power" in out
        solver.compute_power_distribution.assert_called_once_with(15e6)

    def test_quick_solve_return_power_without_geometry_spec_uses_default(self):
        """quick_solve(return_power=True) uses default 10e6 when no geometry.spec.power_thermal."""
        import numpy as np
        import smrforge.convenience_utils as cu
        if not getattr(cu, "_CORE_AVAILABLE", False):
            pytest.skip("Core not available")
        cu._add_convenience_methods()
        from smrforge.neutronics.solver import MultiGroupDiffusion
        quick_solve = getattr(MultiGroupDiffusion, "quick_solve", None)
        if quick_solve is None:
            pytest.skip("quick_solve not patched")
        solver = Mock()
        solver.solve_steady_state.return_value = (1.0, np.ones(10))
        solver.compute_power_distribution.return_value = np.ones(10) * 0.1
        solver.geometry = None
        out = quick_solve(solver, return_power=True)
        assert isinstance(out, dict)
        solver.compute_power_distribution.assert_called_once_with(10e6)

    def test_quick_solve_return_power_geometry_spec_no_power_thermal_uses_default(self):
        """quick_solve(return_power=True) uses default 10e6 when geometry.spec has no power_thermal attr."""
        import numpy as np
        import smrforge.convenience_utils as cu
        if not getattr(cu, "_CORE_AVAILABLE", False):
            pytest.skip("Core not available")
        cu._add_convenience_methods()
        from smrforge.neutronics.solver import MultiGroupDiffusion
        quick_solve = getattr(MultiGroupDiffusion, "quick_solve", None)
        if quick_solve is None:
            pytest.skip("quick_solve not patched")
        solver = Mock()
        solver.solve_steady_state.return_value = (1.0, np.ones(10))
        solver.compute_power_distribution.return_value = np.ones(10) * 0.1
        # spec without power_thermal so getattr(..., 10e6) is used
        solver.geometry = Mock()
        solver.geometry.spec = type("Spec", (), {})()
        out = quick_solve(solver, return_power=True)
        assert isinstance(out, dict)
        solver.compute_power_distribution.assert_called_once_with(10e6)
