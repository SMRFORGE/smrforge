"""
Tests for smrforge.core.decay_chain_utils module.
"""

import numpy as np
import pytest
from unittest.mock import Mock, patch

from smrforge.core.reactor_core import Nuclide, DecayData
from smrforge.core.decay_chain_utils import (
    DecayChain,
    build_fission_product_chain,
    solve_bateman_equations,
    get_prompt_delayed_chi_for_transient,
    collapse_with_adjoint_for_sensitivity,
)


@pytest.fixture
def sample_nuclides():
    """Create sample nuclides for testing."""
    return [
        Nuclide(Z=92, A=235),
        Nuclide(Z=92, A=236),
        Nuclide(Z=92, A=237),
    ]


@pytest.fixture
def mock_decay_data():
    """Create a mock DecayData instance."""
    decay_data = Mock(spec=DecayData)
    decay_data._get_daughters = Mock(return_value=[])
    decay_data.build_decay_matrix = Mock(return_value=np.zeros((3, 3)))
    return decay_data


class TestDecayChain:
    """Tests for DecayChain class."""
    
    def test_decay_chain_init(self, sample_nuclides):
        """Test DecayChain initialization."""
        chain = DecayChain(sample_nuclides)
        
        assert chain.nuclides == sample_nuclides
        assert chain.decay_data is not None
        assert isinstance(chain.parent_daughters, dict)
    
    def test_decay_chain_init_with_decay_data(self, sample_nuclides, mock_decay_data):
        """Test DecayChain initialization with provided decay data."""
        chain = DecayChain(sample_nuclides, decay_data=mock_decay_data)
        
        assert chain.decay_data == mock_decay_data
        assert chain.nuclides == sample_nuclides
    
    def test_build_relationships(self, sample_nuclides, mock_decay_data):
        """Test _build_relationships method."""
        # Mock daughters for first nuclide
        daughters = [(sample_nuclides[1], 0.5), (sample_nuclides[2], 0.3)]
        mock_decay_data._get_daughters.return_value = daughters
        
        chain = DecayChain(sample_nuclides, decay_data=mock_decay_data)
        
        # Should have called _get_daughters for each nuclide
        assert mock_decay_data._get_daughters.called
    
    def test_build_decay_matrix(self, sample_nuclides, mock_decay_data):
        """Test build_decay_matrix method."""
        chain = DecayChain(sample_nuclides, decay_data=mock_decay_data)
        
        matrix = chain.build_decay_matrix()
        
        mock_decay_data.build_decay_matrix.assert_called_once_with(sample_nuclides)
        assert isinstance(matrix, np.ndarray)
    
    def test_evolve(self, sample_nuclides, mock_decay_data):
        """Test evolve method."""
        # Create a simple decay matrix (diagonal with decay constants)
        decay_matrix = np.array([
            [-0.1, 0.0, 0.0],
            [0.1, -0.05, 0.0],
            [0.0, 0.05, 0.0],
        ])
        mock_decay_data.build_decay_matrix.return_value = decay_matrix
        
        chain = DecayChain(sample_nuclides, decay_data=mock_decay_data)
        initial = np.array([1.0, 0.0, 0.0])
        
        final = chain.evolve(initial, time=10.0)
        
        assert isinstance(final, np.ndarray)
        assert final.shape == (3,)
        assert np.all(final >= 0)  # Concentrations should be non-negative
    
    def test_get_chain_depth(self, sample_nuclides):
        """Test get_chain_depth method."""
        chain = DecayChain(sample_nuclides)
        
        depth = chain.get_chain_depth(sample_nuclides[0])
        
        # Currently returns placeholder value
        assert isinstance(depth, int)
    
    def test_get_chain_depth_nonexistent(self, sample_nuclides):
        """Test get_chain_depth for nuclide not in chain."""
        chain = DecayChain(sample_nuclides)
        other_nuclide = Nuclide(Z=1, A=1)
        
        depth = chain.get_chain_depth(other_nuclide)
        
        assert depth == -1
    
    def test_get_chain_string(self, sample_nuclides, mock_decay_data):
        """Test get_chain_string method."""
        # Mock daughters for first nuclide
        daughters = [(sample_nuclides[1], 0.5)]
        mock_decay_data._get_daughters.return_value = daughters
        
        chain = DecayChain(sample_nuclides, decay_data=mock_decay_data)
        chain_string = chain.get_chain_string()
        
        assert isinstance(chain_string, str)
        assert len(chain_string) > 0


