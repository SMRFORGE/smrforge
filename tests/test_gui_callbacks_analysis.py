import builtins
import importlib
import sys
import warnings
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


def _import_module_without_dash(module_name: str):
    import smrforge.gui.components  # noqa: F401

    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "dash" or name.startswith("dash."):
            raise ImportError("forced dash ImportError for coverage")
        if name == "dash_bootstrap_components":
            raise ImportError("forced dbc ImportError for coverage")
        return real_import(name, globals, locals, fromlist, level)

    sys.modules.pop(module_name, None)
    with patch("builtins.__import__", side_effect=guarded_import):
        return importlib.import_module(module_name)


def test_register_analysis_callbacks_no_dash_returns_early():
    mod = _import_module_without_dash("smrforge.gui.callbacks.analysis")
    assert mod._DASH_AVAILABLE is False
    app = DummyApp()
    assert mod.register_analysis_callbacks(app) is None
    assert app.callbacks == []


def test_analysis_callbacks_cover_update_options_and_run_paths():
    import dash_bootstrap_components as dbc

    from smrforge.gui.callbacks import analysis as an

    an = importlib.reload(an)
    assert an._DASH_AVAILABLE is True

    app = DummyApp()
    an.register_analysis_callbacks(app)
    by_name = {fn.__name__: fn for fn in app.callbacks}

    update_analysis_options = by_name["update_analysis_options"]
    run_analysis = by_name["run_analysis"]

    # update_analysis_options: all branches + has_reactor
    for t in [
        "neutronics",
        "burnup",
        "quick_transient",
        "safety",
        "lumped_thermal",
        "complete",
        "other",
    ]:
        out = update_analysis_options(t, {"x": 1})
        assert isinstance(out, tuple) and len(out) == 6
        assert (
            out[-1] is False
        )  # run button enabled when reactor exists (except quick/lumped)
    out = update_analysis_options("neutronics", {})
    assert out[-1] is True  # disabled without reactor

    # Helper: Dummy spec + reactor
    class DummySpec:
        def __init__(self, **kwargs):
            self.name = kwargs.get("name", "R")
            self.power_thermal = kwargs.get("power_thermal", 10e6)
            self.core_height = kwargs.get("core_height", 200.0)
            self.core_diameter = kwargs.get("core_diameter", 100.0)
            self.enrichment = kwargs.get("enrichment", 0.195)
            self.reactor_type = kwargs.get("reactor_type", "prismatic")
            self.fuel_type = kwargs.get("fuel_type", "UCO")
            self.outlet_temperature = kwargs.get("outlet_temperature", 900.0)
            self.inlet_temperature = kwargs.get("inlet_temperature", 800.0)
            self.max_fuel_temperature = kwargs.get("max_fuel_temperature", 1400.0)
            self.heavy_metal_loading = kwargs.get("heavy_metal_loading", 150.0)

    class DummySolver:
        def __init__(self):
            self.k_eff = 1.001
            self.flux = None

        def compute_power_distribution(self, *_args, **_kwargs):
            import numpy as np

            return np.array([10.0, 20.0, 30.0])

    class DummyReactor:
        def __init__(self, solve_keff_behavior="ok", include_solver=True, flux_size=3):
            self._behavior = solve_keff_behavior
            self._solver = DummySolver() if include_solver else None
            if self._solver is not None:
                import numpy as np

                self._solver.flux = np.linspace(1.0, float(flux_size), flux_size)

        def solve_keff(self):
            if self._behavior == "warn_with_keff":
                warnings.warn("validation: k_eff check", UserWarning)
                return 1.0001
            if self._behavior == "warn_no_keff":
                warnings.warn("validation: solver check", UserWarning)
                return 1.0002
            if self._behavior == "raise":
                raise RuntimeError("neutronics solve failed")
            return 1.0000

        def _get_solver(self):
            return object()

    reactor_spec = {
        "name": "R",
        "power_thermal": 10e6,
        "core_height": 200.0,
        "core_diameter": 100.0,
        "enrichment": 0.195,
        "reactor_type": "prismatic",
        "fuel_type": "UCO",
    }

    # Early return: requires reactor but reactor_spec empty
    out_results, feedback, progress = run_analysis(
        1,
        "neutronics",
        {},
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )
    assert out_results == {}
    assert isinstance(feedback, dbc.Alert)
    assert progress == ""

    # Invalid reactor_spec format
    out_results, feedback, progress = run_analysis(
        1,
        "neutronics",
        "not a dict",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )
    assert out_results == {}
    assert isinstance(feedback, dbc.Alert)

    # Neutronics success + warning path (validation warning contains 'k_eff')
    with (
        patch("smrforge.validation.models.ReactorSpecification", DummySpec),
        patch(
            "smrforge.create_reactor",
            return_value=DummyReactor(
                solve_keff_behavior="warn_with_keff", flux_size=2000
            ),
        ),
    ):
        out_results, feedback, progress = run_analysis(
            1,
            "neutronics",
            reactor_spec,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        assert "neutronics" in out_results
        assert isinstance(feedback, dbc.Alert)

    # Neutronics warning path (validation warning without 'k_eff' -> else formatting)
    with (
        patch("smrforge.validation.models.ReactorSpecification", DummySpec),
        patch(
            "smrforge.create_reactor",
            return_value=DummyReactor(solve_keff_behavior="warn_no_keff", flux_size=3),
        ),
    ):
        out_results, feedback, progress = run_analysis(
            1,
            "neutronics",
            reactor_spec,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        assert out_results.get("neutronics", {}).get("status") == "success"

    # Neutronics: cover compute_power_distribution exception logging branch
    reactor_with_bad_power = DummyReactor(solve_keff_behavior="ok", flux_size=3)

    def _raise_power(*_args, **_kwargs):
        raise RuntimeError("no power")

    reactor_with_bad_power._solver.compute_power_distribution = _raise_power
    with (
        patch("smrforge.validation.models.ReactorSpecification", DummySpec),
        patch("smrforge.create_reactor", return_value=reactor_with_bad_power),
    ):
        out_results, feedback, progress = run_analysis(
            1,
            "neutronics",
            reactor_spec,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        assert out_results.get("neutronics", {}).get("status") == "success"

    # Neutronics exception: fallback to solver.k_eff
    with (
        patch("smrforge.validation.models.ReactorSpecification", DummySpec),
        patch(
            "smrforge.create_reactor",
            return_value=DummyReactor(solve_keff_behavior="raise"),
        ),
    ):
        out_results, feedback, progress = run_analysis(
            1,
            "neutronics",
            reactor_spec,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        assert out_results.get("neutronics", {}).get("status") in ("success", "error")

    # Neutronics exception: solver exists but no k_eff -> error status
    bad_solver_reactor = DummyReactor(solve_keff_behavior="raise")
    bad_solver_reactor._solver.k_eff = None
    with (
        patch("smrforge.validation.models.ReactorSpecification", DummySpec),
        patch("smrforge.create_reactor", return_value=bad_solver_reactor),
    ):
        out_results, feedback, progress = run_analysis(
            1,
            "neutronics",
            reactor_spec,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        assert out_results.get("neutronics", {}).get("status") == "error"

    # Neutronics exception: no solver -> error status
    with (
        patch("smrforge.validation.models.ReactorSpecification", DummySpec),
        patch(
            "smrforge.create_reactor",
            return_value=DummyReactor(
                solve_keff_behavior="raise", include_solver=False
            ),
        ),
    ):
        out_results, feedback, progress = run_analysis(
            1,
            "neutronics",
            reactor_spec,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        assert out_results.get("neutronics", {}).get("status") == "error"

    # Burnup: full solver path (stub)
    class DummyInv:
        def __init__(self):
            import numpy as np

            self.burnup = np.array([0.0, 1.0, 2.0])

    class DummyBurnSolver:
        def __init__(self, *_args, **_kwargs):
            pass

        def solve(self):
            return DummyInv()

    with (
        patch("smrforge.validation.models.ReactorSpecification", DummySpec),
        patch("smrforge.create_reactor", return_value=DummyReactor()),
        patch("smrforge.burnup.solver.BurnupSolver", DummyBurnSolver),
    ):
        out_results, feedback, progress = run_analysis(
            1,
            "burnup",
            reactor_spec,
            None,
            None,
            "0, 1, 2",
            1e6,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        assert out_results.get("burnup", {}).get("status") == "success"

    # Burnup: simplified model fallback (force exception)
    with (
        patch("smrforge.validation.models.ReactorSpecification", DummySpec),
        patch("smrforge.create_reactor", return_value=DummyReactor()),
        patch(
            "smrforge.burnup.solver.BurnupSolver", side_effect=RuntimeError("no solver")
        ),
    ):
        out_results, feedback, progress = run_analysis(
            1,
            "burnup",
            reactor_spec,
            None,
            None,
            "0, 10",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        assert "warning" in out_results.get("burnup", {})

    # Quick transient success and error
    with patch(
        "smrforge.convenience.transients.quick_transient",
        return_value={
            "time": [0, 1],
            "power": [1, 2],
            "T_fuel": [10, 11],
            "T_moderator": [9, 10],
            "reactivity": [0.0, 0.1],
        },
    ):
        out_results, feedback, progress = run_analysis(
            1,
            "quick_transient",
            {},
            None,
            None,
            None,
            None,
            "reactivity_insertion",
            10.0,
            1e6,
            1200.0,
            0.001,
            True,
            1.0,
            False,
            None,
            None,
            None,
            None,
            None,
        )
        assert out_results.get("quick_transient", {}).get("status") == "success"

    with patch(
        "smrforge.convenience.transients.quick_transient",
        side_effect=RuntimeError("boom"),
    ):
        out_results, feedback, progress = run_analysis(
            1,
            "quick_transient",
            {},
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        assert out_results.get("quick_transient", {}).get("status") == "error"

    # Lumped thermal success + error
    class DummyLumped:
        def __init__(self, *args, **kwargs):
            pass

        def solve_transient(self, **kwargs):
            return {"time": [0, 1], "T_fuel": [1, 2], "T_moderator": [3, 4]}

    with (
        patch("smrforge.thermal.lumped.LumpedThermalHydraulics", DummyLumped),
        patch("smrforge.thermal.lumped.ThermalLump", lambda **kwargs: object()),
        patch("smrforge.thermal.lumped.ThermalResistance", lambda **kwargs: object()),
    ):
        out_results, feedback, progress = run_analysis(
            1,
            "lumped_thermal",
            {},
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            10.0,
            1.0,
            True,
        )
        assert out_results.get("lumped_thermal", {}).get("status") == "success"

    with patch(
        "smrforge.thermal.lumped.LumpedThermalHydraulics",
        side_effect=RuntimeError("fail"),
    ):
        out_results, feedback, progress = run_analysis(
            1,
            "lumped_thermal",
            {},
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            10.0,
            1.0,
            True,
        )
        assert out_results.get("lumped_thermal", {}).get("status") == "error"

    # Safety branches for transient type + error path
    class DummyPKSolver:
        def __init__(self, *_args, **_kwargs):
            pass

        def solve_transient(self, **kwargs):
            # Exercise rho_external / power_removal callables so their return-lines are covered.
            rho = kwargs.get("rho_external")
            qrem = kwargs.get("power_removal")
            if callable(rho):
                rho(0.0)
                rho(10.0)
            if callable(qrem):
                qrem(0.0, 1000.0, 800.0)
                qrem(10.0, 1000.0, 800.0)
            return {
                "time": [0, 1],
                "power": [1, 2],
                "T_fuel": [10, 11],
                "T_mod": [9, 10],
                "reactivity": [0.0, -0.01],
            }

    for tt in ["slb", "lofc", "other"]:
        with (
            patch("smrforge.validation.models.ReactorSpecification", DummySpec),
            patch("smrforge.create_reactor", return_value=DummyReactor()),
            patch("smrforge.safety.transients.PointKineticsSolver", DummyPKSolver),
        ):
            out_results, feedback, progress = run_analysis(
                1,
                "safety",
                reactor_spec,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                tt,
                10.0,
                None,
                None,
                None,
            )
            assert out_results.get("safety", {}).get("status") == "success"

    with (
        patch("smrforge.validation.models.ReactorSpecification", DummySpec),
        patch("smrforge.create_reactor", return_value=DummyReactor()),
        patch(
            "smrforge.safety.transients.PointKineticsSolver",
            side_effect=RuntimeError("pk fail"),
        ),
    ):
        out_results, feedback, progress = run_analysis(
            1,
            "safety",
            reactor_spec,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            "slb",
            10.0,
            None,
            None,
            None,
        )
        assert out_results.get("safety", {}).get("status") == "error"

    # Complete analysis: force errors to trigger has_errors message formatting
    with (
        patch("smrforge.validation.models.ReactorSpecification", DummySpec),
        patch("smrforge.create_reactor", return_value=DummyReactor()),
        patch(
            "smrforge.convenience.transients.quick_transient",
            side_effect=RuntimeError("boom"),
        ),
        patch(
            "smrforge.burnup.solver.BurnupSolver", side_effect=RuntimeError("no solver")
        ),
        patch(
            "smrforge.safety.transients.PointKineticsSolver",
            side_effect=RuntimeError("pk fail"),
        ),
    ):
        out_results, feedback, progress = run_analysis(
            1,
            "complete",
            reactor_spec,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            "slb",
            10.0,
            None,
            None,
            None,
        )
        assert isinstance(feedback, dbc.Alert)
        assert any(v.get("status") == "error" for v in out_results.values())

    # Success formatting branch (no warnings/errors) should include k-eff detail line
    with (
        patch("smrforge.validation.models.ReactorSpecification", DummySpec),
        patch(
            "smrforge.create_reactor",
            return_value=DummyReactor(solve_keff_behavior="ok"),
        ),
    ):
        out_results, feedback, progress = run_analysis(
            1,
            "neutronics",
            reactor_spec,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        assert out_results.get("neutronics", {}).get("status") == "success"
        assert isinstance(feedback, dbc.Alert)

    # Outer exception formatting: validation error message
    with patch(
        "smrforge.validation.models.ReactorSpecification",
        side_effect=RuntimeError("validation bad"),
    ):
        out_results, feedback, progress = run_analysis(
            1,
            "neutronics",
            reactor_spec,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        assert out_results == {}
        assert isinstance(feedback, dbc.Alert)

    # Outer exception formatting: solve/neutronics hint
    with (
        patch("smrforge.validation.models.ReactorSpecification", DummySpec),
        patch(
            "smrforge.create_reactor",
            side_effect=RuntimeError("neutronics solve blew up"),
        ),
    ):
        out_results, feedback, progress = run_analysis(
            1,
            "neutronics",
            reactor_spec,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        assert out_results == {}
        assert isinstance(feedback, dbc.Alert)
