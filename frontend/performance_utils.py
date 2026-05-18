"""
Performance Utilities Module

This module provides utilities for optimizing frontend performance, including
debouncing, throttling, lazy loading, and caching helpers.

Requirements: 10.1, 10.2, 10.8
"""

import time
from typing import Callable, Any, Optional, List, Dict
from functools import wraps
import streamlit as st


class Debouncer:
    """
    Debounce utility for delaying function execution until after a wait period.
    
    Useful for search inputs and other user interactions that should not
    trigger immediate updates.
    
    Example:
        >>> debouncer = Debouncer(delay=0.3)  # 300ms delay
        >>> debouncer.debounce(search_function, query)
    """
    
    def __init__(self, delay: float = 0.3):
        """
        Initialize debouncer with delay period.
        
        Args:
            delay: Delay in seconds before executing function (default: 0.3)
        """
        self.delay = delay
        self.last_call_time = 0
        self.last_args = None
        self.last_kwargs = None
    
    def debounce(self, func: Callable, *args, **kwargs) -> Optional[Any]:
        """
        Debounce function call - only execute if delay period has passed.
        
        Args:
            func: Function to debounce
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result if executed, None if debounced
        """
        current_time = time.time()
        
        # Store current call
        self.last_args = args
        self.last_kwargs = kwargs
        
        # Check if enough time has passed
        if current_time - self.last_call_time >= self.delay:
            self.last_call_time = current_time
            return func(*args, **kwargs)
        
        return None
    
    def should_execute(self) -> bool:
        """
        Check if enough time has passed to execute debounced function.
        
        Returns:
            True if delay period has passed, False otherwise
        """
        current_time = time.time()
        return current_time - self.last_call_time >= self.delay


