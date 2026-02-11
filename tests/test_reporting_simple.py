"""Tests for smrforge.reporting simple report generator."""

from pathlib import Path

import pytest

from smrforge.reporting import generate_markdown_report
from smrforge.reporting.simple_report import generate_pdf_report


class TestGenerateMarkdownReport:
    """Test generate_markdown_report."""

    def test_basic_report(self):
        """Test basic report with k_eff and power."""
        results = {"k_eff": 1.05, "power_thermal_mw": 10.0}
        report = generate_markdown_report(results, title="Test Report")
        assert isinstance(report, str)
        assert "Test Report" in report
        assert "k-effective" in report or "k_eff" in report
        assert "1.05" in report
        assert "10.0" in report or "10" in report

    def test_report_with_output_path(self, tmp_path):
        """Test report writes to file."""
        results = {"k_eff": 1.0}
        out = tmp_path / "report.md"
        generate_markdown_report(results, output_path=out)
        assert out.exists()
        assert "1.0" in out.read_text()

    def test_report_with_power_distribution(self):
        """Test report includes power distribution summary."""
        import numpy as np

        results = {
            "k_eff": 1.0,
            "power_distribution": np.array([1.0, 2.0, 3.0]),
        }
        report = generate_markdown_report(results)
        assert "power density" in report.lower() or "power" in report.lower()

    def test_report_avoids_numpy_or_ambiguous(self):
        """Test report does not use 'or' with numpy arrays (avoids truth value error)."""
        import numpy as np

        results = {
            "k_eff": 1.0,
            "power_distribution": np.array([1.0, 2.0]),
        }
        report = generate_markdown_report(results)
        assert isinstance(report, str)
        assert len(report) > 0

    def test_report_with_design_name_and_additional_keys(self):
        """Test report includes design_name and additional numeric/string keys."""
        results = {
            "k_eff": 1.05,
            "design_name": "valar-10",
            "power_mw": 10.0,
            "custom_metric": 42,
            "notes": "short",
        }
        report = generate_markdown_report(results)
        assert "valar-10" in report or "Design" in report
        assert "42" in report or "custom" in report.lower()


class TestGeneratePdfReport:
    """Test generate_pdf_report (optional weasyprint)."""

    def test_pdf_report_produces_output(self, tmp_path):
        """Test PDF report produces either PDF or Markdown fallback."""
        results = {"k_eff": 1.0}
        out = tmp_path / "report.pdf"
        result = generate_pdf_report(results, output_path=out)
        # With weasyprint: returns Path, PDF exists
        # Without weasyprint: returns None, Markdown written
        assert out.exists() or (tmp_path / "report.md").exists()
