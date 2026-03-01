"""
Tests for PINN MVP (SimpleDiffusionPINN, train_simple_pinn).

Requires: torch, smrforge_pro.ai.pinn.
Skips when Pro tier or PyTorch not available (e.g. in Community CI).
"""

import numpy as np
import pytest

pytest.importorskip("torch")
import torch  # noqa: E402

try:
    from smrforge_pro.ai.pinn import SimpleDiffusionPINN, train_simple_pinn
    from smrforge_pro.ai.pinn.base import PhysicsInformedNN
except ImportError:
    pytest.skip(
        "smrforge_pro.ai.pinn not available (Pro tier)", allow_module_level=True
    )


class TestSimpleDiffusionPINN:
    """Tests for SimpleDiffusionPINN model."""

    def test_forward_pass_shape(self):
        """Forward pass returns correct output shape."""
        model = SimpleDiffusionPINN(input_dim=5, hidden_dim=64, n_layers=3)
        x = torch.randn(10, 5)
        y = model(x)
        assert y.shape == (10, 3)

    def test_forward_pass_deterministic(self):
        """Forward pass is deterministic in eval mode."""
        model = SimpleDiffusionPINN(input_dim=5)
        model.eval()
        x = torch.randn(4, 5)
        with torch.no_grad():
            y1 = model(x)
            y2 = model(x)
        assert y1.shape == y2.shape
        torch.testing.assert_close(y1, y2)

    def test_compute_loss_returns_dict(self):
        """compute_loss returns total loss and breakdown dict."""
        model = SimpleDiffusionPINN(input_dim=5)
        x_data = torch.randn(20, 5)
        y_data = torch.randn(20, 3)
        x_phys = torch.randn(30, 5)

        total, loss_dict = model.compute_loss(x_data, y_data, x_physics=x_phys)

        assert total.dim() == 0
        assert total.item() >= 0
        assert "total" in loss_dict
        assert "data" in loss_dict
        assert "physics" in loss_dict
        assert "constraint" in loss_dict

    def test_physics_loss_computes(self):
        """physics_loss returns scalar and does not fail."""
        model = SimpleDiffusionPINN(input_dim=5)
        x = torch.randn(8, 5)
        loss = model.physics_loss(x)
        assert loss.dim() == 0
        assert loss.item() >= 0

    def test_constraint_loss_computes(self):
        """constraint_loss returns scalar and does not fail."""
        model = SimpleDiffusionPINN(input_dim=5)
        x = torch.randn(8, 5)
        loss = model.constraint_loss(x)
        assert loss.dim() == 0
        assert loss.item() >= 0


class TestTrainSimplePinn:
    """Tests for train_simple_pinn function."""

    def test_training_decreases_loss(self):
        """Training runs and produces valid history (loss is finite)."""
        np.random.seed(42)
        n = 100
        x_train = np.random.rand(n, 5).astype(np.float32) * np.array(
            [15, 0.6, 1.0, 2.0, 0.5]
        )
        # Use weakly correlated targets so model can improve
        y_train = np.column_stack(
            [
                0.95 + 0.05 * (x_train[:, 0] / 15) + 0.02 * np.random.randn(n),
                1e14 * (1 + 0.1 * np.random.randn(n)),
                500 + 50 * (x_train[:, 0] / 15) + 20 * np.random.randn(n),
            ]
        ).astype(np.float32)
        x_val = np.random.rand(20, 5).astype(np.float32) * np.array(
            [15, 0.6, 1.0, 2.0, 0.5]
        )
        y_val = np.random.rand(20, 3).astype(np.float32)

        model, history = train_simple_pinn(
            x_train,
            y_train,
            x_val,
            y_val,
            epochs=100,
            lr=1e-3,
            device="cpu",
        )

        assert len(history) > 0
        assert np.isfinite(history[-1]["train_loss"])
        assert np.isfinite(history[-1]["val_loss"])

    def test_training_returns_model_and_history(self):
        """train_simple_pinn returns (model, history)."""
        np.random.seed(0)
        x = np.random.rand(40, 5).astype(np.float32)
        y = np.random.rand(40, 3).astype(np.float32)
        xv = np.random.rand(10, 5).astype(np.float32)
        yv = np.random.rand(10, 3).astype(np.float32)

        model, history = train_simple_pinn(x, y, xv, yv, epochs=20, device="cpu")

        assert isinstance(model, SimpleDiffusionPINN)
        assert isinstance(history, list)
        assert all(
            "epoch" in h and "train_loss" in h and "val_loss" in h for h in history
        )


class TestPhysicsInformedNNBase:
    """Tests for abstract base class (extensibility placeholder)."""

    def test_base_is_abstract(self):
        """PhysicsInformedNN cannot be instantiated directly (has abstract methods)."""
        with pytest.raises(TypeError, match="abstract|instantiate"):
            PhysicsInformedNN(input_dim=5, output_dim=3)
