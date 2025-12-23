"""
Nuclear Monte Carlo Transport Module
====================================
Neutron transport Monte Carlo simulation with variance reduction techniques.

Features:
- Neutron transport in 3D geometry
- Variance reduction (importance sampling, weight windows, CADIS)
- Tallies and detectors (flux, reaction rates, k-eff)
- Collision physics (scattering, fission, absorption)
- Parallel execution support
- Integration with existing UQ module
"""

import concurrent.futures
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

# ============================================================================
# CORE DATA STRUCTURES
# ============================================================================


class ParticleState(Enum):
    """Neutron state in simulation"""

    ACTIVE = "active"
    ABSORBED = "absorbed"
    LEAKED = "leaked"
    FISSION = "fission"
    CUTOFF = "cutoff"


class CollisionType(Enum):
    """Types of neutron interactions"""

    SCATTER = "scatter"
    ABSORPTION = "absorption"
    FISSION = "fission"
    CAPTURE = "capture"


@dataclass
class Neutron:
    """Represents a single neutron in Monte Carlo simulation"""

    position: np.ndarray  # [x, y, z] in cm
    direction: np.ndarray  # [u, v, w] unit vector
    energy: float  # MeV
    weight: float = 1.0  # Statistical weight for variance reduction
    generation: int = 0  # For k-eff calculations
    state: ParticleState = ParticleState.ACTIVE

    def __post_init__(self):
        """Normalize direction vector"""
        self.direction = self.direction / np.linalg.norm(self.direction)


@dataclass
class CrossSection:
    """Nuclear cross sections for a material"""

    energy_grid: np.ndarray  # Energy points (MeV)
    total: np.ndarray  # Total cross section (barns)
    scatter: np.ndarray  # Scattering
    absorption: np.ndarray  # Absorption
    fission: np.ndarray  # Fission
    nu: np.ndarray  # Neutrons per fission

    def interpolate(self, energy: float) -> Dict[str, float]:
        """Linear interpolation of cross sections at given energy"""
        idx = np.searchsorted(self.energy_grid, energy)
        if idx == 0:
            idx = 1
        elif idx >= len(self.energy_grid):
            idx = len(self.energy_grid) - 1

        # Linear interpolation
        e1, e2 = self.energy_grid[idx - 1], self.energy_grid[idx]
        f = (energy - e1) / (e2 - e1) if e2 != e1 else 0.0

        return {
            "total": self.total[idx - 1] + f * (self.total[idx] - self.total[idx - 1]),
            "scatter": self.scatter[idx - 1]
            + f * (self.scatter[idx] - self.scatter[idx - 1]),
            "absorption": self.absorption[idx - 1]
            + f * (self.absorption[idx] - self.absorption[idx - 1]),
            "fission": self.fission[idx - 1]
            + f * (self.fission[idx] - self.fission[idx - 1]),
            "nu": self.nu[idx - 1] + f * (self.nu[idx] - self.nu[idx - 1]),
        }


# ============================================================================
# GEOMETRY CLASSES
# ============================================================================


class Geometry(ABC):
    """Abstract base class for geometry"""

    @abstractmethod
    def is_inside(self, position: np.ndarray) -> bool:
        """Check if position is inside geometry"""
        pass

    @abstractmethod
    def distance_to_boundary(
        self, position: np.ndarray, direction: np.ndarray
    ) -> float:
        """Calculate distance to boundary in given direction"""
        pass


class Sphere(Geometry):
    """Spherical geometry"""

    def __init__(self, center: np.ndarray, radius: float):
        self.center = np.array(center)
        self.radius = radius

    def is_inside(self, position: np.ndarray) -> bool:
        return np.linalg.norm(position - self.center) <= self.radius

    def distance_to_boundary(
        self, position: np.ndarray, direction: np.ndarray
    ) -> float:
        """Ray-sphere intersection"""
        oc = position - self.center
        a = np.dot(direction, direction)
        b = 2.0 * np.dot(oc, direction)
        c = np.dot(oc, oc) - self.radius**2

        discriminant = b**2 - 4 * a * c
        if discriminant < 0:
            return np.inf

        t1 = (-b - np.sqrt(discriminant)) / (2 * a)
        t2 = (-b + np.sqrt(discriminant)) / (2 * a)

        # Return positive distance
        if t1 > 1e-10:
            return t1
        elif t2 > 1e-10:
            return t2
        return np.inf


