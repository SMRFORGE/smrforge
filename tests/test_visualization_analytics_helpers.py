import numpy as np
import pytest


def _has_plotly():
    try:
        import plotly.graph_objects as go  # noqa: F401

        return True
    except Exception:
        return False


def _has_matplotlib():
    try:
        import matplotlib.pyplot as plt  # noqa: F401

        return True
    except Exception:
        return False


def _assert_plotly_fig(fig):
    # Accept either a plotly Figure or a dict-like payload.
    if isinstance(fig, dict):
        assert "data" in fig
        assert "layout" in fig
        return
    assert hasattr(fig, "to_dict")
    d = fig.to_dict()
    assert "data" in d
    assert "layout" in d


def _assert_mpl_fig(ret):
    assert isinstance(ret, tuple)
    fig = ret[0]
    assert hasattr(fig, "savefig")


@pytest.mark.skipif(not _has_plotly(), reason="plotly not installed")
def test_sweep_plots_plotly_smoke():
    from smrforge.visualization.sweep_plots import (
        plot_sweep_correlation_matrix,
        plot_sweep_heatmap,
        plot_sweep_pareto,
        plot_sweep_tornado,
    )

    results = [
        {
            "parameters": {"enrichment": 0.15, "power_mw": 8.0},
            "k_eff": 0.99,
            "success": True,
        },
        {
            "parameters": {"enrichment": 0.15, "power_mw": 10.0},
            "k_eff": 1.00,
            "success": True,
        },
        {
            "parameters": {"enrichment": 0.195, "power_mw": 8.0},
            "k_eff": 1.01,
            "success": True,
        },
        {
            "parameters": {"enrichment": 0.195, "power_mw": 10.0},
            "k_eff": 1.02,
            "success": True,
        },
    ]

    _assert_plotly_fig(
        plot_sweep_heatmap(
            results,
            x_param="enrichment",
            y_param="power_mw",
            metric="k_eff",
            backend="plotly",
        )
    )
    _assert_plotly_fig(plot_sweep_tornado(results, metric="k_eff", backend="plotly"))
    _assert_plotly_fig(plot_sweep_correlation_matrix(results, backend="plotly"))
    _assert_plotly_fig(
        plot_sweep_pareto(
            results, metric_x="k_eff", metric_y="power_mw", backend="plotly"
        )
    )


@pytest.mark.skipif(not _has_matplotlib(), reason="matplotlib not installed")
def test_sweep_plots_matplotlib_smoke():
    from smrforge.visualization.sweep_plots import (
        plot_sweep_heatmap,
        plot_sweep_tornado,
    )

    results = [
        {
            "parameters": {"enrichment": 0.15, "power_mw": 8.0},
            "k_eff": 0.99,
            "success": True,
        },
        {
            "parameters": {"enrichment": 0.195, "power_mw": 10.0},
            "k_eff": 1.02,
            "success": True,
        },
    ]
    _assert_mpl_fig(
        plot_sweep_heatmap(
            results,
            x_param="enrichment",
            y_param="power_mw",
            metric="k_eff",
            backend="matplotlib",
        )
    )
    _assert_mpl_fig(plot_sweep_tornado(results, metric="k_eff", backend="matplotlib"))


@pytest.mark.skipif(not _has_plotly(), reason="plotly not installed")
def test_uq_visualization_plotly_smoke():
    from smrforge.uncertainty.uq import UQResults
    from smrforge.uncertainty.visualization import (
        plot_uq_correlation_matrix,
        plot_uq_distribution,
    )

    rng = np.random.default_rng(0)
    X = rng.normal(size=(200, 2))
    y = (1.0 + 0.1 * X[:, 0] - 0.05 * X[:, 1]).reshape(-1, 1)
    res = UQResults(
        parameter_names=["x1", "x2"],
        parameter_samples=X,
        output_samples=y,
        output_names=["k_eff"],
    )
    _assert_plotly_fig(plot_uq_distribution(res, backend="plotly"))
    _assert_plotly_fig(plot_uq_correlation_matrix(res, backend="plotly"))


