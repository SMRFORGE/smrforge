import builtins
import importlib
import sys
from types import SimpleNamespace

import numpy as np
import pytest


def test_convenience_module_core_paths(tmp_path):
    import smrforge

    smrforge = importlib.reload(smrforge)

    # Load smrforge/convenience.py via the fallback loader in smrforge/__init__.py.
    # This repo also has a package at smrforge/convenience/, so importing
    # `smrforge.convenience` does NOT import the convenience.py module.
    orig_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "smrforge.convenience":
            raise ImportError("force fallback loader for convenience.py")
        return orig_import(name, globals, locals, fromlist, level)

    with pytest.MonkeyPatch.context() as mp_import:
        mp_import.setattr(builtins, "__import__", guarded_import)
        smrforge = importlib.reload(smrforge)

    conv = sys.modules.get("smrforge.convenience_file")
    assert conv is not None

    # Cover _get_library() return line (preset availability depends on environment).
    try:
        lib = conv._get_library()
        assert lib is not None
    except ImportError:
        pass

    # Patch heavy geometry + solver work while still executing convenience.py code.
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

        # create_reactor custom path (missing line cluster around SimpleReactor())
        reactor = smrforge.create_reactor()
        assert isinstance(reactor, conv.SimpleReactor)

        # _get_core else branch + geometry creation path
        core = reactor._get_core()
        assert isinstance(core, DummyCore)
        assert core.calls  # lattice+mesh calls happened

        # _get_xs_data else branch + _create_simple_xs
        xs = reactor._get_xs_data()
        assert xs.n_groups == 2

        # _get_solver + solve_keff happy path
        k = reactor.solve_keff()
        assert k == 1.0

        # quick_keff covers create_reactor call lines
        assert smrforge.quick_keff() == 1.0

        # compare_designs try/except branches
        def fake_analyze(name):
            if name == "bad":
                raise RuntimeError("nope")
            return {"k_eff": 1.0}

        mp.setattr(conv, "analyze_preset", fake_analyze)
        out = smrforge.compare_designs(["ok", "bad"])
        assert out["ok"]["k_eff"] == 1.0
        assert "error" in out["bad"]

        # solve(): include and exclude power_distribution branches
        result_ok = reactor.solve()
        assert "power_distribution" in result_ok

        class DummySolverNoPower(DummySolver):
            def compute_power_distribution(self, power_thermal):
                raise RuntimeError("boom")

        reactor._solver = DummySolverNoPower(reactor._get_core(), reactor._get_xs_data(), reactor._get_solver().options)
        result_no_power = reactor.solve()
        assert "power_distribution" not in result_no_power

        # save/load paths
        p = tmp_path / "r.json"
        reactor.save(p)
        loaded = conv.SimpleReactor.load(p)
        assert loaded.spec.name == reactor.spec.name

        # from_preset: attribute wiring
        preset = SimpleNamespace(spec=reactor.spec)
        r2 = conv.SimpleReactor.from_preset(preset)
        assert r2.spec.name == reactor.spec.name


def test_package_init_fallback_and_importerror_branches():
    import smrforge

    smrforge = importlib.reload(smrforge)

    orig_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        # Force specific optional imports to fail to cover ImportError branches.
        pkg = None
        if globals and isinstance(globals, dict):
            pkg = globals.get("__package__")
        if (
            name == "smrforge.convenience"
            or name.endswith("smrforge.validation.integration")
            or name.endswith("smrforge.uncertainty.visualization")
            or name.endswith("smrforge.burnup.visualization")
            or name.endswith("validation.integration")
            or name.endswith("uncertainty.visualization")
            or name.endswith("burnup.visualization")
            or (pkg == "smrforge.burnup" and name in {"visualization", ".visualization"})
            or (pkg == "smrforge.uncertainty" and name in {"visualization", ".visualization"})
            or (pkg == "smrforge.validation" and name in {"integration", ".integration"})
        ):
            raise ImportError("forced for coverage")
        return orig_import(name, globals, locals, fromlist, level)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(builtins, "__import__", guarded_import)

        # smrforge/__init__.py convenience fallback loader path (missing 87-115)
        smrforge = importlib.reload(smrforge)
        assert hasattr(smrforge, "create_reactor")

        # burnup/__init__.py visualization ImportError branch (missing 41-42)
        import smrforge.burnup as burnup

        sys.modules.pop("smrforge.burnup.visualization", None)
        burnup = importlib.reload(burnup)
        assert burnup._VISUALIZATION_AVAILABLE is False

        # uncertainty/__init__.py visualization ImportError branch (missing 12-13)
        import smrforge.uncertainty as uq

        sys.modules.pop("smrforge.uncertainty.visualization", None)
        uq = importlib.reload(uq)
        assert isinstance(uq.__all__, list)

        # validation/__init__.py integration ImportError branch (missing 38-39)
        import smrforge.validation as v

        v = importlib.reload(v)
        assert v._INTEGRATION_AVAILABLE is False

