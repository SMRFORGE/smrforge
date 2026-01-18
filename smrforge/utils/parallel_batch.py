"""
Parallel batch processing utilities for parameter sweeps.

This module provides utilities for automatically parallelizing batch calculations,
improving efficiency for parameter sweeps and design studies.
"""

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
from typing import Callable, List, Optional, Protocol, TypeVar, Union

from ..utils.logging import get_logger

logger = get_logger("smrforge.utils.parallel_batch")

T = TypeVar("T")
R = TypeVar("R")


class ReactorLike(Protocol):
    """
    Protocol for reactor-like objects that have a solve_keff() method.
    
    Used for duck typing - any object with a solve_keff() method that returns
    a float can be used with batch_solve_keff().
    """
    
    def solve_keff(self) -> float:
        """Solve for k-effective eigenvalue."""
        ...


def batch_process(
    items: List[T],
    func: Callable[[T], R],
    parallel: bool = True,
    max_workers: Optional[int] = None,
    use_threads: bool = False,
    show_progress: bool = False,
) -> List[R]:
    """
    Process items in parallel with automatic parallelization.
    
    Automatically parallelizes batch calculations for faster execution.
    Uses ProcessPoolExecutor by default (better for CPU-bound tasks) or
    ThreadPoolExecutor for I/O-bound tasks.
    
    Args:
        items: List of items to process
        func: Function to apply to each item (must be picklable if using processes)
        parallel: Enable parallel processing (default: True)
        max_workers: Maximum number of workers (default: CPU count)
        use_threads: Use ThreadPoolExecutor instead of ProcessPoolExecutor (for I/O-bound)
        show_progress: Show progress bar if Rich is available
    
    Returns:
        List of results in same order as items
    
    Raises:
        RuntimeError: If parallel processing fails (errors are logged, not raised by default).
        PicklingError: If func or items are not picklable when using ProcessPoolExecutor.
    
    Examples:
        >>> from smrforge.utils.parallel_batch import batch_process
        >>> 
        >>> # Parallel k-eff calculations
        >>> enrichments = [0.15, 0.17, 0.19, 0.21]
        >>> reactors = [create_reactor(enrichment=e) for e in enrichments]
        >>> 
        >>> k_effs = batch_process(
        ...     reactors,
        ...     lambda r: r.solve_keff(),
        ...     parallel=True,
        ...     max_workers=4
        ... )
        >>> 
        >>> print(k_effs)  # [1.023, 1.045, 1.067, 1.089]
    """
    if not items:
        return []
    
    # Serial execution if disabled or single item
    if not parallel or len(items) == 1:
        logger.debug(f"Processing {len(items)} items serially")
        return [func(item) for item in items]
    
    # Determine number of workers
    if max_workers is None:
        max_workers = cpu_count()
    
    # Limit workers to number of items
    max_workers = min(max_workers, len(items))
    
    logger.info(f"Processing {len(items)} items in parallel with {max_workers} workers")
    
    # Use threads or processes
    executor_class = ThreadPoolExecutor if use_threads else ProcessPoolExecutor
    
    # Try to import Rich for progress bars
    try:
        from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
        
        _RICH_AVAILABLE = True
    except ImportError:
        _RICH_AVAILABLE = False
    
    # Execute in parallel
    if _RICH_AVAILABLE and show_progress:
        with executor_class(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {executor.submit(func, item): item for item in items}
            
            # Track progress
            results = [None] * len(items)
            item_to_index = {item: i for i, item in enumerate(items)}
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            ) as progress:
                task = progress.add_task("Processing...", total=len(items))
                
                for future in as_completed(futures):
                    item = futures[future]
                    try:
                        result = future.result()
                        idx = item_to_index[item]
                        results[idx] = result
                        progress.update(task, advance=1)
                    except Exception as e:
                        logger.error(f"Error processing item {item}: {e}")
                        idx = item_to_index[item]
                        results[idx] = e  # Store error for now
    
    else:
        with executor_class(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {executor.submit(func, item): item for item in items}
            
            # Collect results in order
            results = [None] * len(items)
            item_to_index = {item: i for i, item in enumerate(items)}
            
            for future in as_completed(futures):
                item = futures[future]
                try:
                    result = future.result()
                    idx = item_to_index[item]
                    results[idx] = result
                except Exception as e:
                    logger.error(f"Error processing item {item}: {e}")
                    idx = item_to_index[item]
                    results[idx] = e  # Store error for now
    
    # Check for errors
    errors = [r for r in results if isinstance(r, Exception)]
    if errors:
        logger.warning(f"{len(errors)} errors occurred during batch processing")
        # Raise first error or return results with errors
        # For now, return results and let user handle errors
    
    return results


def batch_solve_keff(
    reactors: List[ReactorLike],
    parallel: bool = True,
    max_workers: Optional[int] = None,
    show_progress: bool = True,
) -> List[float]:
    """
    Batch solve k-eff for multiple reactors in parallel.
    
    Convenience function for parallel k-eff calculations.
    
    Args:
        reactors: List of reactor objects (must have solve_keff() method)
        parallel: Enable parallel processing (default: True)
        max_workers: Maximum number of workers (default: CPU count)
        show_progress: Show progress bar (default: True)
    
    Returns:
        List of k-eff values in same order as reactors
    
    Raises:
        AttributeError: If reactor objects don't have solve_keff() method.
        RuntimeError: If parallel processing fails.
    
    Example:
        >>> from smrforge.utils.parallel_batch import batch_solve_keff
        >>> 
        >>> # Create reactors with different enrichments
        >>> reactors = [
        ...     create_reactor(enrichment=e)
        ...     for e in [0.15, 0.17, 0.19, 0.21]
        ... ]
        >>> 
        >>> # Solve in parallel
        >>> k_effs = batch_solve_keff(reactors, parallel=True)
        >>> 
        >>> # Plot enrichment vs k-eff
        >>> import matplotlib.pyplot as plt
        >>> plt.plot([0.15, 0.17, 0.19, 0.21], k_effs)
        >>> plt.xlabel("Enrichment")
        >>> plt.ylabel("k-eff")
    """
    return batch_process(
        items=reactors,
        func=lambda r: r.solve_keff(),
        parallel=parallel,
        max_workers=max_workers,
        show_progress=show_progress,
    )
