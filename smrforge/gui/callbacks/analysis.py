"""
Analysis callbacks.
"""

try:
    import dash_bootstrap_components as dbc
    from dash import Input, Output, State, html
    from dash.exceptions import PreventUpdate

    _DASH_AVAILABLE = True
except ImportError:
    _DASH_AVAILABLE = False

from smrforge.utils.logging import get_logger

logger = get_logger(__name__)

from smrforge.gui.components.analysis_panel import (
    create_burnup_options,
    create_lumped_thermal_options,
    create_neutronics_options,
    create_quick_transient_options,
    create_safety_options,
)


def register_analysis_callbacks(app):
    """Register analysis callbacks."""
    if not _DASH_AVAILABLE:
        return

    @app.callback(
        Output("neutronics-options", "children"),
        Output("burnup-options", "children"),
        Output("quick-transient-options", "children"),
        Output("safety-options", "children"),
        Output("lumped-thermal-options", "children"),
        Output("run-analysis-button", "disabled"),
        Input("analysis-type-radio", "value"),
        Input("reactor-spec-store", "data"),
        prevent_initial_call=False,
    )
    def update_analysis_options(analysis_type, reactor_spec):
        """Update analysis options based on selected type."""
        # Check if reactor_spec has actual data (not just empty dict)
        has_reactor = bool(reactor_spec) and (
            isinstance(reactor_spec, dict) and len(reactor_spec) > 0
        )
        logger.debug(
            f"update_analysis_options: has_reactor={has_reactor}, reactor_spec type={type(reactor_spec)}, keys={list(reactor_spec.keys())[:5] if isinstance(reactor_spec, dict) else 'N/A'}"
        )

        # Quick transient and lumped thermal don't require a reactor spec
        # Note: All option components are always in the layout (hidden initially)
        # We just update their visibility based on analysis type
        # Always return all components to keep them in DOM for State validation
        if analysis_type == "neutronics":
            return (
                create_neutronics_options(),
                create_burnup_options(),  # Keep in DOM, just hidden
                create_quick_transient_options(),  # Keep in DOM, just hidden
                create_safety_options(),  # Keep in DOM, just hidden
                create_lumped_thermal_options(),  # Keep in DOM, just hidden
                not has_reactor,
            )
        elif analysis_type == "burnup":
            return (
                create_neutronics_options(),  # Keep in DOM, just hidden
                create_burnup_options(),
                create_quick_transient_options(),  # Keep in DOM, just hidden
                create_safety_options(),  # Keep in DOM, just hidden
                create_lumped_thermal_options(),  # Keep in DOM, just hidden
                not has_reactor,
            )
        elif analysis_type == "quick_transient":
            return (
                create_neutronics_options(),  # Keep in DOM, just hidden
                create_burnup_options(),  # Keep in DOM, just hidden
                create_quick_transient_options(),
                create_safety_options(),  # Keep in DOM, just hidden
                create_lumped_thermal_options(),  # Keep in DOM, just hidden
                False,
            )
        elif analysis_type == "safety":
            return (
                create_neutronics_options(),  # Keep in DOM, just hidden
                create_burnup_options(),  # Keep in DOM, just hidden
                create_quick_transient_options(),  # Keep in DOM, just hidden
                create_safety_options(),
                create_lumped_thermal_options(),  # Keep in DOM, just hidden
                not has_reactor,
            )
        elif analysis_type == "lumped_thermal":
            return (
                create_neutronics_options(),  # Keep in DOM, just hidden
                create_burnup_options(),  # Keep in DOM, just hidden
                create_quick_transient_options(),  # Keep in DOM, just hidden
                create_safety_options(),  # Keep in DOM, just hidden
                create_lumped_thermal_options(),
                False,
            )
        else:  # complete
            return (
                create_neutronics_options(),
                create_burnup_options(),
                create_quick_transient_options(),  # Keep in DOM, just hidden
                create_safety_options(),
                create_lumped_thermal_options(),  # Keep in DOM, just hidden
                not has_reactor,
            )

    @app.callback(
        Output("analysis-results-store", "data"),
        Output("analysis-feedback", "children"),
        Output("analysis-progress", "children"),
        Input("run-analysis-button", "n_clicks"),
        State("analysis-type-radio", "value"),
        State("reactor-spec-store", "data"),
        State("neutronics-max-iter", "value"),
        State("neutronics-tolerance", "value"),
        State("burnup-time-steps", "value"),
        State("burnup-power-density", "value"),
        State("quick-transient-type-dropdown", "value"),
        State("quick-transient-duration", "value"),
        State("quick-transient-power", "value"),
        State("quick-transient-temperature", "value"),
        State("quick-transient-reactivity", "value"),
        State("quick-transient-scram-available", "value"),
        State("quick-transient-scram-delay", "value"),
        State("quick-transient-long-term", "value"),
        State("transient-type-dropdown", "value"),
        State("transient-time", "value"),
        State("lumped-thermal-duration", "value"),
        State("lumped-thermal-max-step", "value"),
        State("lumped-thermal-adaptive", "value"),
        prevent_initial_call=True,
    )
    def run_analysis(
        n_clicks,
        analysis_type,
        reactor_spec,
        max_iter,
        tolerance,
        time_steps,
        power_density,
        quick_transient_type,
        quick_transient_duration,
        quick_transient_power,
        quick_transient_temperature,
        quick_transient_reactivity,
        quick_transient_scram_available,
        quick_transient_scram_delay,
        quick_transient_long_term,
        transient_type,
        transient_time,
        lumped_thermal_duration,
        lumped_thermal_max_step,
        lumped_thermal_adaptive,
    ):
        """Run analysis."""
        logger.info(f"Running {analysis_type} analysis")

        # Quick transient and lumped thermal don't require reactor spec
        requires_reactor = analysis_type in [
            "neutronics",
            "burnup",
            "safety",
            "complete",
        ]

        # Check if reactor_spec has actual data (not just empty dict)
        if requires_reactor and (
            not reactor_spec
            or (isinstance(reactor_spec, dict) and len(reactor_spec) == 0)
        ):
            logger.warning("No reactor specification available for analysis")
            return (
                {},
                dbc.Alert(
                    "No reactor specification available. Create a reactor first.",
                    color="warning",
                ),
                "",
            )

        results = {}

        try:
            import numpy as np

            # Only create reactor if needed
            if requires_reactor:
                import smrforge as smr
                from smrforge.validation.models import ReactorSpecification

                # Create reactor from spec
                # Ensure reactor_spec is a dict and has all required fields
                if not isinstance(reactor_spec, dict):
                    logger.error("Invalid reactor specification format")
                    return (
                        {},
                        dbc.Alert(
                            "Invalid reactor specification format.", color="danger"
                        ),
                        "",
                    )

                spec = ReactorSpecification(**reactor_spec)
                logger.info(f"Creating reactor from spec: {spec.name}")

                # Create reactor with all spec parameters
                reactor = smr.create_reactor(
                    power_mw=spec.power_thermal / 1e6,
                    core_height=spec.core_height,
                    core_diameter=spec.core_diameter,
                    enrichment=spec.enrichment,
                    reactor_type=(
                        spec.reactor_type.value
                        if hasattr(spec.reactor_type, "value")
                        else str(spec.reactor_type)
                    ),
                    fuel_type=(
                        spec.fuel_type.value
                        if hasattr(spec.fuel_type, "value")
                        else str(spec.fuel_type)
                    ),
                )
                logger.info("Reactor created successfully")
            else:
                reactor = None

            if analysis_type in ["neutronics", "complete"]:
                # Run neutronics
                logger.info("Running neutronics analysis")
                try:
                    # solve_keff() may raise ValueError if validation fails, but it handles
                    # it internally and returns k_eff anyway. We catch it here just in case.
                    import warnings

                    with warnings.catch_warnings(record=True) as w:
                        warnings.simplefilter("always")
                        k_eff = reactor.solve_keff()

                        # Check if there were validation warnings
                        validation_warning = None
                        for warning in w:
                            if "validation" in str(warning.message).lower():
                                validation_warning = str(warning.message)
                                logger.warning(
                                    f"Solution validation warning: {validation_warning}"
                                )

                        # Try to get flux and power distribution from solver
                        flux_data = None
                        power_data = None
                        if hasattr(reactor, "_solver") and reactor._solver is not None:
                            solver = reactor._solver
                            if hasattr(solver, "flux") and solver.flux is not None:
                                # Extract flux data (flatten for storage)
                                flux = solver.flux
                                if flux is not None and flux.size > 0:
                                    # Store flux statistics and sample data
                                    flux_data = {
                                        "max": float(np.max(flux)),
                                        "min": float(np.min(flux)),
                                        "mean": float(np.mean(flux)),
                                        "shape": list(flux.shape),
                                        "sample": (
                                            flux.flatten()[:1000].tolist()
                                            if flux.size > 1000
                                            else flux.flatten().tolist()
                                        ),
                                    }

                            if hasattr(solver, "compute_power_distribution"):
                                try:
                                    power = solver.compute_power_distribution(
                                        spec.power_thermal
                                    )
                                    if power is not None and power.size > 0:
                                        power_data = {
                                            "max": float(np.max(power)),
                                            "min": float(np.min(power)),
                                            "mean": float(np.mean(power)),
                                            "shape": list(power.shape),
                                            "sample": (
                                                power.flatten()[:1000].tolist()
                                                if power.size > 1000
                                                else power.flatten().tolist()
                                            ),
                                        }
                                except Exception as e:
                                    logger.debug(
                                        f"Could not compute power distribution: {e}"
                                    )

                        results["neutronics"] = {
                            "k_eff": float(k_eff),
                            "status": "success",
                        }
                        if flux_data:
                            results["neutronics"]["flux"] = flux_data
                        if power_data:
                            results["neutronics"]["power"] = power_data
                        if validation_warning:
                            # Use the actual warning message, or provide a more informative one
                            warning_msg = str(validation_warning)
                            # Extract key info if available (k_eff value, etc.)
                            if "k_eff" in warning_msg:
                                results["neutronics"]["warning"] = warning_msg
                            else:
                                results["neutronics"][
                                    "warning"
                                ] = f"Solution validation warning: {warning_msg[:200]}"

                        logger.info(
                            f"Neutronics analysis completed: k_eff = {k_eff:.6f}"
                        )
                except Exception as e:
                    logger.error(f"Neutronics analysis failed: {e}", exc_info=True)
                    # Try to get k_eff from solver if it exists
                    if hasattr(reactor, "_solver") and reactor._solver is not None:
                        if (
                            hasattr(reactor._solver, "k_eff")
                            and reactor._solver.k_eff is not None
                        ):
                            k_eff = reactor._solver.k_eff
                            results["neutronics"] = {
                                "k_eff": float(k_eff),
                                "status": "success",
                                "warning": f"Analysis completed with errors: {str(e)[:100]}",
                            }
                            logger.warning(
                                f"Using k_eff from solver despite error: {k_eff:.6f}"
                            )
                        else:
                            results["neutronics"] = {"status": "error", "error": str(e)}
                    else:
                        results["neutronics"] = {"status": "error", "error": str(e)}

            if analysis_type in ["burnup", "complete"]:
                logger.info("Running burnup analysis")
                # Best-effort: attempt full burnup solver; fall back to a lightweight model.
                try:
                    from smrforge.burnup.solver import BurnupOptions, BurnupSolver

                    # Parse time steps (days)
                    steps = []
                    if time_steps:
                        for part in str(time_steps).split(","):
                            part = part.strip()
                            if part:
                                steps.append(float(part))
                    if not steps:
                        steps = [0.0, 365.0, 730.0]

                    opts = BurnupOptions(
                        time_steps=steps,
                        power_density=float(power_density) if power_density else 1e6,
                        initial_enrichment=float(spec.enrichment),
                    )
                    burn = BurnupSolver(reactor._get_solver(), opts)
                    inv = burn.solve()

                    results["burnup"] = {
                        "status": "success",
                        "time_days": [float(x) for x in steps],
                        "burnup_mwd_per_kg": [float(x) for x in inv.burnup.tolist()],
                        "message": "Burnup solver completed",
                    }
                except Exception as e:
                    logger.warning(
                        f"Full burnup solver unavailable, using simplified model: {e}"
                    )
                    # Simplified burnup: compute MWd/kgU from power and heavy metal loading
                    # and apply an exponential depletion of effective enrichment.
                    steps = []
                    if time_steps:
                        for part in str(time_steps).split(","):
                            part = part.strip()
                            if part:
                                steps.append(float(part))
                    if not steps:
                        steps = [0.0, 365.0, 730.0]

                    power_mw = float(spec.power_thermal) / 1e6
                    hm_kg = float(getattr(spec, "heavy_metal_loading", 150.0) or 150.0)
                    burnup = []
                    eff_enr = []
                    for d in steps:
                        b = (
                            power_mw * d / hm_kg
                        )  # MWd/kg (capacity factor omitted for simplicity)
                        burnup.append(float(b))
                        eff_enr.append(
                            float(spec.enrichment) * float(np.exp(-b / 50.0))
                        )

                    results["burnup"] = {
                        "status": "success",
                        "time_days": [float(x) for x in steps],
                        "burnup_mwd_per_kg": burnup,
                        "effective_enrichment": eff_enr,
                        "message": "Simplified burnup completed (configure ENDF for full depletion physics)",
                        "warning": str(e),
                    }

            if analysis_type in ["quick_transient"]:
                # Run quick transient analysis
                logger.info("Running quick transient analysis")
                try:
                    from smrforge.convenience.transients import quick_transient

                    # Use parameters from UI
                    power = (
                        float(quick_transient_power) if quick_transient_power else 1e6
                    )
                    temperature = (
                        float(quick_transient_temperature)
                        if quick_transient_temperature
                        else 1200.0
                    )
                    transient_type_val = (
                        quick_transient_type
                        if quick_transient_type
                        else "reactivity_insertion"
                    )
                    duration = (
                        float(quick_transient_duration)
                        if quick_transient_duration
                        else 100.0
                    )
                    reactivity = (
                        float(quick_transient_reactivity)
                        if quick_transient_reactivity
                        else 0.001
                    )
                    scram_available = (
                        bool(quick_transient_scram_available)
                        if quick_transient_scram_available
                        else True
                    )
                    scram_delay = (
                        float(quick_transient_scram_delay)
                        if quick_transient_scram_delay
                        else 1.0
                    )
                    long_term = (
                        bool(quick_transient_long_term)
                        if quick_transient_long_term
                        else False
                    )

                    transient_result = quick_transient(
                        power=power,
                        temperature=temperature,
                        transient_type=transient_type_val,
                        reactivity_insertion=(
                            reactivity
                            if transient_type_val
                            in ["reactivity_insertion", "reactivity_step"]
                            else None
                        ),
                        duration=duration,
                        scram_available=scram_available,
                        scram_delay=scram_delay,
                        long_term_optimization=long_term if duration > 86400 else False,
                        plot=False,  # Plot will be handled separately in UI
                    )

                    results["quick_transient"] = {
                        "status": "success",
                        "time": transient_result.get("time", []),
                        "power": transient_result.get("power", []),
                        "T_fuel": transient_result.get("T_fuel", []),
                        "T_moderator": transient_result.get("T_moderator", []),
                        "reactivity": transient_result.get("reactivity", []),
                    }
                except Exception as e:
                    logger.error(f"Quick transient analysis failed: {e}", exc_info=True)
                    results["quick_transient"] = {"status": "error", "error": str(e)}

            if analysis_type in ["lumped_thermal"]:
                # Run lumped thermal hydraulics
                logger.info("Running lumped thermal hydraulics analysis")
                try:
                    from smrforge.thermal.lumped import (
                        LumpedThermalHydraulics,
                        ThermalLump,
                        ThermalResistance,
                    )

                    # Use parameters from UI
                    duration = (
                        float(lumped_thermal_duration)
                        if lumped_thermal_duration
                        else 3600.0
                    )
                    max_step = (
                        float(lumped_thermal_max_step)
                        if lumped_thermal_max_step
                        else 3600.0
                    )
                    adaptive = (
                        bool(lumped_thermal_adaptive)
                        if lumped_thermal_adaptive
                        else True
                    )

                    # Create default 2-lump system (fuel + moderator)
                    fuel = ThermalLump(
                        name="fuel",
                        capacitance=1e8,  # J/K
                        temperature=1200.0,  # K
                        heat_source=lambda t: 1e6 if t < 100.0 else 1e5,  # Decay heat
                    )
                    moderator = ThermalLump(
                        name="moderator",
                        capacitance=5e7,  # J/K
                        temperature=800.0,  # K
                        heat_source=lambda t: 0.0,
                    )
                    resistance = ThermalResistance(
                        name="fuel_to_moderator",
                        resistance=1e-3,  # K/W
                        lump1_name="fuel",
                        lump2_name="moderator",
                    )

                    solver = LumpedThermalHydraulics(
                        lumps={"fuel": fuel, "moderator": moderator},
                        resistances=[resistance],
                    )

                    # Pass adaptive and max_step to solve_transient, not __init__
                    thermal_result = solver.solve_transient(
                        t_span=(0.0, duration),
                        max_step=max_step if not adaptive else None,
                        adaptive=adaptive,
                    )

                    results["lumped_thermal"] = {
                        "status": "success",
                        "result": {
                            "time": thermal_result.get("time", []),
                            "T_fuel": thermal_result.get("T_fuel", []),
                            "T_moderator": thermal_result.get("T_moderator", []),
                        },
                    }
                except Exception as e:
                    logger.error(f"Lumped thermal analysis failed: {e}", exc_info=True)
                    results["lumped_thermal"] = {"status": "error", "error": str(e)}

            if analysis_type in ["safety", "complete"]:
                logger.info("Running safety analysis (point kinetics)")
                try:
                    import numpy as _np

                    from smrforge.safety.transients import (
                        PointKineticsParameters,
                        PointKineticsSolver,
                    )

                    # Typical 6-group delayed neutron parameters (representative)
                    beta = _np.array(
                        [0.00021, 0.00141, 0.00127, 0.00255, 0.00074, 0.00027]
                    )
                    lambda_d = _np.array([0.0127, 0.0317, 0.115, 0.311, 1.40, 3.87])

                    params = PointKineticsParameters(
                        beta=beta,
                        lambda_d=lambda_d,
                        alpha_fuel=-5e-5,
                        alpha_moderator=-2e-5,
                        Lambda=1e-4,
                        fuel_heat_capacity=1e6,
                        moderator_heat_capacity=5e6,
                    )
                    solver = PointKineticsSolver(params)

                    t_end = float(transient_time) if transient_time else 3600.0

                    # Map UI transient type into a simple reactivity/power-removal scenario
                    scram_time = 5.0
                    scram_rho = -0.05
                    if transient_type == "slb":
                        # mild positive insertion then scram
                        def rho_ext(t: float) -> float:
                            return 0.001 if t < scram_time else scram_rho

                        def q_removal(t: float, T_fuel: float, T_mod: float) -> float:
                            return float(spec.power_thermal) * (
                                0.95 if t < scram_time else 0.10
                            )

                    elif transient_type == "lofc":

                        def rho_ext(t: float) -> float:
                            return 0.0 if t < scram_time else scram_rho

                        def q_removal(t: float, T_fuel: float, T_mod: float) -> float:
                            return float(spec.power_thermal) * (
                                0.50 if t < scram_time else 0.08
                            )

                    else:

                        def rho_ext(t: float) -> float:
                            return 0.0 if t < scram_time else scram_rho

                        def q_removal(t: float, T_fuel: float, T_mod: float) -> float:
                            return float(spec.power_thermal) * (
                                0.80 if t < scram_time else 0.10
                            )

                    initial = {
                        "power": float(spec.power_thermal),
                        "T_fuel": float(
                            getattr(
                                spec, "max_fuel_temperature", spec.outlet_temperature
                            )
                        ),
                        "T_mod": float(spec.outlet_temperature),
                    }
                    pk = solver.solve_transient(
                        rho_external=rho_ext,
                        power_removal=q_removal,
                        initial_state=initial,
                        t_span=(0.0, t_end),
                        adaptive=True,
                        long_term_optimization=(t_end > 86400),
                    )

                    results["safety"] = {
                        "status": "success",
                        "message": "Safety transient completed (point kinetics)",
                        "time": pk.get("time", []),
                        "power": pk.get("power", []),
                        "T_fuel": pk.get("T_fuel", []),
                        "T_moderator": pk.get("T_mod", pk.get("T_moderator", [])),
                        "reactivity": pk.get("reactivity", []),
                    }
                except Exception as e:
                    logger.error(f"Safety analysis failed: {e}", exc_info=True)
                    results["safety"] = {"status": "error", "error": str(e)}

            # Check if any analysis failed
            has_errors = any(r.get("status") == "error" for r in results.values())
            has_warnings = any("warning" in r for r in results.values())

            if has_errors:
                error_details = [
                    f"{k}: {r.get('error', 'Unknown error')}"
                    for k, r in results.items()
                    if r.get("status") == "error"
                ]
                feedback = dbc.Alert(
                    html.Div(
                        [
                            html.Strong("Analysis completed with errors:"),
                            html.Ul([html.Li(err) for err in error_details]),
                        ]
                    ),
                    color="warning",
                )
            elif has_warnings:
                # Show warnings but still indicate success
                warning_details = []
                success_details = []
                for k, r in results.items():
                    if "warning" in r:
                        warning_details.append(f"{k}: {r.get('warning', '')}")
                    if r.get("status") == "success":
                        if "k_eff" in r:
                            success_details.append(f"k-eff = {r['k_eff']:.6f}")

                feedback = dbc.Alert(
                    html.Div(
                        [
                            html.Strong("✓ Analysis completed with warnings:"),
                            html.Ul([html.Li(w) for w in warning_details]),
                            html.P(
                                [html.Strong("Results: "), ", ".join(success_details)]
                            ),
                        ]
                    ),
                    color="info",
                )
            else:
                # Format success message with results
                result_details = []
                for k, r in results.items():
                    if r.get("status") == "success":
                        if "k_eff" in r:
                            result_details.append(f"k-eff = {r['k_eff']:.6f}")
                        elif "message" in r:
                            result_details.append(r["message"])

                result_text = (
                    f"✓ {analysis_type.capitalize()} analysis completed successfully!"
                )
                if result_details:
                    result_text += f" Results: {', '.join(result_details)}"

                feedback = dbc.Alert(result_text, color="success")

            return results, feedback, ""

        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            # Provide more helpful error messages
            error_msg = str(e)
            if "validation" in error_msg.lower():
                error_msg = "Reactor specification validation failed. Please check all required fields are present."
            elif "solve" in error_msg.lower() or "neutronics" in error_msg.lower():
                error_msg = f"Neutronics solver error: {error_msg[:200]}"

            feedback = dbc.Alert(
                html.Div([html.Strong("Analysis Error:"), html.P(error_msg)]),
                color="danger",
            )
            return {}, feedback, ""
