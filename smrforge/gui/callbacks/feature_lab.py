"""
Feature lab callbacks.
"""

from __future__ import annotations

try:
    import dash_bootstrap_components as dbc
    import plotly.graph_objects as go
    from dash import Input, Output, State
    from dash.exceptions import PreventUpdate

    _DASH_AVAILABLE = True
except ImportError:  # pragma: no cover
    _DASH_AVAILABLE = False

from smrforge.utils.logging import get_logger
from smrforge.visualization._viz_common import as_plotly_dict

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


def _demo_neutronics_dashboard() -> tuple[str, dict]:
    import numpy as np

    from smrforge.visualization.tally_data import plot_neutronics_dashboard

    # Synthetic multi-group flux: [nz, nr, ng]
    ng = 26
    nz, nr = 20, 15
    energy_groups = np.logspace(7, -5, ng + 1)
    group_centers = np.sqrt(energy_groups[:-1] * energy_groups[1:])
    spectrum_shape = np.exp(-0.8 * np.log10(group_centers / group_centers.min() + 1.0))
    spectrum_shape = spectrum_shape / np.max(spectrum_shape)

    # Spatially varying amplitude
    z = np.linspace(0, 1, nz)[:, None]
    r = np.linspace(0, 1, nr)[None, :]
    amp = np.exp(-3.0 * (r - 0.2) ** 2) * (0.8 + 0.2 * np.cos(2 * np.pi * z))
    flux = amp[:, :, None] * spectrum_shape[None, None, :]

    fig = plot_neutronics_dashboard(flux, energy_groups, k_eff=1.0000, backend="plotly")
    text = "\n".join(
        [
            "Neutronics dashboard demo (synthetic)",
            f"  flux shape: {flux.shape} (nz, nr, ng)",
            f"  ng: {ng}",
        ]
    )
    return text, as_plotly_dict(fig)


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
    if t is not None and p is not None and len(t) > 0 and len(p) > 0:
        fig.add_trace(go.Scatter(x=t, y=p, mode="lines", name="Power (W)"))
    if t is not None and tf is not None and len(t) > 0 and len(tf) > 0:
        fig.add_trace(
            go.Scatter(x=t, y=tf, mode="lines", name="T_fuel (K)", yaxis="y2")
        )
    if t is not None and tm is not None and len(t) > 0 and len(tm) > 0:
        fig.add_trace(
            go.Scatter(x=t, y=tm, mode="lines", name="T_moderator (K)", yaxis="y2")
        )
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
            (
                f"  peak power (MW): {(max(p)/1e6):.3f}"
                if p is not None and len(p) > 0
                else "  peak power: N/A"
            ),
        ]
    )
    return text, fig.to_dict()


def _demo_lumped_thermal() -> tuple[str, dict]:
    from smrforge.thermal.lumped import (
        LumpedThermalHydraulics,
        ThermalLump,
        ThermalResistance,
    )

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
    solver = LumpedThermalHydraulics(
        lumps={"fuel": fuel, "moderator": moderator}, resistances=[resistance]
    )
    res = solver.solve_transient(t_span=(0.0, 3600.0), adaptive=True)

    t = res.get("time", [])
    tf = res.get("T_fuel", [])
    tm = res.get("T_moderator", [])

    fig = go.Figure()
    if t is not None and tf is not None and len(t) > 0 and len(tf) > 0:
        fig.add_trace(go.Scatter(x=t, y=tf, mode="lines", name="T_fuel (K)"))
    if t is not None and tm is not None and len(t) > 0 and len(tm) > 0:
        fig.add_trace(go.Scatter(x=t, y=tm, mode="lines", name="T_moderator (K)"))
    fig.update_layout(
        title="Lumped thermal (temperatures)", xaxis_title="Time (s)", yaxis_title="K"
    )

    text = "\n".join(
        [
            "Lumped thermal demo (0-D)",
            f"  points: {len(t)}",
            (
                f"  final T_fuel (K): {tf[-1]:.1f}"
                if tf is not None and len(tf) > 0
                else "  final T_fuel: N/A"
            ),
        ]
    )
    return text, fig.to_dict()