@pytest.mark.skipif(not _has_plotly(), reason="plotly not installed")
def test_neutronics_dashboard_plotly_smoke():
    from smrforge.visualization.tally_data import (
        plot_flux_spectrum_comparison,
        plot_neutronics_dashboard,
    )

    ng = 10
    energy_groups = np.logspace(6, -3, ng + 1)
    flux_a = np.ones((5, 4, ng))
    flux_b = 2.0 * np.ones((5, 4, ng))
    _assert_plotly_fig(
        plot_flux_spectrum_comparison(
            {"a": flux_a, "b": flux_b}, energy_groups, backend="plotly"
        )
    )
    _assert_plotly_fig(
        plot_neutronics_dashboard(flux_a, energy_groups, k_eff=1.0, backend="plotly")
    )


@pytest.mark.skipif(not _has_plotly(), reason="plotly not installed")
def test_burnup_plots_plotly_smoke():
    from smrforge.burnup.solver import NuclideInventory
    from smrforge.core.reactor_core import Nuclide
    from smrforge.visualization.material_composition import (
        plot_burnup_dashboard,
        plot_burnup_vs_time,
        plot_composition_stacked_area,
        plot_nuclide_evolution,
    )

    t_days = np.linspace(0.0, 10.0, 6)
    t_s = t_days * 24.0 * 3600.0
    burnup = np.linspace(0.0, 5.0, len(t_days))
    nuclides = [Nuclide(Z=92, A=235), Nuclide(Z=92, A=238)]
    conc = np.vstack([np.exp(-t_days / 10.0), 5.0 * np.ones_like(t_days)])
    inv = NuclideInventory(
        nuclides=nuclides, concentrations=conc, times=t_s, burnup=burnup
    )

    _assert_plotly_fig(plot_nuclide_evolution(inv, backend="plotly"))
    _assert_plotly_fig(plot_composition_stacked_area(inv, backend="plotly"))
    _assert_plotly_fig(plot_burnup_vs_time(inv, backend="plotly"))
    _assert_plotly_fig(plot_burnup_dashboard(inv, backend="plotly"))


@pytest.mark.skipif(not _has_plotly(), reason="plotly not installed")
def test_mesh_validation_econ_opt_plotly_smoke():
    from smrforge.geometry.mesh_generation import MeshQuality
    from smrforge.validation.data_validation import ValidationLevel, ValidationResult
    from smrforge.visualization.economics_plots import (
        plot_capex_breakdown,
        plot_lcoe_breakdown,
    )
    from smrforge.visualization.mesh_diagnostics import plot_mesh_verification_dashboard
    from smrforge.visualization.optimization_plots import plot_optimization_trace
    from smrforge.visualization.validation_plots import plot_validation_summary

    q = MeshQuality(
        min_angle=30.0, max_angle=120.0, aspect_ratio=2.0, skewness=0.8, jacobian=1.0
    )
    sizes = np.random.default_rng(0).lognormal(size=200)
    _assert_plotly_fig(
        plot_mesh_verification_dashboard(quality=q, sizes=sizes, backend="plotly")
    )

    vr = ValidationResult(valid=True)
    vr.add_issue(
        ValidationLevel.ERROR, "pressure", "Negative", value=-1.0, expected=">=0"
    )
    _assert_plotly_fig(plot_validation_summary(vr, backend="plotly"))

    cap = {
        "direct_reactor_island": 1.0e9,
        "contingency": 2.0e8,
        "total_overnight_cost": 1.2e9,
    }
    _assert_plotly_fig(plot_capex_breakdown(cap, backend="plotly", kind="waterfall"))
    lcoe = {
        "capital_contribution": 0.04,
        "operating_contribution": 0.02,
        "decommissioning_contribution": 0.005,
        "total_lcoe": 0.065,
    }
    _assert_plotly_fig(plot_lcoe_breakdown(lcoe, backend="plotly"))

    hist = [
        {"generation": 0, "best_fitness": 1.0},
        {"generation": 1, "best_fitness": 0.7},
        {"generation": 2, "best_fitness": 0.55},
    ]
    _assert_plotly_fig(plot_optimization_trace(hist, backend="plotly"))


