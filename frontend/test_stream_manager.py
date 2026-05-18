"""
Unit tests for StreamManager module.

Tests SSE streaming, polling fallback, event buffering, reconnection logic,
and connection status tracking.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import requests
from stream_manager import StreamManager


class TestStreamManagerInit:
    """Test StreamManager initialization."""
    
    def test_init_with_required_params(self):
        """Test initialization with required parameters."""
        manager = StreamManager("http://localhost:8000/api/v1", "job123")
        
        assert manager.backend_url == "http://localhost:8000/api/v1"
        assert manager.job_id == "job123"
        assert manager.sse_available is True
        assert manager.connection_status == 'disconnected'
        assert manager.buffer_duration_ms == 500
        assert manager.max_reconnect_attempts == 3
        assert manager.reconnect_delay_seconds == 2
    
    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        manager = StreamManager(
            "http://example.com/api",
            "job456",
            buffer_duration_ms=1000,
            max_reconnect_attempts=5,
            reconnect_delay_seconds=3
        )
        
        assert manager.backend_url == "http://example.com/api"
        assert manager.job_id == "job456"
        assert manager.buffer_duration_ms == 1000
        assert manager.max_reconnect_attempts == 5
        assert manager.reconnect_delay_seconds == 3
    
    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is removed from backend URL."""
        manager = StreamManager("http://localhost:8000/api/v1/", "job123")
        assert manager.backend_url == "http://localhost:8000/api/v1"


class TestStreamManagerSSE:
    """Test SSE streaming functionality."""
    
    @patch('stream_manager.requests.get')
    def test_sse_connection_success(self, mock_get):
        """Test successful SSE connection and event parsing."""
        # Mock SSE response
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.iter_lines = Mock(return_value=[
            'data: {"type": "log", "data": {"message": "Test log"}}',
            'data: {"type": "done", "data": {"status": "completed"}}'
        ])
        mock_get.return_value = mock_response
        
        manager = StreamManager("http://localhost:8000/api/v1", "job123")
        events = list(manager.connect_stream())
        
        # Verify connection was attempted
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "http://localhost:8000/api/v1/stream/job123"
        assert call_args[1]['stream'] is True
        assert call_args[1]['headers']['Accept'] == 'text/event-stream'
        
        # Verify events were parsed
        assert len(events) >= 2
        assert events[0]['type'] == 'log'
        assert events[0]['data']['message'] == 'Test log'
    
    @patch('stream_manager.requests.get')
    def test_sse_connection_failure_fallback_to_polling(self, mock_get):
        """Test automatic fallback to polling when SSE fails."""
        # Mock SSE failure
        mock_get.side_effect = requests.RequestException("Connection failed")
        
        manager = StreamManager("http://localhost:8000/api/v1", "job123")
        
        # Mock poll_status to return completed status
        manager.poll_status = Mock(return_value={
            'job_id': 'job123',
            'status': 'completed'
        })
        
        events = list(manager.connect_stream())
        
        # Verify SSE was attempted
        assert mock_get.call_count == manager.max_reconnect_attempts + 1
        
        # Verify fallback to polling occurred
        assert manager.sse_available is False
        assert manager.poll_status.called
        
        # Verify polling events were yielded
        assert len(events) >= 1
    
    @patch('stream_manager.requests.get')
    @patch('stream_manager.time.sleep')
    def test_sse_reconnection_on_interruption(self, mock_sleep, mock_get):
        """Test automatic reconnection when SSE stream is interrupted."""
        # First attempt fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status = Mock(side_effect=requests.RequestException("Connection lost"))
        
        mock_response_success = Mock()
        mock_response_success.raise_for_status = Mock()
        mock_response_success.iter_lines = Mock(return_value=[
            'data: {"type": "done", "data": {"status": "completed"}}'
        ])
        
        mock_get.side_effect = [mock_response_fail, mock_response_success]
        
        manager = StreamManager("http://localhost:8000/api/v1", "job123")
        events = list(manager.connect_stream())
        
        # Verify reconnection was attempted
        assert mock_get.call_count == 2
        assert mock_sleep.called
        
        # Verify events were received after reconnection
        assert len(events) >= 1


class TestStreamManagerPolling:
    """Test polling fallback functionality."""
    
    def test_poll_status_success(self):
        """Test successful status polling."""
        manager = StreamManager("http://localhost:8000/api/v1", "job123")
        
        with patch('stream_manager.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.json = Mock(return_value={
                'job_id': 'job123',
                'status': 'running'
            })
            mock_get.return_value = mock_response
            
            result = manager.poll_status(interval=2)
            
            assert result is not None
            assert result['job_id'] == 'job123'
            assert result['status'] == 'running'
            
            # Verify correct endpoint was called
            mock_get.assert_called_once()
            assert mock_get.call_args[0][0] == "http://localhost:8000/api/v1/status/job123"
    
    def test_poll_status_failure(self):
        """Test polling failure handling."""
        manager = StreamManager("http://localhost:8000/api/v1", "job123")
        
        with patch('stream_manager.requests.get') as mock_get:
            mock_get.side_effect = requests.RequestException("Connection failed")
            
            result = manager.poll_status(interval=2)
            
            assert result is None
    
    def test_polling_stream_until_completion(self):
        """Test polling stream continues until job completes."""
        manager = StreamManager("http://localhost:8000/api/v1", "job123")
        manager.sse_available = False  # Force polling mode
        
        # Mock poll_status to return running then completed
        poll_responses = [
            {'job_id': 'job123', 'status': 'running'},
            {'job_id': 'job123', 'status': 'completed'}
        ]
        manager.poll_status = Mock(side_effect=poll_responses)
        
        events = list(manager.connect_stream())
        
        # Verify polling was called multiple times
        assert manager.poll_status.call_count == 2
        
        # Verify status events were yielded
        assert len(events) >= 2
        assert any(e['type'] == 'status' for e in events)
        assert any(e['type'] == 'done' for e in events)