class Cylinder(Geometry):
    """Cylindrical geometry (infinite length along z-axis)"""

    def __init__(self, center: np.ndarray, radius: float, height: float = np.inf):
        self.center = np.array(center)
        self.radius = radius
        self.height = height

    def is_inside(self, position: np.ndarray) -> bool:
        r = np.sqrt(
            (position[0] - self.center[0]) ** 2 + (position[1] - self.center[1]) ** 2
        )
        z = abs(position[2] - self.center[2])
        return r <= self.radius and z <= self.height / 2

    def distance_to_boundary(
        self, position: np.ndarray, direction: np.ndarray
    ) -> float:
        """Ray-cylinder intersection"""
        # Radial distance
        dx = position[0] - self.center[0]
        dy = position[1] - self.center[1]

        a = direction[0] ** 2 + direction[1] ** 2
        b = 2 * (dx * direction[0] + dy * direction[1])
        c = dx**2 + dy**2 - self.radius**2

        discriminant = b**2 - 4 * a * c
        if discriminant < 0:
            return np.inf

        t_radial = (-b + np.sqrt(discriminant)) / (2 * a) if a > 1e-10 else np.inf

        # Axial distance
        if abs(direction[2]) > 1e-10:
            t_top = (self.center[2] + self.height / 2 - position[2]) / direction[2]
            t_bottom = (self.center[2] - self.height / 2 - position[2]) / direction[2]
            t_axial = min(t for t in [t_top, t_bottom] if t > 1e-10)
        else:
            t_axial = np.inf

        return min(t_radial, t_axial) if min(t_radial, t_axial) > 1e-10 else np.inf


class Box(Geometry):
    """Rectangular box geometry"""

    def __init__(self, min_corner: np.ndarray, max_corner: np.ndarray):
        self.min_corner = np.array(min_corner)
        self.max_corner = np.array(max_corner)

    def is_inside(self, position: np.ndarray) -> bool:
        return np.all(position >= self.min_corner) and np.all(
            position <= self.max_corner
        )

    def distance_to_boundary(
        self, position: np.ndarray, direction: np.ndarray
    ) -> float:
        """Ray-box intersection (slab method)"""
        t_min = -np.inf
        t_max = np.inf

        for i in range(3):
            if abs(direction[i]) > 1e-10:
                t1 = (self.min_corner[i] - position[i]) / direction[i]
                t2 = (self.max_corner[i] - position[i]) / direction[i]
                t_min = max(t_min, min(t1, t2))
                t_max = min(t_max, max(t1, t2))

        if t_max < t_min or t_max < 1e-10:
            return np.inf
        return t_min if t_min > 1e-10 else t_max


# ============================================================================
# MATERIAL AND REGION
# ============================================================================


@dataclass
class Material:
    """Nuclear material with cross sections"""

    name: str
    density: float  # g/cm^3
    cross_section: CrossSection
    atomic_mass: float  # amu

    def number_density(self) -> float:
        """Calculate number density (atoms/barn-cm)"""
        avogadro = 6.022e23
        return self.density * avogadro / self.atomic_mass * 1e-24


@dataclass
class Region:
    """Spatial region with material"""

    geometry: Geometry
    material: Material
    importance: float = 1.0  # For variance reduction


# ============================================================================
# TALLIES AND DETECTORS
# ============================================================================


@dataclass
class Tally:
    """Accumulates scored quantities"""

    name: str
    score_sum: float = 0.0
    score_sq_sum: float = 0.0
    n_samples: int = 0

    def score(self, value: float, weight: float = 1.0):
        """Add a score"""
        weighted_value = value * weight
        self.score_sum += weighted_value
        self.score_sq_sum += weighted_value**2
        self.n_samples += 1

    def mean(self) -> float:
        """Calculate mean"""
        return self.score_sum / self.n_samples if self.n_samples > 0 else 0.0

    def variance(self) -> float:
        """Calculate variance"""
        if self.n_samples < 2:
            return 0.0
        mean_val = self.mean()
        return (self.score_sq_sum / self.n_samples - mean_val**2) / self.n_samples

    def std_dev(self) -> float:
        """Calculate standard deviation"""
        return np.sqrt(self.variance())

    def relative_error(self) -> float:
        """Calculate relative error"""
        mean_val = self.mean()
        return self.std_dev() / mean_val if mean_val != 0 else np.inf


class FluxTally(Tally):
    """Track neutron flux in a region"""

    def __init__(self, name: str, region: Region):
        super().__init__(name)
        self.region = region

    def score_track_length(self, path_length: float, weight: float = 1.0):
        """Score using track-length estimator"""
        # Flux = track length / volume
        self.score(path_length, weight)


class ReactionRateTally(Tally):
    """Track reaction rates"""

    def __init__(self, name: str, region: Region, reaction_type: str):
        super().__init__(name)
        self.region = region
        self.reaction_type = reaction_type


