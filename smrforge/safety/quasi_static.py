"""
Quasi-static spatial dynamics using shape/amplitude factorization.

Implements the quasi-static method for reactor transient analysis where
the flux is factorized as phi(r,t) = shape(r,t) * amplitude(t).
The shape function evolves slowly; the amplitude captures fast changes.
Used for spatial kinetics in LOFC, ATWS, and other transients.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from scipy.integrate import odeint

from ..utils.logging import get_logger

logger = get_logger("smrforge.safety.quasi_static")


@dataclass
class QuasiStaticOptions:
    """Options for quasi-static solver."""

    max_shape_steps: int = 100
    shape_tolerance: float = 1e-6
    amplitude_tolerance: float = 1e-8
    min_shape_update_interval: float = 0.01  # seconds
    use_constant_shape: bool = False  # If True, skip shape updates (faster)


@dataclass
class QuasiStaticResult:
    """Result of quasi-static transient solve."""

    times: np.ndarray
    amplitudes: np.ndarray
    shapes: List[np.ndarray]
    power_history: np.ndarray
    reactivity_history: np.ndarray
    converged: bool
    n_shape_updates: int


class QuasiStaticSolver:
    """
    Quasi-static solver using shape/amplitude factorization.

    Factorizes the space-time dependent flux as:
        phi(r,t) = shape(r,t) * amplitude(t)

    The amplitude equation (point kinetics) advances quickly.
    The shape function is updated periodically to capture spatial feedback.

    Attributes:
        n_nodes: Number of spatial nodes
        lambda_i: Delayed neutron precursor decay constants [1/s]
        beta_i: Delayed neutron fractions
        beta_total: Total delayed neutron fraction
        gen_time: Neutron generation time [s]

    Example:
        >>> solver = QuasiStaticSolver(
        ...     n_nodes=10,
        ...     beta_total=0.007,
        ...     gen_time=1e-5,
        ... )
        >>> result = solver.solve(
        ...     t_span=(0, 100),
        ...     reactivity_fn=lambda t: 0.001 * np.sin(0.1 * t),
        ...     initial_power=1.0,
        ... )
    """

    def __init__(
        self,
        n_nodes: int = 10,
        beta_total: float = 0.007,
        gen_time: float = 1e-5,
        n_precursor_groups: int = 6,
        options: Optional[QuasiStaticOptions] = None,
    ):
        """
        Initialize quasi-static solver.

        Args:
            n_nodes: Number of spatial nodes for shape function
            beta_total: Total delayed neutron fraction
            gen_time: Neutron generation time [s]
            n_precursor_groups: Number of delayed neutron precursor groups
            options: Solver options (default: QuasiStaticOptions())
        """
        self.n_nodes = n_nodes
        self.beta_total = beta_total
        self.gen_time = gen_time
        self.n_precursor_groups = n_precursor_groups
        self.options = options or QuasiStaticOptions()

        # Standard 6-group delayed neutron data (approximate U-235)
        self.lambda_i = np.array(
            [0.0127, 0.0317, 0.116, 0.311, 1.14, 3.01]
        )[:n_precursor_groups]
        self.beta_i = np.array(
            [0.000266, 0.001491, 0.001316, 0.002849, 0.000896, 0.000182]
        )[:n_precursor_groups]
        # Scale to match beta_total
        if np.sum(self.beta_i) > 0:
            self.beta_i = self.beta_i * (beta_total / np.sum(self.beta_i))

        logger.debug(
            f"QuasiStaticSolver: n_nodes={n_nodes}, beta={beta_total}, "
            f"Lambda={gen_time:.2e}s"
        )

    def _point_kinetics_rhs(
        self,
        t: float,
        y: np.ndarray,
        rho: float,
    ) -> np.ndarray:
        """
        Point kinetics RHS: [n, c1, c2, ..., c6].

        dy/dt = (rho - beta)/Lambda * n + sum(lambda_i * c_i)
        dc_i/dt = beta_i/Lambda * n - lambda_i * c_i
        """
        y = np.atleast_1d(np.asarray(y))
        n = y[0]
        c = y[1 : 1 + self.n_precursor_groups]
        rho_beta_over_L = (rho - self.beta_total) / self.gen_time
        dn_dt = rho_beta_over_L * n + np.dot(self.lambda_i, c)
        dc_dt = (self.beta_i / self.gen_time) * n - self.lambda_i * c
        return np.concatenate([[dn_dt], dc_dt])

    def _update_shape(
        self,
        shape: np.ndarray,
        amplitude: float,
        reactivity: float,
        material_feedback: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Update shape function (simplified diffusion-like relaxation).

        In full implementation, this would solve the static eigenvalue problem
        with updated material properties. Here we use a relaxation step.
        """
        if material_feedback is not None and material_feedback.size == shape.size:
            # Simple feedback: perturb shape toward feedback distribution
            alpha = 0.1 * np.clip(reactivity, -0.01, 0.01)
            shape_new = shape + alpha * (material_feedback - shape)
        else:
            # Mild smoothing (mimics spatial coupling)
            shape_new = np.copy(shape)
            for i in range(1, self.n_nodes - 1):
                shape_new[i] = 0.25 * (shape[i - 1] + 2 * shape[i] + shape[i + 1])
        # Normalize
        norm = np.sum(np.abs(shape_new))
        if norm > 0:
            shape_new = shape_new / norm
        return shape_new

    def solve(
        self,
        t_span: Tuple[float, float],
        reactivity_fn: Callable[[float], float],
        initial_power: float = 1.0,
        n_times: int = 200,
        material_feedback_fn: Optional[Callable[[float, np.ndarray], np.ndarray]] = None,
    ) -> QuasiStaticResult:
        """
        Solve quasi-static transient.

        Args:
            t_span: (t_start, t_end) in seconds
            reactivity_fn: Reactivity vs time [$/pcm], rho(t)
            initial_power: Initial power (normalized to 1.0)
            n_times: Number of output time points
            material_feedback_fn: Optional (t, shape) -> feedback_shape for
                temperature/density feedback

        Returns:
            QuasiStaticResult with times, amplitudes, shapes, power, reactivity
        """
        t0, t1 = t_span
        times = np.linspace(t0, t1, n_times)

        # Initial shape (cosine-like)
        shape = np.cos(np.pi * np.linspace(0, 1, self.n_nodes))
        shape = np.maximum(shape, 0.01)
        shape = shape / np.sum(shape)

        # Initial amplitude and precursors
        n0 = initial_power
        c0 = (self.beta_i / (self.gen_time * self.lambda_i)) * n0
        y0 = np.concatenate([[n0], c0])

        last_shape_update = t0
        shapes: List[np.ndarray] = [shape.copy()]
        amplitudes: List[float] = [n0]
        power_history = [n0]
        reactivity_history = [reactivity_fn(t0)]
        n_shape_updates = 0

        dt = (t1 - t0) / max(1, n_times - 1)

        for i in range(1, n_times):
            t = times[i]
            rho = reactivity_fn(t)

            # Advance point kinetics
            y_prev = np.concatenate([[amplitudes[-1]], c0]) if i == 1 else y_prev
            ts = [times[i - 1], t]
            sol = odeint(
                self._point_kinetics_rhs,
                y_prev,
                ts,
                args=(rho,),
                tfirst=True,
            )
            y_prev = sol[-1]
            n_new = y_prev[0]
            c0 = y_prev[1:]

            amplitudes.append(n_new)
            power_history.append(n_new)
            reactivity_history.append(rho)

            # Shape update?
            if (
                not self.options.use_constant_shape
                and (t - last_shape_update) >= self.options.min_shape_update_interval
            ):
                feedback = None
                if material_feedback_fn is not None:
                    feedback = material_feedback_fn(t, shape)
                shape_new = self._update_shape(shape, n_new, rho, feedback)
                # Check convergence
                if np.max(np.abs(shape_new - shape)) < self.options.shape_tolerance:
                    n_shape_updates += 1
                    shape = shape_new
                    shapes.append(shape.copy())
                    last_shape_update = t

        return QuasiStaticResult(
            times=np.array(times),
            amplitudes=np.array(amplitudes),
            shapes=shapes,
            power_history=np.array(power_history),
            reactivity_history=np.array(reactivity_history),
            converged=True,
            n_shape_updates=n_shape_updates,
        )
