import importlib
from types import SimpleNamespace
from unittest.mock import patch

import pytest


class DummyApp:
    def __init__(self):
        self.callbacks = []

    def callback(self, *args, **kwargs):
        def decorator(fn):
            self.callbacks.append(fn)
            return fn

        return decorator


def test_feature_lab_demo_functions_and_callback_dispatch():
    import dash

    from smrforge.gui.callbacks import feature_lab as fl

    fl = importlib.reload(fl)
    assert fl._DASH_AVAILABLE is True

    # Cover _blank_figure
    fig = fl._blank_figure("x")
    assert isinstance(fig, dict)

    # Patch heavy external calls while still executing feature_lab code paths.
    import plotly.graph_objects as go

    dummy_spec = SimpleNamespace(
        name="R",
        reactor_type="prismatic",
        power_thermal=10e6,
        enrichment=0.195,
    )
    dummy_reactor = SimpleNamespace(
        spec=dummy_spec,
        solve_keff=lambda: 1.0000,
        _get_core=lambda: object(),
    )

    with (
        patch("smrforge.list_presets", return_value=["valar-10"]),
        patch("smrforge.create_reactor", return_value=dummy_reactor),
        patch("smrforge.visualization.advanced.plot_ray_traced_geometry", return_value=go.Figure()),
        patch("smrforge.convenience.transients.quick_transient", return_value={"time": [0, 1], "power": [1, 2], "T_fuel": [10, 11], "T_moderator": [9, 10]}),
        patch("smrforge.visualization.material_composition.plot_burnup_dashboard", return_value=go.Figure()),
        patch("smrforge.visualization.mesh_diagnostics.plot_mesh_verification_dashboard", return_value=go.Figure()),
        patch("smrforge.visualization.validation_plots.plot_validation_summary", return_value=go.Figure()),
        patch("smrforge.visualization.validation_plots.plot_validation_issues", return_value=go.Figure()),
        patch("smrforge.visualization.economics_plots.plot_capex_breakdown", return_value=go.Figure()),
        patch("smrforge.visualization.economics_plots.plot_lcoe_breakdown", return_value=go.Figure()),
        patch("smrforge.visualization.optimization_plots.plot_optimization_trace", return_value=go.Figure()),
        patch("smrforge.visualization.sweep_plots.plot_sweep_heatmap", return_value=go.Figure()),
        patch("smrforge.visualization.sweep_plots.plot_sweep_tornado", return_value=go.Figure()),
        patch("smrforge.uncertainty.visualization.plot_uq_distribution", return_value=go.Figure()),
        patch("smrforge.uncertainty.visualization.plot_uq_correlation_matrix", return_value=go.Figure()),
    ):
        # Execute each demo at least once
        for fn in [
            fl._demo_presets,
            fl._demo_keff,
            fl._demo_neutronics_dashboard,
            fl._demo_viz_geometry,
            fl._demo_quick_transient,
            fl._demo_lumped_thermal,
            fl._demo_parameter_sweep,
            fl._demo_sweep_heatmap,
            fl._demo_sweep_tornado,
            fl._demo_uq_mc,
            fl._demo_uq_distribution,
            fl._demo_uq_correlations,
            fl._demo_burnup_dashboard,
            fl._demo_mesh_diagnostics,
            fl._demo_validation_viz,
            fl._demo_optimization,
            fl._demo_optimization_trace,
            fl._demo_economics,
            fl._demo_economics_capex,
            fl._demo_economics_lcoe,
            fl._demo_control_pid,
        ]:
            text, fig = fn()
            assert isinstance(text, str)
            assert isinstance(fig, dict)

        # Cover branches inside quick/lumped demos when data arrays are empty
        with patch("smrforge.convenience.transients.quick_transient", return_value={"time": [], "power": [], "T_fuel": [], "T_moderator": []}):
            text, fig = fl._demo_quick_transient()
            assert "peak power: N/A" in text

        class DummyLumped:
            def __init__(self, *args, **kwargs):
                pass

            def solve_transient(self, *args, **kwargs):
                return {"time": [], "T_fuel": [], "T_moderator": []}

        with (
            patch("smrforge.thermal.lumped.LumpedThermalHydraulics", DummyLumped),
            patch("smrforge.thermal.lumped.ThermalLump", lambda **kwargs: object()),
            patch("smrforge.thermal.lumped.ThermalResistance", lambda **kwargs: object()),
        ):
            text, fig = fl._demo_lumped_thermal()
            assert "final T_fuel: N/A" in text

        # Parameter sweep: df.empty branch and non-empty branch
        class DummyDf:
            def __init__(self, empty: bool):
                self.empty = empty
                self.columns = ["enrichment", "power_mw", "k_eff"]

        class DummySweepResult:
            def __init__(self, empty: bool):
                self.results = [1, 2]
                self.failed_cases = []
                self._df = DummyDf(empty)

            def to_dataframe(self):
                return self._df

        class DummySweep:
            def __init__(self, cfg):
                self.cfg = cfg

            def run(self):
                return DummySweepResult(empty=True)

        with patch("smrforge.workflows.parameter_sweep.ParameterSweep", DummySweep):
            text, fig = fl._demo_parameter_sweep()
            assert "cases" in text

        class DummySweep2(DummySweep):
            def run(self):
                return DummySweepResult(empty=False)

        with patch("smrforge.workflows.parameter_sweep.ParameterSweep", DummySweep2):
            text, fig = fl._demo_parameter_sweep()
            assert "cases" in text

    # Cover callback dispatcher run_demo
    app = DummyApp()
    fl.register_feature_lab_callbacks(app)
    (run_demo,) = [fn for fn in app.callbacks if fn.__name__ == "run_demo"]

    with pytest.raises(dash.exceptions.PreventUpdate):
        run_demo(None, "presets")

    out = run_demo(1, "unknown-demo-id")
    assert out[3] == "warning"

    with patch.dict(fl._DEMO_RUNNERS, {"x": lambda: ("ok", fl._blank_figure("ok"))}):
        out = run_demo(1, "x")
        assert out[3] == "success"

    with patch.dict(fl._DEMO_RUNNERS, {"boom": lambda: (_ for _ in ()).throw(RuntimeError("boom"))}):
        out = run_demo(1, "boom")
        assert out[3] == "danger"