def _demo_parameter_sweep() -> tuple[str, dict]:
    from smrforge.visualization.sweep_plots import plot_sweep_heatmap
    from smrforge.workflows.parameter_sweep import ParameterSweep, SweepConfig

    cfg = SweepConfig(
        parameters={"enrichment": [0.15, 0.195, 0.24], "power_mw": [8.0, 10.0, 12.0]},
        analysis_types=["keff"],
        # Use a custom base reactor name so create_reactor doesn't lock into a preset.
        reactor_template={"name": "sweep-demo"},
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

    if df.empty:
        return text, _blank_figure("Sweep completed (no data)")

    fig = plot_sweep_heatmap(
        result,
        x_param="enrichment",
        y_param="power_mw",
        metric="k_eff",
        backend="plotly",
    )
    return text, as_plotly_dict(fig)


def _demo_sweep_heatmap() -> tuple[str, dict]:
    from smrforge.visualization.sweep_plots import plot_sweep_heatmap
    from smrforge.workflows.parameter_sweep import ParameterSweep, SweepConfig

    cfg = SweepConfig(
        parameters={"enrichment": [0.15, 0.195, 0.24], "power_mw": [8.0, 10.0, 12.0]},
        analysis_types=["keff"],
        reactor_template={"name": "sweep-viz"},
        parallel=False,
    )
    res = ParameterSweep(cfg).run()
    fig = plot_sweep_heatmap(
        res, x_param="enrichment", y_param="power_mw", metric="k_eff", backend="plotly"
    )
    text = "\n".join(["Sweep visualization: heatmap", f"  cases: {len(res.results)}"])
    return text, as_plotly_dict(fig)


def _demo_sweep_tornado() -> tuple[str, dict]:
    from smrforge.visualization.sweep_plots import plot_sweep_tornado
    from smrforge.workflows.parameter_sweep import ParameterSweep, SweepConfig

    cfg = SweepConfig(
        parameters={"enrichment": [0.15, 0.195, 0.24], "power_mw": [8.0, 10.0, 12.0]},
        analysis_types=["keff"],
        reactor_template={"name": "sweep-viz"},
        parallel=False,
    )
    res = ParameterSweep(cfg).run()
    fig = plot_sweep_tornado(res, metric="k_eff", mode="range", backend="plotly")
    text = "\n".join(["Sweep visualization: tornado", f"  cases: {len(res.results)}"])
    return text, as_plotly_dict(fig)


def _demo_uq_mc() -> tuple[str, dict]:
    import numpy as np

    from smrforge.uncertainty.uq import MonteCarloSampler, UncertainParameter

    params = [
        UncertainParameter(
            name="enrichment", distribution="normal", nominal=0.195, uncertainty=0.01
        ),
        UncertainParameter(
            name="power_mw",
            distribution="uniform",
            nominal=10.0,
            uncertainty=(8.0, 12.0),
        ),
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


def _demo_uq_distribution() -> tuple[str, dict]:
    import numpy as np

    from smrforge.uncertainty.uq import UncertainParameter, UQResults
    from smrforge.uncertainty.visualization import plot_uq_distribution

    params = [
        UncertainParameter(
            name="enrichment", distribution="normal", nominal=0.195, uncertainty=0.01
        ),
        UncertainParameter(
            name="power_mw",
            distribution="uniform",
            nominal=10.0,
            uncertainty=(8.0, 12.0),
        ),
    ]
    n = 1000
    samples = np.column_stack(
        [p.sample(n, random_state=10 + i) for i, p in enumerate(params)]
    )
    # Simple model: keff responds mostly to enrichment, lightly to power
    keff = 1.0 + 0.8 * (samples[:, 0] - 0.195) - 0.002 * (samples[:, 1] - 10.0)
    outputs = keff.reshape(-1, 1)
    percentiles = {p: np.percentile(outputs, p, axis=0) for p in (5, 25, 50, 75, 95)}
    res = UQResults(
        parameter_names=[p.name for p in params],
        parameter_samples=samples,
        output_samples=outputs,
        output_names=["k_eff"],
        mean=np.mean(outputs, axis=0),
        std=np.std(outputs, axis=0),
        percentiles=percentiles,
    )
    fig = plot_uq_distribution(res, output_idx=0, backend="plotly")
    text = "\n".join(["UQ distribution demo (synthetic model)", f"  n_samples: {n}"])
    return text, as_plotly_dict(fig)


def _demo_uq_correlations() -> tuple[str, dict]:
    import numpy as np

    from smrforge.uncertainty.uq import UncertainParameter, UQResults
    from smrforge.uncertainty.visualization import plot_uq_correlation_matrix

    params = [
        UncertainParameter(
            name="enrichment", distribution="normal", nominal=0.195, uncertainty=0.01
        ),
        UncertainParameter(
            name="power_mw",
            distribution="uniform",
            nominal=10.0,
            uncertainty=(8.0, 12.0),
        ),
        UncertainParameter(
            name="core_height",
            distribution="uniform",
            nominal=200.0,
            uncertainty=(180.0, 220.0),
        ),
    ]
    n = 800
    samples = np.column_stack(
        [p.sample(n, random_state=20 + i) for i, p in enumerate(params)]
    )
    keff = (
        1.0
        + 0.9 * (samples[:, 0] - 0.195)
        - 0.001 * (samples[:, 1] - 10.0)
        + 0.0002 * (samples[:, 2] - 200.0)
    )
    outputs = keff.reshape(-1, 1)
    percentiles = {p: np.percentile(outputs, p, axis=0) for p in (5, 50, 95)}
    res = UQResults(
        parameter_names=[p.name for p in params],
        parameter_samples=samples,
        output_samples=outputs,
        output_names=["k_eff"],
        mean=np.mean(outputs, axis=0),
        std=np.std(outputs, axis=0),
        percentiles=percentiles,
    )
    fig = plot_uq_correlation_matrix(res, include_outputs=True, backend="plotly")
    text = "\n".join(["UQ correlations demo (synthetic model)", f"  n_samples: {n}"])
    return text, as_plotly_dict(fig)


def _demo_burnup_dashboard() -> tuple[str, dict]:
    import numpy as np

    from smrforge.burnup.solver import NuclideInventory
    from smrforge.core.reactor_core import Nuclide
    from smrforge.visualization.material_composition import plot_burnup_dashboard

    # Synthetic inventory (no nuclear data required)
    t_days = np.linspace(0.0, 365.0, 61)
    t_s = t_days * 24.0 * 3600.0
    burnup = 50.0 * (t_days / t_days.max())

    u235 = Nuclide(Z=92, A=235)
    u238 = Nuclide(Z=92, A=238)
    pu239 = Nuclide(Z=94, A=239)
    xe135 = Nuclide(Z=54, A=135)
    nuclides = [u235, u238, pu239, xe135]

    c_u235 = 1.0 * np.exp(-2.0 * t_days / t_days.max())
    c_u238 = 5.0 * np.ones_like(t_days)
    c_pu239 = 0.2 + 0.8 * (1.0 - np.exp(-3.0 * t_days / t_days.max()))
    c_xe = 1e-3 + 2e-2 * (1.0 - np.exp(-4.0 * t_days / t_days.max()))
    concentrations = np.vstack([c_u235, c_u238, c_pu239, c_xe])

    inv = NuclideInventory(
        nuclides=nuclides, concentrations=concentrations, times=t_s, burnup=burnup
    )
    fig = plot_burnup_dashboard(inv, backend="plotly")
    text = "\n".join(
        ["Burnup dashboard demo (synthetic inventory)", f"  steps: {len(t_days)}"]
    )
    return text, as_plotly_dict(fig)


def _demo_mesh_diagnostics() -> tuple[str, dict]:
    import numpy as np

    from smrforge.geometry.mesh_generation import AdvancedMeshGenerator
    from smrforge.visualization.mesh_diagnostics import plot_mesh_verification_dashboard

    rng = np.random.default_rng(0)
    pts = rng.normal(size=(200, 2))
    pts = pts / np.max(np.linalg.norm(pts, axis=1)) * 50.0
    gen = AdvancedMeshGenerator()
    vertices, triangles = gen.generate_2d_unstructured_mesh(points=pts)
    quality = gen.evaluate_mesh_quality(vertices, triangles)

    # Synthetic size distribution (lognormal)
    sizes = rng.lognormal(mean=0.0, sigma=0.7, size=500)
    fig = plot_mesh_verification_dashboard(
        quality=quality, sizes=sizes, backend="plotly"
    )
    text = "\n".join(
        [
            "Mesh diagnostics demo",
            f"  vertices: {len(vertices)}",
            f"  triangles: {len(triangles)}",
        ]
    )
    return text, as_plotly_dict(fig)


def _demo_validation_viz() -> tuple[str, dict]:
    from smrforge.validation.data_validation import ValidationLevel, ValidationResult
    from smrforge.visualization.validation_plots import (
        plot_validation_issues,
        plot_validation_summary,
    )

    res = ValidationResult(valid=True)
    res.add_issue(
        ValidationLevel.WARNING,
        "temperature",
        "Below expected minimum",
        value=250.0,
        expected=">= 273 K",
    )
    res.add_issue(
        ValidationLevel.ERROR,
        "pressure",
        "Negative pressure",
        value=-1.0,
        expected=">= 0 Pa",
    )
    res.add_issue(
        ValidationLevel.ERROR,
        "k_eff",
        "Unphysical criticality",
        value=4.2,
        expected="<= 3.0",
    )

    fig = plot_validation_summary(res, backend="plotly")
    # If user wants details, they can switch to issues plot; keep summary here.
    text = "\n".join(
        [
            "Validation visualization demo",
            f"  valid: {res.valid}",
            f"  issues: {len(res.issues)}",
        ]
    )
    return text, as_plotly_dict(fig)


def _demo_optimization() -> tuple[str, dict]:
    import numpy as np

    from smrforge.optimization.design import DesignOptimizer

    # Simple convex objective for a fast demo
    def obj(x: np.ndarray) -> float:
        return float((x[0] - 1.5) ** 2 + 0.1 * (x[1] + 0.5) ** 2)

    opt = DesignOptimizer(
        objective=obj, bounds=[(-5.0, 5.0), (-5.0, 5.0)], method="minimize"
    )
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


def _demo_optimization_trace() -> tuple[str, dict]:
    import numpy as np

    from smrforge.visualization.optimization_plots import plot_optimization_trace

    # Synthetic decreasing objective history (fast + deterministic).
    it = np.arange(40)
    hist = (1.0 / (1.0 + 0.15 * it)) + 0.01 * np.sin(it / 3.0)
    fig = plot_optimization_trace(
        hist, backend="plotly", title="Optimization trace (synthetic)"
    )
    text = "\n".join(["Optimization trace demo", f"  iterations: {len(hist)}"])
    return text, as_plotly_dict(fig)


def _demo_economics() -> tuple[str, dict]:
    from smrforge.economics.cost_modeling import (
        CapitalCostEstimator,
        OperatingCostEstimator,
    )

    power_electric = 10e6 * 0.33  # 10 MWth at ~33% efficiency
    cap = CapitalCostEstimator(
        power_electric=power_electric, reactor_type="prismatic", nth_of_a_kind=1
    )
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
    fig.update_layout(
        title="Capital cost breakdown (top components)",
        xaxis_tickangle=-30,
        yaxis_title="USD",
    )
    return text, fig.to_dict()


def _demo_economics_capex() -> tuple[str, dict]:
    from smrforge.economics.cost_modeling import (
        CapitalCostEstimator,
        LCOECalculator,
        OperatingCostEstimator,
    )
    from smrforge.visualization.economics_plots import plot_capex_breakdown

    power_electric = 10e6 * 0.33
    cap = CapitalCostEstimator(
        power_electric=power_electric, reactor_type="prismatic", nth_of_a_kind=1
    )
    overnight = cap.estimate_overnight_cost()
    breakdown = cap.get_cost_breakdown()
    fig = plot_capex_breakdown(
        breakdown, backend="plotly", kind="waterfall", title="CAPEX waterfall"
    )
    text = "\n".join(
        ["Economics demo: CAPEX waterfall", f"  overnight cost (USD): {overnight:,.0f}"]
    )
    return text, as_plotly_dict(fig)


def _demo_economics_lcoe() -> tuple[str, dict]:
    from smrforge.economics.cost_modeling import (
        CapitalCostEstimator,
        LCOECalculator,
        OperatingCostEstimator,
    )
    from smrforge.visualization.economics_plots import plot_lcoe_breakdown

    power_electric = 10e6 * 0.33
    cap = CapitalCostEstimator(
        power_electric=power_electric, reactor_type="prismatic", nth_of_a_kind=1
    )
    op = OperatingCostEstimator(
        power_electric=power_electric,
        fuel_loading=150.0,
        cycle_length=3650.0,
        target_burnup=150.0,
        capacity_factor=0.95,
    )
    lcoe = LCOECalculator(
        capital_cost=cap.estimate_overnight_cost(),
        power_electric=power_electric,
        operating_cost_estimator=op,
    )
    breakdown = lcoe.get_cost_breakdown()
    fig = plot_lcoe_breakdown(breakdown, backend="plotly", title="LCOE breakdown")
    text = "\n".join(
        [
            "Economics demo: LCOE",
            f"  total LCOE (USD/kWh): {breakdown.get('total_lcoe', lcoe.calculate_lcoe()):.4f}",
        ]
    )
    return text, as_plotly_dict(fig)


def _demo_control_pid() -> tuple[str, dict]:
    import numpy as np

    from smrforge.control.controllers import PIDController

    pid = PIDController(
        Kp=0.8, Ki=0.2, Kd=0.05, setpoint=1.0, output_min=0.0, output_max=2.0
    )

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
    "neutronics_dashboard": _demo_neutronics_dashboard,
    "quick_transient": _demo_quick_transient,
    "lumped_thermal": _demo_lumped_thermal,
    "parameter_sweep": _demo_parameter_sweep,
    "sweep_heatmap": _demo_sweep_heatmap,
    "sweep_tornado": _demo_sweep_tornado,
    "uq_mc": _demo_uq_mc,
    "uq_distribution": _demo_uq_distribution,
    "uq_correlations": _demo_uq_correlations,
    "burnup_dashboard": _demo_burnup_dashboard,
    "mesh_diagnostics": _demo_mesh_diagnostics,
    "validation_viz": _demo_validation_viz,
    "optimization": _demo_optimization,
    "optimization_trace": _demo_optimization_trace,
    "economics": _demo_economics,
    "economics_capex": _demo_economics_capex,
    "economics_lcoe": _demo_economics_lcoe,
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
            return (
                "",
                _blank_figure("Unknown demo"),
                "Unknown demo selected.",
                "warning",
                True,
            )

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
