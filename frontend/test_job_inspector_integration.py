"""
Integration Tests for Job Inspector Page

Tests the complete Job Inspector workflow including data fetching,
enrichment, and component rendering.

Requirements: 2.1-2.9, 3.1-3.5, 5.1-5.8, 6.1-6.8, 12.1-12.5
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add frontend directory to path
sys.path.insert(0, os.path.dirname(__file__))


class TestJobInspectorIntegration(unittest.TestCase):
    """Integration tests for Job Inspector page."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_status_data = {
            'job_id': 'test-job-123',
            'status': 'completed',
            'company': 'Test Company',
            'created_at': '2024-01-15T10:00:00Z',
            'completed_at': '2024-01-15T10:10:00Z',
            'total_cost_usd': 0.15,
            'final_report': {
                'job_id': 'test-job-123',
                'research': {
                    'report': 'Research findings...',
                    'sources': ['https://example.com']
                },
                'strategy': {
                    'report': 'Strategy recommendations...',
                    'critic_verdict': 'APPROVED',
                    'critic_score': 8
                },
                'execution_plan': {
                    'phase_30_days': [
                        {'task': 'Task 1', 'owner': 'Team A', 'kpi': 'Metric 1', 'priority': 'high'}
                    ],
                    'phase_60_days': [],
                    'phase_90_days': []
                },
                'qa': {
                    'score': 8,
                    'passed': True,
                    'gaps': []
                }
            }
        }
        
        self.mock_agent_data = [
            {
                'agent': 'research',
                'status': 'completed',
                'model_used': 'gpt-3.5-turbo',
                'tokens_used': 500,
                'execution_time_ms': 3000,
                'started_at': '2024-01-15T10:00:00Z',
                'completed_at': '2024-01-15T10:00:03Z',
                'error_message': None
            },
            {
                'agent': 'strategy',
                'status': 'completed',
                'model_used': 'gpt-4',
                'tokens_used': 1000,
                'execution_time_ms': 5000,
                'started_at': '2024-01-15T10:00:03Z',
                'completed_at': '2024-01-15T10:00:08Z',
                'error_message': None
            }
        ]
        
        self.mock_log_data = [
            {
                'agent': 'research',
                'level': 'INFO',
                'event_type': 'agent_started',
                'message': 'Research agent started',
                'details': {},
                'timestamp': '2024-01-15T10:00:00Z'
            },
            {
                'agent': 'research',
                'level': 'INFO',
                'event_type': 'decision',
                'message': 'Selected comprehensive market research approach',
                'details': {'confidence': 0.9},
                'timestamp': '2024-01-15T10:00:01Z'
            },
            {
                'agent': 'research',
                'level': 'INFO',
                'event_type': 'memory_retrieval',
                'message': 'Retrieved 3 similar past analyses',
                'details': {'query': 'market research', 'results_count': 3},
                'timestamp': '2024-01-15T10:00:02Z'
            },
            {
                'agent': 'strategy',
                'level': 'INFO',
                'event_type': 'agent_started',
                'message': 'Strategy agent started',
                'details': {},
                'timestamp': '2024-01-15T10:00:03Z'
            },
            {
                'agent': 'strategy',
                'level': 'INFO',
                'event_type': 'collaboration_request',
                'message': 'Requesting research validation',
                'details': {'requested_agent': 'research'},
                'timestamp': '2024-01-15T10:00:04Z'
            },
            {
                'agent': 'strategy',
                'level': 'INFO',
                'event_type': 'model_selection',
                'message': 'Selected GPT-4 for complex strategy formulation',
                'details': {'model': 'gpt-4', 'reason': 'high complexity'},
                'timestamp': '2024-01-15T10:00:05Z'
            }
        ]
    
    def test_enrich_agent_data_extracts_all_event_types(self):
        """Test that enrichment extracts decisions, collaborations, memory, and model selections."""
        from test_job_inspector import TestEnrichAgentDataWithLogs
        
        test_instance = TestEnrichAgentDataWithLogs()
        enriched = test_instance._enrich_agent_data_with_logs(
            self.mock_agent_data,
            self.mock_log_data
        )
        
        # Verify research agent enrichment
        research_agent = enriched[0]
        assert research_agent['agent'] == 'research'
        assert len(research_agent['decisions']) == 1
        assert research_agent['decisions'][0]['type'] == 'decision'
        assert len(research_agent['memory_retrievals']) == 1
        assert research_agent['memory_retrievals'][0]['results_count'] == 3
        
        # Verify strategy agent enrichment
        strategy_agent = enriched[1]
        assert strategy_agent['agent'] == 'strategy'
        assert len(strategy_agent['collaborations']) == 1
        assert strategy_agent['collaborations'][0]['requested_agent'] == 'research'
        assert len(strategy_agent['model_selections']) == 1
        assert strategy_agent['model_selections'][0]['selected_model'] == 'gpt-4'
    
    def test_process_logs_marks_decision_logs(self):
        """Test that log processing correctly marks decision logs."""
        from test_job_inspector import TestProcessLogsForDisplay
        
        test_instance = TestProcessLogsForDisplay()
        processed = test_instance._process_logs_for_display(self.mock_log_data)
        
        # Count decision logs
        decision_logs = [log for log in processed if log.get('is_decision')]
        assert len(decision_logs) == 3  # decision, collaboration_request, model_selection
        
        # Verify specific decision logs
        decision_log = next(log for log in processed if log['event_type'] == 'decision')
        assert decision_log['is_decision'] is True
        assert 'structured_data' in decision_log
        assert decision_log['structured_data']['confidence'] == 0.9
    
    def test_cost_calculation_for_multiple_agents(self):
        """Test that costs are calculated correctly for multiple agents."""
        from test_job_inspector import TestEnrichAgentDataWithLogs
        
        test_instance = TestEnrichAgentDataWithLogs()
        enriched = test_instance._enrich_agent_data_with_logs(
            self.mock_agent_data,
            self.mock_log_data
        )
        
        # Verify costs
        research_cost = enriched[0]['cost_usd']
        strategy_cost = enriched[1]['cost_usd']
        
        # GPT-3.5: 500 tokens * $0.002/1000 = $0.001
        assert research_cost == 0.001
        
        # GPT-4: 1000 tokens * $0.03/1000 = $0.03
        assert strategy_cost == 0.03
        
        # Total cost
        total_cost = research_cost + strategy_cost
        assert total_cost == 0.031
    
    def test_timeline_displays_all_agent_information(self):
        """Test that timeline component receives all necessary agent information."""
        from test_job_inspector import TestEnrichAgentDataWithLogs
        
        test_instance = TestEnrichAgentDataWithLogs()
        enriched = test_instance._enrich_agent_data_with_logs(
            self.mock_agent_data,
            self.mock_log_data
        )
        
        # Verify all required fields are present for timeline rendering
        for agent in enriched:
            assert 'agent' in agent
            assert 'status' in agent
            assert 'model_used' in agent
            assert 'execution_time_ms' in agent
            assert 'cost_usd' in agent
            assert 'decisions' in agent
            assert 'collaborations' in agent
            assert 'memory_retrievals' in agent
            assert 'model_selections' in agent
            assert 'output_preview' in agent
    
    def test_log_panel_receives_processed_logs(self):
        """Test that log panel receives properly processed logs."""
        from test_job_inspector import TestProcessLogsForDisplay
        
        test_instance = TestProcessLogsForDisplay()
        processed = test_instance._process_logs_for_display(self.mock_log_data)
        
        # Verify all logs are processed
        assert len(processed) == len(self.mock_log_data)
        
        # Verify each log has required fields
        for log in processed:
            assert 'agent' in log
            assert 'level' in log
            assert 'event_type' in log
            assert 'message' in log
            assert 'timestamp' in log
            assert 'is_decision' in log
    
    def test_key_insights_calculation(self):
        """Test that key insights are calculated correctly."""
        from test_job_inspector import TestEnrichAgentDataWithLogs
        
        test_instance = TestEnrichAgentDataWithLogs()
        enriched = test_instance._enrich_agent_data_with_logs(
            self.mock_agent_data,
            self.mock_log_data
        )
        
        # Calculate total decisions
        total_decisions = sum(len(agent.get('decisions', [])) for agent in enriched)
        assert total_decisions == 1  # Only research agent has a decision
        
        # Calculate total collaborations
        total_collaborations = sum(len(agent.get('collaborations', [])) for agent in enriched)
        assert total_collaborations == 1  # Only strategy agent has a collaboration
        
        # Calculate total memory retrievals
        total_memory = sum(len(agent.get('memory_retrievals', [])) for agent in enriched)
        assert total_memory == 1  # Only research agent has memory retrieval
        
        # Calculate total model selections
        total_models = sum(len(agent.get('model_selections', [])) for agent in enriched)
        assert total_models == 1  # Only strategy agent has model selection
    
    def test_empty_logs_handling(self):
        """Test that enrichment handles empty logs gracefully."""
        from test_job_inspector import TestEnrichAgentDataWithLogs
        
        test_instance = TestEnrichAgentDataWithLogs()
        enriched = test_instance._enrich_agent_data_with_logs(
            self.mock_agent_data,
            []  # Empty logs
        )
        
        # Verify agents are still enriched with empty arrays
        for agent in enriched:
            assert agent['decisions'] == []
            assert agent['collaborations'] == []
            assert agent['memory_retrievals'] == []
            assert agent['model_selections'] == []
            assert 'cost_usd' in agent  # Cost should still be calculated
    
    def test_missing_details_handling(self):
        """Test that processing handles logs without details field."""
        from test_job_inspector import TestProcessLogsForDisplay
        
        logs_without_details = [
            {
                'agent': 'test',
                'level': 'INFO',
                'event_type': 'info',
                'message': 'Test message',
                'timestamp': '2024-01-15T10:00:00Z'
                # No 'details' field
            }
        ]
        
        test_instance = TestProcessLogsForDisplay()
        processed = test_instance._process_logs_for_display(logs_without_details)
        
        # Should not crash and should process the log
        assert len(processed) == 1
        assert processed[0]['is_decision'] is False
        assert 'structured_data' not in processed[0]


if __name__ == '__main__':
    unittest.main()
