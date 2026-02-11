"""
Unit tests for memory pool utilities.
"""

import numpy as np
import pytest

from smrforge.utils.memory_pool import ParticleMemoryPool


class TestParticleMemoryPool:
    """Tests for ParticleMemoryPool class."""

    def test_particle_memory_pool_initialization(self):
        """Test ParticleMemoryPool initialization."""
        pool = ParticleMemoryPool(capacity=1000)

        assert pool.capacity == 1000
        assert pool.active_size == 0
        assert pool.position.shape == (1000, 3)
        assert pool.direction.shape == (1000, 3)
        assert pool.energy.shape == (1000,)
        assert pool.weight.shape == (1000,)

    def test_particle_memory_pool_custom_dtype(self):
        """Test ParticleMemoryPool with custom dtype."""
        pool = ParticleMemoryPool(capacity=100, dtype=np.float32)

        assert pool.dtype == np.float32
        assert pool.position.dtype == np.float32

    def test_get_arrays(self):
        """Test getting arrays from pool."""
        pool = ParticleMemoryPool(capacity=1000)

        pos, dir, energy, weight, gen, alive, mat_id = pool.get_arrays(500)

        assert pool.active_size == 500
        assert pos.shape == (500, 3)
        assert dir.shape == (500, 3)
        assert energy.shape == (500,)
        assert weight.shape == (500,)
        assert gen.shape == (500,)
        assert alive.shape == (500,)
        assert mat_id.shape == (500,)

    def test_get_arrays_exceeds_capacity(self):
        """Test that getting arrays exceeding capacity raises error."""
        pool = ParticleMemoryPool(capacity=100)

        with pytest.raises(ValueError, match="exceeds|capacity"):
            pool.get_arrays(200)

    def test_return_arrays(self):
        """Test returning arrays to pool."""
        pool = ParticleMemoryPool(capacity=1000)

        pool.get_arrays(500)
        assert pool.active_size == 500

        pool.return_arrays()
        assert pool.active_size == 0

    def test_reset(self):
        """Test resetting pool (using clear)."""
        pool = ParticleMemoryPool(capacity=1000)

        pool.get_arrays(500)
        pool.clear()

        assert pool.active_size == 0

    def test_clear(self):
        """Test clearing pool."""
        pool = ParticleMemoryPool(capacity=1000)

        pool.get_arrays(500)
        pool.clear()

        assert pool.active_size == 0

    def test_array_views_are_shared(self):
        """Test that array views share memory with pool arrays."""
        pool = ParticleMemoryPool(capacity=1000)

        pos, dir, energy, weight, gen, alive, mat_id = pool.get_arrays(500)

        # Modify through view
        pos[0, 0] = 1.0
        energy[0] = 2.0

        # Check that pool arrays are modified
        assert pool.position[0, 0] == 1.0
        assert pool.energy[0] == 2.0

    def test_grow_pool(self):
        """Test growing pool capacity."""
        pool = ParticleMemoryPool(capacity=100)

        pool.grow(200)

        assert pool.capacity == 200
        assert pool.position.shape == (200, 3)

    def test_grow_pool_default(self):
        """Test growing pool with default (2x capacity)."""
        pool = ParticleMemoryPool(capacity=100)

        pool.grow()

        assert pool.capacity == 200

    def test_grow_pool_no_change(self):
        """Test growing pool with smaller capacity (no change)."""
        pool = ParticleMemoryPool(capacity=100)
        original_capacity = pool.capacity

        pool.grow(50)  # Smaller than current

        assert pool.capacity == original_capacity

    def test_pool_repr(self):
        """Test pool string representation."""
        pool = ParticleMemoryPool(capacity=1000, dtype=np.float32)

        repr_str = repr(pool)
        assert "ParticleMemoryPool" in repr_str
        assert "capacity=1000" in repr_str
        assert "dtype" in repr_str

    def test_memory_pool_manager(self):
        """Test MemoryPoolManager."""
        from smrforge.utils.memory_pool import MemoryPoolManager

        manager = MemoryPoolManager(default_capacity=500)

        pool1 = manager.get_pool("source")
        pool2 = manager.get_pool("fission")

        assert pool1.capacity == 500
        assert pool2.capacity == 500
        assert pool1 is not pool2

    def test_memory_pool_manager_custom_capacity(self):
        """Test MemoryPoolManager with custom capacity."""
        from smrforge.utils.memory_pool import MemoryPoolManager

        manager = MemoryPoolManager(default_capacity=500)

        pool = manager.get_pool("source", capacity=1000)

        assert pool.capacity == 1000

    def test_memory_pool_manager_clear_all(self):
        """Test clearing all pools."""
        from smrforge.utils.memory_pool import MemoryPoolManager

        manager = MemoryPoolManager()
        pool1 = manager.get_pool("source")
        pool2 = manager.get_pool("fission")

        pool1.get_arrays(100)
        pool2.get_arrays(200)

        manager.clear_all()

        assert pool1.active_size == 0
        assert pool2.active_size == 0

    def test_memory_pool_manager_repr(self):
        """Test MemoryPoolManager string representation."""
        from smrforge.utils.memory_pool import MemoryPoolManager

        manager = MemoryPoolManager()
        manager.get_pool("source")
        manager.get_pool("fission")

        repr_str = repr(manager)
        assert "MemoryPoolManager" in repr_str
        assert "source" in repr_str or "fission" in repr_str


