"""
Feature lab callbacks.
"""

from __future__ import annotations

try:
    from dash import Input, Output, State
    from dash.exceptions import PreventUpdate
    import dash_bootstrap_components as dbc
    import plotly.graph_objects as go

    _DASH_AVAILABLE = True
except ImportError:  # pragma: no cover
    _DASH_AVAILABLE = False

from smrforge.utils.logging import get_logger

logger = get_logger(__name__)


def _blank_figure(title: str) -> dict:
    fig = go.Figure()
    fig.update_layout(title=title)
    return fig.to_dict()


def _demo_presets() -> tuple[str, dict]:
    import smrforge as smr

    presets = smr.list_presets()
    preset = presets[0] if presets else "valar-10"
    reactor = smr.create_reactor(preset)
    text = "\n".join(
        [
            "Loaded presets:",
            f"  count: {len(presets)}",
            f"  first: {preset}",
            "",
            "Created reactor:",
            f"  name: {reactor.spec.name}",
            f"  type: {reactor.spec.reactor_type}",
            f"  power_thermal (MW): {reactor.spec.power_thermal/1e6:.2f}",
            f"  enrichment: {reactor.spec.enrichment}",
        ]
    )
    return text, _blank_figure("Presets demo (no plot)")


def _demo_keff() -> tuple[str, dict]:
    import smrforge as smr

    reactor = smr.create_reactor("valar-10")
    k = reactor.solve_keff()
    text = "\n".join(
        [
            "Neutronics demo (convenience API)",
            f"  reactor: {reactor.spec.name}",
            f"  k_eff: {k:.6f}",
        ]
    )
    return text, _blank_figure(f"k-eff = {k:.6f} (no plot)")


def _demo_viz_geometry() -> tuple[str, dict]:
    import smrforge as smr
    from smrforge.visualization.advanced import plot_ray_traced_geometry

    reactor = smr.create_reactor("valar-10")
    core = reactor._get_core()
    fig = plot_ray_traced_geometry(
        core,
        origin=(0.0, 0.0, 200.0),
        width=(300.0, 300.0, 400.0),
        basis="xy",
        backend="plotly",
    )
    text = "\n".join(
        [
            "Visualization demo (ray-traced geometry, plotly)",
            f"  reactor: {reactor.spec.name}",
            "  plot: plot_ray_traced_geometry(core, backend='plotly')",
        ]
    )
    return text, fig.to_dict() if hasattr(fig, "to_dict") else fig


def _demo_quick_transient() -> tuple[str, dict]:
    from smrforge.convenience.transients import quick_transient

    result = quick_transient(
        power=1e6,
        temperature=1200.0,
        transient_type="reactivity_insertion",
        reactivity_insertion=0.001,
        duration=100.0,
        scram_available=True,
        scram_delay=1.0,
        plot=False,
    )
    t = result.get("time", [])
    p = result.get("power", [])
    tf = result.get("T_fuel", [])
    tm = result.get("T_moderator", [])

    fig = go.Figure()
    if t and p:
        fig.add_trace(go.Scatter(x=t, y=p, mode="lines", name="Power (W)"))
    if t and tf:
        fig.add_trace(go.Scatter(x=t, y=tf, mode="lines", name="T_fuel (K)", yaxis="y2"))
    if t and tm:
        fig.add_trace(go.Scatter(x=t, y=tm, mode="lines", name="T_moderator (K)", yaxis="y2"))
    fig.update_layout(
        title="Quick transient (power + temperatures)",
        xaxis_title="Time (s)",
        yaxis=dict(title="Power (W)"),
        yaxis2=dict(title="Temperature (K)", overlaying="y", side="right"),
        legend=dict(orientation="h"),
    )

    text = "\n".join(
        [
            "Quick transient demo (point kinetics)",
            f"  points: {len(t)}",
            f"  peak power (MW): {(max(p)/1e6):.3f}" if p else "  peak power: N/A",
        ]
    )
    return text, fig.to_dict()


