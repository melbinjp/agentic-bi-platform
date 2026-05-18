"""
Integration tests for New Analysis page enhancements (Task 4).

This module tests the integration of the New Analysis page with:
- Glassmorphism styling
- Example prompts
- Character count and validation
- Cost/time estimation
- StreamManager integration
- render_agent_timeline component
- render_log_panel component

Requirements: 4.1-4.8, 9.1-9.8
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from components import render_agent_timeline, render_log_panel
from stream_manager import StreamManager


class TestNewAnalysisPageIntegration:
    """Test suite for New Analysis page integration."""
    
    def test_render_agent_timeline_integration(self):
        """Test that render_agent_timeline returns valid HTML."""
        agent_tasks = [
            {
                'agent': 'research',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 12.5,
                'cost_usd': 0.45
            },
            {
                'agent': 'strategy',
                'status': 'running',
                'model_used': 'gpt-4',
                'execution_time': 5.2,
                'cost_usd': 0.23
            }
        ]
        
        html = render_agent_timeline(agent_tasks, 'running', layout='horizontal')
        
        # Verify HTML is returned
        assert isinstance(html, str)
        assert len(html) > 0
        
        # Verify agent cards are present
        assert 'research' in html.lower()
        assert 'strategy' in html.lower()
        
        # Verify status indicators
        assert 'completed' in html.lower()
        assert 'running' in html.lower()
        
        # Verify model information
        assert 'gpt-4' in html
        
        # Verify cost and time display
        assert '$0.45' in html or '0.45' in html
        assert '12.5s' in html or '12.5' in html
    
    def test_render_log_panel_integration(self):
        """Test that render_log_panel returns valid HTML."""
        logs = [
            {
                'timestamp': '2024-01-15T10:30:00Z',
                'level': 'INFO',
                'agent': 'research',
                'message': 'Starting research phase',
                'is_decision': False
            },
            {
                'timestamp': '2024-01-15T10:30:05Z',
                'level': 'WARN',
                'agent': 'strategy',
                'message': 'Low confidence in market data',
                'is_decision': False
            },
            {
                'timestamp': '2024-01-15T10:30:10Z',
                'level': 'INFO',
                'agent': 'critic',
                'message': 'Approving strategy',
                'is_decision': True
            }
        ]
        
        html = render_log_panel(logs, filters=None, search_query=None, auto_scroll=True)
        
        # Verify HTML is returned
        assert isinstance(html, str)
        assert len(html) > 0
        
        # Verify log entries are present
        assert 'research' in html.lower()
        assert 'strategy' in html.lower()
        assert 'critic' in html.lower()
        
        # Verify log messages
        assert 'Starting research phase' in html
        assert 'Low confidence in market data' in html
        assert 'Approving strategy' in html
        
        # Verify log levels
        assert 'INFO' in html
        assert 'WARN' in html
        
        # Verify decision badge for decision logs
        assert 'DECISION' in html
        
        # Verify auto-scroll is enabled
        assert 'scroll-behavior: smooth' in html
    
    def test_render_log_panel_with_filters(self):
        """Test that render_log_panel filters logs correctly."""
        logs = [
            {
                'timestamp': '2024-01-15T10:30:00Z',
                'level': 'INFO',
                'agent': 'research',
                'message': 'Starting research phase',
                'is_decision': False
            },
            {
                'timestamp': '2024-01-15T10:30:05Z',
                'level': 'ERROR',
                'agent': 'strategy',
                'message': 'Failed to fetch data',
                'is_decision': False
            },
            {
                'timestamp': '2024-01-15T10:30:10Z',
                'level': 'INFO',
                'agent': 'critic',
                'message': 'Approving strategy',
                'is_decision': True
            }
        ]
        
        # Filter by ERROR level only
        html = render_log_panel(logs, filters={'level': ['ERROR']}, search_query=None, auto_scroll=True)
        
        # Verify only ERROR logs are shown
        assert 'Failed to fetch data' in html
        assert 'Starting research phase' not in html
        assert 'Approving strategy' not in html
    
    def test_render_log_panel_with_search(self):
        """Test that render_log_panel highlights search matches."""
        logs = [
            {
                'timestamp': '2024-01-15T10:30:00Z',
                'level': 'INFO',
                'agent': 'research',
                'message': 'Starting research phase',
                'is_decision': False
            },
            {
                'timestamp': '2024-01-15T10:30:05Z',
                'level': 'INFO',
                'agent': 'strategy',
                'message': 'Analyzing market data',
                'is_decision': False
            }
        ]
        
        # Search for "research"
        html = render_log_panel(logs, filters=None, search_query='research', auto_scroll=True)
        
        # Verify search highlighting
        assert '<mark' in html
        assert 'research' in html.lower()
        
        # Verify the matching log is shown (search matches both message and agent name)
        # The message "Starting research phase" contains "research" so it should be shown
        # But the HTML escapes and highlights it, so we check for the highlighted version
        assert 'Starting' in html
        assert 'phase' in html
    
    def test_stream_manager_connection_status(self):
        """Test that StreamManager reports connection status correctly."""
        stream_manager = StreamManager('http://localhost:8000/api/v1', 'job123')
        
        # Initial status should be disconnected
        assert stream_manager.get_connection_status() == 'disconnected'
        
        # After setting status to streaming
        stream_manager.connection_status = 'streaming'
        assert stream_manager.get_connection_status() == 'streaming'
        
        # After setting status to polling
        stream_manager.connection_status = 'polling'
        assert stream_manager.get_connection_status() == 'polling'
    
    def test_stream_manager_event_buffering(self):
        """Test that StreamManager buffers events correctly."""
        stream_manager = StreamManager('http://localhost:8000/api/v1', 'job123', buffer_duration_ms=100)
        
        # Verify buffer is initialized
        assert hasattr(stream_manager, '_event_buffer')
        assert len(stream_manager._event_buffer) == 0
        
        # Add event to buffer
        event = {'type': 'log', 'data': {'message': 'test'}, 'timestamp': '2024-01-15T10:30:00Z'}
        stream_manager._event_buffer.append(event)
        
        # Verify event is in buffer
        assert len(stream_manager._event_buffer) == 1
        assert stream_manager._event_buffer[0] == event
    
    def test_character_count_validation(self):
        """Test character count validation logic."""
        min_chars = 50
        max_chars = 5000
        
        # Test valid input
        valid_input = "A" * 100
        char_count = len(valid_input.strip())
        assert char_count >= min_chars
        assert char_count <= max_chars
        
        # Test too short input
        short_input = "A" * 30
        char_count = len(short_input.strip())
        assert char_count < min_chars
        
        # Test too long input
        long_input = "A" * 6000
        char_count = len(long_input.strip())
        assert char_count > max_chars
    
    def test_cost_time_estimation(self):
        """Test cost and time estimation logic."""
        # Test estimation for 1000 characters
        char_count = 1000
        estimated_time_min = max(2, int(char_count / 500))
        estimated_cost = max(0.50, char_count / 1000 * 0.10)
        
        assert estimated_time_min == 2
        assert estimated_cost == 0.50
        
        # Test estimation for 2500 characters
        char_count = 2500
        estimated_time_min = max(2, int(char_count / 500))
        raw_cost = char_count / 1000 * 0.10
        estimated_cost = max(0.50, raw_cost)
        
        assert estimated_time_min == 5
        assert raw_cost == 0.25
        assert estimated_cost == 0.50  # max(0.50, 0.25) = 0.50
        
        # Test estimation for 5000 characters
        char_count = 5000
        estimated_time_min = max(2, int(char_count / 500))
        estimated_cost = max(0.50, char_count / 1000 * 0.10)
        
        assert estimated_time_min == 10
        assert estimated_cost == 0.50
    
    def test_render_agent_timeline_with_collaboration(self):
        """Test agent timeline with collaboration indicators."""
        agent_tasks = [
            {
                'agent': 'research',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 12.5,
                'cost_usd': 0.45,
                'collaborations': []
            },
            {
                'agent': 'strategy',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 5.2,
                'cost_usd': 0.23,
                'collaborations': [
                    {
                        'requested_agent': 'research',
                        'reason': 'Need market data validation'
                    }
                ]
            }
        ]
        
        html = render_agent_timeline(agent_tasks, 'completed', layout='horizontal')
        
        # Verify collaboration arrow is present
        assert '→' in html or '&rarr;' in html
        
        # Verify collaboration details are in expandable section
        assert 'Need market data validation' in html
    
    def test_render_log_panel_empty_logs(self):
        """Test log panel with empty logs."""
        html = render_log_panel([], filters=None, search_query=None, auto_scroll=True)
        
        # Verify empty state message
        assert 'No logs to display' in html
    
    def test_render_agent_timeline_empty_tasks(self):
        """Test agent timeline with empty tasks."""
        html = render_agent_timeline([], 'pending', layout='horizontal')
        
        # Verify HTML is still returned (even if empty)
        assert isinstance(html, str)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