class Throttler:
    """
    Throttle utility for limiting function execution rate.
    
    Useful for log updates and other high-frequency events that should
    be rate-limited.
    
    Example:
        >>> throttler = Throttler(rate=10)  # Max 10 calls per second
        >>> throttler.throttle(update_logs, new_logs)
    """
    
    def __init__(self, rate: int = 10):
        """
        Initialize throttler with maximum rate.
        
        Args:
            rate: Maximum calls per second (default: 10)
        """
        self.rate = rate
        self.min_interval = 1.0 / rate
        self.last_call_time = 0
        self.call_count = 0
    
    def throttle(self, func: Callable, *args, **kwargs) -> Optional[Any]:
        """
        Throttle function call - only execute if rate limit not exceeded.
        
        Args:
            func: Function to throttle
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result if executed, None if throttled
        """
        current_time = time.time()
        
        # Check if enough time has passed
        if current_time - self.last_call_time >= self.min_interval:
            self.last_call_time = current_time
            self.call_count += 1
            return func(*args, **kwargs)
        
        return None
    
    def should_execute(self) -> bool:
        """
        Check if rate limit allows execution.
        
        Returns:
            True if execution allowed, False if throttled
        """
        current_time = time.time()
        return current_time - self.last_call_time >= self.min_interval
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get throttler statistics.
        
        Returns:
            Dictionary with call_count and rate information
        """
        return {
            'call_count': self.call_count,
            'rate': self.rate,
            'min_interval': self.min_interval
        }


class LazyLoader:
    """
    Lazy loading utility for loading data in chunks.
    
    Useful for large log lists and other data that should be loaded
    incrementally.
    
    Example:
        >>> loader = LazyLoader(all_logs, chunk_size=50)
        >>> first_chunk = loader.load_next()
        >>> second_chunk = loader.load_next()
    """
    
    def __init__(self, data: List[Any], chunk_size: int = 50):
        """
        Initialize lazy loader with data and chunk size.
        
        Args:
            data: Full data list to load lazily
            chunk_size: Number of items to load per chunk (default: 50)
        """
        self.data = data
        self.chunk_size = chunk_size
        self.current_index = 0
        self.total_items = len(data)
    
    def load_next(self) -> List[Any]:
        """
        Load next chunk of data.
        
        Returns:
            List of items in next chunk (may be smaller than chunk_size at end)
        """
        if self.current_index >= self.total_items:
            return []
        
        end_index = min(self.current_index + self.chunk_size, self.total_items)
        chunk = self.data[self.current_index:end_index]
        self.current_index = end_index
        
        return chunk
    
    def load_all_remaining(self) -> List[Any]:
        """
        Load all remaining data.
        
        Returns:
            List of all remaining items
        """
        remaining = self.data[self.current_index:]
        self.current_index = self.total_items
        return remaining
    
    def has_more(self) -> bool:
        """
        Check if more data is available to load.
        
        Returns:
            True if more data available, False otherwise
        """
        return self.current_index < self.total_items
    
    def reset(self):
        """Reset loader to beginning."""
        self.current_index = 0
    
    def get_progress(self) -> Dict[str, Any]:
        """
        Get loading progress information.
        
        Returns:
            Dictionary with current_index, total_items, and percentage
        """
        percentage = (self.current_index / self.total_items * 100) if self.total_items > 0 else 0
        
        return {
            'current_index': self.current_index,
            'total_items': self.total_items,
            'percentage': round(percentage, 1),
            'has_more': self.has_more()
        }


def debounce_search(search_query: str, delay: float = 0.3) -> bool:
    """
    Debounce search input using Streamlit session state.
    
    This function uses session state to track the last search query and
    timestamp, only returning True if enough time has passed since the
    last change.
    
    Args:
        search_query: Current search query string
        delay: Delay in seconds before executing search (default: 0.3)
        
    Returns:
        True if search should execute, False if debounced
        
    Example:
        >>> query = st.text_input("Search")
        >>> if debounce_search(query):
        ...     results = perform_search(query)
    """
    # Initialize session state
    if 'last_search_query' not in st.session_state:
        st.session_state['last_search_query'] = ''
    if 'last_search_time' not in st.session_state:
        st.session_state['last_search_time'] = 0
    
    current_time = time.time()
    
    # Check if query changed
    if search_query != st.session_state['last_search_query']:
        st.session_state['last_search_query'] = search_query
        st.session_state['last_search_time'] = current_time
        return False  # Don't execute yet, wait for delay
    
    # Check if enough time has passed
    time_since_last_change = current_time - st.session_state['last_search_time']
    
    if time_since_last_change >= delay:
        return True  # Execute search
    
    return False  # Still waiting


def throttle_updates(update_key: str, rate: int = 10) -> bool:
    """
    Throttle updates using Streamlit session state.
    
    This function uses session state to track update timestamps and
    enforce a maximum update rate.
    
    Args:
        update_key: Unique key for this update stream (e.g., 'log_updates')
        rate: Maximum updates per second (default: 10)
        
    Returns:
        True if update should execute, False if throttled
        
    Example:
        >>> if throttle_updates('log_updates', rate=10):
        ...     update_log_panel(new_logs)
    """
    # Initialize session state
    state_key = f'throttle_{update_key}_last_time'
    if state_key not in st.session_state:
        st.session_state[state_key] = 0
    
    current_time = time.time()
    min_interval = 1.0 / rate
    
    # Check if enough time has passed
    time_since_last_update = current_time - st.session_state[state_key]
    
    if time_since_last_update >= min_interval:
        st.session_state[state_key] = current_time
        return True  # Execute update
    
    return False  # Throttled


def lazy_load_logs(all_logs: List[Dict], chunk_size: int = 50) -> List[Dict]:
    """
    Lazy load logs using Streamlit session state.
    
    This function manages lazy loading state and returns the appropriate
    chunk of logs to display.
    
    Args:
        all_logs: Full list of log entries
        chunk_size: Number of logs to load per chunk (default: 50)
        
    Returns:
        List of logs to display (initial chunk or all if "Load More" clicked)
        
    Example:
        >>> all_logs = get_all_logs(job_id)
        >>> visible_logs = lazy_load_logs(all_logs, chunk_size=50)
        >>> render_log_panel(visible_logs)
    """
    # Initialize session state
    if 'logs_loaded_count' not in st.session_state:
        st.session_state['logs_loaded_count'] = chunk_size
    
    # Get current loaded count
    loaded_count = st.session_state['logs_loaded_count']
    
    # Return visible logs
    visible_logs = all_logs[:loaded_count]
    
    return visible_logs


def load_more_logs(increment: int = 50):
    """
    Increment the number of loaded logs.
    
    Call this function when user clicks "Load More" button.
    
    Args:
        increment: Number of additional logs to load (default: 50)
        
    Example:
        >>> if st.button("Load More Logs"):
        ...     load_more_logs(increment=50)
        ...     st.rerun()
    """
    if 'logs_loaded_count' not in st.session_state:
        st.session_state['logs_loaded_count'] = increment
    else:
        st.session_state['logs_loaded_count'] += increment


def reset_lazy_loading():
    """
    Reset lazy loading state.
    
    Call this function when switching to a different job or resetting view.
    """
    if 'logs_loaded_count' in st.session_state:
        del st.session_state['logs_loaded_count']


# Performance monitoring utilities

def measure_render_time(func: Callable) -> Callable:
    """
    Decorator to measure and log render time of a function.
    
    Useful for identifying performance bottlenecks.
    
    Args:
        func: Function to measure
        
    Returns:
        Wrapped function that logs execution time
        
    Example:
        >>> @measure_render_time
        ... def render_timeline(tasks):
        ...     # Render logic
        ...     pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        elapsed = (end_time - start_time) * 1000  # Convert to ms
        
        # Log to console (not visible to user)
        print(f"⏱️ {func.__name__} took {elapsed:.2f}ms")
        
        return result
    
    return wrapper


if __name__ == "__main__":
    # Test debouncer
    print("Testing Debouncer:")
    debouncer = Debouncer(delay=0.3)
    
    def search(query):
        print(f"  Searching for: {query}")
        return f"Results for {query}"
    
    # Rapid calls - should only execute last one after delay
    debouncer.debounce(search, "a")
    time.sleep(0.1)
    debouncer.debounce(search, "ab")
    time.sleep(0.1)
    debouncer.debounce(search, "abc")
    time.sleep(0.4)  # Wait for delay
    result = debouncer.debounce(search, "abc")
    print(f"  Result: {result}\n")
    
    # Test throttler
    print("Testing Throttler:")
    throttler = Throttler(rate=5)  # Max 5 calls per second
    
    def update_logs(log):
        print(f"  Updating logs: {log}")
    
    # Rapid calls - should throttle
    for i in range(10):
        result = throttler.throttle(update_logs, f"Log {i}")
        if result is None:
            print(f"  Log {i} throttled")
        time.sleep(0.05)  # 50ms between calls
    
    print(f"  Stats: {throttler.get_stats()}\n")
    
    # Test lazy loader
    print("Testing LazyLoader:")
    all_data = list(range(100))
    loader = LazyLoader(all_data, chunk_size=20)
    
    chunk_num = 1
    while loader.has_more():
        chunk = loader.load_next()
        print(f"  Chunk {chunk_num}: {len(chunk)} items (indices {chunk[0]}-{chunk[-1]})")
        progress = loader.get_progress()
        print(f"  Progress: {progress['percentage']}%")
        chunk_num += 1