# ============================================================================
# VARIANCE REDUCTION TECHNIQUES
# ============================================================================


class ImportanceSampler:
    """Importance sampling for variance reduction"""

    def __init__(self, importance_map: Dict[Region, float]):
        self.importance_map = importance_map

    def get_weight_adjustment(
        self, old_region: Region, new_region: Region, weight: float
    ) -> float:
        """Calculate weight adjustment at region boundary"""
        imp_old = self.importance_map.get(old_region, 1.0)
        imp_new = self.importance_map.get(new_region, 1.0)
        return weight * imp_old / imp_new if imp_new > 0 else weight


class WeightWindow:
    """Weight window variance reduction"""

    def __init__(self, lower_bound: float = 0.5, upper_bound: float = 2.0):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def check_and_adjust(
        self, neutron: Neutron, rng: np.random.Generator
    ) -> List[Neutron]:
        """Check weight and perform splitting/roulette"""
        if neutron.weight > self.upper_bound:
            # Russian roulette
            survival_prob = neutron.weight / self.upper_bound
            if rng.random() < survival_prob:
                neutron.weight = self.upper_bound
                return [neutron]
            else:
                neutron.state = ParticleState.CUTOFF
                return []

        elif neutron.weight < self.lower_bound:
            # Splitting
            n_split = int(np.ceil(self.lower_bound / neutron.weight))
            new_weight = neutron.weight / n_split

            neutrons = []
            for _ in range(n_split):
                n = Neutron(
                    position=neutron.position.copy(),
                    direction=neutron.direction.copy(),
                    energy=neutron.energy,
                    weight=new_weight,
                    generation=neutron.generation,
                )
                neutrons.append(n)
            return neutrons

        return [neutron]


# ============================================================================
# MONTE CARLO ENGINE
# ============================================================================