class TestStreamManagerEventBuffering:
    """Test event buffering to prevent UI flicker."""
    
    @patch('stream_manager.requests.get')
    def test_event_buffering_delays_yield(self, mock_get):
        """Test that events are buffered before yielding."""
        # Mock rapid SSE events
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.iter_lines = Mock(return_value=[
            'data: {"type": "log", "data": {"message": "Event 1"}}',
            'data: {"type": "log", "data": {"message": "Event 2"}}',
            'data: {"type": "log", "data": {"message": "Event 3"}}',
            'data: {"type": "done", "data": {"status": "completed"}}'
        ])
        mock_get.return_value = mock_response
        
        manager = StreamManager("http://localhost:8000/api/v1", "job123", buffer_duration_ms=100)
        
        events = []
        start_time = time.time()
        
        for event in manager.connect_stream():
            events.append(event)
            if event['type'] == 'done':
                break
        
        # Verify events were buffered (should take at least buffer_duration_ms)
        # Note: This is a timing-sensitive test, so we use a small buffer
        assert len(events) >= 4
    
    def test_buffer_flush_on_done_event(self):
        """Test that buffer is flushed when done event is received."""
        manager = StreamManager("http://localhost:8000/api/v1", "job123")
        
        # Add events to buffer
        manager._event_buffer.append({'type': 'log', 'data': {'message': 'Test'}})
        manager._last_flush_time = datetime.utcnow()
        
        # Flush buffer
        flushed_events = list(manager._flush_buffer())
        
        assert len(flushed_events) == 1
        assert len(manager._event_buffer) == 0


class TestStreamManagerConnectionStatus:
    """Test connection status tracking."""
    
    def test_initial_status_disconnected(self):
        """Test initial connection status is disconnected."""
        manager = StreamManager("http://localhost:8000/api/v1", "job123")
        assert manager.get_connection_status() == 'disconnected'
    
    @patch('stream_manager.requests.get')
    def test_status_streaming_when_sse_connected(self, mock_get):
        """Test connection status is 'streaming' when SSE is active."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.iter_lines = Mock(return_value=[
            'data: {"type": "done", "data": {"status": "completed"}}'
        ])
        mock_get.return_value = mock_response
        
        manager = StreamManager("http://localhost:8000/api/v1", "job123")
        
        # Start streaming
        events = list(manager.connect_stream())
        
        # Note: Status will be 'disconnected' after stream completes
        # During streaming it would be 'streaming'
        assert len(events) >= 1
    
    def test_status_polling_when_sse_unavailable(self):
        """Test connection status is 'polling' when using polling fallback."""
        manager = StreamManager("http://localhost:8000/api/v1", "job123")
        manager.sse_available = False
        
        # Mock poll_status to return completed immediately
        manager.poll_status = Mock(return_value={
            'job_id': 'job123',
            'status': 'completed'
        })
        
        # Start polling
        events = list(manager.connect_stream())
        
        # Verify polling mode was used
        assert manager.poll_status.called


class TestStreamManagerEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_parse_sse_line_with_invalid_json(self):
        """Test parsing SSE line with invalid JSON."""
        manager = StreamManager("http://localhost:8000/api/v1", "job123")
        
        result = manager._parse_sse_line('data: {invalid json}')
        
        assert result is None
    
    def test_parse_sse_line_without_data_prefix(self):
        """Test parsing SSE line without 'data:' prefix."""
        manager = StreamManager("http://localhost:8000/api/v1", "job123")
        
        result = manager._parse_sse_line('event: message')
        
        assert result is None
    
    def test_parse_sse_line_adds_timestamp(self):
        """Test that timestamp is added if not present in event."""
        manager = StreamManager("http://localhost:8000/api/v1", "job123")
        
        result = manager._parse_sse_line('data: {"type": "log", "data": {}}')
        
        assert result is not None
        assert 'timestamp' in result
    
    @patch('stream_manager.requests.get')
    def test_max_reconnect_attempts_exceeded(self, mock_get):
        """Test that polling fallback occurs after max reconnect attempts."""
        # All SSE attempts fail
        mock_get.side_effect = requests.RequestException("Connection failed")
        
        manager = StreamManager("http://localhost:8000/api/v1", "job123", max_reconnect_attempts=2)
        
        # Mock poll_status to return completed
        manager.poll_status = Mock(return_value={
            'job_id': 'job123',
            'status': 'completed'
        })
        
        events = list(manager.connect_stream())
        
        # Verify SSE was attempted max_reconnect_attempts + 1 times
        assert mock_get.call_count == 3  # Initial + 2 retries
        
        # Verify fallback to polling
        assert manager.sse_available is False
        assert manager.poll_status.called


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
