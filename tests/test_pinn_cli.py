"""
Tests for PINN CLI commands (pinn train, pinn predict).

Requires: torch, smrforge_pro.
Skips when Pro tier not available.
"""

from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("torch")
try:
    from click.testing import CliRunner

    from smrforge_pro.cli.pinn_commands import pinn
except ImportError:
    pytest.skip(
        "smrforge_pro.cli.pinn_commands not available (Pro tier)",
        allow_module_level=True,
    )


class TestPinnCLI:
    """Tests for pinn train and pinn predict CLI."""

    def test_pinn_group_exists(self):
        """pinn command group exists and has train, predict."""
        runner = CliRunner()
        result = runner.invoke(pinn, ["--help"])
        assert result.exit_code == 0
        assert "train" in result.output
        assert "predict" in result.output

    def test_pinn_train_creates_model(self, tmp_path):
        """pinn train produces a valid .pt file."""
        # Create minimal dataset
        x = np.random.rand(40, 5).astype(np.float32)
        y = np.random.rand(40, 3).astype(np.float32)
        ds_path = tmp_path / "dataset.npz"
        np.savez(ds_path, x=x, y=y)

        out_path = tmp_path / "model.pt"
        runner = CliRunner()
        result = runner.invoke(
            pinn,
            [
                "train",
                "--dataset",
                str(ds_path),
                "--output",
                str(out_path),
                "--epochs",
                "20",
            ],
        )

        assert result.exit_code == 0, result.output
        assert out_path.exists()
        # Verify it's loadable
        import torch

        ckpt = torch.load(out_path, map_location="cpu", weights_only=True)
        assert "model_state" in ckpt
        assert "input_dim" in ckpt

    def test_pinn_predict_output(self, tmp_path):
        """pinn predict produces k_eff, flux, temp output."""
        # Train a tiny model first
        x = np.random.rand(30, 5).astype(np.float32)
        y = np.random.rand(30, 3).astype(np.float32)
        ds_path = tmp_path / "ds.npz"
        model_path = tmp_path / "m.pt"
        np.savez(ds_path, x=x, y=y)

        runner = CliRunner()
        runner.invoke(
            pinn,
            [
                "train",
                "--dataset",
                str(ds_path),
                "--output",
                str(model_path),
                "--epochs",
                "15",
            ],
        )

        params = '{"a":1.0,"b":0.5,"c":1.2,"d":0.6,"e":0.3}'
        result = runner.invoke(
            pinn, ["predict", "--model", str(model_path), "--params", params]
        )

        assert result.exit_code == 0
        assert "k-eff:" in result.output
        assert "flux:" in result.output
        assert "temp:" in result.output

    def test_pinn_predict_invalid_json(self, tmp_path):
        """pinn predict fails gracefully on invalid JSON params."""
        # Need a valid model file; create minimal one
        import torch

        from smrforge_pro.ai.pinn import SimpleDiffusionPINN

        net = SimpleDiffusionPINN(input_dim=5)
        model_path = tmp_path / "dummy.pt"
        torch.save({"model_state": net.state_dict(), "input_dim": 5}, model_path)

        runner = CliRunner()
        result = runner.invoke(
            pinn,
            ["predict", "--model", str(model_path), "--params", "not-json"],
        )
        assert result.exit_code != 0