import numpy as np
import pytest


def _has_plotly():
    try:
        import plotly.graph_objects as go  # noqa: F401

        return True
    except Exception:
        return False


def _has_matplotlib():
    try:
        import matplotlib.pyplot as plt  # noqa: F401

        return True
    except Exception:
        return False


def _assert_plotly_fig(fig):
    # Accept either a plotly Figure or a dict-like payload.
    if isinstance(fig, dict):
        assert "data" in fig
        assert "layout" in fig
        return
    assert hasattr(fig, "to_dict")
    d = fig.to_dict()
    assert "data" in d
    assert "layout" in d


def _assert_mpl_fig(ret):
    assert isinstance(ret, tuple)
    fig = ret[0]
    assert hasattr(fig, "savefig")


@pytest.mark.skipif(not _has_plotly(), reason="plotly not installed")
def test_sweep_plots_plotly_smoke():
    from smrforge.visualization.sweep_plots import (
        plot_sweep_correlation_matrix,
        plot_sweep_heatmap,
        plot_sweep_pareto,
        plot_sweep_tornado,
    )

    results = [
        {
            "parameters": {"enrichment": 0.15, "power_mw": 8.0},
            "k_eff": 0.99,
            "success": True,
        },
        {
            "parameters": {"enrichment": 0.15, "power_mw": 10.0},
            "k_eff": 1.00,
            "success": True,
        },
        {
            "parameters": {"enrichment": 0.195, "power_mw": 8.0},
            "k_eff": 1.01,
            "success": True,
        },
        {
            "parameters": {"enrichment": 0.195, "power_mw": 10.0},
            "k_eff": 1.02,
            "success": True,
        },
    ]

    _assert_plotly_fig(
        plot_sweep_heatmap(
            results,
            x_param="enrichment",
            y_param="power_mw",
            metric="k_eff",
            backend="plotly",
        )
    )
    _assert_plotly_fig(plot_sweep_tornado(results, metric="k_eff", backend="plotly"))
    _assert_plotly_fig(plot_sweep_correlation_matrix(results, backend="plotly"))
    _assert_plotly_fig(
        plot_sweep_pareto(
            results, metric_x="k_eff", metric_y="power_mw", backend="plotly"
        )
    )


@pytest.mark.skipif(not _has_matplotlib(), reason="matplotlib not installed")
def test_sweep_plots_matplotlib_smoke():
    from smrforge.visualization.sweep_plots import (
        plot_sweep_heatmap,
        plot_sweep_tornado,
    )

    results = [
        {
            "parameters": {"enrichment": 0.15, "power_mw": 8.0},
            "k_eff": 0.99,
            "success": True,
        },
        {
            "parameters": {"enrichment": 0.195, "power_mw": 10.0},
            "k_eff": 1.02,
            "success": True,
        },
    ]
    _assert_mpl_fig(
        plot_sweep_heatmap(
            results,
            x_param="enrichment",
            y_param="power_mw",
            metric="k_eff",
            backend="matplotlib",
        )
    )
    _assert_mpl_fig(plot_sweep_tornado(results, metric="k_eff", backend="matplotlib"))


@pytest.mark.skipif(not _has_plotly(), reason="plotly not installed")
def test_uq_visualization_plotly_smoke():
    from smrforge.uncertainty.uq import UQResults
    from smrforge.uncertainty.visualization import (
        plot_uq_correlation_matrix,
        plot_uq_distribution,
    )

    rng = np.random.default_rng(0)
    X = rng.normal(size=(200, 2))
    y = (1.0 + 0.1 * X[:, 0] - 0.05 * X[:, 1]).reshape(-1, 1)
    res = UQResults(
        parameter_names=["x1", "x2"],
        parameter_samples=X,
        output_samples=y,
        output_names=["k_eff"],
    )
    _assert_plotly_fig(plot_uq_distribution(res, backend="plotly"))
    _assert_plotly_fig(plot_uq_correlation_matrix(res, backend="plotly"))


