"""
MPI-distributed batch processing for multi-node parallel runs.

When running under `mpirun` or `mpiexec`, distributes work across MPI ranks
and gathers results. Falls back to serial when MPI not available or size=1.

Example:
    mpirun -np 8 python -c "
        from smrforge.utils.mpi_batch import mpi_batch_process
        items = list(range(100))
        results = mpi_batch_process(items, lambda x: x**2)
    "
"""

from typing import Callable, List, Optional, TypeVar

from ..utils.logging import get_logger

logger = get_logger("smrforge.utils.mpi_batch")

T = TypeVar("T")
R = TypeVar("R")

_MPI_AVAILABLE = False
_MPI_COMM = None
_MPI_SUM = None

try:
    from mpi4py import MPI

    _MPI_AVAILABLE = True
    _MPI_COMM = MPI.COMM_WORLD
    _MPI_SUM = MPI.SUM
except ImportError:
    pass


def mpi_available() -> bool:
    """Check if MPI is available and size > 1."""
    if not _MPI_AVAILABLE or _MPI_COMM is None:
        return False
    return _MPI_COMM.Get_size() > 1


def mpi_rank() -> int:
    """MPI rank (0 if not running under MPI)."""
    if _MPI_COMM is None:
        return 0
    return _MPI_COMM.Get_rank()


def mpi_size() -> int:
    """MPI size (1 if not running under MPI)."""
    if _MPI_COMM is None:
        return 1
    return _MPI_COMM.Get_size()


def mpi_batch_process(
    items: List[T],
    func: Callable[[T], R],
    use_mpi: bool = True,
) -> List[R]:
    """
    Process items in parallel across MPI ranks.

    When use_mpi=True and MPI size > 1:
    - Partitions items across ranks (contiguous blocks)
    - Each rank processes its local items
    - Root gathers results in order

    When MPI unavailable or size=1: runs serially on rank 0.

    Args:
        items: List of items to process
        func: Function to apply (must be picklable for MPI)
        use_mpi: If False, only rank 0 runs; others return empty

    Returns:
        List of results in same order as items (gathered on rank 0)
    """
    if not items:
        return []

    if not use_mpi or not mpi_available():
        return [func(item) for item in items]

    rank = mpi_rank()
    size = mpi_size()
    n = len(items)

    # Partition: rank k gets items [start:end]
    chunk = (n + size - 1) // size
    start = rank * chunk
    end = min(start + chunk, n)
    local_items = items[start:end]

    # Local computation
    local_results = [func(item) for item in local_items]

    # Gather to root
    if size > 1:
        all_results = _MPI_COMM.gather(local_results, root=0)
        if rank == 0:
            # Flatten in order
            return [r for chunk_res in all_results for r in chunk_res]
        return []

    return local_results


def mpi_broadcast(obj: T, root: int = 0) -> Optional[T]:
    """Broadcast object from root to all ranks. Returns None on non-root if not in-place."""
    if _MPI_COMM is None:
        return obj
    return _MPI_COMM.bcast(obj, root=root)


def mpi_reduce_sum(value: float, root: int = 0) -> float:
    """Sum value across all ranks, return result on root."""
    if _MPI_COMM is None or _MPI_SUM is None:
        return value
    total = _MPI_COMM.allreduce(value, op=_MPI_SUM)
    return total
