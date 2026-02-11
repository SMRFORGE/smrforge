"""
Parallel batch processing utilities for parameter sweeps.

This module provides utilities for automatically parallelizing batch calculations,
improving efficiency for parameter sweeps and design studies.
"""

import os
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
from typing import Callable, List, Optional, Protocol, TypeVar, Union

from ..utils.logging import get_logger

# Try to import executor lock for test isolation (optional)
try:
    from tests.parallel_executor_lock import get_executor_lock

    _EXECUTOR_LOCK_AVAILABLE = True
except ImportError:
    _EXECUTOR_LOCK_AVAILABLE = False
    get_executor_lock = None

# On Windows, prefer threads over processes to avoid pickling issues
# and reduce resource contention
_IS_WINDOWS = sys.platform == "win32"

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


def _resolve_max_workers(max_workers: Optional[int]) -> int:
    """Resolve max_workers: env SMRFORGE_MAX_BATCH_WORKERS, then cpu_count, then cap."""
    if max_workers is not None:
        return max(1, int(max_workers))
    env_max = os.environ.get("SMRFORGE_MAX_BATCH_WORKERS")
    if env_max is not None:
        try:
            return max(1, int(env_max))
        except ValueError:
            pass
    return cpu_count()


def batch_process(
    items: List[T],
    func: Callable[[T], R],
    parallel: bool = True,
    max_workers: Optional[int] = None,
    use_threads: bool = False,
    show_progress: bool = False,
    timeout: Optional[float] = 60.0,
    per_future_timeout: Optional[float] = 60.0,
    raise_on_failure: bool = False,
) -> List[Union[R, Exception]]:
    """
    Process items in parallel with automatic parallelization.

    Automatically parallelizes batch calculations for faster execution.
    Uses ProcessPoolExecutor by default (better for CPU-bound tasks) or
    ThreadPoolExecutor for I/O-bound tasks.

    Args:
        items: List of items to process
        func: Function to apply to each item (must be picklable if using processes)
        parallel: Enable parallel processing (default: True)
        max_workers: Maximum number of workers (default: CPU count, or SMRFORGE_MAX_BATCH_WORKERS)
        use_threads: Use ThreadPoolExecutor instead of ProcessPoolExecutor (for I/O-bound)
        show_progress: Show progress bar if Rich is available
        timeout: Total timeout in seconds for the batch (None = no limit). Default 60.
        per_future_timeout: Timeout in seconds per future.result() (None = wait indefinitely). Default 60.
        raise_on_failure: If True, raise the first exception encountered; otherwise return it in the list.

    Returns:
        List of results in same order as items (failed items may be Exception instances unless raise_on_failure).

    Raises:
        RuntimeError: If parallel processing fails (errors are logged, not raised by default).
        PicklingError: If func or items are not picklable when using ProcessPoolExecutor.
        Exception: If raise_on_failure is True and any item raises.

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

    # Determine number of workers (env SMRFORGE_MAX_BATCH_WORKERS can cap)
    max_workers = _resolve_max_workers(max_workers)
    # Limit workers to number of items and ensure at least 1
    max_workers = max(1, min(max_workers, len(items)))

    logger.info(f"Processing {len(items)} items in parallel with {max_workers} workers")

    # Use threads or processes
    # On Windows, default to threads to avoid pickling issues and reduce resource contention
    if not use_threads and _IS_WINDOWS:
        logger.debug(
            "Windows detected: defaulting to ThreadPoolExecutor instead of ProcessPoolExecutor"
        )
        executor_class = ThreadPoolExecutor
    else:
        executor_class = ThreadPoolExecutor if use_threads else ProcessPoolExecutor

    # Try to import Rich for progress bars
    try:
        from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

        _RICH_AVAILABLE = True
    except ImportError:
        _RICH_AVAILABLE = False

    # Execute in parallel
    # Use lock if available (for test isolation)
    executor_lock = get_executor_lock() if _EXECUTOR_LOCK_AVAILABLE else None

    if _RICH_AVAILABLE and show_progress:
        # Use lock if available to limit concurrent executors
        lock_context = (
            executor_lock
            if executor_lock
            else type(
                "DummyContext",
                (),
                {"__enter__": lambda self: self, "__exit__": lambda *args: None},
            )()
        )
        with lock_context:
            with executor_class(max_workers=max_workers) as executor:
                # Submit all tasks and track by index (handles unhashable items)
                futures = {}
                for i, item in enumerate(items):
                    future = executor.submit(func, item)
                    futures[future] = i  # Store index instead of item

                # Track progress
                results = [None] * len(items)

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                ) as progress:
                    task = progress.add_task("Processing...", total=len(items))

                    # Process all futures - ensure we get all results before shutdown
                    completed_count = 0
                    import time

                    start_time = time.time()
                    batch_timeout = timeout
                    future_timeout = per_future_timeout

                    for future in as_completed(futures, timeout=batch_timeout):
                        if (
                            batch_timeout is not None
                            and (time.time() - start_time) > batch_timeout
                        ):
                            logger.warning(
                                "Timeout waiting for futures, cancelling remaining"
                            )
                            break
                        idx = futures[future]  # Get index directly
                        item = items[idx]  # Get item for logging
                        try:
                            result = future.result(timeout=future_timeout)
                            results[idx] = result
                            progress.update(task, advance=1)
                            completed_count += 1
                        except Exception as e:
                            logger.error(f"Error processing item {item}: {e}")
                            results[idx] = e  # Store error for now
                            completed_count += 1
                            if raise_on_failure:
                                for f in futures:
                                    if not f.done():
                                        f.cancel()
                                raise

                    # Cancel any remaining futures
                    for future in futures:
                        if not future.done():
                            future.cancel()

                    # Verify all futures completed
                    if completed_count < len(items):
                        logger.warning(
                            f"Only {completed_count}/{len(items)} futures completed"
                        )
                # Context manager ensures executor.shutdown() is called automatically

    else:
        # Use lock if available to limit concurrent executors
        lock_context = (
            executor_lock
            if executor_lock
            else type(
                "DummyContext",
                (),
                {"__enter__": lambda self: self, "__exit__": lambda *args: None},
            )()
        )
        with lock_context:
            with executor_class(max_workers=max_workers) as executor:
                # Submit all tasks and track by index (handles unhashable items)
                futures = {}
                for i, item in enumerate(items):
                    future = executor.submit(func, item)
                    futures[future] = i  # Store index instead of item

                # Collect results in order
                results = [None] * len(items)

                # Process all futures - ensure we get all results before shutdown
                completed_count = 0
                import time

                start_time = time.time()
                batch_timeout = timeout
                future_timeout = per_future_timeout

                try:
                    for future in as_completed(futures, timeout=batch_timeout):
                        if (
                            batch_timeout is not None
                            and (time.time() - start_time) > batch_timeout
                        ):
                            logger.warning(
                                "Timeout waiting for futures, cancelling remaining"
                            )
                            break
                        idx = futures[future]  # Get index directly
                        item = items[idx]  # Get item for logging
                        try:
                            result = future.result(timeout=future_timeout)
                            results[idx] = result
                            completed_count += 1
                        except Exception as e:
                            logger.error(f"Error processing item {item}: {e}")
                            results[idx] = e  # Store error for now
                            completed_count += 1
                            if raise_on_failure:
                                for f in futures:
                                    if not f.done():
                                        f.cancel()
                                raise
                except Exception as e:
                    logger.warning(
                        f"Error in as_completed: {e}, cancelling remaining futures"
                    )

                # Cancel any remaining futures
                for future in futures:
                    if not future.done():
                        future.cancel()

                # Verify all futures completed
                if completed_count < len(items):
                    logger.warning(
                        f"Only {completed_count}/{len(items)} futures completed"
                    )
                # Context manager ensures executor.shutdown() is called automatically

    # Check for errors
    errors = [r for r in results if isinstance(r, Exception)]
    if errors:
        logger.warning(f"{len(errors)} errors occurred during batch processing")
        if raise_on_failure:
            raise errors[0]

    return results


def batch_solve_keff(
    reactors: List[ReactorLike],
    parallel: bool = True,
    max_workers: Optional[int] = None,
    show_progress: bool = True,
    timeout: Optional[float] = 60.0,
    per_future_timeout: Optional[float] = 60.0,
    raise_on_failure: bool = False,
) -> List[Union[float, Exception]]:
    """
    Batch solve k-eff for multiple reactors in parallel.

    Convenience function for parallel k-eff calculations.

    Args:
        reactors: List of reactor objects (must have solve_keff() method)
        parallel: Enable parallel processing (default: True)
        max_workers: Maximum number of workers (default: CPU count or SMRFORGE_MAX_BATCH_WORKERS)
        show_progress: Show progress bar (default: True)
        timeout: Total batch timeout in seconds (None = no limit)
        per_future_timeout: Timeout per solve_keff() call in seconds (None = wait indefinitely)
        raise_on_failure: If True, raise on first failure; otherwise return exceptions in list

    Returns:
        List of k-eff values in same order as reactors (or Exception for failures)

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
        timeout=timeout,
        per_future_timeout=per_future_timeout,
        raise_on_failure=raise_on_failure,
    )
