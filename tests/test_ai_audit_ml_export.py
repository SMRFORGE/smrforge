"""Tests for AI audit and ML export (Pro tier; Community has stubs that raise)."""

from pathlib import Path

import pytest

from smrforge.validation.regulatory_traceability import (
    CalculationAuditTrail,
    create_audit_trail,
)


class TestAiAudit:
    def test_record_ai_model_requires_pro(self):
        """Community: record_ai_model raises ImportError when Pro not installed; works when Pro is installed."""
        from smrforge.ai.audit import record_ai_model

        trail = create_audit_trail("keff", {}, {"k_eff": 1.0})
        try:
            record_ai_model(trail, "rbf", version="1.0", config_hash="abc")
            assert len(trail.ai_models_used) == 1
            assert trail.ai_models_used[0]["name"] == "rbf"
        except ImportError as e:
            assert "SMRForge Pro" in str(e)

    def test_ai_models_used_in_to_dict(self):
        """CalculationAuditTrail.ai_models_used still serializes (data structure)."""
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
        import json

        data = json.loads(p.read_text())
        data.pop("ai_models_used", None)
        p.write_text(json.dumps(data, indent=2))
        loaded = CalculationAuditTrail.load(p)
        assert loaded.ai_models_used == []


class TestMlExport:
    def test_export_ml_dataset_requires_pro(self, tmp_path):
        """Community: export_ml_dataset raises ImportError when Pro not installed; works when Pro is installed."""
        from smrforge.workflows.ml_export import export_ml_dataset

        results = [
            {"parameters": {"x": 0.1}, "k_eff": 1.02},
        ]
        try:
            out = export_ml_dataset(results, tmp_path / "design.parquet")
            assert out.exists()
        except ImportError as e:
            assert "SMRForge Pro" in str(e)
