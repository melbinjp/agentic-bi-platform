"""
Unit Tests for API Client Module

Tests the APIClient class and safe_api_call decorator with various
scenarios including successful requests, error handling, and retry logic.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from api_client import APIClient, safe_api_call
import streamlit as st


@pytest.fixture(autouse=True)
def clear_st_cache():
    """Clear Streamlit cache before each test to prevent test pollution."""
    st.cache_data.clear()


class TestSafeAPICallDecorator:
    """Test the @safe_api_call decorator for error handling."""
    
    def test_successful_call(self):
        """Test decorator allows successful calls to pass through."""
        @safe_api_call
        def mock_api_method():
            return {"success": True, "data": "test"}
        
        result = mock_api_method()
        assert result == {"success": True, "data": "test"}
    
    def test_connection_error_handling(self, capsys):
        """Test decorator catches ConnectionError and returns None."""
        @safe_api_call
        def mock_api_method(self):
            raise requests.ConnectionError("Cannot connect")
        
        mock_self = Mock()
        mock_self.backend_url = "http://localhost:8000"
        
        result = mock_api_method(mock_self)
        assert result is None
        
        captured = capsys.readouterr()
        assert "Connection error" in captured.out
    
    def test_timeout_error_handling(self, capsys):
        """Test decorator catches Timeout and returns None."""
        @safe_api_call
        def mock_api_method(self):
            raise requests.Timeout("Request timed out")
        
        mock_self = Mock()
        mock_self.timeout = 10
        
        result = mock_api_method(mock_self)
        assert result is None
        
        captured = capsys.readouterr()
        assert "Timeout error" in captured.out
    
    def test_http_error_500_handling(self, capsys):
        """Test decorator catches 5xx HTTP errors."""
        @safe_api_call
        def mock_api_method():
            response = Mock()
            response.status_code = 500
            response.text = "Internal server error"
            error = requests.HTTPError()
            error.response = response
            raise error
        
        result = mock_api_method()
        assert result is None
        
        captured = capsys.readouterr()
        assert "Server error" in captured.out
    
    def test_http_error_404_handling(self, capsys):
        """Test decorator catches 404 errors."""
        @safe_api_call
        def mock_api_method():
            response = Mock()
            response.status_code = 404
            response.text = "Not found"
            error = requests.HTTPError()
            error.response = response
            raise error
        
        result = mock_api_method()
        assert result is None
        
        captured = capsys.readouterr()
        assert "Not found" in captured.out
    
    def test_http_error_429_handling(self, capsys):
        """Test decorator catches rate limit errors."""
        @safe_api_call
        def mock_api_method():
            response = Mock()
            response.status_code = 429
            response.text = "Too many requests"
            error = requests.HTTPError()
            error.response = response
            raise error
        
        result = mock_api_method()
        assert result is None
        
        captured = capsys.readouterr()
        assert "Rate limited" in captured.out
    
    def test_unexpected_error_handling(self, capsys):
        """Test decorator catches unexpected exceptions."""
        @safe_api_call
        def mock_api_method():
            raise ValueError("Unexpected error")
        
        result = mock_api_method()
        assert result is None
        
        captured = capsys.readouterr()
        assert "Unexpected error" in captured.out


class TestAPIClientInitialization:
    """Test APIClient initialization and configuration."""
    
    def test_init_with_default_params(self):
        """Test client initialization with default parameters."""
        client = APIClient("http://localhost:8000/api/v1")
        
        assert client.backend_url == "http://localhost:8000/api/v1"
        assert client.timeout == 10
        assert client.session is not None
    
    def test_init_with_custom_timeout(self):
        """Test client initialization with custom timeout."""
        client = APIClient("http://localhost:8000", timeout=30)
        
        assert client.timeout == 30
    
    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is removed from backend URL."""
        client = APIClient("http://localhost:8000/api/v1/")
        
        assert client.backend_url == "http://localhost:8000/api/v1"
    
    def test_session_has_retry_adapter(self):
        """Test that session is configured with retry adapter."""
        client = APIClient("http://localhost:8000")
        
        # Check that adapters are mounted
        assert "http://" in client.session.adapters
        assert "https://" in client.session.adapters


