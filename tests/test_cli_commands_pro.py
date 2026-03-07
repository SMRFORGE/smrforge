"""
Tests for Pro-tier CLI commands (convert, visualize tally, report validation, workflow ml-export).

When Pro is not installed, these commands exit with code 1 and a helpful message.
When Pro is installed, they delegate to Pro implementations.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestConvertExport:
    """Tests for smrforge convert serpent|openmc|mcnp."""

    def test_convert_serpent_creates_file(self, tmp_path):
        """convert serpent --reactor preset --output file creates .serp file."""
        from smrforge.cli.commands.convert import convert_export

        args = Mock(
            reactor="valar-10",
            output=tmp_path / "out.serp",
            format="serpent",
        )
        with patch("sys.exit"):
            convert_export(args)
        assert (tmp_path / "out.serp").exists()

    def test_convert_requires_reactor_and_output(self):
        """convert exits when --reactor or --output missing."""
        from smrforge.cli.commands.convert import convert_export

        args = Mock(reactor="", output=None)
        with patch("smrforge.cli.commands.convert._print_error"):
            with patch("sys.exit") as mock_exit:
                convert_export(args)
        mock_exit.assert_called_once_with(1)


class TestVisualizeTally:
    """Tests for smrforge visualize tally (Pro)."""

    def test_visualize_tally_exits_with_nonexistent_statepoint(self):
        """visualize tally exits 1 when statepoint not found or Pro not installed."""
        from smrforge.cli.commands.visualize import visualize_tally

        args = Mock(
            statepoint=Path("/nonexistent_12345.h5"),
            tally_id=None,
            score=None,
            output=None,
            backend="plotly",
            no_uncertainty=False,
        )
        # With nonexistent statepoint: Pro installed -> "Statepoint not found" exit 1
        # Pro not installed -> ImportError -> exit 1. Either way we get SystemExit.
        with pytest.raises(SystemExit):
            visualize_tally(args)


class TestReportValidation:
    """Tests for smrforge report validation (Pro)."""

    def test_report_validation_runs_or_exits(self, tmp_path):
        """report validation runs when Pro available or exits when Pro missing."""
        from smrforge.cli.commands.report import report_validation

        pred = tmp_path / "pred.txt"
        ref = tmp_path / "ref.txt"
        pred.write_text("1.0\n1.1")
        ref.write_text("1.0\n1.1")
        args = Mock(
            predictions=pred,
            reference=ref,
            output=tmp_path / "report.json",
            metric="output",
            pdf=False,
        )
        try:
            report_validation(args)
        except (SystemExit, ImportError):
            pass  # Expected when Pro not installed


class TestWorkflowMlExport:
    """Tests for smrforge workflow ml-export."""

    def test_ml_export_requires_results_file(self):
        """workflow ml-export exits when results file not found."""
        from smrforge.cli.commands.workflow import workflow_ml_export

        args = Mock(results=Path("/nonexistent_12345.json"), output=None)
        with patch("smrforge.cli.commands.workflow._print_error"):
            with patch("smrforge.cli.common.sys.exit", side_effect=SystemExit) as mock_exit:
                with pytest.raises(SystemExit):
                    workflow_ml_export(args)
        mock_exit.assert_called_once_with(1)
