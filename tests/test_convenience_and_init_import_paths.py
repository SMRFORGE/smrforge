"""
Tests for convenience package import paths and __init__ ImportError handling.
"""

import builtins
import importlib
import sys
from types import SimpleNamespace

import numpy as np
import pytest


def test_convenience_module_core_paths(tmp_path):
    """Test core convenience paths using the convenience package."""
    import smrforge
    import smrforge.convenience as conv

    # Patch heavy geometry + solver work
    class DummyCore:
        def __init__(self, name):
            self.name = name
            self.calls = []

        def build_hexagonal_lattice(self, **kwargs):
            self.calls.append(("build_hexagonal_lattice", kwargs))

        def generate_mesh(self, **kwargs):
            self.calls.append(("generate_mesh", kwargs))

    class DummySolver:
        def __init__(self, core, xs_data, options):
            self.core = core
            self.xs_data = xs_data
            self.options = options

        def solve_steady_state(self):
            return 1.0, np.ones(3)

        def compute_power_distribution(self, power_thermal):
            return np.array([power_thermal])

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(conv, "PrismaticCore", DummyCore)
        mp.setattr(conv, "MultiGroupDiffusion", DummySolver)

        # create_reactor custom path
        reactor = smrforge.create_reactor()
        assert isinstance(reactor, conv.SimpleReactor)

        core = reactor._get_core()
        assert isinstance(core, DummyCore)
        assert core.calls

        xs = reactor._get_xs_data()
        assert xs.n_groups == 2

        k = reactor.solve_keff()
        assert k == 1.0

        assert smrforge.quick_keff() == 1.0

        def fake_analyze(name):
            if name == "bad":
                raise RuntimeError("nope")
            return {"k_eff": 1.0}

        mp.setattr(conv, "analyze_preset", fake_analyze)
        out = smrforge.compare_designs(["ok", "bad"])
        assert out["ok"]["k_eff"] == 1.0
        assert "error" in out["bad"]

        result_ok = reactor.solve()
        assert "power_distribution" in result_ok

        class DummySolverNoPower(DummySolver):
            def compute_power_distribution(self, power_thermal):
                raise RuntimeError("boom")

        reactor._solver = DummySolverNoPower(
            reactor._get_core(), reactor._get_xs_data(), reactor._get_solver().options
        )
        result_no_power = reactor.solve()
        assert "power_distribution" not in result_no_power

        p = tmp_path / "r.json"
        reactor.save(p)
        loaded = conv.SimpleReactor.load(p)
        assert loaded.spec.name == reactor.spec.name

        preset = SimpleNamespace(spec=reactor.spec)
        r2 = conv.SimpleReactor.from_preset(preset)
        assert r2.spec.name == reactor.spec.name


def test_package_init_convenience_importerror_handling():
    """Test __init__.py handles convenience ImportError (no fallback)."""
    import smrforge

    smrforge = importlib.reload(smrforge)

    orig_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "smrforge.convenience":
            raise ImportError("forced for coverage")
        if name.endswith("smrforge.validation.integration"):
            raise ImportError("forced for coverage")
        if name.endswith("smrforge.uncertainty.visualization"):
            raise ImportError("forced for coverage")
        if name.endswith("smrforge.burnup.visualization"):
            raise ImportError("forced for coverage")
        if name.endswith("validation.integration"):
            raise ImportError("forced for coverage")
        if name.endswith("uncertainty.visualization"):
            raise ImportError("forced for coverage")
        if name.endswith("burnup.visualization"):
            raise ImportError("forced for coverage")
        pkg = globals.get("__package__") if isinstance(globals, dict) else None
        if pkg == "smrforge.burnup" and name in {"visualization", ".visualization"}:
            raise ImportError("forced for coverage")
        if pkg == "smrforge.uncertainty" and name in {"visualization", ".visualization"}:
            raise ImportError("forced for coverage")
        if pkg == "smrforge.validation" and name in {"integration", ".integration"}:
            raise ImportError("forced for coverage")
        return orig_import(name, globals, locals, fromlist, level)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(builtins, "__import__", guarded_import)

        smrforge = importlib.reload(smrforge)
        assert smrforge._CONVENIENCE_AVAILABLE is False

        import smrforge.burnup as burnup

        sys.modules.pop("smrforge.burnup.visualization", None)
        burnup = importlib.reload(burnup)
        assert burnup._VISUALIZATION_AVAILABLE is False

        import smrforge.uncertainty as uq

        sys.modules.pop("smrforge.uncertainty.visualization", None)
        uq = importlib.reload(uq)
        assert isinstance(uq.__all__, list)

        import smrforge.validation as v

        v = importlib.reload(v)
        assert v._INTEGRATION_AVAILABLE is False
