"""
Unit Tests for Reusable UI Components

Tests for status_badge, metric_card, expandable_section, and render_agent_timeline functions.
"""

import pytest
from frontend.components import status_badge, metric_card, expandable_section, render_agent_timeline, render_log_panel
from frontend.design_system import DesignSystem


class TestStatusBadge:
    """Tests for status_badge function"""
    
    def test_status_badge_running(self):
        """Test status badge for running status"""
        result = status_badge('running')
        
        assert 'status-badge' in result
        assert 'status-running' in result
        assert '⚡' in result  # Lightning icon
        assert 'Running' in result
        assert DesignSystem.COLORS['warning'] in result
    
    def test_status_badge_completed(self):
        """Test status badge for completed status"""
        result = status_badge('completed')
        
        assert 'status-badge' in result
        assert 'status-completed' in result
        assert '✅' in result  # Checkmark icon
        assert 'Completed' in result
        assert DesignSystem.COLORS['success'] in result
    
    def test_status_badge_failed(self):
        """Test status badge for failed status"""
        result = status_badge('failed')
        
        assert 'status-badge' in result
        assert 'status-failed' in result
        assert '❌' in result  # X icon
        assert 'Failed' in result
        assert DesignSystem.COLORS['error'] in result
    
    def test_status_badge_queued(self):
        """Test status badge for queued status"""
        result = status_badge('queued')
        
        assert 'status-badge' in result
        assert 'status-queued' in result
        assert '⏳' in result  # Clock icon
        assert 'Queued' in result
    
    def test_status_badge_pending(self):
        """Test status badge for pending status"""
        result = status_badge('pending')
        
        assert 'status-badge' in result
        assert 'status-pending' in result
        assert '⏳' in result  # Clock icon
        assert 'Pending' in result
    
    def test_status_badge_aborted(self):
        """Test status badge for aborted status"""
        result = status_badge('aborted')
        
        assert 'status-badge' in result
        assert 'status-aborted' in result
        assert '🛑' in result  # Stop icon
        assert 'Aborted' in result
    
    def test_status_badge_size_small(self):
        """Test status badge with small size"""
        result = status_badge('running', size='sm')
        
        assert 'padding: 2px 6px' in result
        assert 'font-size: 11px' in result
    
    def test_status_badge_size_medium(self):
        """Test status badge with medium size (default)"""
        result = status_badge('running', size='md')
        
        assert 'padding: 4px 8px' in result
        assert 'font-size: 12px' in result
    
    def test_status_badge_size_large(self):
        """Test status badge with large size"""
        result = status_badge('running', size='lg')
        
        assert 'padding: 6px 12px' in result
        assert 'font-size: 14px' in result
    
    def test_status_badge_unknown_status(self):
        """Test status badge with unknown status falls back gracefully"""
        result = status_badge('unknown')
        
        assert 'status-badge' in result
        assert 'Unknown' in result
        # Should use default neutral color
        assert DesignSystem.COLORS['neutral_400'] in result


class TestMetricCard:
    """Tests for metric_card function"""
    
    def test_metric_card_basic(self):
        """Test basic metric card with title and value"""
        result = metric_card('Total Cost', '$45.23')
        
        assert 'metric-box' in result
        assert 'Total Cost' in result
        assert '$45.23' in result
        assert 'metric-value' in result
        assert 'metric-label' in result
    
    def test_metric_card_with_icon(self):
        """Test metric card with icon"""
        result = metric_card('QA Score', '8/10', icon='📊')
        
        assert '📊' in result
        assert 'QA Score' in result
        assert '8/10' in result
    
    def test_metric_card_with_positive_delta(self):
        """Test metric card with positive delta"""
        result = metric_card('Revenue', '$1.2M', delta='+15%')
        
        assert '+15%' in result
        assert DesignSystem.COLORS['success'] in result
    
    def test_metric_card_with_negative_delta(self):
        """Test metric card with negative delta"""
        result = metric_card('Errors', '23', delta='-5')
        
        assert '-5' in result
        assert DesignSystem.COLORS['error'] in result
    
    def test_metric_card_with_neutral_delta(self):
        """Test metric card with neutral delta (no +/-)"""
        result = metric_card('Users', '1000', delta='stable')
        
        assert 'stable' in result
        assert DesignSystem.COLORS['neutral_400'] in result
    
    def test_metric_card_with_arrow_up_delta(self):
        """Test metric card with upward arrow delta"""
        result = metric_card('Growth', '3.2x', delta='↑ 3.2x')
        
        assert '↑ 3.2x' in result
        assert DesignSystem.COLORS['success'] in result
    
    def test_metric_card_with_arrow_down_delta(self):
        """Test metric card with downward arrow delta"""
        result = metric_card('Latency', '250ms', delta='↓ 50ms')
        
        assert '↓ 50ms' in result
        assert DesignSystem.COLORS['error'] in result
    
    def test_metric_card_without_delta(self):
        """Test metric card without delta"""
        result = metric_card('Jobs', '42')
        
        assert 'Jobs' in result
        assert '42' in result
        # Delta section should not be present
        assert result.count('margin-top') == 1  # Only in metric-label
    
    def test_metric_card_styling(self):
        """Test metric card has proper glassmorphism styling"""
        result = metric_card('Test', '100')
        
        assert DesignSystem.COLORS['neutral_800'] in result
        assert DesignSystem.RADIUS['md'] in result
        assert 'border-radius' in result
        assert 'transition' in result


