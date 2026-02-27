"""Tests for polynomial chaos expansion."""

import numpy as np
import pytest

from smrforge.uncertainty.uq import UncertainParameter, polynomial_chaos_expansion


class TestPolynomialChaosExpansion:
    """Tests for polynomial_chaos_expansion."""

    def test_pce_simple_model(self):
        """Test PCE with simple linear model."""
        params = [
            UncertainParameter("x", "uniform", 1.0, (0.5, 1.5)),
        ]

        def model(d):
            return {"y": d["x"] * 2.0}

        results = polynomial_chaos_expansion(
            params, model, ["y"], degree=2, n_samples=100, random_state=42
        )
        assert "y" in results
        assert "mean" in results["y"]
        assert "std" in results["y"]
        assert 1.0 < results["y"]["mean"] < 3.0

    def test_pce_sparse_option(self):
        """PCE with sparse=True runs without error."""
        params = [
            UncertainParameter("x", "uniform", 1.0, (0.5, 1.5)),
        ]

        def model(d):
            return {"y": d["x"] ** 2}

        results = polynomial_chaos_expansion(
            params,
            model,
            ["y"],
            degree=2,
            n_samples=100,
            sparse=True,
            random_state=42,
        )
        assert "y" in results
        assert "mean" in results["y"]

    def test_pce_adaptive_degree_option(self):
        """PCE with adaptive_degree=True runs without error."""
        params = [
            UncertainParameter("x", "uniform", 1.0, (0.5, 1.5)),
        ]

        def model(d):
            return {"y": d["x"]}

        results = polynomial_chaos_expansion(
            params,
            model,
            ["y"],
            degree=2,
            n_samples=100,
            adaptive_degree=True,
            max_degree=3,
            random_state=42,
        )
        assert "y" in results
        assert "mean" in results["y"]