class TestMemoryPoolEdgeCases:
    """Edge case tests for memory_pool.py to improve coverage to 60%+."""

    def test_pool_get_arrays_exact_capacity(self):
        """Test getting arrays at exact capacity."""
        pool = ParticleMemoryPool(capacity=100)
        pos, dir, energy, weight, gen, alive, mat_id = pool.get_arrays(100)

        assert pool.active_size == 100
        assert pos.shape == (100, 3)

    def test_pool_get_arrays_zero(self):
        """Test getting arrays for zero particles."""
        pool = ParticleMemoryPool(capacity=100)
        pos, dir, energy, weight, gen, alive, mat_id = pool.get_arrays(0)

        assert pool.active_size == 0
        assert pos.shape == (0, 3)

    def test_pool_grow_exact_current_capacity(self):
        """Test growing pool to exact current capacity (no change)."""
        pool = ParticleMemoryPool(capacity=100)
        original_capacity = pool.capacity

        pool.grow(100)  # Same as current

        assert pool.capacity == original_capacity

    def test_pool_grow_larger_multiple(self):
        """Test growing pool to much larger capacity."""
        pool = ParticleMemoryPool(capacity=100)
        pool.grow(1000)

        assert pool.capacity == 1000
        assert pool.position.shape == (1000, 3)

    def test_pool_grow_preserves_data(self):
        """Test that growing pool preserves existing data."""
        pool = ParticleMemoryPool(capacity=100)
        pos, _, _, _, _, _, _ = pool.get_arrays(50)
        pos[0, 0] = 42.0

        pool.grow(200)

        assert pool.position[0, 0] == 42.0

    def test_pool_manager_get_pool_existing(self):
        """Test getting existing pool returns same instance."""
        from smrforge.utils.memory_pool import MemoryPoolManager

        manager = MemoryPoolManager()
        pool1 = manager.get_pool("test_pool")
        pool2 = manager.get_pool("test_pool")

        assert pool1 is pool2

    def test_pool_manager_get_pool_custom_capacity_then_default(self):
        """Test getting pool with custom capacity then getting same pool again."""
        from smrforge.utils.memory_pool import MemoryPoolManager

        manager = MemoryPoolManager(default_capacity=100)
        pool1 = manager.get_pool("test", capacity=500)
        # Getting same pool again should return same instance, not create new with default
        pool2 = manager.get_pool("test")

        assert pool1 is pool2
        assert pool1.capacity == 500  # Should keep original capacity

    def test_pool_manager_clear_all_empty(self):
        """Test clearing all pools when manager is empty."""
        from smrforge.utils.memory_pool import MemoryPoolManager

        manager = MemoryPoolManager()
        manager.clear_all()  # Should not error

    def test_pool_manager_multiple_pools_different_capacities(self):
        """Test manager with multiple pools having different capacities."""
        from smrforge.utils.memory_pool import MemoryPoolManager

        manager = MemoryPoolManager(default_capacity=100)
        pool1 = manager.get_pool("small", capacity=50)
        pool2 = manager.get_pool("large", capacity=500)

        assert pool1.capacity == 50
        assert pool2.capacity == 500

    def test_pool_repr_with_active_size(self):
        """Test pool repr with active size."""
        pool = ParticleMemoryPool(capacity=100)
        pool.get_arrays(25)

        repr_str = repr(pool)
        assert "active_size=25" in repr_str

    def test_pool_manager_repr_empty(self):
        """Test manager repr when no pools exist."""
        from smrforge.utils.memory_pool import MemoryPoolManager

        manager = MemoryPoolManager()
        repr_str = repr(manager)
        assert "MemoryPoolManager" in repr_str
        assert "pools=[]" in repr_str or "pools=" in repr_str