def _demo_lumped_thermal() -> tuple[str, dict]:
    from smrforge.thermal.lumped import LumpedThermalHydraulics, ThermalLump, ThermalResistance

    fuel = ThermalLump(
        name="fuel",
        capacitance=1e8,
        temperature=1200.0,
        heat_source=lambda t: 1e6 if t < 100.0 else 1e5,
    )
    moderator = ThermalLump(
        name="moderator",
        capacitance=5e7,
        temperature=800.0,
        heat_source=lambda t: 0.0,
    )
    resistance = ThermalResistance(
        name="fuel_to_moderator",
        resistance=1e-3,
        lump1_name="fuel",
        lump2_name="moderator",
    )
    solver = LumpedThermalHydraulics(lumps={"fuel": fuel, "moderator": moderator}, resistances=[resistance])
    res = solver.solve_transient(t_span=(0.0, 3600.0), adaptive=True)

    t = res.get("time", [])
    tf = res.get("T_fuel", [])
    tm = res.get("T_moderator", [])

    fig = go.Figure()
    if t and tf:
        fig.add_trace(go.Scatter(x=t, y=tf, mode="lines", name="T_fuel (K)"))
    if t and tm:
        fig.add_trace(go.Scatter(x=t, y=tm, mode="lines", name="T_moderator (K)"))
    fig.update_layout(title="Lumped thermal (temperatures)", xaxis_title="Time (s)", yaxis_title="K")

    text = "\n".join(
        [
            "Lumped thermal demo (0-D)",
            f"  points: {len(t)}",
            f"  final T_fuel (K): {tf[-1]:.1f}" if tf else "  final T_fuel: N/A",
        ]
    )
    return text, fig.to_dict()


def _demo_parameter_sweep() -> tuple[str, dict]:
    from smrforge.workflows.parameter_sweep import ParameterSweep, SweepConfig

    cfg = SweepConfig(
        parameters={"enrichment": [0.15, 0.195, 0.24]},
        analysis_types=["keff"],
        reactor_template="valar-10",
        parallel=False,
    )
    sweep = ParameterSweep(cfg)
    result = sweep.run()
    df = result.to_dataframe()

    text = "\n".join(
        [
            "Parameter sweep demo",
            f"  cases: {len(result.results)} (failed: {len(result.failed_cases)})",
            "",
            "Columns:",
            f"  {list(df.columns)}" if hasattr(df, "columns") else "  (no dataframe)",
        ]
    )

    fig = go.Figure()
    if not df.empty and "k_eff" in df.columns:
        fig.add_trace(go.Scatter(x=df["parameters"].apply(lambda p: p["enrichment"]), y=df["k_eff"], mode="markers+lines"))
        fig.update_layout(title="k_eff vs enrichment", xaxis_title="enrichment", yaxis_title="k_eff")
    else:
        fig.update_layout(title="Sweep completed (no plotable data)")
    return text, fig.to_dict()


def _demo_uq_mc() -> tuple[str, dict]:
    from smrforge.uncertainty.uq import MonteCarloSampler, UncertainParameter
    import numpy as np

    params = [
        UncertainParameter(name="enrichment", distribution="normal", nominal=0.195, uncertainty=0.01),
        UncertainParameter(name="power_mw", distribution="uniform", nominal=10.0, uncertainty=(8.0, 12.0)),
    ]
    sampler = MonteCarloSampler(params)
    samples = sampler.sample_monte_carlo(1000, random_state=0)
    means = np.mean(samples, axis=0)
    stds = np.std(samples, axis=0)

    text = "\n".join(
        [
            "UQ demo (sampling only)",
            f"  n_samples: {samples.shape[0]}",
            f"  enrichment mean±std: {means[0]:.4f} ± {stds[0]:.4f}",
            f"  power_mw mean±std: {means[1]:.2f} ± {stds[1]:.2f}",
        ]
    )

    fig = go.Figure()
    fig.add_trace(go.Histogram(x=samples[:, 0], name="enrichment", opacity=0.6))
    fig.add_trace(go.Histogram(x=samples[:, 1], name="power_mw", opacity=0.6))
    fig.update_layout(barmode="overlay", title="UQ sampling histograms")
    return text, fig.to_dict()


def _demo_optimization() -> tuple[str, dict]:
    import numpy as np
    from smrforge.optimization.design import DesignOptimizer

    # Simple convex objective for a fast demo
    def obj(x: np.ndarray) -> float:
        return float((x[0] - 1.5) ** 2 + 0.1 * (x[1] + 0.5) ** 2)

    opt = DesignOptimizer(objective=obj, bounds=[(-5.0, 5.0), (-5.0, 5.0)], method="minimize")
    res = opt.optimize(max_iterations=50)

    text = "\n".join(
        [
            "Optimization demo",
            f"  success: {res.success}",
            f"  x_opt: {res.x_opt}",
            f"  f_opt: {res.f_opt:.6f}",
        ]
    )
    return text, _blank_figure("Optimization demo (no plot)")


