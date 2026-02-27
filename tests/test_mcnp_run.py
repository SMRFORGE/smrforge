"""Tests for smrforge.io.mcnp_run: run_mcnp, parse_mcnp_output, run_and_parse."""

from pathlib import Path
from unittest.mock import patch

import pytest

from smrforge.io.mcnp_run import parse_mcnp_output, run_mcnp, run_and_parse


class TestRunMCNP:
    """Test run_mcnp."""

    def test_run_mcnp_raises_when_input_missing(self, tmp_path):
        """FileNotFoundError when input file not found."""
        with pytest.raises(FileNotFoundError, match="not found"):
            run_mcnp(tmp_path, "nonexistent.inp")

    @patch("subprocess.run")
    def test_run_mcnp_success(self, mock_run, tmp_path):
        """Successful run_mcnp path."""
        inp = tmp_path / "model.inp"
        inp.write_text("C MCNP input\n")
        mock_run.return_value = __import__("unittest").mock.Mock(
            returncode=0, stdout="ok", stderr=""
        )
        result = run_mcnp(tmp_path, "model.inp")
        assert result.returncode == 0
        mock_run.assert_called_once()


class TestParseMCNPOutput:
    """Test parse_mcnp_output."""

    def test_parse_keff_pattern(self):
        """Parse k-eff from MCNP output text."""
        text = "best estimate of the combined xxx and yyy  1.01234  ( 0.00123 )"
        result = parse_mcnp_output(text)
        assert "k_eff" in result
        assert abs(result["k_eff"] - 1.01234) < 1e-5

    def test_parse_empty_returns_empty(self):
        """Empty text returns empty dict."""
        result = parse_mcnp_output("")
        assert result == {}


class TestRunAndParse:
    """Test run_and_parse."""

    @patch("subprocess.run")
    def test_run_and_parse_includes_returncode(self, mock_run, tmp_path):
        """run_and_parse returns returncode, stdout, stderr."""
        inp = tmp_path / "m.inp"
        inp.write_text("C test\n")
        mock_run.return_value = __import__("unittest").mock.Mock(
            returncode=0,
            stdout="keff = 1.0 0.001",
            stderr="",
        )
        out = run_and_parse(tmp_path, "m.inp")
        assert "returncode" in out
        assert "stdout" in out
        assert "stderr" in out
