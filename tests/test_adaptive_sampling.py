"""
Tests for smrforge.neutronics.adaptive_sampling module.
"""

import numpy as np
import pytest
from unittest.mock import Mock, MagicMock, patch

from smrforge.neutronics.adaptive_sampling import (
    AdaptiveMonteCarloSolver,
    ImportanceMap,
    create_adaptive_solver,
)


@pytest.fixture
def mock_mc_solver():
    """Create a mock Monte Carlo solver."""
    solver = Mock()
    solver.geometry = Mock()
    solver.geometry.h_core = 200.0
    solver.geometry.r_reflector = 100.0
    
    # Mock particle banks
    solver.fission_bank = Mock()
    solver.fission_bank.size = 100
    solver.fission_bank.position = np.random.rand(100, 3) * 100
    solver.source_bank = Mock()
    solver.source_bank.size = 50
    solver.source_bank.clear = Mock()
    solver.source_bank.add_particle = Mock()
    
    solver.n_particles = 1000
    
    # Mock methods
    solver._track_generation = Mock()
    solver._initialize_source = Mock()
    solver._resample_source = Mock()
    
    return solver


class TestImportanceMap:
    """Tests for ImportanceMap dataclass."""
    
    def test_importance_map_init(self):
        """Test ImportanceMap initialization."""
        z_centers = np.linspace(0, 200, 10)
        r_centers = np.linspace(0, 100, 5)
        importance = np.ones((10, 5))
        
        imp_map = ImportanceMap(
            z_centers=z_centers,
            r_centers=r_centers,
            importance=importance
        )
        
        assert imp_map.z_centers.shape == (10,)
        assert imp_map.r_centers.shape == (5,)
        assert imp_map.importance.shape == (10, 5)
        # Should be normalized (max = 1.0)
        assert np.max(imp_map.importance) <= 1.0
    
    def test_importance_map_normalization(self):
        """Test that importance map is normalized."""
        z_centers = np.linspace(0, 200, 5)
        r_centers = np.linspace(0, 100, 5)
        importance = np.ones((5, 5)) * 10.0  # Non-normalized
        
        imp_map = ImportanceMap(
            z_centers=z_centers,
            r_centers=r_centers,
            importance=importance
        )
        
        # Should be normalized to max = 1.0
        assert np.max(imp_map.importance) == 1.0
    
    def test_get_sampling_probability(self):
        """Test get_sampling_probability method."""
        z_centers = np.linspace(0, 200, 10)
        r_centers = np.linspace(0, 100, 5)
        importance = np.ones((10, 5))
        importance[5, 2] = 2.0  # Higher importance at center
        
        imp_map = ImportanceMap(
            z_centers=z_centers,
            r_centers=r_centers,
            importance=importance
        )
        
        # Test sampling probability
        prob = imp_map.get_sampling_probability(100.0, 50.0)
        assert 0.0 <= prob <= 1.0
    
    def test_get_total_importance(self):
        """Test get_total_importance method."""
        z_centers = np.linspace(0, 200, 5)
        r_centers = np.linspace(0, 100, 5)
        importance = np.ones((5, 5))
        
        imp_map = ImportanceMap(
            z_centers=z_centers,
            r_centers=r_centers,
            importance=importance
        )
        
        total = imp_map.get_total_importance()
        assert total > 0
        assert isinstance(total, (float, np.floating))