def _demo_economics() -> tuple[str, dict]:
    from smrforge.economics.cost_modeling import CapitalCostEstimator, OperatingCostEstimator

    power_electric = 10e6 * 0.33  # 10 MWth at ~33% efficiency
    cap = CapitalCostEstimator(power_electric=power_electric, reactor_type="prismatic", nth_of_a_kind=1)
    op = OperatingCostEstimator(
        power_electric=power_electric,
        fuel_loading=150.0,
        cycle_length=3650.0,
        target_burnup=150.0,
        capacity_factor=0.95,
    )

    overnight = cap.estimate_overnight_cost()
    annual = op.estimate_total_annual_cost()
    breakdown = cap.get_cost_breakdown()

    text = "\n".join(
        [
            "Economics demo",
            f"  overnight cost (USD): {overnight:,.0f}",
            f"  annual opex (USD/yr): {annual:,.0f}",
        ]
    )

    fig = go.Figure()
    items = [(k, v) for k, v in breakdown.items() if k != "total_overnight_cost"]
    items = sorted(items, key=lambda kv: kv[1], reverse=True)[:10]
    fig.add_trace(go.Bar(x=[k for k, _ in items], y=[v for _, v in items]))
    fig.update_layout(title="Capital cost breakdown (top components)", xaxis_tickangle=-30, yaxis_title="USD")
    return text, fig.to_dict()


def _demo_control_pid() -> tuple[str, dict]:
    import numpy as np
    from smrforge.control.controllers import PIDController

    pid = PIDController(Kp=0.8, Ki=0.2, Kd=0.05, setpoint=1.0, output_min=0.0, output_max=2.0)

    t = np.linspace(0, 20, 401)
    y = np.zeros_like(t)
    u = np.zeros_like(t)

    # First-order plant: dy/dt = (u - y)/tau
    tau = 2.0
    for i in range(1, len(t)):
        dt = t[i] - t[i - 1]
        u[i] = pid.update(float(y[i - 1]), float(t[i]), float(dt))
        y[i] = y[i - 1] + dt * (u[i] - y[i - 1]) / tau

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=y, mode="lines", name="measurement"))
    fig.add_trace(go.Scatter(x=t, y=u, mode="lines", name="control output"))
    fig.update_layout(title="PID demo (step response)", xaxis_title="Time (s)")

    text = "\n".join(
        [
            "Control demo (PID)",
            f"  final measurement: {y[-1]:.3f}",
            f"  final output: {u[-1]:.3f}",
        ]
    )
    return text, fig.to_dict()


_DEMO_RUNNERS = {
    "presets": _demo_presets,
    "keff": _demo_keff,
    "viz_geometry": _demo_viz_geometry,
    "quick_transient": _demo_quick_transient,
    "lumped_thermal": _demo_lumped_thermal,
    "parameter_sweep": _demo_parameter_sweep,
    "uq_mc": _demo_uq_mc,
    "optimization": _demo_optimization,
    "economics": _demo_economics,
    "control_pid": _demo_control_pid,
}


def register_feature_lab_callbacks(app):
    """Register feature lab callbacks."""
    if not _DASH_AVAILABLE:  # pragma: no cover
        return

    @app.callback(
        Output("feature-demo-output", "children"),
        Output("feature-demo-graph", "figure"),
        Output("feature-demo-status", "children"),
        Output("feature-demo-status", "color"),
        Output("feature-demo-status", "is_open"),
        Input("run-feature-demo-button", "n_clicks"),
        State("feature-demo-dropdown", "value"),
        prevent_initial_call=True,
    )
    def run_demo(n_clicks, demo_id):
        if not n_clicks:
            raise PreventUpdate

        runner = _DEMO_RUNNERS.get(demo_id)
        if runner is None:
            return "", _blank_figure("Unknown demo"), "Unknown demo selected.", "warning", True

        try:
            text, fig = runner()
            return text, fig, "Demo completed.", "success", True
        except Exception as e:
            logger.error(f"Feature demo failed ({demo_id}): {e}", exc_info=True)
            return (
                f"Demo failed: {demo_id}\n\n{e}",
                _blank_figure("Demo failed"),
                f"Demo failed: {e}",
                "danger",
                True,
            )