class TestBuildFissionProductChain:
    """Tests for build_fission_product_chain function."""
    
    def test_build_fission_product_chain(self):
        """Test build_fission_product_chain function."""
        parent = Nuclide(Z=92, A=235)
        
        chain = build_fission_product_chain(parent, max_depth=2)
        
        assert isinstance(chain, DecayChain)
        assert parent in chain.nuclides
    
    def test_build_fission_product_chain_with_decay_data(self, mock_decay_data):
        """Test build_fission_product_chain with provided decay data."""
        parent = Nuclide(Z=94, A=239)
        
        chain = build_fission_product_chain(parent, max_depth=1, decay_data=mock_decay_data)
        
        assert isinstance(chain, DecayChain)
        assert chain.decay_data == mock_decay_data
    
    def test_build_fission_product_chain_max_depth(self):
        """Test build_fission_product_chain respects max_depth."""
        parent = Nuclide(Z=92, A=235)
        
        chain_shallow = build_fission_product_chain(parent, max_depth=1)
        chain_deep = build_fission_product_chain(parent, max_depth=5)
        
        # Deeper chain should have more or equal nuclides
        assert len(chain_deep.nuclides) >= len(chain_shallow.nuclides)

    def test_build_fission_product_chain_max_depth_zero(self):
        """Test build_fission_product_chain with max_depth=0 (only parent, no recursion)."""
        parent = Nuclide(Z=92, A=235)
        chain = build_fission_product_chain(parent, max_depth=0)
        assert isinstance(chain, DecayChain)
        assert len(chain.nuclides) == 1
        assert chain.nuclides[0] == parent


