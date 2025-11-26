"""
Parallel processing utilities for the job scraper.

Supports both threading (I/O-bound) and multiprocessing (CPU-bound) operations.
"""

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import logging
import time
from typing import Callable, List, Any, Optional
from utils.concurrency_config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


def parallel_fetch(
    fetch_function: Callable,
    items: List[Any],
    max_workers: int = None,
    description: str = "items",
    use_processes: bool = False,
    retry_count: int = None
) -> List[Any]:
    """
    Execute a fetch function in parallel for a list of items.
    
    Args:
        fetch_function: Function that takes an item and returns a result
        items: List of items to process
        max_workers: Maximum number of parallel workers (default from config)
        description: Description for logging
        use_processes: If True, use ProcessPoolExecutor instead of ThreadPoolExecutor
        retry_count: Number of retries for failed items (default from config)
        
    Returns:
        List of results (excluding None values from failed fetches)
    """
    if max_workers is None:
        max_workers = DEFAULT_CONFIG.process_workers if use_processes else DEFAULT_CONFIG.thread_workers
    
    if retry_count is None:
        retry_count = DEFAULT_CONFIG.max_retries
    
    results = []
    total = len(items)
    
    if total == 0:
        return results
    
    executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
    executor_name = "processes" if use_processes else "threads"
    
    logger.info(f"Processing {total} {description} using {max_workers} {executor_name}")
    
    with executor_class(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_item = {executor.submit(fetch_function, item): item for item in items}
        
        # Process completed tasks
        completed = 0
        failed_items = []
        
        for future in as_completed(future_to_item):
            completed += 1
            item = future_to_item[future]
            
            try:
                result = future.result()
                if result:
                    results.append(result)
                    logger.info(f"✓ Processed {completed}/{total} {description}")
                else:
                    logger.debug(f"✗ No result for {description} {completed}/{total}")
            except Exception as e:
                logger.error(f"✗ Error processing {description} {item}: {e}")
                failed_items.append(item)
    
    # Retry failed items if retry_count > 0
    if failed_items and retry_count > 0:
        logger.info(f"Retrying {len(failed_items)} failed {description}...")
        retry_results = parallel_fetch(
            fetch_function,
            failed_items,
            max_workers=max_workers,
            description=f"{description} (retry)",
            use_processes=use_processes,
            retry_count=retry_count - 1
        )
        results.extend(retry_results)
    
    logger.info(f"Completed processing {total} {description}: {len(results)} successful")
    return results


def parallel_fetch_with_retry(
    fetch_function: Callable,
    items: List[Any],
    max_workers: int = None,
    description: str = "items",
    max_retries: int = None
) -> List[Any]:
    """
    Execute a fetch function in parallel with automatic retry on failure.
    
    This is a convenience wrapper around parallel_fetch with retry enabled.
    
    Args:
        fetch_function: Function that takes an item and returns a result
        items: List of items to process
        max_workers: Maximum number of parallel workers
        description: Description for logging
        max_retries: Maximum number of retries per item
        
    Returns:
        List of results (excluding None values from failed fetches)
    """
    return parallel_fetch(
        fetch_function,
        items,
        max_workers=max_workers,
        description=description,
        use_processes=False,
        retry_count=max_retries
    )


def batch_process(
    items: List[Any],
    batch_size: int,
    process_function: Callable[[List[Any]], List[Any]]
) -> List[Any]:
    """
    Process items in batches.
    
    Useful for operations that benefit from batching (e.g., database inserts).
    
    Args:
        items: List of items to process
        batch_size: Number of items per batch
        process_function: Function that processes a batch and returns results
        
    Returns:
        Combined results from all batches
    """
    results = []
    total_batches = (len(items) + batch_size - 1) // batch_size
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_num = i // batch_size + 1
        
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)")
        
        try:
            batch_results = process_function(batch)
            results.extend(batch_results)
        except Exception as e:
            logger.error(f"Error processing batch {batch_num}: {e}")
    
    return results