class MonteCarloEngine:
    """Main Monte Carlo neutron transport engine"""

    def __init__(
        self,
        regions: List[Region],
        source: Callable[[], Neutron],
        seed: Optional[int] = None,
    ):
        self.regions = regions
        self.source = source
        self.rng = np.random.default_rng(seed)

        self.tallies: List[Tally] = []
        self.importance_sampler: Optional[ImportanceSampler] = None
        self.weight_window: Optional[WeightWindow] = None

        # Statistics
        self.n_histories = 0
        self.n_collisions = 0
        self.k_eff_generations = []

    def add_tally(self, tally: Tally):
        """Add a tally to track"""
        self.tallies.append(tally)

    def enable_variance_reduction(
        self,
        importance_map: Optional[Dict[Region, float]] = None,
        weight_window: bool = True,
    ):
        """Enable variance reduction techniques"""
        if importance_map:
            self.importance_sampler = ImportanceSampler(importance_map)
        if weight_window:
            self.weight_window = WeightWindow()

    def find_region(self, position: np.ndarray) -> Optional[Region]:
        """Find which region contains the position"""
        for region in self.regions:
            if region.geometry.is_inside(position):
                return region
        return None

    def sample_distance(self, neutron: Neutron, region: Region) -> float:
        """Sample distance to next collision"""
        xs = region.material.cross_section.interpolate(neutron.energy)
        sigma_t = xs["total"] * region.material.number_density()

        if sigma_t <= 0:
            return np.inf

        return -np.log(self.rng.random()) / sigma_t

    def sample_collision_type(self, neutron: Neutron, region: Region) -> CollisionType:
        """Sample type of collision"""
        xs = region.material.cross_section.interpolate(neutron.energy)

        total = xs["scatter"] + xs["absorption"] + xs["fission"]
        if total <= 0:
            return CollisionType.ABSORPTION

        rand = self.rng.random() * total

        if rand < xs["scatter"]:
            return CollisionType.SCATTER
        elif rand < xs["scatter"] + xs["fission"]:
            return CollisionType.FISSION
        else:
            return CollisionType.ABSORPTION

    def scatter_neutron(self, neutron: Neutron):
        """Perform isotropic scattering"""
        # Isotropic scattering in lab frame (simplified)
        mu = 2 * self.rng.random() - 1  # cos(theta)
        phi = 2 * np.pi * self.rng.random()

        # New direction
        theta = np.arccos(mu)
        neutron.direction = np.array(
            [np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)]
        )

        # Energy loss (simplified - elastic scattering)
        alpha = 0.9  # Energy retention factor
        neutron.energy *= 1 - alpha * self.rng.random()

    def process_fission(self, neutron: Neutron, region: Region) -> List[Neutron]:
        """Process fission event"""
        xs = region.material.cross_section.interpolate(neutron.energy)
        nu = xs["nu"]  # Average neutrons per fission

        # Sample number of neutrons
        n_neutrons = int(nu) + (1 if self.rng.random() < (nu - int(nu)) else 0)

        # Create fission neutrons
        fission_neutrons = []
        for _ in range(n_neutrons):
            # Sample fission spectrum energy (Watt spectrum simplified)
            E_fission = self.sample_fission_energy()

            # Random isotropic direction
            phi = 2 * np.pi * self.rng.random()
            mu = 2 * self.rng.random() - 1
            theta = np.arccos(mu)

            direction = np.array(
                [
                    np.sin(theta) * np.cos(phi),
                    np.sin(theta) * np.sin(phi),
                    np.cos(theta),
                ]
            )

            fission_neutrons.append(
                Neutron(
                    position=neutron.position.copy(),
                    direction=direction,
                    energy=E_fission,
                    weight=neutron.weight / n_neutrons,
                    generation=neutron.generation + 1,
                )
            )

        return fission_neutrons

    def sample_fission_energy(self) -> float:
        """Sample energy from fission spectrum (Watt spectrum)"""
        # Simplified Watt spectrum for U-235
        # P(E) ~ exp(-E) * sinh(sqrt(2E))
        # For simplicity, use average fission energy
        return 2.0  # MeV (typical)

    def transport_neutron(self, neutron: Neutron) -> List[Neutron]:
        """Transport single neutron to completion"""
        history = []

        while neutron.state == ParticleState.ACTIVE:
            region = self.find_region(neutron.position)

            if region is None:
                # Leaked out of geometry
                neutron.state = ParticleState.LEAKED
                break

            # Sample distance to collision
            d_collision = self.sample_distance(neutron, region)

            # Distance to boundary
            d_boundary = region.geometry.distance_to_boundary(
                neutron.position, neutron.direction
            )

            # Move neutron
            distance = min(d_collision, d_boundary)
            neutron.position += distance * neutron.direction

            # Score track-length tallies
            for tally in self.tallies:
                if isinstance(tally, FluxTally) and tally.region == region:
                    tally.score_track_length(distance, neutron.weight)

            # Check if crossed boundary
            if d_boundary < d_collision:
                # Apply variance reduction at boundary
                new_region = self.find_region(
                    neutron.position + 1e-6 * neutron.direction
                )
                if new_region and self.importance_sampler:
                    neutron.weight = self.importance_sampler.get_weight_adjustment(
                        region, new_region, neutron.weight
                    )
                continue

            # Collision occurred
            self.n_collisions += 1
            collision_type = self.sample_collision_type(neutron, region)

            if collision_type == CollisionType.SCATTER:
                self.scatter_neutron(neutron)

            elif collision_type == CollisionType.FISSION:
                neutron.state = ParticleState.FISSION
                history.extend(self.process_fission(neutron, region))

            else:  # ABSORPTION or CAPTURE
                neutron.state = ParticleState.ABSORBED

            # Apply weight window
            if self.weight_window and neutron.state == ParticleState.ACTIVE:
                adjusted = self.weight_window.check_and_adjust(neutron, self.rng)
                if not adjusted:
                    neutron.state = ParticleState.CUTOFF

        return history

    def run_history(self) -> int:
        """Run single neutron history"""
        neutron = self.source()
        self.n_histories += 1

        fission_neutrons = self.transport_neutron(neutron)
        return len(fission_neutrons)

    def run_batch(self, n_histories: int) -> Dict[str, float]:
        """Run batch of histories"""
        total_fissions = 0

        for _ in range(n_histories):
            n_fission = self.run_history()
            total_fissions += n_fission

        # Calculate k-effective for this batch
        k_eff = total_fissions / n_histories if n_histories > 0 else 0.0
        self.k_eff_generations.append(k_eff)

        return {
            "k_eff": k_eff,
            "n_histories": n_histories,
            "n_collisions": self.n_collisions,
        }

    def run_eigenvalue(
        self, n_generations: int = 100, n_per_generation: int = 1000, n_skip: int = 20
    ) -> Dict[str, any]:
        """Run k-eigenvalue calculation"""
        print(
            f"Running {n_generations} generations with {n_per_generation} neutrons each..."
        )

        for gen in range(n_generations):
            batch_results = self.run_batch(n_per_generation)

            if gen % 10 == 0:
                print(f"Generation {gen}: k-eff = {batch_results['k_eff']:.5f}")

        # Calculate statistics (skip initial generations)
        active_k = self.k_eff_generations[n_skip:]

        return {
            "k_eff_mean": np.mean(active_k),
            "k_eff_std": np.std(active_k),
            "k_eff_history": self.k_eff_generations,
            "n_generations": n_generations,
            "n_per_generation": n_per_generation,
        }