class TestSolveBatemanEquations:
    """Tests for solve_bateman_equations function."""
    
    def test_solve_bateman_equations_dense_matrix(self):
        """Test solve_bateman_equations with dense matrix."""
        # Simple decay chain: A -> B -> C
        decay_matrix = np.array([
            [-0.1, 0.0, 0.0],
            [0.1, -0.05, 0.0],
            [0.0, 0.05, 0.0],
        ])
        
        initial = np.array([1.0, 0.0, 0.0])
        times = np.array([0.0, 10.0, 20.0])
        
        result = solve_bateman_equations(decay_matrix, initial, times)
        
        assert result.shape == (3, 3)  # (n_times, n_nuclides)
        assert np.all(result >= 0)  # Concentrations should be non-negative
        assert np.allclose(result[0], initial)  # Initial condition
    
    def test_solve_bateman_equations_sparse_matrix(self):
        """Test solve_bateman_equations with sparse matrix."""
        from scipy.sparse import csr_matrix
        
        # Create sparse decay matrix
        decay_matrix = csr_matrix([
            [-0.1, 0.0, 0.0],
            [0.1, -0.05, 0.0],
            [0.0, 0.05, 0.0],
        ])
        
        initial = np.array([1.0, 0.0, 0.0])
        times = np.array([0.0, 10.0, 20.0])
        
        result = solve_bateman_equations(decay_matrix, initial, times)
        
        assert result.shape == (3, 3)
        assert np.all(result >= 0)
    
    def test_solve_bateman_equations_single_time_point(self):
        """Test solve_bateman_equations with single time point."""
        decay_matrix = np.array([
            [-0.1, 0.0, 0.0],
            [0.1, -0.05, 0.0],
            [0.0, 0.05, 0.0],
        ])
        
        initial = np.array([1.0, 0.0, 0.0])
        times = np.array([10.0])  # Single time point
        
        result = solve_bateman_equations(decay_matrix, initial, times)
        
        # Should return 1D array for single time point
        assert result.ndim == 1 or result.shape[0] == 1
        assert np.all(result >= 0)
    
    def test_get_chain_string_with_daughters(self, sample_nuclides, mock_decay_data):
        """Test get_chain_string with daughters."""
        # Mock daughters for first nuclide
        daughters = [(sample_nuclides[1], 0.5), (sample_nuclides[2], 0.3)]
        mock_decay_data._get_daughters.return_value = daughters
        
        chain = DecayChain(sample_nuclides, decay_data=mock_decay_data)
        chain_string = chain.get_chain_string()
        
        assert isinstance(chain_string, str)
        assert sample_nuclides[0].name in chain_string
        assert sample_nuclides[1].name in chain_string
    
    def test_get_chain_string_stable_nuclide(self, sample_nuclides, mock_decay_data):
        """Test get_chain_string for stable nuclide (no daughters)."""
        # Mock no daughters
        mock_decay_data._get_daughters.return_value = []
        
        chain = DecayChain(sample_nuclides, decay_data=mock_decay_data)
        chain_string = chain.get_chain_string()
        
        assert isinstance(chain_string, str)
        assert "(stable)" in chain_string or sample_nuclides[0].name in chain_string
    
    def test_build_fission_product_chain_empty_daughters(self, mock_decay_data):
        """Test build_fission_product_chain when no daughters exist."""
        parent = Nuclide(Z=1, A=1)  # Simple nuclide
        mock_decay_data._get_daughters.return_value = []
        
        chain = build_fission_product_chain(parent, max_depth=5, decay_data=mock_decay_data)
        
        assert isinstance(chain, DecayChain)
        assert len(chain.nuclides) >= 1  # At least parent
        assert parent in chain.nuclides


class TestGetPromptDelayedChiForTransient:
    """Tests for get_prompt_delayed_chi_for_transient function."""
    
    def test_get_prompt_delayed_chi_for_transient_with_cache(self):
        """Test get_prompt_delayed_chi_for_transient with cache."""
        from smrforge.core.reactor_core import NuclearDataCache
        
        cache = NuclearDataCache()
        u235 = Nuclide(Z=92, A=235)
        group_structure = np.logspace(7, -5, 26)
        
        try:
            chi_p, chi_d, delayed = get_prompt_delayed_chi_for_transient(
                cache, u235, group_structure
            )
            
            assert chi_p.shape == (25,)  # n_groups - 1
            assert chi_d.shape == (25,)
            assert isinstance(delayed, dict)
            assert "beta" in delayed
            assert "beta_i" in delayed
            assert "lambda_i" in delayed
        except (ImportError, AttributeError):
            # May fail if extractors not available
            pytest.skip("Required extractors not available")
    
    def test_get_prompt_delayed_chi_for_transient_default_delayed_data(self):
        """Test get_prompt_delayed_chi_for_transient with default delayed data."""
        from smrforge.core.reactor_core import NuclearDataCache
        
        cache = NuclearDataCache()
        u235 = Nuclide(Z=92, A=235)
        group_structure = np.logspace(7, -5, 26)
        
        # Mock get_delayed_neutron_data to return None
        with patch('smrforge.core.reactor_core.get_delayed_neutron_data', return_value=None):
            try:
                chi_p, chi_d, delayed = get_prompt_delayed_chi_for_transient(
                    cache, u235, group_structure
                )
                
                # Should use default values
                assert delayed["beta"] == 0.0065
                assert len(delayed["beta_i"]) == 6
                assert len(delayed["lambda_i"]) == 6
            except (ImportError, AttributeError):
                pytest.skip("Required extractors not available")


