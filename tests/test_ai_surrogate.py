"""
Tests for AI surrogate and BYOS (Bring-Your-Own Surrogate) features.

Covers: load_surrogate_from_path, register_surrogate path loading,
fit_surrogate audit_trail, parameter sweep with surrogate, validation report.
"""

import pickle
from pathlib import Path

import numpy as np
import pytest

from smrforge.workflows.surrogate import SurrogateModel, fit_surrogate


class _PicklableSurrogate:
    """Surrogate at module level so it can be pickled."""

    def __init__(self):
        self.coef = np.array([1.0])
        self.intercept = 1.0  # y = x + 1 for x in [0,1] -> y in [1,2]
        self.param_names = ["x"]
        self.output_name = "k_eff"
        self.method = "linear"

    def predict(self, X):
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        return (X @ self.coef + self.intercept).ravel()


def _make_picklable_surrogate():
    """Create a surrogate that can be pickled."""
    return _PicklableSurrogate()
from smrforge.validation.regulatory_traceability import create_audit_trail


class TestFitSurrogateWithAuditTrail:
    """Tests for fit_surrogate with audit_trail parameter."""

    def test_fit_surrogate_records_to_audit_trail(self):
        """When audit_trail is provided, record_ai_model is called."""
        X = np.array([[0.0], [1.0], [2.0]])
        y = np.array([1.0, 2.0, 3.0])
        trail = create_audit_trail("keff", inputs={}, outputs={})

        sur = fit_surrogate(X, y, method="linear", audit_trail=trail)

        assert len(trail.ai_models_used) == 1
        assert trail.ai_models_used[0]["name"] == "linear"
        assert sur.method == "linear"

    def test_fit_surrogate_no_audit_trail(self):
        """When audit_trail is None, ai_models_used stays empty."""
        X = np.array([[0.0], [1.0], [2.0]])
        y = np.array([1.0, 2.0, 3.0])

        sur = fit_surrogate(X, y, method="linear", audit_trail=None)

        assert sur.method == "linear"


class TestLoadSurrogateFromPath:
    """Tests for load_surrogate_from_path (pickle only, no onnx/torch)."""

    def test_load_pickle_surrogate(self, tmp_path):
        """Load a pickled surrogate from file."""
        from smrforge.ai.surrogate import load_surrogate_from_path

        sur = _make_picklable_surrogate()
        pkl = tmp_path / "sur.pkl"
        with open(pkl, "wb") as f:
            pickle.dump(sur, f)

        loaded = load_surrogate_from_path(pkl, param_names=["x"], output_name="k_eff")
        pred = loaded.predict(np.array([[0.5]]))
        assert len(pred) == 1
        assert abs(pred[0] - 1.5) < 0.01  # 0.5*1 + 1 = 1.5

    def test_load_surrogate_file_not_found(self):
        """Raise FileNotFoundError for missing file."""
        from smrforge.ai.surrogate import load_surrogate_from_path

        with pytest.raises(FileNotFoundError, match="not found"):
            load_surrogate_from_path("/nonexistent/model.pkl")

    def test_load_surrogate_unsupported_format(self, tmp_path):
        """Raise ValueError for unsupported extension."""
        from smrforge.ai.surrogate import load_surrogate_from_path

        bad = tmp_path / "model.xyz"
        bad.write_text("dummy")
        with pytest.raises(ValueError, match="Unsupported model format"):
            load_surrogate_from_path(bad)


class TestModelHash:
    """Tests for model_hash (audit trail)."""

    def test_model_hash_deterministic(self, tmp_path):
        """Same file produces same hash."""
        from smrforge.ai.surrogate import model_hash

        f = tmp_path / "m.bin"
        f.write_bytes(b"test content")
        h1 = model_hash(f)
        h2 = model_hash(f)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    def test_model_hash_file_not_found(self):
        """Raise FileNotFoundError for missing file."""
        from smrforge.ai.surrogate import model_hash

        with pytest.raises(FileNotFoundError):
            model_hash("/nonexistent")


class TestRegisterSurrogateFromPath:
    """Tests for register_surrogate with path (BYOS)."""

    def test_register_surrogate_path(self, tmp_path):
        """Register surrogate from pickle path."""
        from smrforge.workflows.plugin_registry import get_surrogate, unregister_surrogate

        from smrforge.ai.surrogate import register_surrogate_from_path

        sur = _make_picklable_surrogate()
        pkl = tmp_path / "byos.pkl"
        with open(pkl, "wb") as f:
            pickle.dump(sur, f)

        register_surrogate_from_path("byos_test", pkl)
        try:
            factory = get_surrogate("byos_test")
            assert factory is not None
            obj = factory(
                np.array([[0], [1]]),
                np.array([1.0, 2.0]),
                param_names=["x"],
                output_name="k_eff",
            )
            pred = obj.predict(np.array([[0.5]]))
            assert len(np.asarray(pred).ravel()) == 1
        finally:
            unregister_surrogate("byos_test")


class TestParameterSweepWithSurrogate:
    """Tests for parameter sweep using surrogate for fast evaluation."""

    def test_sweep_with_surrogate_pickle(self, tmp_path):
        """Run sweep using a pickled surrogate instead of physics."""
        from smrforge.workflows.parameter_sweep import ParameterSweep, SweepConfig

        # Create picklable surrogate (fit_surrogate result is not picklable)
        sur = _make_picklable_surrogate()
        pkl = tmp_path / "sur.pkl"
        with open(pkl, "wb") as f:
            pickle.dump(sur, f)

        config = SweepConfig(
            parameters={"x": [0.0, 0.25, 0.5, 0.75, 1.0]},
            analysis_types=["keff"],
            output_dir=tmp_path / "sweep_out",
            surrogate_path=pkl,
            surrogate_output_metric="k_eff",
            parallel=False,
        )
        sweep = ParameterSweep(config)
        results = sweep.run()

        assert len(results.results) == 5
        for r in results.results:
            assert "k_eff" in r
            assert r.get("surrogate_used") is True
            # _PicklableSurrogate: k_eff = x + 1, so x in [0,1] -> k_eff in [1,2]
            assert 1.0 <= r["k_eff"] <= 2.0


class TestSurrogateValidationReport:
    """Tests for generate_validation_report."""

    def test_generate_validation_report(self):
        """Generate validation report from pred vs reference."""
        from smrforge.ai.validation import generate_validation_report

        pred = [1.0, 1.01, 0.99]
        ref = [1.0, 1.0, 1.0]
        report = generate_validation_report(
            pred, ref,
            surrogate_name="test",
            surrogate_hash="abc123",
            param_names=["x"],
            output_metric="k_eff",
        )
        assert report.surrogate_name == "test"
        assert report.surrogate_hash == "abc123"
        assert report.n_reference == 3
        assert len(report.metrics) >= 4
        mae = next(m for m in report.metrics if m.name == "MAE")
        assert mae.value >= 0

    def test_validation_report_length_mismatch(self):
        """Raise ValueError when pred and ref lengths differ."""
        from smrforge.ai.validation import generate_validation_report

        with pytest.raises(ValueError, match="same length"):
            generate_validation_report([1.0, 2.0], [1.0], surrogate_name="x")