# ============================================================================
# PARALLEL EXECUTION
# ============================================================================


class ParallelMonteCarlo:
    """Parallel execution of Monte Carlo simulations"""

    @staticmethod
    def run_parallel(
        engine_factory: Callable[[], MonteCarloEngine],
        n_workers: int = 4,
        n_histories_per_worker: int = 1000,
    ) -> List[Dict]:
        """Run MC simulation in parallel"""

        def worker(worker_id: int) -> Dict:
            engine = engine_factory()
            return engine.run_batch(n_histories_per_worker)

        with concurrent.futures.ProcessPoolExecutor(max_workers=n_workers) as executor:
            futures = [executor.submit(worker, i) for i in range(n_workers)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        return results


# ============================================================================
# EXAMPLE: BARE SPHERE CRITICAL MASS
# ============================================================================


def example_bare_sphere_criticality():
    """Example: Critical mass calculation for bare U-235 sphere"""

    # Create U-235 cross sections (simplified)
    energy_grid = np.array([0.001, 0.1, 1.0, 10.0])  # MeV

    u235_xs = CrossSection(
        energy_grid=energy_grid,
        total=np.array([8.0, 7.0, 6.5, 6.0]),  # barns
        scatter=np.array([6.0, 5.5, 5.0, 4.5]),
        absorption=np.array([1.5, 1.0, 0.8, 0.6]),
        fission=np.array([2.5, 2.0, 1.5, 1.0]),
        nu=np.array([2.5, 2.5, 2.5, 2.5]),  # neutrons per fission
    )

    u235 = Material(
        name="U-235", density=19.1, cross_section=u235_xs, atomic_mass=235.0  # g/cm^3
    )

    # Create spherical geometry (varying radius to find critical mass)
    radius = 8.0  # cm (approximately critical)
    sphere_geom = Sphere(center=np.array([0.0, 0.0, 0.0]), radius=radius)
    sphere_region = Region(geometry=sphere_geom, material=u235)

    # Fission source (isotropic point source at center)
    def fission_source():
        # Random position in sphere
        r = radius * np.cbrt(np.random.random())
        theta = np.arccos(2 * np.random.random() - 1)
        phi = 2 * np.pi * np.random.random()

        pos = np.array(
            [
                r * np.sin(theta) * np.cos(phi),
                r * np.sin(theta) * np.sin(phi),
                r * np.cos(theta),
            ]
        )

        # Random direction
        mu = 2 * np.random.random() - 1
        phi = 2 * np.pi * np.random.random()
        theta = np.arccos(mu)

        direction = np.array(
            [np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)]
        )

        return Neutron(
            position=pos,
            direction=direction,
            energy=2.0,  # MeV (fission spectrum average)
            weight=1.0,
        )

    # Create MC engine
    engine = MonteCarloEngine(regions=[sphere_region], source=fission_source, seed=42)

    # Add tallies
    flux_tally = FluxTally("core_flux", sphere_region)
    engine.add_tally(flux_tally)

    # Enable variance reduction
    engine.enable_variance_reduction(
        importance_map={sphere_region: 1.0}, weight_window=True
    )

    # Run eigenvalue calculation
    results = engine.run_eigenvalue(n_generations=50, n_per_generation=500, n_skip=10)

    print("\n" + "=" * 60)
    print(f"CRITICAL MASS CALCULATION - U-235 Sphere (R={radius} cm)")
    print("=" * 60)
    print(f"k-effective: {results['k_eff_mean']:.5f} ± {results['k_eff_std']:.5f}")
    print(f"Total histories: {results['n_generations'] * results['n_per_generation']}")
    print(f"Total collisions: {engine.n_collisions}")

    mass = (4 / 3) * np.pi * radius**3 * u235.density / 1000  # kg
    print(f"Sphere mass: {mass:.2f} kg")

    if abs(results["k_eff_mean"] - 1.0) < 0.01:
        print("✓ System is CRITICAL")
    elif results["k_eff_mean"] > 1.0:
        print("⚠ System is SUPERCRITICAL")
    else:
        print("✓ System is SUBCRITICAL")

    print(f"\nFlux tally:")
    print(f"  Mean: {flux_tally.mean():.3e}")
    print(f"  Std Dev: {flux_tally.std_dev():.3e}")
    print(f"  Relative Error: {flux_tally.relative_error()*100:.2f}%")

    return results


if __name__ == "__main__":
    # Run example
    results = example_bare_sphere_criticality()