class TestCollapseWithAdjointForSensitivity:
    """Tests for collapse_with_adjoint_for_sensitivity function."""
    
    def test_collapse_with_adjoint_for_sensitivity(self):
        """Test collapse_with_adjoint_for_sensitivity function."""
        fine_groups = np.logspace(7, -5, 100)
        coarse_groups = np.array([2e7, 1e6, 1e5, 1e4, 1e-5])
        
        fine_xs = np.ones(len(fine_groups) - 1) * 0.5
        fine_flux = np.ones(len(fine_groups) - 1) * 1e14
        fine_adjoint = np.ones(len(fine_groups) - 1) * 1e12
        
        try:
            coarse_xs, coarse_adj = collapse_with_adjoint_for_sensitivity(
                fine_groups,
                coarse_groups,
                fine_xs,
                fine_flux,
                fine_adjoint,
                reaction="fission",
            )
            
            assert coarse_xs.shape == (len(coarse_groups) - 1,)
            assert coarse_adj.shape == (len(coarse_groups) - 1,)
            assert np.all(coarse_xs >= 0)
            assert np.all(coarse_adj >= 0)
        except ImportError:
            pytest.skip("multigroup_advanced module not available")
    
    def test_collapse_with_adjoint_for_sensitivity_no_overlap(self):
        """Test collapse when fine groups don't overlap with coarse groups."""
        fine_groups = np.array([1e6, 1e5, 1e4, 1e3])
        coarse_groups = np.array([1e7, 1e6])  # Only overlaps with first fine group
        
        fine_xs = np.array([0.5, 0.3, 0.2])
        fine_flux = np.array([1e14, 1e13, 1e12])
        fine_adjoint = np.array([1e12, 1e11, 1e10])
        
        try:
            coarse_xs, coarse_adj = collapse_with_adjoint_for_sensitivity(
                fine_groups,
                coarse_groups,
                fine_xs,
                fine_flux,
                fine_adjoint,
            )
            
            assert coarse_xs.shape == (1,)
            assert coarse_adj.shape == (1,)
        except ImportError:
            pytest.skip("multigroup_advanced module not available")
    
    def test_collapse_with_adjoint_for_sensitivity_zero_total_de(self):
        """Test collapse when total_dE is zero (edge case)."""
        fine_groups = np.array([1e6, 1e5])
        coarse_groups = np.array([1e7, 1e6])  # No overlap
        
        fine_xs = np.array([0.5])
        fine_flux = np.array([1e14])
        fine_adjoint = np.array([1e12])
        
        try:
            coarse_xs, coarse_adj = collapse_with_adjoint_for_sensitivity(
                fine_groups,
                coarse_groups,
                fine_xs,
                fine_flux,
                fine_adjoint,
            )
            
            # Should handle zero total_dE gracefully
            assert coarse_xs.shape == (1,)
            assert coarse_adj.shape == (1,)
        except ImportError:
            pytest.skip("multigroup_advanced module not available")


class TestDecayChainEdgeCases:
    """Edge case tests for DecayChain to improve coverage."""
    
    def test_decay_chain_evolve_zero_time(self, sample_nuclides, mock_decay_data):
        """Test evolve with zero time (should return initial concentrations)."""
        decay_matrix = np.array([
            [-0.1, 0.0, 0.0],
            [0.1, -0.05, 0.0],
            [0.0, 0.05, 0.0],
        ])
        mock_decay_data.build_decay_matrix.return_value = decay_matrix
        
        chain = DecayChain(sample_nuclides, decay_data=mock_decay_data)
        initial = np.array([1.0, 0.0, 0.0])
        
        final = chain.evolve(initial, time=0.0)
        
        # Should be close to initial (within numerical precision)
        assert np.allclose(final, initial, atol=1e-6)
    
    def test_decay_chain_evolve_very_long_time(self, sample_nuclides, mock_decay_data):
        """Test evolve with very long time."""
        decay_matrix = np.array([
            [-0.1, 0.0, 0.0],
            [0.1, -0.05, 0.0],
            [0.0, 0.05, 0.0],
        ])
        mock_decay_data.build_decay_matrix.return_value = decay_matrix
        
        chain = DecayChain(sample_nuclides, decay_data=mock_decay_data)
        initial = np.array([1.0, 0.0, 0.0])
        
        final = chain.evolve(initial, time=1e6)  # Very long time
        
        # All should decay significantly
        assert np.all(final >= 0)
        # Total should decrease or stay same (within numerical precision for very long time)
        assert final.sum() <= initial.sum() * 1.01  # Allow small numerical error


