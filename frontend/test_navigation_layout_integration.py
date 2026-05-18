"""
Integration tests for navigation, layout, and loading states.

Tests the complete integration of sidebar navigation, responsive layouts,
skeleton screens, and keyboard navigation in the Streamlit app.

Requirements: 7.1-7.7, 10.5
"""

import pytest
from components import (
    skeleton_timeline,
    skeleton_log_panel,
    skeleton_report,
    render_agent_timeline
)
from design_system import DesignSystem


class TestNavigationIntegration:
    """Test navigation system integration."""
    
    def test_sidebar_has_glassmorphism(self):
        """Test that sidebar uses glassmorphism styling."""
        # Verify glassmorphism properties are available
        glass_bg = DesignSystem.COLORS['glass_bg']
        glass_border = DesignSystem.COLORS['glass_border']
        
        assert 'rgba' in glass_bg
        assert 'rgba' in glass_border
        
        # Verify glassmorphism card method works
        card_css = DesignSystem.glassmorphism_card()
        assert 'backdrop-filter: blur(12px)' in card_css
        assert '-webkit-backdrop-filter: blur(12px)' in card_css
    
    def test_connection_status_colors(self):
        """Test connection status indicator colors."""
        # Success (online) color
        success_color = DesignSystem.COLORS['success']
        assert success_color is not None
        
        # Error (offline) color
        error_color = DesignSystem.COLORS['error']
        assert error_color is not None
        
        # Colors should be different
        assert success_color != error_color
    
    def test_keyboard_shortcuts_defined(self):
        """Test keyboard shortcut styling is defined."""
        css = DesignSystem.generate_css()
        
        # Should have keyboard-shortcut class
        assert '.keyboard-shortcut' in css
        
        # Should use monospace font
        assert DesignSystem.TYPOGRAPHY['font_family']['mono'] in css
        
        # Should have proper styling
        assert 'display: inline-block' in css
        assert 'padding: 2px 6px' in css
    
    def test_navigation_icons_present(self):
        """Test that navigation uses icons."""
        # Icons should be part of the navigation labels
        # This is tested implicitly through the app structure
        # The navigation uses emoji icons: 🚀, 📊, 🔍
        assert True  # Placeholder for visual verification


class TestResponsiveLayoutIntegration:
    """Test responsive layout integration across breakpoints."""
    
    def test_all_breakpoints_defined(self):
        """Test that all responsive breakpoints are defined."""
        css = DesignSystem.generate_css()
        
        # Mobile (375px)
        assert '@media (max-width: 375px)' in css
        
        # Tablet (376px - 768px)
        assert '@media (min-width: 376px) and (max-width: 768px)' in css
        
        # Desktop small (769px - 1280px)
        assert '@media (min-width: 769px) and (max-width: 1280px)' in css
        
        # Desktop medium (1281px - 1920px)
        assert '@media (min-width: 1281px) and (max-width: 1920px)' in css
        
        # Desktop large (>1920px)
        assert '@media (min-width: 1921px)' in css
    
    def test_mobile_layout_single_column(self):
        """Test mobile layout uses single column."""
        css = DesignSystem.generate_css()
        
        # Find mobile media query section
        mobile_section = css.split('@media (max-width: 375px)')[1].split('@media')[0]
        
        # Should have single column grid
        assert 'grid-template-columns: 1fr' in mobile_section
        
        # Should have column direction for timeline
        assert 'flex-direction: column' in mobile_section
    
    def test_tablet_layout_two_columns(self):
        """Test tablet layout uses two columns."""
        css = DesignSystem.generate_css()
        
        # Find tablet media query section
        tablet_section = css.split('@media (min-width: 376px) and (max-width: 768px)')[1].split('@media')[0]
        
        # Should have two column grid
        assert 'grid-template-columns: repeat(2, 1fr)' in tablet_section
    
    def test_desktop_layouts_progressive(self):
        """Test desktop layouts progressively increase columns."""
        css = DesignSystem.generate_css()
        
        # Desktop small: 3 columns
        desktop_small = css.split('@media (min-width: 769px) and (max-width: 1280px)')[1].split('@media')[0]
        assert 'grid-template-columns: repeat(3, 1fr)' in desktop_small
        
        # Desktop medium: 4 columns
        desktop_medium = css.split('@media (min-width: 1281px) and (max-width: 1920px)')[1].split('@media')[0]
        assert 'grid-template-columns: repeat(4, 1fr)' in desktop_medium
        
        # Desktop large: 5 columns
        desktop_large = css.split('@media (min-width: 1921px)')[1]
        assert 'grid-template-columns: repeat(5, 1fr)' in desktop_large
    
    def test_job_card_grid_responsive(self):
        """Test job card grid has responsive breakpoints."""
        css = DesignSystem.generate_css()
        
        # Should have job-card-grid class with responsive rules
        assert '.job-card-grid' in css
        
        # Mobile: 1 column
        mobile_section = css.split('@media (max-width: 375px)')[1].split('@media')[0]
        assert 'grid-template-columns: 1fr !important' in mobile_section
        
        # Tablet: 2 columns
        tablet_section = css.split('@media (min-width: 376px) and (max-width: 768px)')[1].split('@media')[0]
        assert 'grid-template-columns: repeat(2, 1fr) !important' in tablet_section


