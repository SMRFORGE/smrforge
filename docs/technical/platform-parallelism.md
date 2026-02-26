# Platform Notes: Parallelism and Performance

**Last Updated:** February 2026  
**Purpose:** Document platform-specific behavior for ProcessPoolExecutor, multiprocessing, and Numba prange/OpenMP.

SMRForge uses parallel execution in several places (parameter sweeps, diffusion solver, Monte Carlo, data downloads). Platform differences affect performance and reliability. This document explains what to expect and how to get the best results on each platform.

---

## 1. Windows: ProcessPoolExecutor → ThreadPoolExecutor Fallback

### Behavior

On Windows, SMRForge **automatically falls back** from `ProcessPoolExecutor` to `ThreadPoolExecutor` for batch processing (e.g. `batch_process`, `batch_solve_keff`, parameter sweeps). This happens because:

- Windows uses **spawn** to create processes (no `fork()`)
- Each spawned worker must receive work via **pickling**
- Reactor objects, lambdas, and complex state are often not picklable or are slow to pickle
- Falling back to threads avoids pickling errors and keeps runs stable

### GIL Limitation

`ThreadPoolExecutor` runs work in the same process using threads. Python's **Global Interpreter Lock (GIL)** typically allows only one thread to run Python bytecode at a time. For CPU-bound workloads (neutronics, solvers, particle tracking), this limits speedup—you may not see meaningful improvement from multiple workers.

### Recommendation for CPU-Bound Runs on Windows

For better CPU-bound performance on Windows:

1. **Use WSL (Windows Subsystem for Linux)**  
   WSL provides a Linux kernel where `fork()` is available. SMRForge can use `ProcessPoolExecutor` there, giving real parallel speedup.

   ```bash
   # In WSL terminal:
   cd /path/to/smrforge
   python -m smrforge ...
   ```

2. **Or run parameter sweeps / design studies inside WSL**  
   Same benefits—process-based parallelism without GIL limits.

---

## 2. Windows: multiprocessing and `if __name__ == "__main__"`

### How Processes Are Started

| Platform | Start method | Notes |
|----------|--------------|-------|
| Linux, macOS | `fork()` | Child inherits parent memory; imports already loaded |
| Windows | `spawn` | New interpreter per worker; re-imports and re-executes module |

### Why the Guard Is Required

On Windows, `spawn` causes each worker to re-execute the script from the top. If process-creation code (e.g. `Pool()`, `ProcessPoolExecutor()`) is at module level without a guard:

- The worker imports the module
- The worker runs the top-level code
- The worker tries to create its own pool or executor
- This can cause infinite recursion or crashes

### Required Pattern

Any script that uses `multiprocessing`, `ProcessPoolExecutor`, or similar **must** protect its entry point:

```python
from smrforge.utils.parallel_batch import batch_process

def worker(item):
    return item.solve_keff()

if __name__ == "__main__":
    reactors = [...]  # create reactors
    results = batch_process(reactors, worker, parallel=True)
```

**Always** wrap pool creation, `batch_process`/`batch_solve_keff` calls, and any other multiprocessing entry logic inside `if __name__ == "__main__":`. This is mandatory on Windows and good practice on all platforms.

---

## 3. Numba `prange` and OpenMP

### What Numba Uses

Numba's `prange` enables parallel loop iterations. Under the hood, Numba uses **OpenMP** (or TBB) for threading. OpenMP requires a runtime library (e.g. `libgomp`, `libomp`) to be present on the system.

### Platform-Specific Availability

| Platform | OpenMP library | Notes |
|----------|----------------|-------|
| **Linux** | `libgomp.so` (GCC) | Usually included with GCC; may need `libgomp` package if missing |
| **macOS** | `libomp` | Apple Clang typically does not include OpenMP; install via Homebrew |
| **Windows** | MSVC / MinGW runtime | Often bundled with compiler; conda-forge builds usually include it |

### If OpenMP Is Missing

- Numba may **fall back to single-threaded** execution—no error, but no speedup from `prange`
- Or you may see warnings about OpenMP not being available

### Recommendations

**macOS:**

```bash
brew install libomp
```

If you still see no parallel speedup, set `OMP_NUM_THREADS`:

```bash
export OMP_NUM_THREADS=4
```

**Linux:**

If parallel Numba loops show no speedup, ensure the OpenMP runtime is installed:

```bash
# Debian/Ubuntu
sudo apt-get install libgomp1

# Fedora/RHEL
sudo dnf install libgomp
```

**Windows:**

- **conda**: Usually works; conda-forge NumPy/Numba builds typically include OpenMP
- **pip only**: If `prange` gives no speedup or warnings, consider using conda for the NumPy/Numba stack, or ensure your toolchain (e.g. Visual Studio) provides OpenMP

---

## Summary

| Topic | Action |
|-------|--------|
| Windows ProcessPoolExecutor fallback | Documented; use WSL for CPU-bound runs if you need process-level parallelism |
| spawn / `if __name__ == "__main__"` | Required in scripts that use multiprocessing or batch_process on Windows |
| Numba prange / OpenMP | Ensure OpenMP runtime (`libomp`, `libgomp`) installed; macOS often needs `brew install libomp` |

---

*See also: [Installation Guide](../guides/installation.md), [Troubleshooting](../guides/troubleshooting.md)*