class TestDecayChainEdgeCasesAdditional:
    """Additional edge case tests for DecayChain to improve coverage."""
    
    def test_build_fission_product_chain_different_max_depth(self, mock_decay_data):
        """Test build_fission_product_chain with different max_depth values."""
        parent = Nuclide(Z=92, A=235)
        
        # Create a chain with multiple generations
        daughter1 = Nuclide(Z=92, A=236)
        daughter2 = Nuclide(Z=92, A=237)
        granddaughter = Nuclide(Z=92, A=238)
        
        def mock_get_daughters(nuc):
            if nuc == parent:
                return [(daughter1, 0.5), (daughter2, 0.3)]
            elif nuc == daughter1:
                return [(granddaughter, 0.4)]
            else:
                return []
        
        mock_decay_data._get_daughters.side_effect = mock_get_daughters
        
        # Test with max_depth=1 (should only get direct daughters)
        chain1 = build_fission_product_chain(parent, max_depth=1, decay_data=mock_decay_data)
        assert len(chain1.nuclides) <= 3  # Parent + up to 2 daughters
        
        # Test with max_depth=2 (should get grandchildren)
        chain2 = build_fission_product_chain(parent, max_depth=2, decay_data=mock_decay_data)
        assert len(chain2.nuclides) >= len(chain1.nuclides)
    
    def test_build_fission_product_chain_max_depth_zero(self, mock_decay_data):
        """Test build_fission_product_chain with max_depth=0."""
        parent = Nuclide(Z=92, A=235)
        mock_decay_data._get_daughters.return_value = [(Nuclide(Z=92, A=236), 0.5)]
        
        chain = build_fission_product_chain(parent, max_depth=0, decay_data=mock_decay_data)
        
        # Should only contain parent
        assert len(chain.nuclides) == 1
        assert parent in chain.nuclides
    
    def test_solve_bateman_equations_empty_times(self):
        """Test solve_bateman_equations with empty times array."""
        decay_matrix = np.array([[-0.1]])
        initial = np.array([1.0])
        times = np.array([])
        
        # Should handle empty times gracefully
        try:
            result = solve_bateman_equations(decay_matrix, initial, times)
            # Result shape depends on implementation
            assert result is not None
        except (ValueError, IndexError):
            # Empty times may raise error, which is acceptable
            pass
    
    def test_solve_bateman_equations_very_small_times(self):
        """Test solve_bateman_equations with very small time values."""
        decay_matrix = np.array([
            [-0.1, 0.0],
            [0.1, -0.05],
        ])
        initial = np.array([1.0, 0.0])
        times = np.array([1e-10, 1e-9])  # Very small times
        
        result = solve_bateman_equations(decay_matrix, initial, times)
        
        # Should be close to initial for very small times
        assert result.shape[0] == 2
        assert np.allclose(result[0], initial, atol=1e-3)
    
    def test_decay_chain_build_relationships_filters_nuclides(self, mock_decay_data):
        """Test _build_relationships filters daughters not in nuclides list."""
        parent = Nuclide(Z=92, A=235)
        daughter_in_list = Nuclide(Z=92, A=236)
        daughter_not_in_list = Nuclide(Z=92, A=237)
        
        nuclides = [parent, daughter_in_list]  # daughter_not_in_list not included
        
        # Mock to return both daughters
        mock_decay_data._get_daughters.return_value = [
            (daughter_in_list, 0.5),
            (daughter_not_in_list, 0.3),
        ]
        
        chain = DecayChain(nuclides, decay_data=mock_decay_data)
        
        # Should only include daughter_in_list in parent_daughters
        assert daughter_in_list in chain.parent_daughters.get(parent, [])
        assert daughter_not_in_list not in chain.parent_daughters.get(parent, [])
    
    @patch('smrforge.core.endf_extractors.extract_chi_prompt_delayed')
    @patch('smrforge.core.reactor_core.get_delayed_neutron_data')
    def test_get_prompt_delayed_chi_for_transient(self, mock_delayed_data, mock_chi):
        """Test get_prompt_delayed_chi_for_transient function."""
        cache = Mock()
        nuclide = Nuclide(Z=92, A=235)
        group_structure = np.logspace(7, -5, 26)
        
        # Mock return values
        mock_chi.return_value = (np.ones(25), np.ones(25) * 0.5)
        mock_delayed_data.return_value = {
            "beta": 0.0065,
            "beta_i": np.array([2.13e-4, 1.43e-3, 1.27e-3, 2.56e-3, 7.48e-4, 2.73e-4]),
            "lambda_i": np.array([0.0124, 0.0305, 0.111, 0.301, 1.14, 3.01]),
        }
        
        chi_p, chi_d, delayed = get_prompt_delayed_chi_for_transient(
            cache, nuclide, group_structure
        )
        
        assert chi_p.shape == (25,)
        assert chi_d.shape == (25,)
        assert "beta" in delayed
        assert "beta_i" in delayed
        assert "lambda_i" in delayed
    
    @patch('smrforge.core.endf_extractors.extract_chi_prompt_delayed')
    @patch('smrforge.core.reactor_core.get_delayed_neutron_data')
    def test_get_prompt_delayed_chi_for_transient_no_delayed_data(self, mock_delayed_data, mock_chi):
        """Test get_prompt_delayed_chi_for_transient when delayed data is None."""
        cache = Mock()
        nuclide = Nuclide(Z=92, A=235)
        group_structure = np.logspace(7, -5, 26)
        
        # Mock return values
        mock_chi.return_value = (np.ones(25), np.ones(25) * 0.5)
        mock_delayed_data.return_value = None  # No delayed data available
        
        chi_p, chi_d, delayed = get_prompt_delayed_chi_for_transient(
            cache, nuclide, group_structure
        )
        
        # Should use default values
        assert "beta" in delayed
        assert delayed["beta"] == 0.0065


class TestCollapseWithAdjointForSensitivityAdditional:
    """Additional tests for collapse_with_adjoint_for_sensitivity using mocks."""
    
    @patch('smrforge.core.multigroup_advanced.collapse_with_adjoint_weighting')
    def test_collapse_with_adjoint_for_sensitivity_with_mock(self, mock_collapse):
        """Test collapse_with_adjoint_for_sensitivity function with mocked collapse."""
        fine_group_structure = np.logspace(7, -5, 100)
        coarse_group_structure = np.array([2e7, 1e6, 1e5, 1e4, 1e-5])
        fine_xs = np.ones(99)
        fine_flux = np.ones(99)
        fine_adjoint = np.ones(99)
        
        # Mock collapse function
        mock_collapse.return_value = np.array([0.8, 0.9, 1.0, 0.95])
        
        coarse_xs, coarse_adj = collapse_with_adjoint_for_sensitivity(
            fine_group_structure,
            coarse_group_structure,
            fine_xs,
            fine_flux,
            fine_adjoint,
            reaction="fission",
        )
        
        assert coarse_xs.shape == (4,)
        assert coarse_adj.shape == (4,)
        assert np.all(coarse_adj >= 0)  # Adjoint should be non-negative