class TestAPIClientRequestMethod:
    """Test the core request method."""
    
    @patch('api_client.requests.Session.request')
    def test_successful_json_response(self, mock_request):
        """Test successful request with JSON response."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        client = APIClient("http://localhost:8000")
        result = client.request("GET", "/health")
        
        assert result == {"status": "ok"}
        mock_request.assert_called_once()
    
    @patch('api_client.requests.Session.request')
    def test_successful_non_json_response(self, mock_request):
        """Test successful request with non-JSON response."""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        client = APIClient("http://localhost:8000")
        result = client.request("POST", "/cancel/job123")
        
        assert result == {"success": True}
    
    @patch('api_client.requests.Session.request')
    def test_request_with_custom_timeout(self, mock_request):
        """Test request with custom timeout parameter."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        client = APIClient("http://localhost:8000", timeout=10)
        result = client.request("GET", "/status/job123", timeout=30)
        
        # Verify custom timeout was used
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs['timeout'] == 30
    
    @patch('api_client.requests.Session.request')
    def test_request_uses_default_timeout(self, mock_request):
        """Test request uses default timeout when not specified."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        client = APIClient("http://localhost:8000", timeout=15)
        result = client.request("GET", "/health")
        
        # Verify default timeout was used
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs['timeout'] == 15


class TestAPIClientMethods:
    """Test individual API client methods."""
    
    def test_submit_job_success(self):
        """Test successful job submission."""
        client = APIClient("http://localhost:8000")
        
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = {
                "job_id": "job123",
                "status": "pending",
                "created_at": "2024-01-01T00:00:00Z"
            }
            
            result = client.submit_job("Analyze AI meeting tools market")
            
            assert result["job_id"] == "job123"
            assert result["status"] == "pending"
            mock_request.assert_called_once()
            
            # Verify payload structure
            call_args = mock_request.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/analyze"
            assert "json" in call_args[1]
    
    def test_submit_job_truncates_long_brief(self):
        """Test that long briefs are truncated to 2000 chars."""
        client = APIClient("http://localhost:8000")
        
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = {"job_id": "job123"}
            
            long_brief = "A" * 3000
            result = client.submit_job(long_brief)
            
            # Verify truncation
            call_args = mock_request.call_args
            payload = call_args[1]["json"]
            assert len(payload["company_description"]) == 2000
    
    def test_get_job_status_success(self):
        """Test successful job status retrieval."""
        client = APIClient("http://localhost:8000")
        
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = {
                "job_id": "job123",
                "status": "completed",
                "final_report": {"research": {}, "strategy": {}}
            }
            
            result = client.get_job_status("job123")
            
            assert result["status"] == "completed"
            assert "final_report" in result
            mock_request.assert_called_once_with("GET", "/status/job123")
    
    def test_get_agent_tasks_success(self):
        """Test successful agent tasks retrieval."""
        client = APIClient("http://localhost:8000")
        
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = [
                {"agent": "orchestrator", "status": "completed"},
                {"agent": "research", "status": "running"}
            ]
            
            result = client.get_agent_tasks("job123")
            
            assert len(result) == 2
            assert result[0]["agent"] == "orchestrator"
            mock_request.assert_called_once_with("GET", "/agents/job123")
    
    def test_get_agent_tasks_returns_empty_list_on_error(self):
        """Test that get_agent_tasks returns empty list on error."""
        client = APIClient("http://localhost:8000")
        
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = None  # Simulates error
            
            result = client.get_agent_tasks("job123")
            
            assert result == []
    
    def test_get_logs_success(self):
        """Test successful logs retrieval."""
        client = APIClient("http://localhost:8000")
        
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = [
                {"agent": "orchestrator", "level": "INFO", "message": "Starting job"},
                {"agent": "research", "level": "INFO", "message": "Researching..."}
            ]
            
            result = client.get_logs("job123")
            
            assert len(result) == 2
            assert result[0]["message"] == "Starting job"
            mock_request.assert_called_once_with("GET", "/logs/job123")
    
    def test_get_logs_returns_empty_list_on_error(self):
        """Test that get_logs returns empty list on error."""
        client = APIClient("http://localhost:8000")
        
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = None  # Simulates error
            
            result = client.get_logs("job123")
            
            assert result == []
    
    def test_cancel_job_success(self):
        """Test successful job cancellation."""
        client = APIClient("http://localhost:8000")
        
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = {
                "job_id": "job123",
                "status": "aborted"
            }
            
            result = client.cancel_job("job123")
            
            assert result["status"] == "aborted"
            mock_request.assert_called_once_with("POST", "/cancel/job123")
    
    def test_list_jobs_success(self):
        """Test successful jobs list retrieval."""
        client = APIClient("http://localhost:8000")
        
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = [
                {"job_id": "job1", "status": "completed"},
                {"job_id": "job2", "status": "running"}
            ]
            
            result = client.list_jobs(limit=10)
            
            assert len(result) == 2
            mock_request.assert_called_once_with("GET", "/jobs", params={"limit": 10})
    
    def test_list_jobs_with_default_limit(self):
        """Test list_jobs uses default limit of 20."""
        client = APIClient("http://localhost:8000")
        
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = []
            
            result = client.list_jobs()
            
            call_args = mock_request.call_args
            assert call_args[1]["params"]["limit"] == 20
    
    def test_list_jobs_returns_empty_list_on_error(self):
        """Test that list_jobs returns empty list on error."""
        client = APIClient("http://localhost:8000")
        
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = None  # Simulates error
            
            result = client.list_jobs()
            
            assert result == []
    
    def test_health_check_healthy(self):
        """Test health check returns True when backend is healthy."""
        client = APIClient("http://localhost:8000")
        
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = {
                "status": "healthy",
                "checks": {"database": {"status": "healthy"}}
            }
            
            result = client.health_check()
            
            assert result is True
            mock_request.assert_called_once_with("GET", "/health")
    
    def test_health_check_unhealthy(self):
        """Test health check returns False when backend is unhealthy."""
        client = APIClient("http://localhost:8000")
        
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = {
                "status": "unhealthy",
                "checks": {"database": {"status": "unhealthy"}}
            }
            
            result = client.health_check()
            
            assert result is False
    
    def test_health_check_connection_error(self):
        """Test health check returns False on connection error."""
        client = APIClient("http://localhost:8000")
        
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = None  # Simulates connection error
            
            result = client.health_check()
            
            assert result is False


class TestAPIClientErrorHandling:
    """Test error handling across API client methods."""
    
    def test_submit_job_returns_none_on_error(self):
        """Test submit_job returns None when request fails."""
        client = APIClient("http://localhost:8000")
        
        with patch.object(client, 'request') as mock_request:
            mock_request.side_effect = requests.ConnectionError()
            
            result = client.submit_job("Test brief")
            
            assert result is None
    
    def test_get_job_status_returns_none_on_error(self):
        """Test get_job_status returns None when request fails."""
        client = APIClient("http://localhost:8000")
        
        with patch.object(client, 'request') as mock_request:
            mock_request.side_effect = requests.Timeout()
            
            result = client.get_job_status("job123")
            
            assert result is None
    
    def test_cancel_job_returns_none_on_error(self):
        """Test cancel_job returns None when request fails."""
        client = APIClient("http://localhost:8000")
        
        with patch.object(client, 'request') as mock_request:
            mock_request.side_effect = requests.HTTPError()
            
            result = client.cancel_job("job123")
            
            assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