class TestAdaptiveMonteCarloSolver:
    """Tests for AdaptiveMonteCarloSolver class."""
    
    def test_adaptive_solver_init(self, mock_mc_solver):
        """Test AdaptiveMonteCarloSolver initialization."""
        solver = AdaptiveMonteCarloSolver(
            mc_solver=mock_mc_solver,
            n_exploration_generations=20,
            n_refinement_generations=80,
            importance_update_frequency=10,
        )
        
        assert solver.mc_solver == mock_mc_solver
        assert solver.n_exploration == 20
        assert solver.n_refinement == 80
        assert solver.importance_update_freq == 10
        assert solver.importance_map is None
        assert len(solver.fission_density_history) == 0
    
    def test_build_importance_map_no_history(self, mock_mc_solver):
        """Test _build_importance_map with no history."""
        solver = AdaptiveMonteCarloSolver(mock_mc_solver)
        
        imp_map = solver._build_importance_map()
        
        assert isinstance(imp_map, ImportanceMap)
        assert np.all(imp_map.importance > 0)  # Should be uniform
    
    def test_build_importance_map_with_history(self, mock_mc_solver):
        """Test _build_importance_map with history."""
        solver = AdaptiveMonteCarloSolver(mock_mc_solver)
        
        # Add some history
        fission_density = np.ones((20, 20))
        fission_density[10, 10] = 5.0  # Higher density at center
        solver.fission_density_history.append(fission_density)
        
        imp_map = solver._build_importance_map()
        
        assert isinstance(imp_map, ImportanceMap)
        assert np.max(imp_map.importance) == 1.0  # Should be normalized
    
    def test_adapt_particle_distribution(self, mock_mc_solver):
        """Test _adapt_particle_distribution method."""
        solver = AdaptiveMonteCarloSolver(mock_mc_solver)
        
        z_centers = np.linspace(0, 200, 10)
        r_centers = np.linspace(0, 100, 5)
        importance = np.ones((10, 5))
        imp_map = ImportanceMap(z_centers=z_centers, r_centers=r_centers, importance=importance)
        
        # Should not raise error
        solver._adapt_particle_distribution(imp_map)
    
    def test_estimate_fission_density(self, mock_mc_solver):
        """Test _estimate_fission_density method."""
        solver = AdaptiveMonteCarloSolver(mock_mc_solver)
        
        # Create mock fission bank with positions
        positions = np.random.rand(100, 3)
        positions[:, 0] *= 100  # x
        positions[:, 1] *= 100  # y
        positions[:, 2] *= 200  # z
        mock_mc_solver.fission_bank.position = positions
        mock_mc_solver.fission_bank.size = 100
        
        fission_density = solver._estimate_fission_density(mock_mc_solver.fission_bank)
        
        assert fission_density.shape == (20, 20)
        assert np.all(fission_density >= 0)
    
    def test_estimate_fission_density_empty(self, mock_mc_solver):
        """Test _estimate_fission_density with empty bank."""
        solver = AdaptiveMonteCarloSolver(mock_mc_solver)
        mock_mc_solver.fission_bank.size = 0
        
        fission_density = solver._estimate_fission_density(mock_mc_solver.fission_bank)
        
        assert fission_density.shape == (20, 20)
        assert np.all(fission_density == 0)
    
    def test_combine_results(self, mock_mc_solver):
        """Test _combine_results method."""
        solver = AdaptiveMonteCarloSolver(mock_mc_solver, n_exploration_generations=2, n_refinement_generations=3)
        
        # Add some k_eff history
        solver.k_eff_history = [1.0, 1.01, 1.02, 1.03, 1.04]
        
        results = solver._combine_results()
        
        assert "k_eff" in results
        assert "k_std" in results
        assert "k_history" in results
        assert isinstance(results["k_eff"], (float, np.floating))
        assert isinstance(results["k_std"], (float, np.floating))
        assert len(results["k_history"]) == 5
    
    def test_combine_results_no_history(self, mock_mc_solver):
        """Test _combine_results with no history."""
        solver = AdaptiveMonteCarloSolver(mock_mc_solver)
        
        with pytest.raises(RuntimeError, match="No k_eff history"):
            solver._combine_results()
    
    def test_resample_source_no_importance_map(self, mock_mc_solver):
        """Test _resample_source without importance map."""
        solver = AdaptiveMonteCarloSolver(mock_mc_solver)
        mock_mc_solver.fission_bank.size = 100
        
        solver._resample_source()
        
        # Should call base solver's resample method
        mock_mc_solver._resample_source.assert_called_once()
    
    def test_resample_source_empty_fission_bank(self, mock_mc_solver):
        """Test _resample_source with empty fission bank."""
        solver = AdaptiveMonteCarloSolver(mock_mc_solver)
        mock_mc_solver.fission_bank.size = 0
        
        solver._resample_source()
        
        # Should initialize source
        mock_mc_solver._initialize_source.assert_called_once()
    
    @patch('smrforge.neutronics.monte_carlo_optimized.sample_isotropic_direction')
    @patch('smrforge.neutronics.monte_carlo_optimized.sample_fission_spectrum')
    def test_resample_source_importance(self, mock_fission_spectrum, mock_isotropic, mock_mc_solver):
        """Test _resample_source_importance method."""
        solver = AdaptiveMonteCarloSolver(mock_mc_solver)
        
        # Create importance map
        z_centers = np.linspace(0, 200, 10)
        r_centers = np.linspace(0, 100, 5)
        importance = np.ones((10, 5))
        solver.importance_map = ImportanceMap(z_centers=z_centers, r_centers=r_centers, importance=importance)
        
        # Create mock fission bank
        positions = np.random.rand(50, 3) * 100
        mock_mc_solver.fission_bank.position = positions
        mock_mc_solver.fission_bank.size = 50
        
        # Mock sample functions
        mock_isotropic.return_value = np.array([0.0, 0.0, 1.0])
        mock_fission_spectrum.return_value = 1e6
        
        solver._resample_source_importance()
        
        # Should have called add_particle
        assert mock_mc_solver.source_bank.add_particle.called


