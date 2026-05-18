"""
API Client Module - Backend Communication Layer

This module provides a centralized API client for communicating with the FastAPI
backend. It implements error handling, retry logic, timeout management, and
consistent error handling across all API methods.

Requirements: 11.1, 11.2, 11.8, 10.2, 10.3
"""

import time
from typing import Optional, Dict, List, Any, Callable
from functools import wraps
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import streamlit as st


def safe_api_call(func: Callable) -> Callable:
    """
    Decorator for consistent error handling across all API methods.
    
    Catches common exceptions and returns None on failure, allowing
    the caller to handle errors gracefully.
    
    Args:
        func: API method to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Optional[Any]:
        try:
            return func(*args, **kwargs)
        except requests.ConnectionError as e:
            # Backend unreachable
            print(f"❌ Connection error: Cannot reach backend at {args[0].backend_url if args else 'unknown'}")
            return None
        except requests.Timeout as e:
            # Request timed out
            print(f"⏱️ Timeout error: Request took longer than {args[0].timeout if args else 'unknown'}s")
            return None
        except requests.HTTPError as e:
            # HTTP error response (4xx, 5xx)
            if e.response:
                status_code = e.response.status_code
                if status_code >= 500:
                    print(f"🔥 Server error ({status_code}): Backend encountered an error")
                elif status_code == 404:
                    print(f"🔍 Not found ({status_code}): Resource not found")
                elif status_code == 429:
                    print(f"⏸️ Rate limited ({status_code}): Too many requests")
                else:
                    print(f"❌ HTTP error ({status_code}): {e.response.text}")
            else:
                print(f"❌ HTTP error: {str(e)}")
            return None
        except Exception as e:
            # Unexpected error
            print(f"⚠️ Unexpected error: {str(e)}")
            return None
    return wrapper


class APIClient:
    """
    Centralized API client for backend communication.
    
    Provides methods for all backend endpoints with built-in error handling,
    retry logic, and timeout management.
    
    Attributes:
        backend_url: Base URL of the backend API
        timeout: Request timeout in seconds
        session: Requests session with retry configuration
    """
    
    def __init__(self, backend_url: str, timeout: int = 10, max_retries: int = 3):
        """
        Initialize API client with backend URL and configuration.
        
        Args:
            backend_url: Base URL of the backend API (e.g., "http://localhost:8000/api/v1")
            timeout: Request timeout in seconds (default: 10)
            max_retries: Maximum number of retry attempts for failed requests (default: 3)
        """
        self.backend_url = backend_url.rstrip("/")
        self.timeout = timeout
        
        # Configure session with retry logic
        self.session = requests.Session()
        
        # Retry strategy: retry on connection errors and 5xx server errors
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,  # Wait 1s, 2s, 4s between retries
            status_forcelist=[500, 502, 503, 504],  # Retry on server errors
            allowed_methods=["GET", "POST"],  # Retry safe methods
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request with error handling, retry logic, and timeout.
        
        This is the core request method used by all other API methods.
        It handles common errors and returns None on failure.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path (e.g., "/health", "/status/job123")
            **kwargs: Additional arguments passed to requests (json, params, headers, etc.)
            
        Returns:
            Response JSON as dictionary, or None on error
        """
        url = f"{self.backend_url}{path}"
        
        # Set default timeout if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()  # Raise HTTPError for bad status codes
            
            # Return JSON response if available
            try:
                return response.json()
            except ValueError:
                # Response is not JSON (e.g., empty response)
                return {"success": True}
                
        except requests.RequestException:
            # Re-raise to be caught by @safe_api_call decorator
            raise
    
    @safe_api_call
    def submit_job(self, brief: str) -> Optional[Dict[str, Any]]:
        """
        Submit new analysis job to the backend.
        
        Args:
            brief: Business brief text (will be used for all required fields)
            
        Returns:
            Job response with job_id and status, or None on error
            
        Example:
            >>> client = APIClient("http://localhost:8000/api/v1")
            >>> result = client.submit_job("Analyze market for AI meeting tools")
            >>> if result:
            ...     print(f"Job submitted: {result['job_id']}")
        """
        payload = {
            "company_description": brief[:2000],
            "product_details": brief[:2000],
            "target_audience": "Infer the target audience from the business brief.",
            "goals": "Infer the business goals from the brief and produce practical milestones.",
            "constraints": "Infer constraints from the business brief. If none are stated, call that out.",
        }
        return self.request("POST", "/analyze", json=payload)
    
    @safe_api_call
    @st.cache_data(ttl=5, show_spinner=False)
    def get_job_status(_self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch job status and final report.
        
        Cached for 5 seconds to reduce API calls during active monitoring.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            Job status with fields:
                - job_id: str
                - status: str (pending, running, completed, failed, aborted)
                - created_at: str (ISO timestamp)
                - final_report: dict (if completed)
                - total_tokens_used: int
                - total_cost_usd: float
            Or None on error
            
        Example:
            >>> status = client.get_job_status("job123")
            >>> if status and status['status'] == 'completed':
            ...     print("Job finished!")
        """
        return _self.request("GET", f"/status/{job_id}")
    
    @safe_api_call
    @st.cache_data(ttl=5, show_spinner=False)
    def get_agent_tasks(_self, job_id: str) -> List[Dict[str, Any]]:
        """
        Fetch agent execution timeline for a job.
        
        Cached for 5 seconds to reduce API calls during active monitoring.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            List of agent task dictionaries with fields:
                - agent: str (agent role name)
                - status: str (queued, running, completed, failed)
                - started_at: str (ISO timestamp)
                - completed_at: str (ISO timestamp, if completed)
                - model_used: str (LLM model identifier)
                - tokens_used: int
                - execution_time_ms: int
                - error_message: str (if failed)
            Or empty list on error
            
        Example:
            >>> tasks = client.get_agent_tasks("job123")
            >>> for task in tasks:
            ...     print(f"{task['agent']}: {task['status']}")
        """
        result = _self.request("GET", f"/agents/{job_id}")
        return result if result is not None else []
    
    @safe_api_call
    def get_logs(self, job_id: str) -> List[Dict[str, Any]]:
        """
        Fetch workflow logs for a job.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            List of log entry dictionaries with fields:
                - agent: str (agent role or 'system')
                - level: str (INFO, WARN, ERROR)
                - event_type: str (event category)
                - message: str (log message)
                - details: dict (structured data)
                - timestamp: str (ISO timestamp)
            Or empty list on error
            
        Example:
            >>> logs = client.get_logs("job123")
            >>> for log in logs:
            ...     print(f"[{log['level']}] {log['message']}")
        """
        result = self.request("GET", f"/logs/{job_id}")
        return result if result is not None else []
    
    @safe_api_call
    def cancel_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Request job cancellation.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            Cancellation response with job_id and status, or None on error
            
        Example:
            >>> result = client.cancel_job("job123")
            >>> if result:
            ...     print(f"Job {result['job_id']} cancelled")
        """
        return self.request("POST", f"/cancel/{job_id}")
    
    @safe_api_call
    @st.cache_data(ttl=30, show_spinner=False)
    def list_jobs(_self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch recent jobs for dashboard.
        
        Cached for 30 seconds to reduce load on dashboard page.
        
        Args:
            limit: Maximum number of jobs to return (default: 20)
            
        Returns:
            List of job summary dictionaries with fields:
                - job_id: str
                - status: str
                - created_at: str (ISO timestamp)
                - completed_at: str (ISO timestamp, if completed)
                - company: str (truncated company description)
                - total_cost_usd: float
            Or empty list on error
            
        Example:
            >>> jobs = client.list_jobs(limit=10)
            >>> print(f"Found {len(jobs)} recent jobs")
        """
        result = _self.request("GET", "/jobs", params={"limit": limit})
        return result if result is not None else []
    
    @safe_api_call
    def health_check(self) -> bool:
        """
        Check backend availability and health.
        
        Returns:
            True if backend is healthy, False otherwise
            
        Example:
            >>> if client.health_check():
            ...     print("Backend is online")
            ... else:
            ...     print("Backend is offline")
        """
        result = self.request("GET", "/health")
        if result is None:
            return False
        
        # Check if status is healthy
        status = result.get("status", "unhealthy")
        return status == "healthy"