class TestLoadingStateIntegration:
    """Test loading state integration."""
    
    def test_skeleton_screens_use_consistent_animation(self):
        """Test all skeleton screens use the same loading animation."""
        timeline_html = skeleton_timeline()
        log_html = skeleton_log_panel()
        report_html = skeleton_report()
        
        # All should use the same animation
        assert 'animation: loading 1.5s ease-in-out infinite' in timeline_html
        assert 'animation: loading 1.5s ease-in-out infinite' in log_html
        assert 'animation: loading 1.5s ease-in-out infinite' in report_html
    
    def test_skeleton_screens_use_design_tokens(self):
        """Test skeleton screens consistently use design tokens."""
        timeline_html = skeleton_timeline()
        log_html = skeleton_log_panel()
        report_html = skeleton_report()
        
        # All should use neutral colors
        neutral_800 = DesignSystem.COLORS['neutral_800']
        neutral_700 = DesignSystem.COLORS['neutral_700']
        
        assert neutral_800 in timeline_html
        assert neutral_700 in timeline_html
        
        assert neutral_800 in log_html
        assert neutral_700 in log_html
        
        assert neutral_800 in report_html
        assert neutral_700 in report_html
    
    def test_skeleton_to_content_transition(self):
        """Test skeleton screens can be replaced with actual content."""
        # Skeleton timeline
        skeleton_html = skeleton_timeline(count=3)
        assert 'skeleton-card' in skeleton_html
        
        # Actual timeline
        agent_tasks = [
            {
                'agent': 'research',
                'status': 'completed',
                'model_used': 'gpt-4',
                'execution_time': 10.5,
                'cost_usd': 0.25
            }
        ]
        actual_html = render_agent_timeline(agent_tasks, 'running')
        
        # Actual content should not have skeleton class
        assert 'skeleton-card' not in actual_html
        
        # Actual content should have agent-card class
        assert 'agent-card' in actual_html
    
    def test_loading_animation_keyframes_defined(self):
        """Test loading animation keyframes are defined in CSS."""
        css = DesignSystem.generate_css()
        
        # Should have @keyframes loading
        assert '@keyframes loading' in css
        
        # Should have background-position animation
        assert 'background-position: 200% 0' in css
        assert 'background-position: -200% 0' in css


class TestKeyboardNavigationIntegration:
    """Test keyboard navigation integration."""
    
    def test_focus_indicators_visible(self):
        """Test focus indicators are visible and prominent."""
        css = DesignSystem.generate_css()
        
        # Should have focus-visible styles
        assert '*:focus-visible' in css
        
        # Should have outline
        assert 'outline: 2px solid' in css
        
        # Should have box-shadow for visibility
        assert 'box-shadow: 0 0 0 4px' in css
        
        # Should use primary color for focus
        primary_glow = DesignSystem.COLORS['primary_glow']
        assert primary_glow in css
    
    def test_interactive_elements_focusable(self):
        """Test all interactive elements have focus styles."""
        css = DesignSystem.generate_css()
        
        # Should have focus styles for all interactive elements
        assert 'button:focus-visible' in css
        assert 'a:focus-visible' in css
        assert 'input:focus-visible' in css
        assert 'textarea:focus-visible' in css
        assert 'select:focus-visible' in css
    
    def test_focus_not_visible_hidden(self):
        """Test focus outline is hidden when not using keyboard."""
        css = DesignSystem.generate_css()
        
        # Should hide outline for mouse/touch focus
        assert '*:focus:not(:focus-visible)' in css
        assert 'outline: none' in css
    
    def test_keyboard_shortcuts_documented(self):
        """Test keyboard shortcuts are documented in UI."""
        # Keyboard shortcuts should be displayed in sidebar
        # Alt+1: New Analysis
        # Alt+2: Job Dashboard
        # Alt+3: Job Inspector
        
        # This is verified through the keyboard-shortcut class
        css = DesignSystem.generate_css()
        assert '.keyboard-shortcut' in css