class TestCreateAdaptiveSolver:
    """Tests for create_adaptive_solver convenience function."""
    
    def test_create_adaptive_solver(self, mock_mc_solver):
        """Test create_adaptive_solver function."""
        solver = create_adaptive_solver(
            mc_solver=mock_mc_solver,
            n_exploration=20,
            n_refinement=80,
        )
        
        assert isinstance(solver, AdaptiveMonteCarloSolver)
        assert solver.n_exploration == 20
        assert solver.n_refinement == 80


class TestAdaptiveMonteCarloSolverExtended:
    """Extended tests for AdaptiveMonteCarloSolver class."""
    
    def test_build_importance_map_zero_max(self, mock_mc_solver):
        """Test _build_importance_map with zero max importance."""
        solver = AdaptiveMonteCarloSolver(mock_mc_solver)
        
        # Add history with all zeros
        fission_density = np.zeros((20, 20))
        solver.fission_density_history.append(fission_density)
        
        imp_map = solver._build_importance_map()
        
        assert isinstance(imp_map, ImportanceMap)
        # Should fallback to uniform
        assert np.all(imp_map.importance > 0)
    
    def test_exploration_phase(self, mock_mc_solver):
        """Test _exploration_phase method."""
        solver = AdaptiveMonteCarloSolver(
            mock_mc_solver,
            n_exploration_generations=5,
            importance_update_frequency=2,
        )
        
        # Mock fission bank
        mock_mc_solver.fission_bank.size = 50
        mock_mc_solver.fission_bank.position = np.random.rand(50, 3) * 100
        mock_mc_solver.source_bank.size = 100
        
        solver._exploration_phase()
        
        # Should have tracked generations
        assert mock_mc_solver._track_generation.called
        # Should have some k_eff history
        assert len(solver.k_eff_history) == 5
    
    def test_exploration_phase_empty_fission_bank(self, mock_mc_solver):
        """Test _exploration_phase with empty fission bank."""
        solver = AdaptiveMonteCarloSolver(
            mock_mc_solver,
            n_exploration_generations=3,
        )
        
        # Empty fission bank
        mock_mc_solver.fission_bank.size = 0
        mock_mc_solver.source_bank.size = 100
        
        solver._exploration_phase()
        
        # Should still complete
        assert len(solver.k_eff_history) == 3
    
    def test_refinement_phase(self, mock_mc_solver):
        """Test _refinement_phase method."""
        solver = AdaptiveMonteCarloSolver(
            mock_mc_solver,
            n_refinement_generations=5,
            importance_update_frequency=2,
        )
        
        # Create importance map
        z_centers = np.linspace(0, 200, 10)
        r_centers = np.linspace(0, 100, 5)
        importance = np.ones((10, 5))
        solver.importance_map = ImportanceMap(z_centers=z_centers, r_centers=r_centers, importance=importance)
        
        # Mock fission bank
        mock_mc_solver.fission_bank.size = 50
        mock_mc_solver.fission_bank.position = np.random.rand(50, 3) * 100
        mock_mc_solver.source_bank.size = 100
        
        solver._refinement_phase()
        
        # Should have tracked generations
        assert mock_mc_solver._track_generation.called
        # Should have k_eff history
        assert len(solver.k_eff_history) == 5
    
    def test_refinement_phase_no_importance_map(self, mock_mc_solver):
        """Test _refinement_phase builds importance map if None."""
        solver = AdaptiveMonteCarloSolver(
            mock_mc_solver,
            n_refinement_generations=3,
        )
        
        # No importance map initially
        assert solver.importance_map is None
        
        # Mock fission bank
        mock_mc_solver.fission_bank.size = 50
        mock_mc_solver.fission_bank.position = np.random.rand(50, 3) * 100
        mock_mc_solver.source_bank.size = 100
        
        solver._refinement_phase()
        
        # Should have built importance map
        assert solver.importance_map is not None
    
    def test_resample_source_importance_with_importance_map(self, mock_mc_solver):
        """Test _resample_source_importance with importance map."""
        solver = AdaptiveMonteCarloSolver(mock_mc_solver)
        
        # Create importance map
        z_centers = np.linspace(0, 200, 10)
        r_centers = np.linspace(0, 100, 5)
        importance = np.ones((10, 5))
        importance[5, 2] = 2.0  # Higher importance
        solver.importance_map = ImportanceMap(z_centers=z_centers, r_centers=r_centers, importance=importance)
        
        # Create mock fission bank with positions
        positions = np.random.rand(50, 3) * 100
        positions[:, 2] = 100.0  # z positions
        positions[:, 0] = 50.0  # x positions
        positions[:, 1] = 0.0  # y positions
        mock_mc_solver.fission_bank.position = positions
        mock_mc_solver.fission_bank.size = 50
        
        solver._resample_source_importance()
        
        # Should have called add_particle
        assert mock_mc_solver.source_bank.clear.called
        assert mock_mc_solver.source_bank.add_particle.called
    
    def test_resample_source_importance_all_zero_importance(self, mock_mc_solver):
        """Test _resample_source_importance with all zero importance."""
        solver = AdaptiveMonteCarloSolver(mock_mc_solver)
        
        # Create importance map with all zeros
        z_centers = np.linspace(0, 200, 10)
        r_centers = np.linspace(0, 100, 5)
        importance = np.zeros((10, 5))
        solver.importance_map = ImportanceMap(z_centers=z_centers, r_centers=r_centers, importance=importance)
        
        # Create mock fission bank
        positions = np.random.rand(50, 3) * 100
        mock_mc_solver.fission_bank.position = positions
        mock_mc_solver.fission_bank.size = 50
        
        solver._resample_source_importance()
        
        # Should still work (falls back to uniform)
        assert mock_mc_solver.source_bank.add_particle.called
    
    def test_solve_eigenvalue(self, mock_mc_solver):
        """Test solve_eigenvalue method."""
        solver = AdaptiveMonteCarloSolver(
            mock_mc_solver,
            n_exploration_generations=2,
            n_refinement_generations=3,
        )
        
        # Mock methods
        mock_mc_solver.fission_bank.size = 50
        mock_mc_solver.fission_bank.position = np.random.rand(50, 3) * 100
        mock_mc_solver.source_bank.size = 100
        
        results = solver.solve_eigenvalue()
        
        assert isinstance(results, dict)
        assert "k_eff" in results
        assert "k_std" in results
        assert "k_history" in results
        assert "n_exploration" in results
        assert "n_refinement" in results
        assert "importance_map" in results
    
    def test_combine_results_fallback_to_all_history(self, mock_mc_solver):
        """Test _combine_results falls back to all history if no refinement."""
        solver = AdaptiveMonteCarloSolver(
            mock_mc_solver,
            n_exploration_generations=5,
            n_refinement_generations=0,  # No refinement
        )
        
        # Add k_eff history
        solver.k_eff_history = [1.0, 1.01, 1.02, 1.03, 1.04]
        
        results = solver._combine_results()
        
        # Should use all history as fallback
        assert "k_eff" in results
        assert len(results["k_history"]) == 5
    
    def test_importance_map_get_sampling_probability_edge_cases(self):
        """Test get_sampling_probability with edge cases."""
        z_centers = np.linspace(0, 200, 10)
        r_centers = np.linspace(0, 100, 5)
        importance = np.ones((10, 5))
        importance[0, 0] = 0.5  # Lower importance
        importance[-1, -1] = 1.0  # Higher importance
        
        imp_map = ImportanceMap(
            z_centers=z_centers,
            r_centers=r_centers,
            importance=importance
        )
        
        # Test at boundaries
        prob_min = imp_map.get_sampling_probability(0.0, 0.0)
        prob_max = imp_map.get_sampling_probability(200.0, 100.0)
        
        assert 0.0 <= prob_min <= 1.0
        assert 0.0 <= prob_max <= 1.0
    
    def test_importance_map_get_sampling_probability_out_of_bounds(self):
        """Test get_sampling_probability with out-of-bounds positions."""
        z_centers = np.linspace(0, 200, 10)
        r_centers = np.linspace(0, 100, 5)
        importance = np.ones((10, 5))
        
        imp_map = ImportanceMap(
            z_centers=z_centers,
            r_centers=r_centers,
            importance=importance
        )
        
        # Test with positions outside bounds (should find closest)
        prob = imp_map.get_sampling_probability(-10.0, -5.0)
        assert 0.0 <= prob <= 1.0
        
        prob2 = imp_map.get_sampling_probability(300.0, 200.0)
        assert 0.0 <= prob2 <= 1.0
    
    def test_estimate_fission_density_with_positions(self, mock_mc_solver):
        """Test _estimate_fission_density with various positions."""
        solver = AdaptiveMonteCarloSolver(mock_mc_solver)
        
        # Create positions at different locations
        positions = np.array([
            [10.0, 0.0, 50.0],   # r=10, z=50
            [20.0, 0.0, 100.0],  # r=20, z=100
            [30.0, 0.0, 150.0],  # r=30, z=150
        ])
        mock_mc_solver.fission_bank.position = positions
        mock_mc_solver.fission_bank.size = 3
        
        fission_density = solver._estimate_fission_density(mock_mc_solver.fission_bank)
        
        assert fission_density.shape == (20, 20)
        assert np.all(fission_density >= 0)
        # Should have some non-zero values
        assert np.sum(fission_density) > 0
    
    def test_estimate_fission_density_boundary_positions(self, mock_mc_solver):
        """Test _estimate_fission_density with boundary positions."""
        solver = AdaptiveMonteCarloSolver(mock_mc_solver)
        
        # Positions at boundaries
        positions = np.array([
            [0.0, 0.0, 0.0],      # r=0, z=0
            [100.0, 0.0, 200.0],  # r=100, z=200 (at boundary)
        ])
        mock_mc_solver.fission_bank.position = positions
        mock_mc_solver.fission_bank.size = 2
        
        fission_density = solver._estimate_fission_density(mock_mc_solver.fission_bank)
        
        assert fission_density.shape == (20, 20)
        assert np.all(fission_density >= 0)
    
    def test_resample_source_with_importance_map(self, mock_mc_solver):
        """Test _resample_source with importance map."""
        solver = AdaptiveMonteCarloSolver(mock_mc_solver)
        
        # Create importance map
        z_centers = np.linspace(0, 200, 10)
        r_centers = np.linspace(0, 100, 5)
        importance = np.ones((10, 5))
        solver.importance_map = ImportanceMap(z_centers=z_centers, r_centers=r_centers, importance=importance)
        
        # Mock fission bank
        mock_mc_solver.fission_bank.size = 50
        mock_mc_solver.fission_bank.position = np.random.rand(50, 3) * 100
        
        solver._resample_source()
        
        # Should use importance-based resampling
        assert mock_mc_solver.source_bank.clear.called or mock_mc_solver._resample_source.called
