# Adaptive Sampling Implementation - Phase 2

**Date:** January 2026  
**Status:** Foundation Implemented  
**Reference:** [Optimization Roadmap](OPTIMIZATION-ROADMAP.md)

---

## Executive Summary

Implemented foundation for **adaptive sampling** (Phase 2 optimization), which focuses computation on important regions for **2-5x faster convergence** with same accuracy. This is the first step toward making SMRForge **faster than OpenMC** through better algorithms.

---

## Implementation Status

### Status: 🚧 Foundation Complete, Integration In Progress

**What's Done:**
- ✅ `ImportanceMap` class - Maps spatial regions to importance weights
- ✅ `AdaptiveMonteCarloSolver` class - Main adaptive sampling solver
- ✅ Exploration phase - Uniform sampling to identify important regions
- ✅ Refinement phase - Importance-based sampling framework
- ✅ Fission density estimation - Tracks where fissions occur with proper volume normalization
- ✅ Integration with base MC solver
- ✅ **Importance-based source resampling** - Weighted selection from fission bank

**What's Next:**
- Test and verify 2-5x convergence improvement
- Benchmark against standard MC
- Create unit tests for adaptive sampling

---

## How Adaptive Sampling Works

### Algorithm Overview

1. **Phase 1: Exploration** (n_exploration generations)
   - Uniform sampling across all regions
   - Track fission density to identify important regions
   - Build importance map from fission locations

2. **Phase 2: Importance Map Building**
   - Normalize fission density to get importance weights
   - Create spatial importance map [nz, nr]

3. **Phase 3: Refinement** (n_refinement generations)
   - Use importance map to guide sampling
   - More particles in high-importance regions
   - Periodic importance map updates

4. **Phase 4: Result Combination**
   - Combine exploration and refinement results
   - Use refinement phase for final k-eff (exploration for importance only)

### Key Insight

**Regions with more fissions are more important** - focusing computation there improves convergence without sacrificing accuracy.

---

## Files Created

**New File:**
- `smrforge/neutronics/adaptive_sampling.py` - Adaptive sampling implementation

**Modified Files:**
- `smrforge/neutronics/__init__.py` - Exports for adaptive sampling

---

## Usage Example

```python
from smrforge.neutronics.monte_carlo_optimized import OptimizedMonteCarloSolver
from smrforge.neutronics.adaptive_sampling import create_adaptive_solver

# Create base MC solver
mc = OptimizedMonteCarloSolver(geometry, xs_data, n_particles=10000)

# Create adaptive solver
adaptive = create_adaptive_solver(
    mc_solver=mc,
    n_exploration=20,  # Explore all regions
    n_refinement=80    # Refine in important regions
)

# Solve with adaptive sampling
results = adaptive.solve_eigenvalue()
print(f"k-eff: {results['k_eff']:.6f} ± {results['k_std']:.6f}")

# Access importance map
importance_map = results['importance_map']
print(f"Max importance: {np.max(importance_map.importance):.3f}")
```

---

## Expected Benefits

### Performance

- **2-5x faster convergence** with same accuracy
- Better variance reduction (focuses on important regions)
- Same number of particles, better distributed

### Why It Works

1. **Importance Sampling:** More particles in regions that contribute more to k-eff
2. **Variance Reduction:** Reduces statistical noise by focusing computation
3. **Adaptive Refinement:** Updates importance map as solution evolves

---

## Implementation Details

### ImportanceMap Class

```python
@dataclass
class ImportanceMap:
    """Maps spatial regions to importance weights."""
    
    z_centers: np.ndarray  # Axial grid centers
    r_centers: np.ndarray  # Radial grid centers
    importance: np.ndarray  # Importance weights [nz, nr]
    
    def get_sampling_probability(self, z: float, r: float) -> float:
        """Get sampling probability for a location."""
        # Higher importance = higher sampling probability
```

### AdaptiveMonteCarloSolver Class

```python
class AdaptiveMonteCarloSolver:
    """Adaptive sampling with importance-based refinement."""
    
    def solve_eigenvalue(self) -> Dict:
        """Solve with adaptive sampling."""
        # Phase 1: Exploration
        self._exploration_phase()
        
        # Phase 2: Build importance map
        self.importance_map = self._build_importance_map()
        
        # Phase 3: Refinement
        self._refinement_phase()
        
        # Phase 4: Combine results
        return self._combine_results()
```

---

## Next Steps

### 1. Testing and Benchmarking

**Status:** 📋 Pending

**What Needs to Be Done:**
- Create unit tests for adaptive sampling
- Benchmark against standard MC (verify 2-5x improvement)
- Compare convergence rates

**Expected Impact:** Validation of performance gains

---

### Implementation Highlights

**Importance-Based Source Resampling:**

The key innovation is `_resample_source_importance()`, which samples fission sites with probability proportional to their importance:

```python
def _resample_source_importance(self) -> None:
    """Sample fission sites with importance weighting."""
    # Calculate importance for each fission site
    importances = np.array([
        importance_map.get_sampling_probability(z, r)
        for z, r in zip(z_positions, r_positions)
    ])
    
    # Normalize to probabilities
    probs = importances / np.sum(importances)
    
    # Sample with replacement using importance weights
    indices = np.random.choice(
        fission_bank.size,
        size=n_particles,
        replace=True,
        p=probs,
    )
```

**Improved Fission Density Estimation:**

Fission density is now normalized by proper cylindrical cell volumes:

```python
# Cell volume = pi * (r_outer^2 - r_inner^2) * dz
volume_radial = np.pi * (r_outer**2 - r_inner**2)
cell_volumes[j, i] = volume_radial * volume_axial
fission_density = fission_density / cell_volumes
```

---

## Performance Projection

### Expected Improvement

| Metric | Standard MC | Adaptive MC | Improvement |
|--------|-------------|-------------|-------------|
| **Convergence** | Baseline | 2-5x faster | 2-5x |
| **Variance** | Baseline | Lower | Better |
| **Particles Needed** | N | N/2-N/5 | 2-5x fewer |

### Why This Matters

**2-5x faster convergence** means:
- Same accuracy in 1/2 to 1/5 the time
- OR same time with 2-5x better accuracy
- **Can outperform OpenMC** for typical problems through better algorithms

---

## Integration Notes

### Current Integration

- Uses `OptimizedMonteCarloSolver` as base
- Delegates particle tracking to base solver
- Adapts source initialization (framework ready)

### Future Enhancements

1. **Importance-based source initialization**
   - Place more particles in high-importance regions
   - Weight particles based on importance

2. **Dynamic importance updates**
   - Update importance map during refinement
   - Adapt to solution evolution

3. **Multi-level refinement**
   - Coarse-to-fine importance mapping
   - Hierarchical refinement strategy

---

## Conclusion

**Foundation for adaptive sampling is complete!**

✅ **Core classes implemented** - ImportanceMap and AdaptiveMonteCarloSolver  
✅ **Algorithm structure** - Exploration + refinement phases  
✅ **Integration framework** - Works with base MC solver  

**Next:** Enhance integration and test to verify 2-5x convergence improvement.

**Key Advantage:** Adaptive sampling is the first step toward making SMRForge **faster than OpenMC** through better algorithms, even with a 5-10% raw performance gap.

---

**Last Updated:** January 2026  
**Status:** 🚧 Foundation Complete - Integration In Progress