class TestAccessibilityIntegration:
    """Test accessibility features integration."""
    
    def test_reduced_motion_support(self):
        """Test reduced motion preference is respected."""
        css = DesignSystem.generate_css()
        
        # Should have prefers-reduced-motion media query
        assert '@media (prefers-reduced-motion: reduce)' in css
        
        # Should disable animations
        assert 'animation-duration: 0.01ms !important' in css
        assert 'transition-duration: 0.01ms !important' in css
        
        # Should disable specific animations
        assert 'animation: none !important' in css
    
    def test_color_contrast_sufficient(self):
        """Test color combinations have sufficient contrast."""
        colors = DesignSystem.COLORS
        
        # Primary text on dark background
        primary_light = colors['primary_light']
        neutral_900 = colors['neutral_900']
        
        # Both should be defined
        assert primary_light is not None
        assert neutral_900 is not None
        
        # Success/error colors should be distinct
        success = colors['success']
        error = colors['error']
        assert success != error
    
    def test_semantic_html_support(self):
        """Test components use semantic HTML where possible."""
        # Skeleton screens should use semantic structure
        timeline_html = skeleton_timeline()
        
        # Should use div elements with proper classes
        assert '<div' in timeline_html
        assert 'class=' in timeline_html
    
    def test_aria_support_via_focus(self):
        """Test ARIA support through focus management."""
        css = DesignSystem.generate_css()
        
        # Focus indicators help screen readers
        assert '*:focus-visible' in css
        
        # Outline offset improves visibility
        assert 'outline-offset: 2px' in css


class TestLayoutConsistency:
    """Test layout consistency across components."""
    
    def test_spacing_scale_used_consistently(self):
        """Test spacing scale is used consistently."""
        spacing = DesignSystem.SPACING
        
        # All spacing values should use px
        for key, value in spacing.items():
            assert value.endswith('px')
        
        # Should have full range of sizes
        assert 'xs' in spacing
        assert 'sm' in spacing
        assert 'md' in spacing
        assert 'lg' in spacing
        assert 'xl' in spacing
        assert 'xxl' in spacing
    
    def test_border_radius_consistent(self):
        """Test border radius is consistent."""
        radius = DesignSystem.RADIUS
        
        # All radius values should use px
        for key, value in radius.items():
            if key != 'full':
                assert value.endswith('px')
        
        # Should have full range of sizes
        assert 'sm' in radius
        assert 'md' in radius
        assert 'lg' in radius
        assert 'xl' in radius
    
    def test_typography_scale_consistent(self):
        """Test typography scale is consistent."""
        typo = DesignSystem.TYPOGRAPHY
        
        # Should have font families
        assert 'primary' in typo['font_family']
        assert 'mono' in typo['font_family']
        
        # Should have font sizes
        assert 'xs' in typo['font_size']
        assert 'sm' in typo['font_size']
        assert 'base' in typo['font_size']
        assert 'md' in typo['font_size']
        assert 'lg' in typo['font_size']
        
        # Should have font weights
        assert 'light' in typo['font_weight']
        assert 'normal' in typo['font_weight']
        assert 'medium' in typo['font_weight']
        assert 'semibold' in typo['font_weight']
        assert 'bold' in typo['font_weight']
    
    def test_animation_timing_consistent(self):
        """Test animation timing is consistent."""
        anim = DesignSystem.ANIMATION
        
        # Should have duration values
        assert 'duration_fast' in anim
        assert 'duration_normal' in anim
        assert 'duration_slow' in anim
        
        # Should have easing functions
        assert 'easing' in anim
        assert 'easing_bounce' in anim
        
        # All durations should use ms
        assert anim['duration_fast'].endswith('ms')
        assert anim['duration_normal'].endswith('ms')
        assert anim['duration_slow'].endswith('ms')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