@pytest.mark.skipif(not _has_plotly(), reason="plotly not installed")
def test_neutronics_dashboard_plotly_smoke():
    from smrforge.visualization.tally_data import (
        plot_flux_spectrum_comparison,
        plot_neutronics_dashboard,
    )

    ng = 10
    energy_groups = np.logspace(6, -3, ng + 1)
    flux_a = np.ones((5, 4, ng))
    flux_b = 2.0 * np.ones((5, 4, ng))
    _assert_plotly_fig(
        plot_flux_spectrum_comparison(
            {"a": flux_a, "b": flux_b}, energy_groups, backend="plotly"
        )
    )
    _assert_plotly_fig(
        plot_neutronics_dashboard(flux_a, energy_groups, k_eff=1.0, backend="plotly")
    )


@pytest.mark.skipif(not _has_plotly(), reason="plotly not installed")
def test_burnup_plots_plotly_smoke():
    from smrforge.burnup.solver import NuclideInventory
    from smrforge.core.reactor_core import Nuclide
    from smrforge.visualization.material_composition import (
        plot_burnup_dashboard,
        plot_burnup_vs_time,
        plot_composition_stacked_area,
        plot_nuclide_evolution,
    )

    t_days = np.linspace(0.0, 10.0, 6)
    t_s = t_days * 24.0 * 3600.0
    burnup = np.linspace(0.0, 5.0, len(t_days))
    nuclides = [Nuclide(Z=92, A=235), Nuclide(Z=92, A=238)]
    conc = np.vstack([np.exp(-t_days / 10.0), 5.0 * np.ones_like(t_days)])
    inv = NuclideInventory(
        nuclides=nuclides, concentrations=conc, times=t_s, burnup=burnup
    )

    _assert_plotly_fig(plot_nuclide_evolution(inv, backend="plotly"))
    _assert_plotly_fig(plot_composition_stacked_area(inv, backend="plotly"))
    _assert_plotly_fig(plot_burnup_vs_time(inv, backend="plotly"))
    _assert_plotly_fig(plot_burnup_dashboard(inv, backend="plotly"))


@pytest.mark.skipif(not _has_plotly(), reason="plotly not installed")
def test_mesh_validation_econ_opt_plotly_smoke():
    from smrforge.geometry.mesh_generation import MeshQuality
    from smrforge.validation.data_validation import ValidationLevel, ValidationResult
    from smrforge.visualization.economics_plots import (
        plot_capex_breakdown,
        plot_lcoe_breakdown,
    )
    from smrforge.visualization.mesh_diagnostics import plot_mesh_verification_dashboard
    from smrforge.visualization.optimization_plots import plot_optimization_trace
    from smrforge.visualization.validation_plots import plot_validation_summary

    q = MeshQuality(
        min_angle=30.0, max_angle=120.0, aspect_ratio=2.0, skewness=0.8, jacobian=1.0
    )
    sizes = np.random.default_rng(0).lognormal(size=200)
    _assert_plotly_fig(
        plot_mesh_verification_dashboard(quality=q, sizes=sizes, backend="plotly")
    )

    vr = ValidationResult(valid=True)
    vr.add_issue(
        ValidationLevel.ERROR, "pressure", "Negative", value=-1.0, expected=">=0"
    )
    _assert_plotly_fig(plot_validation_summary(vr, backend="plotly"))

    cap = {
        "direct_reactor_island": 1.0e9,
        "contingency": 2.0e8,
        "total_overnight_cost": 1.2e9,
    }
    _assert_plotly_fig(plot_capex_breakdown(cap, backend="plotly", kind="waterfall"))
    lcoe = {
        "capital_contribution": 0.04,
        "operating_contribution": 0.02,
        "decommissioning_contribution": 0.005,
        "total_lcoe": 0.065,
    }
    _assert_plotly_fig(plot_lcoe_breakdown(lcoe, backend="plotly"))

    hist = [
        {"generation": 0, "best_fitness": 1.0},
        {"generation": 1, "best_fitness": 0.7},
        {"generation": 2, "best_fitness": 0.55},
    ]
    _assert_plotly_fig(plot_optimization_trace(hist, backend="plotly"))