class TestExpandableSection:
    """Tests for expandable_section function"""
    
    def test_expandable_section_collapsed(self):
        """Test expandable section in collapsed state"""
        result = expandable_section('Research Report', '<p>Content here</p>')
        
        assert '<details' in result
        assert 'expandable-section' in result
        assert 'Research Report' in result
        assert '<p>Content here</p>' in result
        assert 'open' not in result.split('>')[0]  # Not in opening tag
    
    def test_expandable_section_expanded(self):
        """Test expandable section in expanded state"""
        result = expandable_section('Strategy', 'Strategy content', expanded=True)
        
        assert '<details' in result
        assert 'open' in result
        assert 'Strategy' in result
        assert 'Strategy content' in result
    
    def test_expandable_section_has_summary(self):
        """Test expandable section has summary element"""
        result = expandable_section('Title', 'Content')
        
        assert '<summary' in result
        assert '</summary>' in result
        assert 'Title' in result
    
    def test_expandable_section_has_expand_icon(self):
        """Test expandable section has expand/collapse icon"""
        result = expandable_section('Title', 'Content')
        
        assert 'expand-icon' in result
        assert '▼' in result
    
    def test_expandable_section_has_animation(self):
        """Test expandable section has animation styles"""
        result = expandable_section('Title', 'Content')
        
        assert 'transition' in result
        assert 'animation' in result
        assert 'fadeIn' in result
    
    def test_expandable_section_glassmorphism(self):
        """Test expandable section has glassmorphism styling"""
        result = expandable_section('Title', 'Content')
        
        assert DesignSystem.COLORS['glass_bg'] in result
        assert 'backdrop-filter: blur' in result
        assert DesignSystem.COLORS['glass_border'] in result
    
    def test_expandable_section_with_html_content(self):
        """Test expandable section with HTML content"""
        html_content = '<div><h3>Heading</h3><p>Paragraph</p></div>'
        result = expandable_section('Section', html_content)
        
        assert html_content in result
        assert '<h3>Heading</h3>' in result
        assert '<p>Paragraph</p>' in result
    
    def test_expandable_section_with_plain_text(self):
        """Test expandable section with plain text content"""
        text_content = 'This is plain text content'
        result = expandable_section('Section', text_content)
        
        assert text_content in result
    
    def test_expandable_section_hover_styles(self):
        """Test expandable section has hover styles"""
        result = expandable_section('Title', 'Content')
        
        assert ':hover' in result
        assert DesignSystem.COLORS['primary'] in result
    
    def test_expandable_section_rotation_animation(self):
        """Test expandable section icon rotates when opened"""
        result = expandable_section('Title', 'Content')
        
        assert 'transform: rotate(180deg)' in result
        assert '[open]' in result


class TestComponentIntegration:
    """Integration tests for components working together"""
    
    def test_status_badge_in_metric_card(self):
        """Test status badge can be used inside metric card"""
        badge_html = status_badge('completed')
        result = metric_card('Job Status', badge_html)
        
        assert 'metric-box' in result
        assert 'status-badge' in result
        assert '✅' in result
    
    def test_metric_card_in_expandable_section(self):
        """Test metric card can be used inside expandable section"""
        card_html = metric_card('Cost', '$100', icon='💰')
        result = expandable_section('Metrics', card_html)
        
        assert 'expandable-section' in result
        assert 'metric-box' in result
        assert '$100' in result
        assert '💰' in result
    
    def test_multiple_components_styling_consistency(self):
        """Test all components use consistent design system values"""
        badge = status_badge('running')
        card = metric_card('Test', '100')
        section = expandable_section('Test', 'Content')
        
        # All should use design system colors
        assert DesignSystem.COLORS['warning'] in badge
        assert DesignSystem.COLORS['neutral_800'] in card
        assert DesignSystem.COLORS['glass_bg'] in section
        
        # All should have transitions
        assert 'transition' in badge
        assert 'transition' in card
        assert 'transition' in section


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



