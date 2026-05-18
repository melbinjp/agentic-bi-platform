"""
Unit tests for the design system module.

Tests the DesignSystem class methods and design token generation.
"""

import pytest
from frontend.design_system import DesignSystem


class TestDesignSystem:
    """Test suite for DesignSystem class."""
    
    def test_colors_defined(self):
        """Test that all required colors are defined."""
        assert 'primary' in DesignSystem.COLORS
        assert 'success' in DesignSystem.COLORS
        assert 'warning' in DesignSystem.COLORS
        assert 'error' in DesignSystem.COLORS
        assert 'neutral_900' in DesignSystem.COLORS
        assert 'glass_bg' in DesignSystem.COLORS
    
    def test_spacing_defined(self):
        """Test that spacing scale is defined."""
        assert 'xs' in DesignSystem.SPACING
        assert 'sm' in DesignSystem.SPACING
        assert 'md' in DesignSystem.SPACING
        assert 'lg' in DesignSystem.SPACING
        assert 'xl' in DesignSystem.SPACING
    
    def test_radius_defined(self):
        """Test that border radius values are defined."""
        assert 'sm' in DesignSystem.RADIUS
        assert 'md' in DesignSystem.RADIUS
        assert 'lg' in DesignSystem.RADIUS
        assert 'xl' in DesignSystem.RADIUS
    
    def test_shadows_defined(self):
        """Test that shadow values are defined."""
        assert 'sm' in DesignSystem.SHADOWS
        assert 'md' in DesignSystem.SHADOWS
        assert 'lg' in DesignSystem.SHADOWS
        assert 'glow' in DesignSystem.SHADOWS
    
    def test_generate_css_returns_string(self):
        """Test that generate_css returns a non-empty string."""
        css = DesignSystem.generate_css()
        assert isinstance(css, str)
        assert len(css) > 0
        assert '<style>' in css
        assert '</style>' in css
    
    def test_generate_css_contains_animations(self):
        """Test that generated CSS contains animation keyframes."""
        css = DesignSystem.generate_css()
        assert '@keyframes pulse' in css
        assert '@keyframes checkmark' in css
        assert '@keyframes shake' in css
        assert '@keyframes fadeIn' in css
    
    def test_generate_css_contains_glassmorphism(self):
        """Test that generated CSS contains glassmorphism effects."""
        css = DesignSystem.generate_css()
        assert 'backdrop-filter: blur' in css
        assert '-webkit-backdrop-filter: blur' in css
        assert 'glass-card' in css
    
    def test_generate_css_contains_status_classes(self):
        """Test that generated CSS contains status badge classes."""
        css = DesignSystem.generate_css()
        assert 'status-running' in css
        assert 'status-completed' in css
        assert 'status-failed' in css
        assert 'status-queued' in css
    
    def test_glassmorphism_card_default(self):
        """Test glassmorphism_card with default parameters."""
        css = DesignSystem.glassmorphism_card()
        assert isinstance(css, str)
        assert 'backdrop-filter: blur' in css
        assert 'border-radius' in css
        assert 'box-shadow' in css
    
    def test_glassmorphism_card_custom_border(self):
        """Test glassmorphism_card with custom border color."""
        css = DesignSystem.glassmorphism_card(border_color='#ff0000')
        assert '#ff0000' in css
    
    def test_glassmorphism_card_no_hover_glow(self):
        """Test glassmorphism_card without hover glow."""
        css = DesignSystem.glassmorphism_card(hover_glow=False)
        assert isinstance(css, str)
        # Should not contain hover styles when hover_glow is False
        assert ':hover' not in css
    
    def test_glassmorphism_card_custom_padding(self):
        """Test glassmorphism_card with custom padding."""
        css = DesignSystem.glassmorphism_card(padding='lg')
        assert DesignSystem.SPACING['lg'] in css
    
    def test_get_status_color_running(self):
        """Test get_status_color for running status."""
        color = DesignSystem.get_status_color('running')
        assert color == DesignSystem.COLORS['warning']
    
    def test_get_status_color_completed(self):
        """Test get_status_color for completed status."""
        color = DesignSystem.get_status_color('completed')
        assert color == DesignSystem.COLORS['success']
    
    def test_get_status_color_failed(self):
        """Test get_status_color for failed status."""
        color = DesignSystem.get_status_color('failed')
        assert color == DesignSystem.COLORS['error']
    
    def test_get_status_color_queued(self):
        """Test get_status_color for queued status."""
        color = DesignSystem.get_status_color('queued')
        assert color == DesignSystem.COLORS['neutral_400']
    
    def test_get_status_color_unknown(self):
        """Test get_status_color for unknown status returns default."""
        color = DesignSystem.get_status_color('unknown_status')
        assert color == DesignSystem.COLORS['neutral_400']
    
    def test_get_status_icon_running(self):
        """Test get_status_icon for running status."""
        icon = DesignSystem.get_status_icon('running')
        assert icon == '⚡'
    
    def test_get_status_icon_completed(self):
        """Test get_status_icon for completed status."""
        icon = DesignSystem.get_status_icon('completed')
        assert icon == '✅'
    
    def test_get_status_icon_failed(self):
        """Test get_status_icon for failed status."""
        icon = DesignSystem.get_status_icon('failed')
        assert icon == '❌'
    
    def test_get_status_icon_queued(self):
        """Test get_status_icon for queued status."""
        icon = DesignSystem.get_status_icon('queued')
        assert icon == '⏳'
    
    def test_get_status_icon_aborted(self):
        """Test get_status_icon for aborted status."""
        icon = DesignSystem.get_status_icon('aborted')
        assert icon == '🛑'
    
    def test_get_status_icon_unknown(self):
        """Test get_status_icon for unknown status returns default."""
        icon = DesignSystem.get_status_icon('unknown_status')
        assert icon == '•'
    
    def test_typography_defined(self):
        """Test that typography tokens are defined."""
        assert 'font_family' in DesignSystem.TYPOGRAPHY
        assert 'font_size' in DesignSystem.TYPOGRAPHY
        assert 'font_weight' in DesignSystem.TYPOGRAPHY
        assert 'line_height' in DesignSystem.TYPOGRAPHY
    
    def test_animation_defined(self):
        """Test that animation timing tokens are defined."""
        assert 'duration_fast' in DesignSystem.ANIMATION
        assert 'duration_normal' in DesignSystem.ANIMATION
        assert 'duration_slow' in DesignSystem.ANIMATION
        assert 'easing' in DesignSystem.ANIMATION
    
    def test_css_contains_utility_classes(self):
        """Test that generated CSS contains utility classes."""
        css = DesignSystem.generate_css()
        assert 'text-primary' in css
        assert 'bg-success' in css
        assert 'font-bold' in css
        assert 'rounded-lg' in css
        assert 'shadow-glow' in css
    
    def test_css_contains_accessibility_focus(self):
        """Test that generated CSS contains focus styles for accessibility."""
        css = DesignSystem.generate_css()
        assert '*:focus' in css
        assert 'outline:' in css
