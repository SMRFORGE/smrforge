"""
Tests for Design of Experiments (DoE) workflow module.
"""

import numpy as np
import pytest

from smrforge.workflows.doe import (
    full_factorial,
    latin_hypercube,
    random_space_filling,
    sobol_space_filling,
)


class TestFullFactorial:
    def test_single_factor(self):
        design = full_factorial({"a": [1.0, 2.0, 3.0]})
        assert len(design) == 3
        assert design[0] == {"a": 1.0}
        assert design[2] == {"a": 3.0}

    def test_two_factors(self):
        design = full_factorial({"x": [0, 1], "y": [10, 20]})
        assert len(design) == 4
        assert {"x": 0, "y": 10} in design
        assert {"x": 1, "y": 20} in design

    def test_empty_levels(self):
        design = full_factorial({"a": []})
        assert len(design) == 0


class TestLatinHypercube:
    def test_lhs_basic(self):
        try:
            design = latin_hypercube(
                ["a", "b"],
                [(0.0, 1.0), (0.0, 10.0)],
                n_samples=5,
                seed=42,
            )
        except ImportError:
            pytest.skip("scipy.stats.qmc required")
        assert len(design) == 5
        for point in design:
            assert "a" in point and "b" in point
            assert 0 <= point["a"] <= 1
            assert 0 <= point["b"] <= 10

    def test_lhs_raises_without_scipy(self):
        import smrforge.workflows.doe as doe

        if doe._SCIPY_QMC:
            pytest.skip("scipy available")
        with pytest.raises(ImportError, match="scipy"):
            latin_hypercube(["x"], [(0, 1)], 3, seed=0)


class TestRandomSpaceFilling:
    def test_random_basic(self):
        design = random_space_filling(
            ["a", "b"],
            [(0.0, 1.0), (5.0, 5.0)],
            n_samples=10,
            seed=1,
        )
        assert len(design) == 10
        for point in design:
            assert 0 <= point["a"] <= 1
            assert point["b"] == 5.0

    def test_reproducibility(self):
        d1 = random_space_filling(["x"], [(0, 1)], 20, seed=99)
        d2 = random_space_filling(["x"], [(0, 1)], 20, seed=99)
        assert [p["x"] for p in d1] == [p["x"] for p in d2]


class TestSobolSpaceFilling:
    def test_sobol_basic(self):
        try:
            design = sobol_space_filling(
                ["a", "b"],
                [(0.0, 1.0), (0.0, 1.0)],
                n_samples=8,
                seed=0,
            )
        except ImportError:
            pytest.skip("scipy.stats.qmc required")
        assert len(design) == 8
        for point in design:
            assert 0 <= point["a"] <= 1 and 0 <= point["b"] <= 1