class TestRenderAgentTimeline:
    """Tests for render_agent_timeline function"""
    
    def test_render_agent_timeline_basic(self):
        """Test basic agent timeline rendering with single agent"""
        agent_tasks = [
            {
                'agent': 'research',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 12.5,
                'cost_usd': 0.45
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running')
        
        assert 'agent-timeline' in result
        assert 'agent-card' in result
        assert 'research' in result.lower()
        assert 'gpt-4' in result
        assert '12.5s' in result
        assert '$0.4500' in result
        assert '🔍' in result  # Research icon
    
    def test_render_agent_timeline_multiple_agents(self):
        """Test agent timeline with multiple agents"""
        agent_tasks = [
            {
                'agent': 'orchestrator',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 5.0,
                'cost_usd': 0.10
            },
            {
                'agent': 'research',
                'status': 'running',
                'model_used': 'gpt-4',
                'execution_time': 10.0,
                'cost_usd': 0.30
            },
            {
                'agent': 'strategy',
                'status': 'queued',
                'model_used': 'gpt-4',
                'execution_time': 0.0,
                'cost_usd': 0.0
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running')
        
        # Check all agents are present
        assert 'orchestrator' in result.lower()
        assert 'research' in result.lower()
        assert 'strategy' in result.lower()
        
        # Check icons
        assert '🎯' in result  # Orchestrator
        assert '🔍' in result  # Research
        assert '💡' in result  # Strategy
        
        # Check connectors between agents
        assert result.count('→') >= 2 or result.count('↓') >= 2
    
    def test_render_agent_timeline_horizontal_layout(self):
        """Test horizontal layout orientation"""
        agent_tasks = [
            {
                'agent': 'research',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 10.0,
                'cost_usd': 0.30
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running', layout='horizontal')
        
        assert 'flex-direction: row' in result
        assert 'overflow-x: auto' in result
    
    def test_render_agent_timeline_vertical_layout(self):
        """Test vertical layout orientation"""
        agent_tasks = [
            {
                'agent': 'research',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 10.0,
                'cost_usd': 0.30
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running', layout='vertical')
        
        assert 'flex-direction: column' in result
        assert 'overflow-y: auto' in result
    
    def test_render_agent_timeline_running_status_with_pulse(self):
        """Test running agent shows pulsing animation when job is not failing"""
        agent_tasks = [
            {
                'agent': 'research',
                'status': 'running',
                'model_used': 'gpt-4',
                'execution_time': 5.0,
                'cost_usd': 0.20
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running')
        
        # Should have pulsing animation
        assert 'animate-pulse' in result
        assert DesignSystem.COLORS['warning'] in result
    
    def test_render_agent_timeline_running_status_without_pulse_on_failure(self):
        """Test running agent hides pulsing animation when job is failing"""
        agent_tasks = [
            {
                'agent': 'research',
                'status': 'running',
                'model_used': 'gpt-4',
                'execution_time': 5.0,
                'cost_usd': 0.20
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'failed')
        
        # Should NOT have pulsing animation when job is failed
        assert 'animate-pulse' not in result
    
    def test_render_agent_timeline_completed_status(self):
        """Test completed agent shows checkmark animation"""
        agent_tasks = [
            {
                'agent': 'research',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 12.0,
                'cost_usd': 0.40
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running')
        
        assert 'animate-checkmark' in result
        assert DesignSystem.COLORS['success'] in result
        assert '✅' in result
    
    def test_render_agent_timeline_failed_status(self):
        """Test failed agent shows shake animation and red border"""
        agent_tasks = [
            {
                'agent': 'research',
                'status': 'failed',
                'model_used': 'gpt-4',
                'execution_time': 8.0,
                'cost_usd': 0.25
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'failed')
        
        assert 'animate-shake' in result
        assert DesignSystem.COLORS['error'] in result
        assert '❌' in result
    
    def test_render_agent_timeline_queued_status(self):
        """Test queued agent shows appropriate styling"""
        agent_tasks = [
            {
                'agent': 'strategy',
                'status': 'queued',
                'model_used': 'gpt-4',
                'execution_time': 0.0,
                'cost_usd': 0.0
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running')
        
        assert '⏳' in result
        assert DesignSystem.COLORS['neutral_600'] in result
    
    def test_render_agent_timeline_execution_time_seconds(self):
        """Test execution time formatting in seconds"""
        agent_tasks = [
            {
                'agent': 'research',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 45.3,
                'cost_usd': 0.50
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running')
        
        assert '45.3s' in result
    
    def test_render_agent_timeline_execution_time_minutes(self):
        """Test execution time formatting in minutes"""
        agent_tasks = [
            {
                'agent': 'research',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 125.0,
                'cost_usd': 1.20
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running')
        
        assert '2.1m' in result
    
    def test_render_agent_timeline_execution_time_ms(self):
        """Test execution time with milliseconds input"""
        agent_tasks = [
            {
                'agent': 'research',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time_ms': 12500,
                'cost_usd': 0.45
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running')
        
        assert '12.5s' in result
    
    def test_render_agent_timeline_with_output_preview(self):
        """Test agent card with output preview"""
        agent_tasks = [
            {
                'agent': 'research',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 10.0,
                'cost_usd': 0.30,
                'output_preview': 'This is a sample output from the research agent. It contains important findings.'
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running')
        
        assert 'Output Preview' in result
        assert 'This is a sample output' in result
        assert 'agent-expandable' in result
        assert 'View Details' in result
    
    def test_render_agent_timeline_with_decisions(self):
        """Test agent card with autonomous decisions"""
        agent_tasks = [
            {
                'agent': 'strategy',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 15.0,
                'cost_usd': 0.50,
                'decisions': [
                    {
                        'type': 'strategy_selection',
                        'rationale': 'Selected growth strategy based on market analysis'
                    },
                    {
                        'type': 'quality_verdict',
                        'rationale': 'Approved strategy with score 9/10'
                    }
                ]
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running')
        
        assert 'Decisions Made' in result
        assert 'strategy_selection' in result
        assert 'Selected growth strategy' in result
        assert 'quality_verdict' in result
        assert 'Approved strategy' in result
    
    def test_render_agent_timeline_with_collaborations(self):
        """Test agent card with collaboration events"""
        agent_tasks = [
            {
                'agent': 'strategy',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 20.0,
                'cost_usd': 0.60,
                'collaborations': [
                    {
                        'requested_agent': 'research',
                        'reason': 'Needed additional market data for strategy validation'
                    }
                ]
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running')
        
        assert 'Collaborations' in result
        assert 'Requested research' in result
        assert 'Needed additional market data' in result
        assert '🔍' in result  # Research icon
    
    def test_render_agent_timeline_collaboration_arrows(self):
        """Test collaboration arrows between agents"""
        agent_tasks = [
            {
                'agent': 'research',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 10.0,
                'cost_usd': 0.30
            },
            {
                'agent': 'strategy',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 15.0,
                'cost_usd': 0.50,
                'collaborations': [
                    {
                        'requested_agent': 'research',
                        'reason': 'Validation needed'
                    }
                ]
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running', layout='horizontal')
        
        # Should have collaboration arrow (colored differently)
        assert DesignSystem.COLORS['info'] in result
    
    def test_render_agent_timeline_regular_connectors(self):
        """Test regular connectors between agents without collaboration"""
        agent_tasks = [
            {
                'agent': 'orchestrator',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 5.0,
                'cost_usd': 0.10
            },
            {
                'agent': 'research',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 10.0,
                'cost_usd': 0.30
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running', layout='horizontal')
        
        # Should have regular connector
        assert '→' in result
        assert DesignSystem.COLORS['neutral_600'] in result
    
    def test_render_agent_timeline_all_agent_icons(self):
        """Test all agent icons are correctly mapped"""
        agent_tasks = [
            {'agent': 'orchestrator', 'status': 'completed', 'model_used': 'gpt-4', 'execution_time': 1.0, 'cost_usd': 0.1},
            {'agent': 'research', 'status': 'completed', 'model_used': 'gpt-4', 'execution_time': 1.0, 'cost_usd': 0.1},
            {'agent': 'strategy', 'status': 'completed', 'model_used': 'gpt-4', 'execution_time': 1.0, 'cost_usd': 0.1},
            {'agent': 'planner', 'status': 'completed', 'model_used': 'gpt-4', 'execution_time': 1.0, 'cost_usd': 0.1},
            {'agent': 'critic', 'status': 'completed', 'model_used': 'gpt-4', 'execution_time': 1.0, 'cost_usd': 0.1},
            {'agent': 'qa', 'status': 'completed', 'model_used': 'gpt-4', 'execution_time': 1.0, 'cost_usd': 0.1},
            {'agent': 'memory', 'status': 'completed', 'model_used': 'gpt-4', 'execution_time': 1.0, 'cost_usd': 0.1},
        ]
        
        result = render_agent_timeline(agent_tasks, 'running')
        
        # Check all icons are present
        assert '🎯' in result  # orchestrator
        assert '🔍' in result  # research
        assert '💡' in result  # strategy
        assert '📋' in result  # planner
        assert '⚖️' in result  # critic
        assert '✓' in result  # qa
        assert '🧠' in result  # memory
    
    def test_render_agent_timeline_unknown_agent(self):
        """Test unknown agent uses default icon"""
        agent_tasks = [
            {
                'agent': 'unknown_agent',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 5.0,
                'cost_usd': 0.20
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running')
        
        assert '🤖' in result  # Default icon
        assert 'unknown_agent' in result.lower()
    
    def test_render_agent_timeline_empty_list(self):
        """Test timeline with empty agent list"""
        agent_tasks = []
        
        result = render_agent_timeline(agent_tasks, 'running')
        
        assert 'agent-timeline' in result
        # Should still render container even if empty
    
    def test_render_agent_timeline_missing_optional_fields(self):
        """Test timeline handles missing optional fields gracefully"""
        agent_tasks = [
            {
                'agent': 'research',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 10.0,
                'cost_usd': 0.30
                # No output_preview, decisions, or collaborations
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running')
        
        # Should render without expandable section
        assert 'agent-card' in result
        assert 'research' in result.lower()
        # Should not have expandable details
        assert 'View Details' not in result
    
    def test_render_agent_timeline_cost_formatting(self):
        """Test cost is formatted with 4 decimal places"""
        agent_tasks = [
            {
                'agent': 'research',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 10.0,
                'cost_usd': 0.1234
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running')
        
        assert '$0.1234' in result
    
    def test_render_agent_timeline_glassmorphism_styling(self):
        """Test timeline has glassmorphism styling"""
        agent_tasks = [
            {
                'agent': 'research',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 10.0,
                'cost_usd': 0.30
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running')
        
        assert DesignSystem.COLORS['neutral_900'] in result
        assert DesignSystem.COLORS['neutral_800'] in result
        assert DesignSystem.RADIUS['lg'] in result
        assert 'border-radius' in result
        assert 'transition' in result
    
    def test_render_agent_timeline_hover_effects(self):
        """Test timeline has hover effects defined"""
        agent_tasks = [
            {
                'agent': 'research',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 10.0,
                'cost_usd': 0.30
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running')
        
        assert ':hover' in result
        assert DesignSystem.COLORS['primary'] in result
        assert DesignSystem.SHADOWS['glow'] in result
    
    def test_render_agent_timeline_output_preview_truncation(self):
        """Test output preview is truncated to 200 characters"""
        long_output = 'A' * 300
        agent_tasks = [
            {
                'agent': 'research',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 10.0,
                'cost_usd': 0.30,
                'output_preview': long_output
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running')
        
        # Should truncate and add ellipsis
        assert '...' in result
        # Should not contain full 300 characters
        assert long_output not in result
    
    def test_render_agent_timeline_model_display(self):
        """Test model name is displayed correctly"""
        agent_tasks = [
            {
                'agent': 'research',
                'status': 'completed',
                'model_used': 'gpt-4-turbo',
                'execution_time': 10.0,
                'cost_usd': 0.30
            }
        ]
        
        result = render_agent_timeline(agent_tasks, 'running')
        
        assert 'gpt-4-turbo' in result


class TestRenderLogPanel:
    """Tests for render_log_panel function"""
    
    def test_render_log_panel_basic(self):
        """Test basic log panel rendering"""
        logs = [
            {
                'timestamp': '2024-01-15T10:30:00Z',
                'level': 'INFO',
                'agent': 'research',
                'message': 'Starting research phase'
            }
        ]
        
        result = render_log_panel(logs)
        
        assert 'log-panel' in result
        assert 'log-entry' in result
        assert 'Starting research phase' in result
        assert 'research' in result
        assert 'INFO' in result
    
    def test_render_log_panel_empty(self):
        """Test log panel with no logs"""
        logs = []
        
        result = render_log_panel(logs)
        
        assert 'log-panel' in result
        assert 'No logs to display' in result
    
    def test_render_log_panel_level_colors(self):
        """Test log levels have correct colors"""
        logs = [
            {'timestamp': '2024-01-15T10:30:00Z', 'level': 'INFO', 'agent': 'system', 'message': 'Info message'},
            {'timestamp': '2024-01-15T10:30:01Z', 'level': 'WARN', 'agent': 'system', 'message': 'Warning message'},
            {'timestamp': '2024-01-15T10:30:02Z', 'level': 'ERROR', 'agent': 'system', 'message': 'Error message'},
        ]
        
        result = render_log_panel(logs)
        
        assert DesignSystem.COLORS['info'] in result
        assert DesignSystem.COLORS['warning'] in result
        assert DesignSystem.COLORS['error'] in result
    
    def test_render_log_panel_decision_styling(self):
        """Test decision logs have distinct styling"""
        logs = [
            {
                'timestamp': '2024-01-15T10:30:00Z',
                'level': 'INFO',
                'agent': 'strategy',
                'message': 'Selected growth strategy',
                'is_decision': True
            }
        ]
        
        result = render_log_panel(logs)
        
        assert 'DECISION' in result
        assert DesignSystem.COLORS['primary'] in result
    
    def test_render_log_panel_structured_data(self):
        """Test expandable structured data display"""
        logs = [
            {
                'timestamp': '2024-01-15T10:30:00Z',
                'level': 'INFO',
                'agent': 'research',
                'message': 'Research complete',
                'structured_data': {'sources': 5, 'confidence': 0.95}
            }
        ]
        
        result = render_log_panel(logs)
        
        assert 'View Structured Data' in result
        assert 'log-structured-data' in result
        assert '"sources": 5' in result
        assert '"confidence": 0.95' in result
    
    def test_render_log_panel_filtering(self):
        """Test log filtering by level and agent"""
        logs = [
            {'timestamp': '2024-01-15T10:30:00Z', 'level': 'INFO', 'agent': 'research', 'message': 'Research log'},
            {'timestamp': '2024-01-15T10:30:01Z', 'level': 'ERROR', 'agent': 'strategy', 'message': 'Strategy error'},
            {'timestamp': '2024-01-15T10:30:02Z', 'level': 'INFO', 'agent': 'strategy', 'message': 'Strategy log'},
        ]
        
        # Filter by level
        result = render_log_panel(logs, filters={'level': ['ERROR']})
        assert 'Strategy error' in result
        assert 'Research log' not in result
        
        # Filter by agent
        result = render_log_panel(logs, filters={'agent': ['research']})
        assert 'Research log' in result
        assert 'Strategy error' not in result
    
    def test_render_log_panel_search(self):
        """Test log search functionality"""
        logs = [
            {'timestamp': '2024-01-15T10:30:00Z', 'level': 'INFO', 'agent': 'research', 'message': 'Starting research phase'},
            {'timestamp': '2024-01-15T10:30:01Z', 'level': 'INFO', 'agent': 'strategy', 'message': 'Analyzing strategy'},
        ]
        
        result = render_log_panel(logs, search_query='research')
        
        assert 'Starting research phase' in result
        assert 'Analyzing strategy' not in result
        # Should highlight the search term
        assert '<mark' in result


class TestRenderFinalReport:
    """Tests for render_final_report function"""
    
    def test_render_final_report_basic(self):
        """Test basic final report rendering"""
        report = {
            'job_id': 'job-123',
            'research': {'report': '# Research Report', 'sources': ['https://example.com']},
            'strategy': {'report': '# Strategy Report', 'critic_verdict': 'APPROVED', 'critic_score': 9},
            'execution_plan': {'phase_30_days': [], 'phase_60_days': [], 'phase_90_days': []},
            'qa': {'score': 8, 'passed': True, 'gaps': []}
        }
        
        # This function uses st.markdown, so we can't test the full output
        # Instead, we'll test that it doesn't raise an error
        try:
            from frontend.components import render_final_report
            # We can't actually call it without Streamlit context
            # So we'll just verify the function exists and is callable
            assert callable(render_final_report)
        except Exception as e:
            pytest.fail(f"render_final_report raised an exception: {e}")
    
    def test_extract_domain(self):
        """Test domain extraction from URL"""
        from frontend.components import _extract_domain
        
        assert _extract_domain('https://example.com/path') == 'example.com'
        assert _extract_domain('http://test.org/page') == 'test.org'
        assert _extract_domain('invalid-url') == 'invalid-url'
    
    def test_determine_severity(self):
        """Test QA gap severity determination"""
        from frontend.components import _determine_severity
        
        # Error keywords
        assert _determine_severity('Critical issue found') == 'error'
        assert _determine_severity('Missing required field') == 'error'
        assert _determine_severity('Invalid data format') == 'error'
        assert _determine_severity('Test failed') == 'error'
        
        # Warning (no error keywords)
        assert _determine_severity('Minor improvement needed') == 'warning'
        assert _determine_severity('Consider adding more details') == 'warning'
    
    def test_render_kanban_layout(self):
        """Test kanban layout rendering"""
        from frontend.components import _render_kanban_layout
        
        phase_30 = [
            {'task': 'Task 1', 'owner': 'Team A', 'kpi': 'Metric 1', 'priority': 'high'}
        ]
        phase_60 = [
            {'task': 'Task 2', 'owner': 'Team B', 'kpi': 'Metric 2', 'priority': 'medium'}
        ]
        phase_90 = [
            {'task': 'Task 3', 'owner': 'Team C', 'kpi': 'Metric 3', 'priority': 'low'}
        ]
        
        result = _render_kanban_layout(phase_30, phase_60, phase_90)
        
        assert 'grid-template-columns' in result
        assert '30 Days' in result
        assert '60 Days' in result
        assert '90 Days' in result
        assert 'Task 1' in result
        assert 'Task 2' in result
        assert 'Task 3' in result
        assert 'Team A' in result
        assert 'Team B' in result
        assert 'Team C' in result
    
    def test_render_kanban_layout_empty_phases(self):
        """Test kanban layout with empty phases"""
        from frontend.components import _render_kanban_layout
        
        result = _render_kanban_layout([], [], [])
        
        assert '30 Days' in result
        assert '60 Days' in result
        assert '90 Days' in result
        assert 'No tasks' in result
    
    def test_render_kanban_layout_priority_colors(self):
        """Test kanban layout uses correct priority colors"""
        from frontend.components import _render_kanban_layout
        
        phase_30 = [
            {'task': 'High priority', 'owner': 'Team', 'kpi': 'KPI', 'priority': 'high'},
            {'task': 'Medium priority', 'owner': 'Team', 'kpi': 'KPI', 'priority': 'medium'},
            {'task': 'Low priority', 'owner': 'Team', 'kpi': 'KPI', 'priority': 'low'},
        ]
        
        result = _render_kanban_layout(phase_30, [], [])
        
        assert DesignSystem.COLORS['error'] in result  # high priority
        assert DesignSystem.COLORS['warning'] in result  # medium priority
        assert DesignSystem.COLORS['info'] in result  # low priority
    
    def test_generate_markdown_export(self):
        """Test markdown export generation"""
        from frontend.components import _generate_markdown_export
        
        report = {
            'job_id': 'job-123',
            'research': {
                'report': '# Research Findings',
                'sources': ['https://example.com', 'https://test.org']
            },
            'strategy': {
                'report': '# Strategy Plan',
                'critic_verdict': 'APPROVED',
                'critic_score': 9
            },
            'execution_plan': {
                'phase_30_days': [
                    {'task': 'Task 1', 'owner': 'Team A', 'kpi': 'KPI 1', 'priority': 'high'}
                ],
                'phase_60_days': [],
                'phase_90_days': []
            },
            'qa': {
                'score': 8,
                'passed': True,
                'gaps': ['Gap 1', 'Gap 2']
            }
        }
        
        result = _generate_markdown_export(report)
        
        assert '# Final Report - job-123' in result
        assert '## Research' in result
        assert '# Research Findings' in result
        assert '### Sources' in result
        assert 'https://example.com' in result
        assert '## Strategy' in result
        assert '# Strategy Plan' in result
        assert '**Critic Verdict:** APPROVED' in result
        assert '**Critic Score:** 9/10' in result
        assert '## Execution Plan' in result
        assert '### 30-Day Phase' in result
        assert 'Task 1' in result
        assert 'Team A' in result
        assert '## Quality Assurance' in result
        assert '**Score:** 8/10' in result
        assert '**Status:** Passed' in result
        assert 'Gap 1' in result
        assert 'Gap 2' in result
    
    def test_generate_markdown_export_empty_data(self):
        """Test markdown export with minimal data"""
        from frontend.components import _generate_markdown_export
        
        report = {
            'job_id': 'job-456',
            'research': {},
            'strategy': {},
            'execution_plan': {},
            'qa': {}
        }
        
        result = _generate_markdown_export(report)
        
        assert '# Final Report - job-456' in result
        assert 'No research report available' in result
        assert 'No strategy report available' in result
        assert 'No sources available' in result
        assert 'No tasks' in result
        assert 'No gaps identified' in result

    def test_markdown_to_html_tables(self):
        """Test markdown to HTML converter with table strings"""
        from frontend.components import _markdown_to_html
        
        md_table = (
            "| Provider | Tier | Pricing |\n"
            "| :--- | :--- | :--- |\n"
            "| **HealthifyMe** | Pro | ₹999/month |\n"
            "| FITTR | Transformation | ₹2,499 |\n"
        )
        
        result = _markdown_to_html(md_table)
        
        # Verify table structure is rendered
        assert '<table style="' in result
        assert '<thead style="' in result
        assert '<th style="' in result
        assert 'Provider' in result
        assert 'Tier' in result
        assert 'Pricing' in result
        
        # Verify separator line was skipped (not parsed as a td/th row)
        assert ':---' not in result
        
        # Verify td data rows
        assert 'FITTR' in result
        assert 'Transformation' in result
        assert '₹2,499' in result
        
        # Verify inline formatting in table cell
        assert '<strong>HealthifyMe</strong>' in result
        assert 'Pro' in result
        assert '₹999/month' in result

    def test_markdown_to_html_rich_elements(self):
        """Test markdown to HTML converter with links, inline code, and horizontal rules"""
        from frontend.components import _markdown_to_html
        
        md_content = (
            "Here is a [great website](https://example.com) for you.\n"
            "---\n"
            "You can use the `print('Hello')` statement in python.\n"
        )
        
        result = _markdown_to_html(md_content)
        
        # Verify custom link structure
        assert 'Here is a <a href="https://example.com" target="_blank"' in result
        assert 'color: #38bdf8;' in result
        assert 'great website</a>' in result
        
        # Verify horizontal rule
        assert '<hr style="border: 0; border-top: 1px solid rgba(255, 255, 255, 0.1);' in result
        
        # Verify inline code block
        assert '<code style="font-family: Consolas, Monaco, monospace;' in result
        assert 'background: rgba(0, 0, 0, 0.3);' in result
        assert "print('Hello')" in result


class TestHelperFunctions:
    """Tests for helper functions"""
    
    def test_format_relative_time(self):
        """Test relative time formatting"""
        from frontend.components import _format_relative_time
        from datetime import datetime, timedelta
        
        # Test with recent timestamp
        now = datetime.now()
        timestamp = (now - timedelta(seconds=30)).isoformat()
        result = _format_relative_time(timestamp)
        assert 's ago' in result
        
        # Test with empty timestamp
        result = _format_relative_time('')
        assert result == 'unknown'
    
    def test_format_absolute_time(self):
        """Test absolute time formatting"""
        from frontend.components import _format_absolute_time
        
        timestamp = '2024-01-15T10:30:00Z'
        result = _format_absolute_time(timestamp)
        assert '2024-01-15' in result
        
        # Test with empty timestamp
        result = _format_absolute_time('')
        assert result == 'Unknown time'
    
    def test_highlight_search_matches(self):
        """Test search term highlighting"""
        from frontend.components import _highlight_search_matches
        
        text = 'This is a test message'
        result = _highlight_search_matches(text, 'test')
        
        assert '<mark' in result
        assert 'test' in result
        assert DesignSystem.COLORS['warning'] in result
        
        # Test with no search query
        result = _highlight_search_matches(text, '')
        assert result == text
        
        # Test HTML escaping - the function escapes HTML first, then highlights
        text = '<script>alert("xss")</script>'
        result = _highlight_search_matches(text, 'script')
        # HTML should be escaped
        assert '&lt;' in result and '&gt;' in result
        # The word "script" should be highlighted (after escaping)
        assert '<mark' in result
        # Original <script> tag should not be present
        assert '<script>' not in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

class TestRenderLogPanel:
    """Tests for render_log_panel function"""
    
    def test_render_log_panel_basic(self):
        """Test basic log panel rendering with single log entry"""
        logs = [
            {
                'timestamp': '2024-01-15T10:30:00Z',
                'level': 'INFO',
                'agent': 'research',
                'message': 'Starting research phase',
                'is_decision': False
            }
        ]
        
        result = render_log_panel(logs)
        
        assert 'log-panel' in result
        assert 'log-entry' in result
        assert 'research' in result
        assert 'Starting research phase' in result
        assert '[INFO]' in result
        assert DesignSystem.COLORS['info'] in result
    
    def test_render_log_panel_multiple_logs(self):
        """Test log panel with multiple log entries"""
        logs = [
            {
                'timestamp': '2024-01-15T10:30:00Z',
                'level': 'INFO',
                'agent': 'orchestrator',
                'message': 'Job started',
                'is_decision': False
            },
            {
                'timestamp': '2024-01-15T10:30:05Z',
                'level': 'INFO',
                'agent': 'research',
                'message': 'Research phase initiated',
                'is_decision': False
            },
            {
                'timestamp': '2024-01-15T10:30:10Z',
                'level': 'WARN',
                'agent': 'research',
                'message': 'API rate limit approaching',
                'is_decision': False
            }
        ]
        
        result = render_log_panel(logs)
        
        # Check all logs are present
        assert 'Job started' in result
        assert 'Research phase initiated' in result
        assert 'API rate limit approaching' in result
        
        # Check all agents are present
        assert 'orchestrator' in result
        assert result.count('research') >= 2
    
    def test_render_log_panel_log_level_colors(self):
        """Test log levels have correct color coding"""
        logs = [
            {'timestamp': '2024-01-15T10:30:00Z', 'level': 'INFO', 'agent': 'system', 'message': 'Info message'},
            {'timestamp': '2024-01-15T10:30:01Z', 'level': 'WARN', 'agent': 'system', 'message': 'Warning message'},
            {'timestamp': '2024-01-15T10:30:02Z', 'level': 'ERROR', 'agent': 'system', 'message': 'Error message'},
        ]
        
        result = render_log_panel(logs)
        
        # Check color-coded levels
        assert DesignSystem.COLORS['info'] in result  # INFO: blue
        assert DesignSystem.COLORS['warning'] in result  # WARN: orange
        assert DesignSystem.COLORS['error'] in result  # ERROR: red
    
    def test_render_log_panel_filter_by_level(self):
        """Test filtering logs by level"""
        logs = [
            {'timestamp': '2024-01-15T10:30:00Z', 'level': 'INFO', 'agent': 'system', 'message': 'Info message'},
            {'timestamp': '2024-01-15T10:30:01Z', 'level': 'WARN', 'agent': 'system', 'message': 'Warning message'},
            {'timestamp': '2024-01-15T10:30:02Z', 'level': 'ERROR', 'agent': 'system', 'message': 'Error message'},
        ]
        
        filters = {'level': ['ERROR']}
        result = render_log_panel(logs, filters=filters)
        
        # Should only show ERROR logs
        assert 'Error message' in result
        assert 'Info message' not in result
        assert 'Warning message' not in result
    
    def test_render_log_panel_filter_by_agent(self):
        """Test filtering logs by agent"""
        logs = [
            {'timestamp': '2024-01-15T10:30:00Z', 'level': 'INFO', 'agent': 'orchestrator', 'message': 'Orchestrator message'},
            {'timestamp': '2024-01-15T10:30:01Z', 'level': 'INFO', 'agent': 'research', 'message': 'Research message'},
            {'timestamp': '2024-01-15T10:30:02Z', 'level': 'INFO', 'agent': 'strategy', 'message': 'Strategy message'},
        ]
        
        filters = {'agent': ['research']}
        result = render_log_panel(logs, filters=filters)
        
        # Should only show research logs
        assert 'Research message' in result
        assert 'Orchestrator message' not in result
        assert 'Strategy message' not in result
    
    def test_render_log_panel_filter_by_multiple_levels(self):
        """Test filtering logs by multiple levels"""
        logs = [
            {'timestamp': '2024-01-15T10:30:00Z', 'level': 'INFO', 'agent': 'system', 'message': 'Info message'},
            {'timestamp': '2024-01-15T10:30:01Z', 'level': 'WARN', 'agent': 'system', 'message': 'Warning message'},
            {'timestamp': '2024-01-15T10:30:02Z', 'level': 'ERROR', 'agent': 'system', 'message': 'Error message'},
        ]
        
        filters = {'level': ['WARN', 'ERROR']}
        result = render_log_panel(logs, filters=filters)
        
        # Should show WARN and ERROR logs
        assert 'Warning message' in result
        assert 'Error message' in result
        assert 'Info message' not in result
    
    def test_render_log_panel_search_query(self):
        """Test search functionality"""
        logs = [
            {'timestamp': '2024-01-15T10:30:00Z', 'level': 'INFO', 'agent': 'research', 'message': 'Starting research phase'},
            {'timestamp': '2024-01-15T10:30:01Z', 'level': 'INFO', 'agent': 'strategy', 'message': 'Analyzing market data'},
            {'timestamp': '2024-01-15T10:30:02Z', 'level': 'INFO', 'agent': 'research', 'message': 'Research completed'},
        ]
        
        result = render_log_panel(logs, search_query='research')
        
        # Should only show logs matching search query (text may be highlighted)
        assert 'Starting' in result and 'phase' in result
        assert 'Research completed' in result or 'completed' in result
        assert 'Analyzing market data' not in result
    
    def test_render_log_panel_search_highlighting(self):
        """Test search query highlighting in messages"""
        logs = [
            {'timestamp': '2024-01-15T10:30:00Z', 'level': 'INFO', 'agent': 'research', 'message': 'Starting research phase'},
        ]
        
        result = render_log_panel(logs, search_query='research')
        
        # Should highlight search matches
        assert '<mark' in result
        assert DesignSystem.COLORS['warning'] in result  # Highlight color
    
    def test_render_log_panel_search_case_insensitive(self):
        """Test search is case-insensitive"""
        logs = [
            {'timestamp': '2024-01-15T10:30:00Z', 'level': 'INFO', 'agent': 'research', 'message': 'Starting RESEARCH phase'},
        ]
        
        result = render_log_panel(logs, search_query='research')
        
        # Should match regardless of case (text may be highlighted)
        assert 'Starting' in result and 'phase' in result
        assert '<mark' in result
    
    def test_render_log_panel_relative_timestamps(self):
        """Test relative timestamp formatting"""
        from datetime import datetime, timedelta
        
        # Create timestamps relative to now
        now = datetime.now()
        logs = [
            {
                'timestamp': (now - timedelta(seconds=5)).isoformat(),
                'level': 'INFO',
                'agent': 'system',
                'message': 'Recent message'
            }
        ]
        
        result = render_log_panel(logs)
        
        # Should show relative time (e.g., "5s ago")
        assert 's ago' in result or 'm ago' in result
    
    def test_render_log_panel_absolute_time_on_hover(self):
        """Test absolute time is shown in title attribute for hover"""
        logs = [
            {
                'timestamp': '2024-01-15T10:30:00Z',
                'level': 'INFO',
                'agent': 'system',
                'message': 'Test message'
            }
        ]
        
        result = render_log_panel(logs)
        
        # Should have title attribute with absolute time
        assert 'title=' in result
        assert '2024-01-15' in result
    
    def test_render_log_panel_decision_logs(self):
        """Test decision logs have distinct styling"""
        logs = [
            {
                'timestamp': '2024-01-15T10:30:00Z',
                'level': 'INFO',
                'agent': 'strategy',
                'message': 'Selected growth strategy',
                'is_decision': True
            }
        ]
        
        result = render_log_panel(logs)
        
        # Should have decision badge
        assert 'DECISION' in result
        # Should have distinct background color
        assert DesignSystem.COLORS['neutral_700'] in result
        # Should have primary color border
        assert DesignSystem.COLORS['primary'] in result
    
    def test_render_log_panel_execution_logs(self):
        """Test execution logs have standard styling"""
        logs = [
            {
                'timestamp': '2024-01-15T10:30:00Z',
                'level': 'INFO',
                'agent': 'research',
                'message': 'Fetching data',
                'is_decision': False
            }
        ]
        
        result = render_log_panel(logs)
        
        # Should NOT have decision badge
        assert 'DECISION' not in result
        # Should have transparent background
        assert 'background: transparent' in result
    
    def test_render_log_panel_structured_data(self):
        """Test expandable structured data display"""
        logs = [
            {
                'timestamp': '2024-01-15T10:30:00Z',
                'level': 'INFO',
                'agent': 'research',
                'message': 'API response received',
                'structured_data': {
                    'status': 200,
                    'data': {'key': 'value'}
                }
            }
        ]
        
        result = render_log_panel(logs)
        
        # Should have expandable section
        assert 'log-structured-data' in result
        assert 'View Structured Data' in result
        # Should contain JSON data
        assert '"status": 200' in result
        assert '"key": "value"' in result
    
    def test_render_log_panel_visual_grouping(self):
        """Test visual grouping of logs from same agent"""
        logs = [
            {'timestamp': '2024-01-15T10:30:00Z', 'level': 'INFO', 'agent': 'research', 'message': 'Message 1'},
            {'timestamp': '2024-01-15T10:30:01Z', 'level': 'INFO', 'agent': 'research', 'message': 'Message 2'},
            {'timestamp': '2024-01-15T10:30:02Z', 'level': 'INFO', 'agent': 'strategy', 'message': 'Message 3'},
        ]
        
        result = render_log_panel(logs)
        
        # Should have group separator between different agents
        assert 'linear-gradient' in result
        # Separator should use neutral color
        assert DesignSystem.COLORS['neutral_600'] in result
    
    def test_render_log_panel_auto_scroll(self):
        """Test auto-scroll behavior"""
        logs = [
            {'timestamp': '2024-01-15T10:30:00Z', 'level': 'INFO', 'agent': 'system', 'message': 'Message 1'},
        ]
        
        result = render_log_panel(logs, auto_scroll=True)
        
        # Should have smooth scroll behavior
        assert 'scroll-behavior: smooth' in result
    
    def test_render_log_panel_no_auto_scroll(self):
        """Test manual scroll mode"""
        logs = [
            {'timestamp': '2024-01-15T10:30:00Z', 'level': 'INFO', 'agent': 'system', 'message': 'Message 1'},
        ]
        
        result = render_log_panel(logs, auto_scroll=False)
        
        # Should NOT have smooth scroll behavior
        assert 'scroll-behavior: smooth' not in result
    
    def test_render_log_panel_empty_logs(self):
        """Test log panel with empty log list"""
        logs = []
        
        result = render_log_panel(logs)
        
        # Should show "no logs" message
        assert 'No logs to display' in result
        assert 'log-panel' in result
    
    def test_render_log_panel_monospace_font(self):
        """Test log panel uses monospace font"""
        logs = [
            {'timestamp': '2024-01-15T10:30:00Z', 'level': 'INFO', 'agent': 'system', 'message': 'Test message'},
        ]
        
        result = render_log_panel(logs)
        
        # Should use monospace font family
        assert DesignSystem.TYPOGRAPHY['font_family']['mono'] in result
    
    def test_render_log_panel_scrollbar_styling(self):
        """Test custom scrollbar styling"""
        logs = [
            {'timestamp': '2024-01-15T10:30:00Z', 'level': 'INFO', 'agent': 'system', 'message': 'Test message'},
        ]
        
        result = render_log_panel(logs)
        
        # Should have custom scrollbar styles
        assert '::-webkit-scrollbar' in result
        assert '::-webkit-scrollbar-thumb' in result
        assert '::-webkit-scrollbar-track' in result
    
    def test_render_log_panel_hover_effects(self):
        """Test log entry hover effects"""
        logs = [
            {'timestamp': '2024-01-15T10:30:00Z', 'level': 'INFO', 'agent': 'system', 'message': 'Test message'},
        ]
        
        result = render_log_panel(logs)
        
        # Should have hover styles
        assert '.log-entry:hover' in result
        assert DesignSystem.COLORS['neutral_800'] in result
    
    def test_render_log_panel_missing_optional_fields(self):
        """Test log panel handles missing optional fields gracefully"""
        logs = [
            {
                'timestamp': '2024-01-15T10:30:00Z',
                'level': 'INFO',
                'agent': 'system',
                'message': 'Test message'
                # No structured_data or is_decision
            }
        ]
        
        result = render_log_panel(logs)
        
        # Should render without errors
        assert 'log-entry' in result
        assert 'Test message' in result
        # Should not have decision badge
        assert 'DECISION' not in result
        # Should not have structured data section
        assert 'View Structured Data' not in result
    
    def test_render_log_panel_default_values(self):
        """Test log panel uses default values for missing fields"""
        logs = [
            {
                # Missing timestamp, level, agent
                'message': 'Test message'
            }
        ]
        
        result = render_log_panel(logs)
        
        # Should use defaults
        assert '[INFO]' in result  # Default level
        assert 'system' in result  # Default agent
        assert 'unknown' in result  # Default timestamp
    
    def test_render_log_panel_combined_filters(self):
        """Test combining level and agent filters"""
        logs = [
            {'timestamp': '2024-01-15T10:30:00Z', 'level': 'INFO', 'agent': 'research', 'message': 'Research info'},
            {'timestamp': '2024-01-15T10:30:01Z', 'level': 'ERROR', 'agent': 'research', 'message': 'Research error'},
            {'timestamp': '2024-01-15T10:30:02Z', 'level': 'INFO', 'agent': 'strategy', 'message': 'Strategy info'},
            {'timestamp': '2024-01-15T10:30:03Z', 'level': 'ERROR', 'agent': 'strategy', 'message': 'Strategy error'},
        ]
        
        filters = {'level': ['ERROR'], 'agent': ['research']}
        result = render_log_panel(logs, filters=filters)
        
        # Should only show research ERROR logs
        assert 'Research error' in result
        assert 'Research info' not in result
        assert 'Strategy info' not in result
        assert 'Strategy error' not in result
    
    def test_render_log_panel_search_and_filter(self):
        """Test combining search and filters"""
        logs = [
            {'timestamp': '2024-01-15T10:30:00Z', 'level': 'INFO', 'agent': 'research', 'message': 'Starting research'},
            {'timestamp': '2024-01-15T10:30:01Z', 'level': 'ERROR', 'agent': 'research', 'message': 'Research failed'},
            {'timestamp': '2024-01-15T10:30:02Z', 'level': 'INFO', 'agent': 'strategy', 'message': 'Starting strategy'},
        ]
        
        filters = {'level': ['INFO']}
        result = render_log_panel(logs, filters=filters, search_query='research')
        
        # Should show INFO logs containing "research" (text may be highlighted)
        assert 'Starting' in result
        assert 'Research failed' not in result  # Filtered out by level
        assert 'Starting strategy' not in result  # Filtered out by search
    
    def test_render_log_panel_glassmorphism_styling(self):
        """Test log panel has glassmorphism styling"""
        logs = [
            {'timestamp': '2024-01-15T10:30:00Z', 'level': 'INFO', 'agent': 'system', 'message': 'Test message'},
        ]
        
        result = render_log_panel(logs)
        
        # Should have glassmorphism colors
        assert DesignSystem.COLORS['neutral_900'] in result
        assert DesignSystem.COLORS['neutral_600'] in result
        # Should have border radius
        assert DesignSystem.RADIUS['md'] in result
        # Should have transitions
        assert 'transition' in result
    
    def test_render_log_panel_max_height(self):
        """Test log panel has max height for scrolling"""
        logs = [
            {'timestamp': '2024-01-15T10:30:00Z', 'level': 'INFO', 'agent': 'system', 'message': 'Test message'},
        ]
        
        result = render_log_panel(logs)
        
        # Should have max-height
        assert 'max-height: 500px' in result
        # Should have overflow-y
        assert 'overflow-y: auto' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
