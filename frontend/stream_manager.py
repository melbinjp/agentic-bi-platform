"""
Stream Manager Module - Real-Time Updates Handler

This module provides the StreamManager class for handling real-time updates
from the backend via Server-Sent Events (SSE) with automatic fallback to
polling when SSE is unavailable.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8
"""

import time
import requests
from typing import Iterator, Dict, Any, Optional
from collections import deque
from datetime import datetime, timedelta


class StreamManager:
    """
    Manages real-time updates via SSE streaming with polling fallback.
    
    This class attempts to establish an SSE connection for real-time updates.
    If SSE is unavailable or fails, it automatically falls back to polling.
    It includes event buffering to prevent UI flicker and automatic reconnection
    on stream interruption.
    
    Attributes:
        backend_url: Base URL of the backend API
        job_id: Unique job identifier
        sse_available: Whether SSE streaming is currently available
        connection_status: Current connection status ('streaming', 'polling', 'disconnected')
        buffer_duration_ms: Duration to buffer events before yielding (default: 500ms)
        max_reconnect_attempts: Maximum reconnection attempts before falling back to polling
        reconnect_delay_seconds: Delay between reconnection attempts
    """
    
    def __init__(
        self,
        backend_url: str,
        job_id: str,
        buffer_duration_ms: int = 500,
        max_reconnect_attempts: int = 3,
        reconnect_delay_seconds: int = 2
    ):
        """
        Initialize StreamManager with backend URL and job ID.
        
        Args:
            backend_url: Base URL of the backend API (e.g., "http://localhost:8000/api/v1")
            job_id: Unique job identifier to stream updates for
            buffer_duration_ms: Duration to buffer events before yielding (default: 500ms)
            max_reconnect_attempts: Maximum reconnection attempts (default: 3)
            reconnect_delay_seconds: Delay between reconnection attempts (default: 2s)
        """
        self.backend_url = backend_url.rstrip("/")
        self.job_id = job_id
        self.sse_available = True
        self.connection_status = 'disconnected'
        self.buffer_duration_ms = buffer_duration_ms
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay_seconds = reconnect_delay_seconds
        
        # Event buffer for preventing UI flicker
        self._event_buffer: deque = deque()
        self._last_flush_time: Optional[datetime] = None
    
    def connect_stream(self) -> Iterator[Dict[str, Any]]:
        """
        Establish SSE connection and yield events with automatic fallback to polling.
        
        This method first attempts to establish an SSE connection. If SSE is unavailable
        or fails, it automatically falls back to polling. Events are buffered to prevent
        UI flicker from rapid updates.
        
        Yields:
            Dict with keys:
                - type: str ('log', 'status', 'agent_update', 'done', 'error')
                - data: Dict (event-specific payload)
                - timestamp: str (ISO format timestamp)
        
        Example:
            >>> manager = StreamManager("http://localhost:8000/api/v1", "job123")
            >>> for event in manager.connect_stream():
            ...     if event['type'] == 'log':
            ...         print(f"Log: {event['data']['message']}")
            ...     elif event['type'] == 'done':
            ...         break
        """
        # Try SSE streaming first
        if self.sse_available:
            try:
                yield from self._stream_sse()
            except Exception as e:
                print(f"⚠️ SSE streaming failed: {str(e)}")
                self.sse_available = False
                self.connection_status = 'disconnected'
        
        # Fall back to polling if SSE unavailable or failed
        if not self.sse_available:
            print("📊 Falling back to polling mode")
            yield from self._stream_polling()
    
    def _stream_sse(self) -> Iterator[Dict[str, Any]]:
        """
        Stream events via Server-Sent Events (SSE).
        
        Establishes SSE connection and yields parsed events. Implements automatic
        reconnection on stream interruption.
        
        Yields:
            Parsed event dictionaries
            
        Raises:
            requests.RequestException: If SSE connection fails after max retries
        """
        url = f"{self.backend_url}/stream/{self.job_id}"
        reconnect_attempts = 0
        
        while reconnect_attempts <= self.max_reconnect_attempts:
            try:
                # Establish SSE connection with streaming enabled
                response = requests.get(
                    url,
                    stream=True,
                    timeout=None,  # No timeout for streaming
                    headers={'Accept': 'text/event-stream'}
                )
                response.raise_for_status()
                
                self.connection_status = 'streaming'
                reconnect_attempts = 0  # Reset on successful connection
                
                # Parse SSE stream
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        event = self._parse_sse_line(line)
                        if event:
                            # Buffer event and yield if buffer is ready
                            yield from self._buffer_and_yield(event)
                            
                            # Check if job is done
                            if event.get('type') == 'done':
                                # Flush remaining buffered events
                                yield from self._flush_buffer()
                                return
                
                # Stream ended normally
                self.connection_status = 'disconnected'
                return
                
            except requests.RequestException as e:
                reconnect_attempts += 1
                self.connection_status = 'disconnected'
                
                if reconnect_attempts <= self.max_reconnect_attempts:
                    print(f"🔄 SSE connection lost. Reconnecting... (attempt {reconnect_attempts}/{self.max_reconnect_attempts})")
                    time.sleep(self.reconnect_delay_seconds)
                else:
                    # Max retries exceeded, raise to fall back to polling
                    raise requests.RequestException(f"SSE connection failed after {self.max_reconnect_attempts} attempts") from e
    
    def _stream_polling(self) -> Iterator[Dict[str, Any]]:
        """
        Stream events via polling fallback.
        
        Polls the backend at regular intervals for status updates when SSE
        is unavailable. Continues until job is completed or failed.
        
        Yields:
            Parsed event dictionaries
        """
        self.connection_status = 'polling'
        poll_interval = 2  # seconds
        last_status = None
        
        while True:
            try:
                status_data = self.poll_status(interval=poll_interval)
                
                if status_data:
                    current_status = status_data.get('status')
                    
                    # Yield status update if changed
                    if current_status != last_status:
                        event = {
                            'type': 'status',
                            'data': status_data,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        yield from self._buffer_and_yield(event)
                        last_status = current_status
                    
                    # Check if job is done
                    if current_status in ['completed', 'failed', 'aborted']:
                        event = {
                            'type': 'done',
                            'data': {'status': current_status},
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        yield from self._buffer_and_yield(event)
                        # Flush remaining buffered events
                        yield from self._flush_buffer()
                        self.connection_status = 'disconnected'
                        return
                else:
                    # Polling failed, yield error event
                    event = {
                        'type': 'error',
                        'data': {'message': 'Failed to poll status'},
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    yield event
                    self.connection_status = 'disconnected'
                    return
                    
            except Exception as e:
                # Unexpected error during polling
                event = {
                    'type': 'error',
                    'data': {'message': f'Polling error: {str(e)}'},
                    'timestamp': datetime.utcnow().isoformat()
                }
                yield event
                self.connection_status = 'disconnected'
                return
    
    def _parse_sse_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single SSE line into an event dictionary.
        
        SSE format:
            data: {"type": "log", "data": {...}}
        
        Args:
            line: Raw SSE line
            
        Returns:
            Parsed event dictionary or None if line is not a data line
        """
        if line.startswith('data: '):
            try:
                import json
                data_str = line[6:]  # Remove 'data: ' prefix
                event = json.loads(data_str)
                
                # Add timestamp if not present
                if 'timestamp' not in event:
                    event['timestamp'] = datetime.utcnow().isoformat()
                
                return event
            except json.JSONDecodeError:
                # Invalid JSON, skip this line
                return None
        
        return None
    
    def _buffer_and_yield(self, event: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """
        Buffer event and yield buffered events if buffer duration has elapsed.
        
        This prevents UI flicker from rapid updates by batching events within
        the buffer duration window.
        
        Args:
            event: Event to buffer
            
        Yields:
            Buffered events when buffer is ready to flush
        """
        # Add event to buffer
        self._event_buffer.append(event)
        
        # Initialize flush time on first event
        if self._last_flush_time is None:
            self._last_flush_time = datetime.utcnow()
        
        # Check if buffer duration has elapsed
        elapsed_ms = (datetime.utcnow() - self._last_flush_time).total_seconds() * 1000
        
        if elapsed_ms >= self.buffer_duration_ms:
            yield from self._flush_buffer()
    
    def _flush_buffer(self) -> Iterator[Dict[str, Any]]:
        """
        Flush all buffered events.
        
        Yields:
            All events in the buffer
        """
        while self._event_buffer:
            yield self._event_buffer.popleft()
        
        self._last_flush_time = datetime.utcnow()
    
    def poll_status(self, interval: int = 2) -> Optional[Dict[str, Any]]:
        """
        Poll backend for job status (fallback mechanism).
        
        This method is used when SSE streaming is unavailable. It fetches
        the current job status from the backend.
        
        Args:
            interval: Polling interval in seconds (used for sleep between calls)
            
        Returns:
            Job status dictionary with keys:
                - job_id: str
                - status: str (pending, running, completed, failed, aborted)
                - created_at: str (ISO timestamp)
                - final_report: dict (if completed)
            Or None on error
            
        Example:
            >>> manager = StreamManager("http://localhost:8000/api/v1", "job123")
            >>> status = manager.poll_status(interval=2)
            >>> if status:
            ...     print(f"Job status: {status['status']}")
        """
        try:
            url = f"{self.backend_url}/status/{self.job_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            print(f"❌ Polling failed: {str(e)}")
            return None
    
    def get_connection_status(self) -> str:
        """
        Get current connection status.
        
        Returns:
            Connection status: 'streaming', 'polling', or 'disconnected'
            
        Example:
            >>> manager = StreamManager("http://localhost:8000/api/v1", "job123")
            >>> status = manager.get_connection_status()
            >>> print(f"Connection: {status}")
        """
        return self.connection_status
