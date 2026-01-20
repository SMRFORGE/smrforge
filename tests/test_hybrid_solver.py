"""
Tests for smrforge.neutronics.hybrid_solver module.
"""

import numpy as np
import pytest
from unittest.mock import Mock, MagicMock, patch

from smrforge.neutronics.hybrid_solver import (
    HybridSolver,
    RegionPartition,
    create_hybrid_solver,
)


@pytest.fixture
def mock_diffusion_solver():
    """Create a mock diffusion solver."""
    solver = Mock()
    solver.geometry = Mock()
    solver.geometry.n_axial = 5
    solver.geometry.n_radial = 10
    solver.geometry.core_diameter = 100.0
    solver.geometry.r_core = 50.0
    solver.geometry.r_reflector = 75.0
    solver.solve_steady_state = Mock(return_value=(1.05, np.ones((5, 10, 4))))
    return solver


@pytest.fixture
def mock_mc_solver():
    """Create a mock Monte Carlo solver."""
    solver = Mock()
    solver.run_eigenvalue = Mock(return_value={
        "k_eff": 1.052,
        "k_std": 0.001,
    })
    return solver


class TestRegionPartition:
    """Tests for RegionPartition dataclass."""
    
    def test_region_partition_init(self):
        """Test RegionPartition initialization."""
        nz, nr = 5, 10
        diffusion_mask = np.ones((nz, nr), dtype=bool)
        region_ids = np.zeros((nz, nr), dtype=np.int32)
        
        partition = RegionPartition(
            diffusion_mask=diffusion_mask,
            region_ids=region_ids,
            n_diffusion_regions=1,
            n_mc_regions=0,
        )
        
        assert partition.n_diffusion_regions == 1
        assert partition.n_mc_regions == 0
        assert partition.diffusion_mask.shape == (nz, nr)
        assert partition.region_ids.shape == (nz, nr)
    
    def test_region_partition_validation(self):
        """Test RegionPartition validation fails for empty partition."""
        nz, nr = 5, 10
        diffusion_mask = np.zeros((nz, nr), dtype=bool)
        region_ids = np.ones((nz, nr), dtype=np.int32)
        
        with pytest.raises(ValueError, match="must have at least one region"):
            RegionPartition(
                diffusion_mask=diffusion_mask,
                region_ids=region_ids,
                n_diffusion_regions=0,
                n_mc_regions=0,
            )


