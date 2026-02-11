# smrforge/neutronics/monte_carlo.py
"""
Monte Carlo neutron transport for SMRForge.
Simplified implementation for design studies and validation.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from numba import jit, njit, prange
from rich.console import Console
from rich.progress import Progress, track
from rich.table import Table

from ..utils.logging import get_logger
from ..validation.models import CrossSectionData, ReactorSpecification

# Get logger for this module
logger = get_logger("smrforge.neutronics.monte_carlo")


class ParticleType(Enum):
    """Types of particles to track."""

    NEUTRON = "neutron"
    PHOTON = "photon"


class ReactionType(Enum):
    """Nuclear reaction types."""

    SCATTER = "scatter"
    FISSION = "fission"
    CAPTURE = "capture"
    ESCAPE = "escape"


@dataclass
class MCParticle:
    """Monte Carlo particle representation."""

    x: float = 0.0  # Position [cm]
    y: float = 0.0
    z: float = 0.0

    u: float = 0.0  # Direction cosines
    v: float = 0.0
    w: float = 1.0

    energy: float = 2e6  # Energy [eV]
    weight: float = 1.0  # Statistical weight

    alive: bool = True
    generation: int = 0  # For k-eff calculations

    def position(self) -> np.ndarray:
        """Get position as array."""
        return np.array([self.x, self.y, self.z])

    def direction(self) -> np.ndarray:
        """Get direction as array."""
        return np.array([self.u, self.v, self.w])


@dataclass
class MCTally:
    """Monte Carlo tally (detector)."""

    name: str
    tally_type: str  # 'flux', 'fission_rate', 'capture_rate', 'k_eff'
    score: float = 0.0
    score_sq: float = 0.0  # For variance
    count: int = 0

    # Spatial binning (optional)
    r_bins: Optional[np.ndarray] = None
    z_bins: Optional[np.ndarray] = None
    energy_bins: Optional[np.ndarray] = None

    # Binned scores
    bin_scores: Optional[np.ndarray] = None
    bin_scores_sq: Optional[np.ndarray] = None
    bin_counts: Optional[np.ndarray] = None

    def __post_init__(self):
        """Initialize binned arrays if bins provided."""
        if self.r_bins is not None and self.z_bins is not None:
            shape = (len(self.r_bins) - 1, len(self.z_bins) - 1)
            self.bin_scores = np.zeros(shape)
            self.bin_scores_sq = np.zeros(shape)
            self.bin_counts = np.zeros(shape, dtype=int)

    def add_score(self, value: float, position: Optional[Tuple] = None):
        """Add score to tally."""
        self.score += value
        self.score_sq += value**2
        self.count += 1

        if position is not None and self.bin_scores is not None:
            r, z = position
            ir = np.searchsorted(self.r_bins, r) - 1
            iz = np.searchsorted(self.z_bins, z) - 1

            if 0 <= ir < len(self.r_bins) - 1 and 0 <= iz < len(self.z_bins) - 1:
                self.bin_scores[ir, iz] += value
                self.bin_scores_sq[ir, iz] += value**2
                self.bin_counts[ir, iz] += 1

    @property
    def mean(self) -> float:
        """Mean tally value."""
        return self.score / max(self.count, 1)

    @property
    def std(self) -> float:
        """Standard deviation of tally."""
        if self.count < 2:
            return 0.0
        variance = (self.score_sq / self.count) - self.mean**2
        return np.sqrt(max(variance / self.count, 0))

    @property
    def relative_error(self) -> float:
        """Relative error (1 sigma)."""
        if self.mean == 0:
            return float("inf")
        return self.std / abs(self.mean)


class SimplifiedGeometry:
    """
    Simplified geometry for MC tracking.
    Cylindrical core with reflector.
    """

    def __init__(
        self, core_diameter: float, core_height: float, reflector_thickness: float
    ):
        self.r_core = core_diameter / 2  # cm
        self.h_core = core_height  # cm
        self.r_reflector = self.r_core + reflector_thickness
        self.material_map = {"fuel": 0, "reflector": 1, "outside": -1}

    def get_material(self, x: float, y: float, z: float) -> int:
        """Get material ID at position."""
        r = np.sqrt(x**2 + y**2)

        # Outside reactor
        if r > self.r_reflector or z < 0 or z > self.h_core:
            return self.material_map["outside"]

        # In reflector
        if r > self.r_core:
            return self.material_map["reflector"]

        # In fuel
        return self.material_map["fuel"]

    def distance_to_boundary(self, particle: MCParticle) -> Tuple[float, int]:
        """
        Compute distance to next material boundary.

        Returns:
            distance: Distance to boundary [cm]
            next_material: Material ID after crossing
        """
        r = np.sqrt(particle.x**2 + particle.y**2)

        # Distance to cylinder surface
        a = particle.u**2 + particle.v**2
        b = 2 * (particle.x * particle.u + particle.y * particle.v)
        c_core = particle.x**2 + particle.y**2 - self.r_core**2
        c_refl = particle.x**2 + particle.y**2 - self.r_reflector**2

        distances = []
        materials = []

        # Core boundary
        if a > 1e-10:
            disc = b**2 - 4 * a * c_core
            if disc > 0:
                t1 = (-b + np.sqrt(disc)) / (2 * a)
                t2 = (-b - np.sqrt(disc)) / (2 * a)
                for t in [t1, t2]:
                    if t > 1e-6:
                        distances.append(t)
                        materials.append(1)  # Entering reflector

        # Reflector boundary
        if a > 1e-10:
            disc = b**2 - 4 * a * c_refl
            if disc > 0:
                t1 = (-b + np.sqrt(disc)) / (2 * a)
                t2 = (-b - np.sqrt(disc)) / (2 * a)
                for t in [t1, t2]:
                    if t > 1e-6:
                        distances.append(t)
                        materials.append(-1)  # Escaping

        # Axial boundaries
        if abs(particle.w) > 1e-10:
            t_bottom = -particle.z / particle.w
            t_top = (self.h_core - particle.z) / particle.w

            if t_bottom > 1e-6:
                distances.append(t_bottom)
                materials.append(-1)
            if t_top > 1e-6:
                distances.append(t_top)
                materials.append(-1)

        if not distances:
            return 1e10, -1

        min_idx = np.argmin(distances)
        return distances[min_idx], materials[min_idx]


class MonteCarloSolver:
    """
    Simplified Monte Carlo neutron transport solver.

    This is for educational purposes and quick design studies.

    Args:
        geometry: Simplified geometry object
        xs_data: Cross-section data (Pydantic validated)
        n_particles: Number of particles per generation (must be > 0)
        n_generations: Number of generations (must be > 0)
        seed: Random number generator seed for reproducibility (optional)

    Raises:
        ValueError: If input parameters are invalid
    """

    def __init__(
        self,
        geometry: SimplifiedGeometry,
        xs_data: CrossSectionData,
        n_particles: int = 10000,
        n_generations: int = 100,
        seed: Optional[int] = None,
    ):
        # Validate inputs
        self._validate_inputs(geometry, xs_data, n_particles, n_generations)

        self.geometry = geometry
        self.xs_data = xs_data
        self.n_particles = n_particles
        self.n_generations = n_generations

        self.console = Console()
        self.tallies: Dict[str, MCTally] = {}
        self.k_eff_history: List[float] = []

        # Random number generator with seed for reproducibility
        self.rng = np.random.default_rng(seed)
        if seed is not None:
            logger.info(f"Monte Carlo solver initialized with seed={seed}")
        else:
            logger.debug("Monte Carlo solver initialized with random seed")

    def _validate_inputs(
        self,
        geometry: SimplifiedGeometry,
        xs_data: CrossSectionData,
        n_particles: int,
        n_generations: int,
    ) -> None:
        """Validate input parameters."""
        if not isinstance(geometry, SimplifiedGeometry):
            raise ValueError(
                f"geometry must be SimplifiedGeometry, got {type(geometry)}"
            )

        if not isinstance(xs_data, CrossSectionData):
            raise ValueError(f"xs_data must be CrossSectionData, got {type(xs_data)}")

        if n_particles <= 0:
            raise ValueError(f"n_particles must be > 0, got {n_particles}")

        if n_generations <= 0:
            raise ValueError(f"n_generations must be > 0, got {n_generations}")

        # Validate that xs_data has compatible number of materials
        # Geometry expects fuel (0) and reflector (1)
        if xs_data.n_materials < 2:
            logger.warning(
                f"xs_data has {xs_data.n_materials} materials, "
                f"but geometry expects at least 2 (fuel and reflector)"
            )

        # Validate cross-section data has at least one group
        if xs_data.n_groups < 1:
            raise ValueError(
                f"xs_data must have at least 1 group, got {xs_data.n_groups}"
            )

        logger.debug(
            f"Validated inputs: {n_particles} particles, {n_generations} generations, "
            f"{xs_data.n_groups} groups, {xs_data.n_materials} materials"
        )

    def add_tally(self, tally: MCTally):
        """
        Add a tally to track.

        Args:
            tally: MCTally object to add

        Raises:
            ValueError: If tally is not an MCTally instance
        """
        if not isinstance(tally, MCTally):
            raise ValueError(f"tally must be MCTally, got {type(tally)}")
        self.tallies[tally.name] = tally
        logger.debug(f"Added tally: {tally.name} (type: {tally.tally_type})")

    def run_eigenvalue(self) -> Dict:
        """
        Run k-eff calculation using power iteration.

        Returns:
            Dict with k_eff, k_std, k_history, and tallies

        Raises:
            RuntimeError: If calculation fails or produces invalid results
        """
        logger.info(
            f"Starting Monte Carlo eigenvalue calculation: "
            f"{self.n_particles} particles, {self.n_generations} generations"
        )
        self.console.print(f"[bold cyan]Monte Carlo Eigenvalue Calculation[/bold cyan]")
        self.console.print(f"Particles: {self.n_particles}")
        self.console.print(f"Generations: {self.n_generations}")

        # Initialize source
        try:
            source_bank = self._initialize_source()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize source: {e}") from e

        if len(source_bank) == 0:
            raise RuntimeError("Failed to initialize source: empty source bank")

        # Skip first generations (inactive)
        n_inactive = max(10, self.n_generations // 10)

        with Progress() as progress:
            task = progress.add_task("Running generations...", total=self.n_generations)

            for gen in range(self.n_generations):
                # Fission bank for next generation
                fission_bank = []

                # Track particles
                for particle in source_bank:
                    particle.generation = gen
                    fissions = self._track_particle(particle)
                    fission_bank.extend(fissions)

                # Compute k_eff for this generation
                k_gen = len(fission_bank) / len(source_bank)
                self.k_eff_history.append(k_gen)

                # Resample source for next generation
                source_bank = self._resample_source(fission_bank, self.n_particles)

                # Update tallies only after inactive generations
                if gen >= n_inactive:
                    for tally in self.tallies.values():
                        pass  # Tallies already updated in _track_particle

                progress.update(task, advance=1)

        # Compute final k_eff (skip inactive generations)
        active_history = self.k_eff_history[n_inactive:]
        if len(active_history) == 0:
            raise RuntimeError(
                f"All {self.n_generations} generations were inactive. "
                f"Increase n_generations or reduce inactive count."
            )

        k_eff = np.mean(active_history)
        k_std = np.std(active_history)

        # Validate results
        if not np.isfinite(k_eff):
            raise RuntimeError(f"Invalid k_eff: {k_eff}")
        if not np.isfinite(k_std):
            k_std = 0.0
            logger.warning("k_std is not finite, setting to 0.0")

        logger.info(
            f"Monte Carlo calculation complete: k_eff = {k_eff:.6f} ± {k_std:.6f}"
        )
        self.console.print(
            f"\n[bold green]k_eff = {k_eff:.6f} ± {k_std:.6f}[/bold green]"
        )

        return {
            "k_eff": k_eff,
            "k_std": k_std,
            "k_history": self.k_eff_history,
            "tallies": self.tallies,
        }

    def _initialize_source(self) -> List[MCParticle]:
        """Initialize uniform fission source."""
        particles = []

        for _ in range(self.n_particles):
            # Uniform in cylinder
            r = self.geometry.r_core * np.sqrt(self.rng.random())
            theta = 2 * np.pi * self.rng.random()
            x = r * np.cos(theta)
            y = r * np.sin(theta)
            z = self.geometry.h_core * self.rng.random()

            # Isotropic direction
            u, v, w = self._sample_isotropic_direction()

            # Fission spectrum energy
            energy = self._sample_fission_spectrum()

            particle = MCParticle(
                x=x, y=y, z=z, u=u, v=v, w=w, energy=energy, weight=1.0, alive=True
            )
            particles.append(particle)

        return particles

    def _track_particle(self, particle: MCParticle) -> List[MCParticle]:
        """
        Track single particle through geometry.

        Returns:
            List of fission sites for next generation
        """
        fission_sites = []

        while particle.alive:
            # Get current material
            mat_id = self.geometry.get_material(particle.x, particle.y, particle.z)

            # Escaped
            if mat_id < 0:
                particle.alive = False
                break

            # Sample distance to collision
            sigma_t = self._get_total_xs(mat_id, particle.energy)
            if sigma_t <= 0:
                particle.alive = False
                break

            d_collision = -np.log(self.rng.random()) / sigma_t

            # Distance to boundary
            d_boundary, next_mat = self.geometry.distance_to_boundary(particle)

            # Collision occurs before boundary
            if d_collision < d_boundary:
                # Move to collision site
                particle.x += d_collision * particle.u
                particle.y += d_collision * particle.v
                particle.z += d_collision * particle.w

                # Score tallies
                self._score_tallies(particle, d_collision)

                # Sample collision type
                reaction = self._sample_reaction(mat_id, particle.energy)

                if reaction == ReactionType.FISSION:
                    # Create fission sites (use nu=2.5 for simplicity)
                    nu = 2.5
                    for _ in range(int(nu)):
                        fission_site = MCParticle(
                            x=particle.x,
                            y=particle.y,
                            z=particle.z,
                            u=0,
                            v=0,
                            w=0,  # Will be resampled
                            energy=particle.energy,
                            weight=particle.weight,
                        )
                        fission_sites.append(fission_site)

                    particle.alive = False

                elif reaction == ReactionType.SCATTER:
                    # Isotropic scatter (simplified)
                    particle.u, particle.v, particle.w = (
                        self._sample_isotropic_direction()
                    )
                    # Energy stays same (elastic scatter approximation)

                elif reaction == ReactionType.CAPTURE:
                    particle.alive = False

            else:
                # Move to boundary
                particle.x += d_boundary * particle.u
                particle.y += d_boundary * particle.v
                particle.z += d_boundary * particle.w

                # Check if escaped
                if next_mat < 0:
                    particle.alive = False

        return fission_sites

    def _sample_isotropic_direction(self) -> Tuple[float, float, float]:
        """Sample isotropic direction."""
        mu = 2 * self.rng.random() - 1  # cos(theta)
        phi = 2 * np.pi * self.rng.random()

        sin_theta = np.sqrt(1 - mu**2)
        u = sin_theta * np.cos(phi)
        v = sin_theta * np.sin(phi)
        w = mu

        return u, v, w

    def _sample_fission_spectrum(self) -> float:
        """Sample energy from fission spectrum."""
        # Watt spectrum approximation (simplified)
        # Real implementation would use proper sampling
        E_mean = 2e6  # 2 MeV
        return self.rng.exponential(E_mean)

    def _get_total_xs(self, mat_id: int, energy: float) -> float:
        """Get total cross section (simplified - 1 group)."""
        if mat_id >= 0 and mat_id < self.xs_data.n_materials:
            # Use highest energy group as approximation
            return self.xs_data.sigma_t[mat_id, 0]
        return 0.0

    def _sample_reaction(self, mat_id: int, energy: float) -> ReactionType:
        """
        Sample reaction type.

        Args:
            mat_id: Material ID
            energy: Neutron energy [eV]

        Returns:
            ReactionType enum value

        Raises:
            IndexError: If mat_id is out of bounds
        """
        if mat_id < 0 or mat_id >= self.xs_data.n_materials:
            raise IndexError(
                f"Material ID {mat_id} out of range [0, {self.xs_data.n_materials})"
            )

        # Simplified - use 1 group approximation
        sigma_t = self.xs_data.sigma_t[mat_id, 0]
        sigma_s = self.xs_data.sigma_s[mat_id, 0, 0]
        sigma_f = self.xs_data.sigma_f[mat_id, 0]
        sigma_c = sigma_t - sigma_s - sigma_f

        # Validate cross sections
        if sigma_t <= 0:
            raise ValueError(
                f"Invalid total cross section: {sigma_t} for material {mat_id}"
            )

        # Sample
        xi = self.rng.random() * sigma_t

        if xi < sigma_s:
            return ReactionType.SCATTER
        elif xi < sigma_s + sigma_f:
            return ReactionType.FISSION
        else:
            return ReactionType.CAPTURE

    def _score_tallies(self, particle: MCParticle, distance: float):
        """Score tallies for this particle."""
        for tally in self.tallies.values():
            if tally.tally_type == "flux":
                # Track length estimator
                tally.add_score(
                    particle.weight * distance,
                    position=(np.sqrt(particle.x**2 + particle.y**2), particle.z),
                )

    def _resample_source(
        self, fission_bank: List[MCParticle], n_target: int
    ) -> List[MCParticle]:
        """Resample source from fission bank."""
        if len(fission_bank) == 0:
            return self._initialize_source()

        # Randomly select with replacement
        indices = self.rng.choice(len(fission_bank), size=n_target, replace=True)

        source = []
        for idx in indices:
            particle = fission_bank[idx]
            # Resample direction and energy
            particle.u, particle.v, particle.w = self._sample_isotropic_direction()
            particle.energy = self._sample_fission_spectrum()
            particle.alive = True
            source.append(particle)

        return source

    def print_results(self):
        """Print formatted results."""
        table = Table(title="Monte Carlo Tallies")
        table.add_column("Tally", style="cyan")
        table.add_column("Mean", justify="right")
        table.add_column("Std Dev", justify="right")
        table.add_column("Rel. Error", justify="right")

        for name, tally in self.tallies.items():
            table.add_row(
                name,
                f"{tally.mean:.4e}",
                f"{tally.std:.4e}",
                f"{tally.relative_error*100:.2f}%",
            )

        self.console.print(table)


if __name__ == "__main__":
    console = Console()
    console.print("[bold cyan]Monte Carlo Neutronics Module Demo[/bold cyan]\n")

    # Test simplified MC
    console.print("[bold]1. Simplified Monte Carlo[/bold]")

    # Create geometry
    geometry = SimplifiedGeometry(
        core_diameter=200.0, core_height=400.0, reflector_thickness=50.0
    )

    # Create cross sections
    xs_data = CrossSectionData(
        n_groups=1,
        n_materials=2,
        sigma_t=np.array([[0.5], [0.3]]),
        sigma_a=np.array([[0.05], [0.01]]),
        sigma_f=np.array([[0.04], [0.0]]),
        nu_sigma_f=np.array([[0.10], [0.0]]),
        sigma_s=np.array([[[0.41]], [[0.29]]]),
        chi=np.array([[1.0], [1.0]]),
        D=np.array([[1.0], [1.5]]),
    )

    # Run MC
    mc = MonteCarloSolver(
        geometry=geometry, xs_data=xs_data, n_particles=1000, n_generations=50
    )

    # Add flux tally
    flux_tally = MCTally(
        name="core_flux",
        tally_type="flux",
        r_bins=np.linspace(0, 100, 11),
        z_bins=np.linspace(0, 400, 21),
    )
    mc.add_tally(flux_tally)

    results = mc.run_eigenvalue()
    mc.print_results()

    console.print("\n[bold green]Monte Carlo module ready![/bold green]")
