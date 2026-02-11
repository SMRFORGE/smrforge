"""Tests for AI audit and ML export (NUCLEAR_INDUSTRY_ANALYSIS § 3.2)."""

from pathlib import Path

import pytest

from smrforge.ai.audit import record_ai_model
from smrforge.validation.regulatory_traceability import (
    CalculationAuditTrail,
    create_audit_trail,
)
from smrforge.workflows.ml_export import export_ml_dataset


class TestAiAudit:
    def test_record_ai_model(self):
        trail = create_audit_trail("keff", {}, {"k_eff": 1.0})
        record_ai_model(trail, "rbf", version="1.0", config_hash="abc")
        assert len(trail.ai_models_used) == 1
        assert trail.ai_models_used[0]["name"] == "rbf"
        assert trail.ai_models_used[0]["version"] == "1.0"
        assert trail.ai_models_used[0]["config_hash"] == "abc"

    def test_ai_models_used_in_to_dict(self):
        trail = create_audit_trail(
            "burnup", {}, {}, ai_models_used=[{"name": "gp", "version": "0.1"}]
        )
        d = trail.to_dict()
        assert "ai_models_used" in d
        assert d["ai_models_used"] == [{"name": "gp", "version": "0.1"}]

    def test_load_backward_compat_no_ai_models(self, tmp_path):
        """Old JSON without ai_models_used loads with empty list."""
        from datetime import datetime

        trail = CalculationAuditTrail(
            calculation_id="test",
            calculation_type="keff",
            timestamp=datetime.now(),
            inputs={},
            outputs={},
        )
        p = tmp_path / "old.json"
        trail.save(p)
        # Manually remove ai_models_used from JSON to simulate old file
        import json

        data = json.loads(p.read_text())
        data.pop("ai_models_used", None)
        p.write_text(json.dumps(data, indent=2))
        loaded = CalculationAuditTrail.load(p)
        assert loaded.ai_models_used == []


class TestMlExport:
    def test_export_parquet(self, tmp_path):
        results = [
            {"parameters": {"x": 0.1, "y": 0.2}, "k_eff": 1.02, "power": 50.0},
            {"parameters": {"x": 0.2, "y": 0.3}, "k_eff": 1.05, "power": 55.0},
        ]
        out = export_ml_dataset(results, tmp_path / "design.parquet")
        assert out.exists()
        import pandas as pd

        df = pd.read_parquet(out)
        assert "param_x" in df.columns
        assert "output_k_eff" in df.columns
        assert len(df) == 2

    def test_export_hdf5(self, tmp_path):
        results = [{"parameters": {"a": 1.0}, "k_eff": 1.0}]
        out = export_ml_dataset(results, tmp_path / "design.h5", format="hdf5")
        assert out.exists()
        import h5py

        with h5py.File(out, "r") as f:
            assert "param_a" in f
            assert "output_k_eff" in f
            assert "schema" in f.attrs