class TestHybridSolver:
    """Tests for HybridSolver class."""
    
    def test_hybrid_solver_init(self, mock_diffusion_solver, mock_mc_solver):
        """Test HybridSolver initialization."""
        solver = HybridSolver(
            diffusion_solver=mock_diffusion_solver,
            mc_solver=mock_mc_solver,
            use_adaptive_partitioning=True,
            mc_threshold=0.05,
        )
        
        assert solver.diffusion_solver == mock_diffusion_solver
        assert solver.mc_solver == mock_mc_solver
        assert solver.use_adaptive_partitioning is True
        assert solver.mc_threshold == 0.05
        assert solver.partition is None
        assert solver.k_eff_diffusion is None
        assert solver.k_eff_mc_correction is None
        assert solver.k_eff_hybrid is None
    
    def test_identify_complex_regions(self, mock_diffusion_solver, mock_mc_solver):
        """Test _identify_complex_regions method."""
        solver = HybridSolver(
            diffusion_solver=mock_diffusion_solver,
            mc_solver=mock_mc_solver,
        )
        
        partition = solver._identify_complex_regions()
        
        assert isinstance(partition, RegionPartition)
        assert partition.diffusion_mask.shape == (5, 10)
        assert partition.region_ids.shape == (5, 10)
        assert partition.n_diffusion_regions >= 0
        assert partition.n_mc_regions >= 0
        assert partition.n_diffusion_regions + partition.n_mc_regions > 0
    
    def test_get_material_map(self, mock_diffusion_solver, mock_mc_solver):
        """Test _get_material_map method."""
        solver = HybridSolver(
            diffusion_solver=mock_diffusion_solver,
            mc_solver=mock_mc_solver,
        )
        
        material_map = solver._get_material_map()
        
        assert material_map.shape == (5, 10)
        assert material_map.dtype == np.int32
    
    def test_has_material_discontinuity(self, mock_diffusion_solver, mock_mc_solver):
        """Test _has_material_discontinuity method."""
        solver = HybridSolver(
            diffusion_solver=mock_diffusion_solver,
            mc_solver=mock_mc_solver,
        )
        
        # Create material map with discontinuity
        material_map = np.zeros((5, 10), dtype=np.int32)
        material_map[:, 5:] = 1  # Split down the middle
        
        # Check at boundary
        has_discontinuity = solver._has_material_discontinuity(material_map, 2, 5)
        assert has_discontinuity is True
        
        # Check in uniform region
        has_discontinuity = solver._has_material_discontinuity(material_map, 2, 2)
        assert has_discontinuity is False
    
    def test_identify_complex_regions_from_flux(self, mock_diffusion_solver, mock_mc_solver):
        """Test _identify_complex_regions_from_flux method."""
        solver = HybridSolver(
            diffusion_solver=mock_diffusion_solver,
            mc_solver=mock_mc_solver,
        )
        
        # Create flux with high gradient
        flux = np.ones((5, 10, 4))
        flux[:, :, 0] = np.linspace(0.5, 1.5, 50).reshape(5, 10)  # High gradient
        
        partition = solver._identify_complex_regions_from_flux(flux)
        
        assert isinstance(partition, RegionPartition)
        assert partition.diffusion_mask.shape == (5, 10)
    
    def test_compute_flux_gradient_magnitude(self, mock_diffusion_solver, mock_mc_solver):
        """Test _compute_flux_gradient_magnitude method."""
        solver = HybridSolver(
            diffusion_solver=mock_diffusion_solver,
            mc_solver=mock_mc_solver,
        )
        
        # Create flux with known gradient
        flux = np.ones((5, 10))
        flux[:, :] = np.linspace(1.0, 2.0, 50).reshape(5, 10)
        
        gradient = solver._compute_flux_gradient_magnitude(flux)
        
        assert gradient.shape == (5, 10)
        assert np.all(gradient >= 0)  # Gradient magnitude is non-negative
    
    def test_solve_eigenvalue_adaptive(self, mock_diffusion_solver, mock_mc_solver):
        """Test solve_eigenvalue with adaptive partitioning."""
        solver = HybridSolver(
            diffusion_solver=mock_diffusion_solver,
            mc_solver=mock_mc_solver,
            use_adaptive_partitioning=True,
        )
        
        results = solver.solve_eigenvalue()
        
        assert "k_eff" in results
        assert "k_std" in results
        assert "k_eff_diffusion" in results
        assert "k_eff_mc_correction" in results
        assert "partition" in results
        assert isinstance(results["k_eff"], (float, np.floating))
        assert solver.k_eff_diffusion is not None
        assert solver.partition is not None
    
    def test_solve_eigenvalue_non_adaptive(self, mock_diffusion_solver, mock_mc_solver):
        """Test solve_eigenvalue without adaptive partitioning."""
        solver = HybridSolver(
            diffusion_solver=mock_diffusion_solver,
            mc_solver=mock_mc_solver,
            use_adaptive_partitioning=False,
        )
        
        results = solver.solve_eigenvalue()
        
        assert "k_eff" in results
        assert results["k_eff"] == results["k_eff_diffusion"]
        assert solver.partition is not None
        assert solver.partition.n_mc_regions == 0  # No MC regions if not adaptive
    
    def test_solve_mc_regions(self, mock_diffusion_solver, mock_mc_solver):
        """Test _solve_mc_regions method."""
        solver = HybridSolver(
            diffusion_solver=mock_diffusion_solver,
            mc_solver=mock_mc_solver,
        )
        solver.k_eff_diffusion = 1.05
        
        mc_results = solver._solve_mc_regions()
        
        assert "k_eff_correction" in mc_results
        assert "k_eff_mc" in mc_results
        assert "k_std" in mc_results
        assert isinstance(mc_results["k_eff_correction"], (float, np.floating))
    
    def test_solve_eigenvalue_with_mc_correction(self, mock_diffusion_solver, mock_mc_solver):
        """Test solve_eigenvalue when MC regions are identified."""
        # Create partition with MC regions
        nz, nr = 5, 10
        diffusion_mask = np.ones((nz, nr), dtype=bool)
        diffusion_mask[0:2, :] = False  # Mark some regions as MC
        region_ids = np.where(diffusion_mask, 0, 1).astype(np.int32)
        
        partition = RegionPartition(
            diffusion_mask=diffusion_mask,
            region_ids=region_ids,
            n_diffusion_regions=np.sum(diffusion_mask),
            n_mc_regions=np.sum(~diffusion_mask),
        )
        
        solver = HybridSolver(
            diffusion_solver=mock_diffusion_solver,
            mc_solver=mock_mc_solver,
            use_adaptive_partitioning=True,
        )
        
        # Mock the identify method to return our partition
        solver._identify_complex_regions_from_flux = Mock(return_value=partition)
        
        results = solver.solve_eigenvalue()
        
        assert "k_eff" in results
        assert results["k_eff"] != results["k_eff_diffusion"]  # Should have correction
        assert solver.k_eff_mc_correction is not None


class TestCreateHybridSolver:
    """Tests for create_hybrid_solver convenience function."""
    
    def test_create_hybrid_solver(self, mock_diffusion_solver, mock_mc_solver):
        """Test create_hybrid_solver function."""
        solver = create_hybrid_solver(
            diffusion_solver=mock_diffusion_solver,
            mc_solver=mock_mc_solver,
            use_adaptive=True,
        )
        
        assert isinstance(solver, HybridSolver)
        assert solver.use_adaptive_partitioning is True
    
    def test_create_hybrid_solver_non_adaptive(self, mock_diffusion_solver, mock_mc_solver):
        """Test create_hybrid_solver with use_adaptive=False."""
        solver = create_hybrid_solver(
            diffusion_solver=mock_diffusion_solver,
            mc_solver=mock_mc_solver,
            use_adaptive=False,
        )
        
        assert isinstance(solver, HybridSolver)
        assert solver.use_adaptive_partitioning is False
