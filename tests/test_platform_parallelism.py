"""
Tests for platform-specific parallelism behavior.

Covers behavior documented in docs/technical/platform-parallelism.md:
- Windows fallback from ProcessPoolExecutor to ThreadPoolExecutor
- multiprocessing spawn / if __name__ == "__main__" guard pattern
- Numba prange / OpenMP availability
"""

import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from smrforge.utils.parallel_batch import batch_process

pytestmark = pytest.mark.parallel_batch


class TestWindowsThreadPoolExecutorFallback:
    """Tests for Windows ProcessPoolExecutor -> ThreadPoolExecutor fallback."""

    def test_windows_uses_thread_pool_executor_even_when_use_threads_false(self):
        """On Windows, batch_process uses ThreadPoolExecutor even with use_threads=False."""
        with patch(
            "smrforge.utils.parallel_batch._IS_WINDOWS", True
        ), patch(
            "smrforge.utils.parallel_batch.ProcessPoolExecutor", MagicMock()
        ) as mock_pp, patch(
            "smrforge.utils.parallel_batch.ThreadPoolExecutor", MagicMock()
        ) as mock_tp:
            # Real executor instance - use ThreadPoolExecutor as base for context manager
            real_executor = MagicMock()
            real_executor.__enter__ = MagicMock(return_value=real_executor)
            real_executor.__exit__ = MagicMock(return_value=None)
            real_executor.submit = MagicMock(side_effect=lambda fn, arg: self._make_done_future(fn(arg)))

            mock_tp.return_value = real_executor

            def double(x):
                return x * 2

            result = batch_process(
                [1, 2, 3], double, parallel=True, use_threads=False, max_workers=2
            )
            assert result == [2, 4, 6]
            mock_tp.assert_called()
            mock_pp.assert_not_called()

    def test_non_windows_uses_process_pool_executor_when_use_threads_false(self):
        """On non-Windows, batch_process uses ProcessPoolExecutor when use_threads=False."""
        with patch(
            "smrforge.utils.parallel_batch._IS_WINDOWS", False
        ), patch(
            "smrforge.utils.parallel_batch.ProcessPoolExecutor", MagicMock()
        ) as mock_pp, patch(
            "smrforge.utils.parallel_batch.ThreadPoolExecutor", MagicMock()
        ) as mock_tp:
            from concurrent.futures import Future

            real_executor = MagicMock()
            real_executor.__enter__ = MagicMock(return_value=real_executor)
            real_executor.__exit__ = MagicMock(return_value=None)
            futures_done = []

            def submit_side_effect(fn, arg):
                f = Future()
                f.set_result(fn(arg))
                futures_done.append(f)
                return f

            real_executor.submit = MagicMock(side_effect=submit_side_effect)
            mock_pp.return_value = real_executor

            def double(x):
                return x * 2

            result = batch_process(
                [1, 2, 3], double, parallel=True, use_threads=False, max_workers=2
            )
            assert result == [2, 4, 6]
            mock_pp.assert_called()
            mock_tp.assert_not_called()

    @staticmethod
    def _make_done_future(value):
        from concurrent.futures import Future

        f = Future()
        f.set_result(value)
        return f


class TestMultiprocessingMainGuard:
    """Tests for if __name__ == '__main__' guard with multiprocessing."""

    def test_batch_process_script_with_main_guard_completes_via_subprocess(self):
        """Script using batch_process inside if __name__ == '__main__' runs correctly."""
        script = '''
from smrforge.utils.parallel_batch import batch_process

def worker(x):
    return x * 2

if __name__ == "__main__":
    result = batch_process([1, 2, 3], worker, parallel=True, use_threads=True, max_workers=1)
    assert result == [2, 4, 6], f"Got {result}"
    print("OK")
'''
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(script)
            path = f.name
        try:
            proc = subprocess.run(
                [sys.executable, path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(Path(__file__).parent.parent),
            )
            assert proc.returncode == 0, (proc.stdout, proc.stderr)
            assert "OK" in proc.stdout
        finally:
            Path(path).unlink(missing_ok=True)


class TestNumbaPrangeSmoke:
    """Smoke tests for Numba prange / OpenMP path."""

    def test_numba_prange_parallel_loop_runs(self):
        """Numba prange parallel loop executes without error (OpenMP runtime used if available)."""
        from numba import njit, prange

        @njit(parallel=True)
        def parallel_sum(arr):
            total = 0.0
            for i in prange(len(arr)):
                total += arr[i]
            return total

        arr = np.ones(1000, dtype=np.float64)
        result = parallel_sum(arr)
        assert result == pytest.approx(1000.0)

    def test_solver_parallel_numba_path_runs(self):
        """Diffusion solver parallel Numba scattering source update executes."""
        from smrforge.geometry import PrismaticCore
        from smrforge.neutronics.solver import MultiGroupDiffusion
        from smrforge.validation.models import CrossSectionData, SolverOptions

        geometry = PrismaticCore(name="Test")
        geometry.core_height = 100.0
        geometry.core_diameter = 50.0
        geometry.generate_mesh(n_radial=4, n_axial=3)

        xs = CrossSectionData(
            n_groups=2,
            n_materials=1,
            sigma_t=np.array([[0.5, 0.8]]),
            sigma_a=np.array([[0.1, 0.2]]),
            sigma_f=np.array([[0.05, 0.15]]),
            nu_sigma_f=np.array([[0.125, 0.375]]),
            sigma_s=np.array([[[0.39, 0.01], [0.0, 0.58]]]),
            chi=np.array([[1.0, 0.0]]),
            D=np.array([[1.5, 0.4]]),
        )
        opts = SolverOptions(
            max_iterations=100,
            tolerance=1e-3,
            parallel=True,
            parallel_group_solve=False,
            verbose=False,
            skip_solution_validation=True,
        )
        solver = MultiGroupDiffusion(geometry, xs, opts)
        k_eff, flux = solver.solve_steady_state()
        assert k_eff > 0
        assert flux.shape[0] == 3 and flux.shape[1] == 4 and flux.shape[2] == 2
