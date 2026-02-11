"""
Tests for smrforge.io.serpent_run: run_serpent, parse_res_file, run_and_parse.

Serpent round-trip: Pro export -> run Serpent -> parse _res.m -> use in SMRForge.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from smrforge.io import parse_serpent_res
from smrforge.io import run_serpent as io_run_serpent
from smrforge.io.serpent_run import parse_res_file, run_and_parse, run_serpent


class TestRunSerpent:
    """Test run_serpent."""

    def test_run_serpent_raises_when_input_missing(self, tmp_path):
        """Cover FileNotFoundError when input file not found."""
        with pytest.raises(
            FileNotFoundError, match="input file not found|Serpent input file not found"
        ):
            run_serpent(tmp_path, "nonexistent.sss")

    @patch("subprocess.run")
    def test_run_serpent_success(self, mock_run, tmp_path):
        """Cover successful run_serpent path."""
        inp = tmp_path / "model.sss"
        inp.write_text("% Serpent input\n")
        mock_run.return_value = __import__("unittest").mock.Mock(
            returncode=0, stdout="ok", stderr=""
        )
        result = run_serpent(tmp_path, "model.sss")
        assert result.returncode == 0
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_run_serpent_nonzero_returncode(self, mock_run, tmp_path):
        """Cover run_serpent when Serpent fails."""
        inp = tmp_path / "m.sss"
        inp.write_text("% input\n")
        mock_run.return_value = __import__("unittest").mock.Mock(
            returncode=1, stdout="", stderr="error"
        )
        result = run_serpent(tmp_path, "m.sss")
        assert result.returncode == 1

    @patch("subprocess.run")
    def test_run_serpent_with_env(self, mock_run, tmp_path):
        """Cover run_serpent env parameter."""
        inp = tmp_path / "m.sss"
        inp.write_text("% input\n")
        mock_run.return_value = __import__("unittest").mock.Mock(
            returncode=0, stdout="", stderr=""
        )
        run_serpent(tmp_path, "m.sss", env={"SERPENT_XS": "/path"})
        call_kw = mock_run.call_args[1]
        assert call_kw["env"].get("SERPENT_XS") == "/path"


class TestParseResFile:
    """Test parse_res_file."""

    def test_parse_res_file_not_found(self):
        """Cover FileNotFoundError when res file not found."""
        with pytest.raises(
            FileNotFoundError,
            match="result file not found|Serpent result file not found",
        ):
            parse_res_file("/nonexistent/model_res.m")

    def test_parse_res_file_extracts_keff(self, tmp_path):
        """Cover parse_res_file with IMP_KEFF line."""
        res = tmp_path / "model_res.m"
        res.write_text("IMP_KEFF (idx, [1: 2]) = [ 1.04349E+00 0.00189 ];\n")
        parsed = parse_res_file(res)
        assert parsed["k_eff"] == pytest.approx(1.04349, rel=1e-4)
        assert "k_eff_std" in parsed
        assert parsed["k_eff_source"] == "IMP_KEFF"

    def test_parse_res_file_ana_keff_fallback(self, tmp_path):
        """Cover ANA_KEFF when IMP_KEFF not present."""
        res = tmp_path / "model_res.m"
        res.write_text(
            "ANA_KEFF (idx, [1: 6]) = [ 1.04533E+00 0.00258 1.03781E-01 0.00248 ];\n"
        )
        parsed = parse_res_file(res)
        assert parsed["k_eff"] == pytest.approx(1.04533, rel=1e-4)
        assert parsed["k_eff_source"] == "ANA_KEFF"

    def test_parse_res_file_extracts_cycles(self, tmp_path):
        """Cover cycles extraction."""
        res = tmp_path / "model_res.m"
        res.write_text(
            "CYCLES (idx, 1) = [ 600 ] ;\n" "IMP_KEFF (idx, [1: 2]) = [ 1.04 0.001 ];\n"
        )
        parsed = parse_res_file(res)
        assert parsed["k_eff"] == 1.04
        assert parsed.get("cycles") == 600


class TestRunAndParse:
    """Test run_and_parse."""

    @patch("smrforge.io.serpent_run.run_serpent")
    def test_run_and_parse_success(self, mock_run, tmp_path):
        """Cover run_and_parse when Serpent succeeds and res exists."""
        from unittest.mock import Mock

        inp = tmp_path / "m.sss"
        inp.write_text("% input\n")
        res = tmp_path / "m_res.m"
        res.write_text("IMP_KEFF (idx, [1: 2]) = [ 1.05 0.002 ];\n")

        mock_run.return_value = Mock(returncode=0, stdout="ok", stderr="")
        out = run_and_parse(tmp_path, "m.sss")
        assert out["returncode"] == 0
        assert out["k_eff"] == 1.05
        assert "k_eff_std" in out

    @patch("smrforge.io.serpent_run.run_serpent")
    def test_run_and_parse_no_res_file(self, mock_run, tmp_path):
        """Cover run_and_parse when no _res.m files (still returns returncode)."""
        from unittest.mock import Mock

        inp = tmp_path / "m.sss"
        inp.write_text("% input\n")
        mock_run.return_value = Mock(returncode=0, stdout="ok", stderr="")
        out = run_and_parse(tmp_path, "m.sss")
        assert out["returncode"] == 0
        assert "k_eff" not in out

    @patch("smrforge.io.serpent_run.run_serpent")
    def test_run_and_parse_nonzero_returncode(self, mock_run, tmp_path):
        """Cover run_and_parse when Serpent fails - no parse attempted."""
        inp = tmp_path / "m.sss"
        inp.write_text("% input\n")
        from unittest.mock import Mock

        mock_run.return_value = Mock(returncode=1, stdout="", stderr="fail")
        out = run_and_parse(tmp_path, "m.sss")
        assert out["returncode"] == 1
        assert "k_eff" not in out


class TestIoConvenience:
    """Test io.run_serpent and io.parse_serpent_res."""

    @patch("subprocess.run")
    def test_io_run_serpent(self, mock_run, tmp_path):
        inp = tmp_path / "m.sss"
        inp.write_text("% input\n")
        mock_run.return_value = __import__("unittest").mock.Mock(
            returncode=0, stdout="", stderr=""
        )
        r = io_run_serpent(tmp_path, "m.sss")
        assert r.returncode == 0

    def test_io_parse_serpent_res(self, tmp_path):
        res = tmp_path / "m_res.m"
        res.write_text("IMP_KEFF (idx, [1: 2]) = [ 1.03 0.002 ];\n")
        out = parse_serpent_res(res)
        assert out["k_eff"] == 1.03
