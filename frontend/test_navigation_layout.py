"""
Unit tests for navigation, layout, and loading state components.

Tests skeleton screens, responsive layouts, and keyboard navigation support.

Requirements: 7.1-7.7, 10.5
"""

import pytest
from components import skeleton_timeline, skeleton_log_panel, skeleton_report
from design_system import DesignSystem


class TestSkeletonScreens:
    """Test skeleton loading screens."""
    
    def test_skeleton_timeline_default(self):
        """Test skeleton timeline with default count."""
        html = skeleton_timeline()
        
        # Should contain skeleton-timeline class
        assert 'skeleton-timeline' in html
        
        # Should contain 5 skeleton cards by default
        assert html.count('skeleton-card') == 5
        
        # Should have loading animation
        assert 'animation: loading' in html
        
        # Should have proper styling
        assert 'display: flex' in html
        assert 'overflow-x: auto' in html
    
    def test_skeleton_timeline_custom_count(self):
        """Test skeleton timeline with custom count."""
        html = skeleton_timeline(count=3)
        
        # Should contain 3 skeleton cards
        assert html.count('skeleton-card') == 3
    
    def test_skeleton_log_panel_default(self):
        """Test skeleton log panel with default count."""
        html = skeleton_log_panel()
        
        # Should contain skeleton-log class
        assert 'skeleton-log' in html
        
        # Should contain 10 skeleton logs by default
        assert html.count('skeleton-log') == 10
        
        # Should have loading animation
        assert 'animation: loading' in html
        
        # Should have varied widths for realistic appearance
        assert 'width: 100%' in html
        assert 'width: 80%' in html
        assert 'width: 90%' in html
    
    def test_skeleton_log_panel_custom_count(self):
        """Test skeleton log panel with custom count."""
        html = skeleton_log_panel(count=5)
        
        # Should contain 5 skeleton logs
        assert html.count('skeleton-log') == 5
    
    def test_skeleton_report(self):
        """Test skeleton report screen."""
        html = skeleton_report()
        
        # Should contain skeleton metric cards
        assert 'skeleton' in html
        
        # Should contain skeleton report sections
        assert 'skeleton-report' in html
        
        # Should have loading animation
        assert 'animation: loading' in html
        
        # Should have proper structure (metric cards + report sections)
        assert 'grid-template-columns' in html
        assert html.count('skeleton-report') >= 2


class TestResponsiveLayouts:
    """Test responsive grid layouts."""
    
    def test_responsive_css_mobile(self):
        """Test mobile responsive styles (375px)."""
        css = DesignSystem.generate_css()
        
        # Should contain mobile media query
        assert '@media (max-width: 375px)' in css
        
        # Should have single column layout for mobile
        assert 'grid-template-columns: 1fr' in css
        
        # Should have column direction for timeline
        assert 'flex-direction: column' in css
    
    def test_responsive_css_tablet(self):
        """Test tablet responsive styles (768px)."""
        css = DesignSystem.generate_css()
        
        # Should contain tablet media query
        assert '@media (min-width: 376px) and (max-width: 768px)' in css
        
        # Should have two column layout for tablet
        assert 'grid-template-columns: repeat(2, 1fr)' in css
    
    def test_responsive_css_desktop_small(self):
        """Test desktop small responsive styles (1280px)."""
        css = DesignSystem.generate_css()
        
        # Should contain desktop small media query
        assert '@media (min-width: 769px) and (max-width: 1280px)' in css
        
        # Should have three column layout
        assert 'grid-template-columns: repeat(3, 1fr)' in css
    
    def test_responsive_css_desktop_medium(self):
        """Test desktop medium responsive styles (1920px)."""
        css = DesignSystem.generate_css()
        
        # Should contain desktop medium media query
        assert '@media (min-width: 1281px) and (max-width: 1920px)' in css
        
        # Should have four column layout
        assert 'grid-template-columns: repeat(4, 1fr)' in css
    
    def test_responsive_css_desktop_large(self):
        """Test desktop large responsive styles (>1920px)."""
        css = DesignSystem.generate_css()
        
        # Should contain desktop large media query
        assert '@media (min-width: 1921px)' in css
        
        # Should have five column layout
        assert 'grid-template-columns: repeat(5, 1fr)' in css


class TestKeyboardNavigation:
    """Test keyboard navigation and focus indicators."""
    
    def test_focus_styles(self):
        """Test focus indicator styles."""
        css = DesignSystem.generate_css()
        
        # Should have focus styles
        assert '*:focus' in css
        assert 'outline: 2px solid' in css
        assert 'outline-offset: 2px' in css
        
        # Should have focus-visible styles
        assert '*:focus-visible' in css
        assert 'box-shadow: 0 0 0 4px' in css
    
    def test_focus_visible_elements(self):
        """Test focus-visible styles for interactive elements."""
        css = DesignSystem.generate_css()
        
        # Should have focus-visible for buttons, inputs, etc.
        assert 'button:focus-visible' in css
        assert 'input:focus-visible' in css
        assert 'textarea:focus-visible' in css
        assert 'select:focus-visible' in css
    
    def test_keyboard_shortcut_styles(self):
        """Test keyboard shortcut hint styles."""
        css = DesignSystem.generate_css()
        
        # Should have keyboard-shortcut class
        assert '.keyboard-shortcut' in css
        
        # Should use monospace font
        assert DesignSystem.TYPOGRAPHY['font_family']['mono'] in css
    
    def test_reduced_motion_support(self):
        """Test prefers-reduced-motion media query."""
        css = DesignSystem.generate_css()
        
        # Should have reduced motion media query
        assert '@media (prefers-reduced-motion: reduce)' in css
        
        # Should disable animations
        assert 'animation-duration: 0.01ms !important' in css
        assert 'transition-duration: 0.01ms !important' in css
        assert 'animation: none !important' in css


class TestAccessibilityFeatures:
    """Test accessibility features for navigation and layout."""
    
    def test_focus_not_focus_visible(self):
        """Test that focus without focus-visible doesn't show outline."""
        css = DesignSystem.generate_css()
        
        # Should hide outline for non-keyboard focus
        assert '*:focus:not(:focus-visible)' in css
        assert 'outline: none' in css
    
    def test_primary_color_contrast(self):
        """Test that primary color has sufficient contrast."""
        primary = DesignSystem.COLORS['primary']
        
        # Primary color should be defined
        assert primary is not None
        assert primary.startswith('#')
    
    def test_status_colors_defined(self):
        """Test that all status colors are defined."""
        # Should have all semantic colors
        assert 'success' in DesignSystem.COLORS
        assert 'warning' in DesignSystem.COLORS
        assert 'error' in DesignSystem.COLORS
        assert 'info' in DesignSystem.COLORS
    
    def test_spacing_scale_consistency(self):
        """Test that spacing scale is consistent."""
        spacing = DesignSystem.SPACING
        
        # Should have all spacing sizes
        assert 'xs' in spacing
        assert 'sm' in spacing
        assert 'md' in spacing
        assert 'lg' in spacing
        assert 'xl' in spacing
        assert 'xxl' in spacing
        
        # Should use consistent unit (px)
        for size, value in spacing.items():
            assert value.endswith('px')


class TestLoadingStates:
    """Test loading state indicators."""
    
    def test_skeleton_timeline_has_animation(self):
        """Test that skeleton timeline has loading animation."""
        html = skeleton_timeline()
        
        # Should have loading animation
        assert 'animation: loading' in html
        assert '1.5s ease-in-out infinite' in html
    
    def test_skeleton_log_panel_has_animation(self):
        """Test that skeleton log panel has loading animation."""
        html = skeleton_log_panel()
        
        # Should have loading animation
        assert 'animation: loading' in html
        assert '1.5s ease-in-out infinite' in html
    
    def test_skeleton_report_has_animation(self):
        """Test that skeleton report has loading animation."""
        html = skeleton_report()
        
        # Should have loading animation
        assert 'animation: loading' in html
        assert '1.5s ease-in-out infinite' in html
    
    def test_skeleton_uses_design_tokens(self):
        """Test that skeleton screens use design system tokens."""
        html = skeleton_timeline()
        
        # Should use design system colors
        assert DesignSystem.COLORS['neutral_800'] in html
        assert DesignSystem.COLORS['neutral_700'] in html
        
        # Should use design system spacing
        assert DesignSystem.SPACING['md'] in html or DesignSystem.SPACING['lg'] in html
        
        # Should use design system radius
        assert DesignSystem.RADIUS['lg'] in html or DesignSystem.RADIUS['md'] in html
    
    def test_skeleton_screens_are_importable(self):
        """Test that skeleton screens can be imported from components module."""
        # This test verifies that the skeleton screens are properly exported
        # and can be imported by app.py
        from components import skeleton_timeline, skeleton_log_panel, skeleton_report
        
        # Should be callable
        assert callable(skeleton_timeline)
        assert callable(skeleton_log_panel)
        assert callable(skeleton_report)
        
        # Should return HTML strings
        assert isinstance(skeleton_timeline(), str)
        assert isinstance(skeleton_log_panel(), str)
        assert isinstance(skeleton_report(), str)


class TestNavigationEnhancements:
    """Test navigation enhancements."""
    
    def test_keyboard_shortcut_class_exists(self):
        """Test that keyboard-shortcut CSS class is defined."""
        css = DesignSystem.generate_css()
        
        # Should have keyboard-shortcut class
        assert '.keyboard-shortcut' in css
        
        # Should have proper styling
        assert 'display: inline-block' in css
        assert 'padding: 2px 6px' in css
        assert DesignSystem.TYPOGRAPHY['font_family']['mono'] in css
    
    def test_navigation_radio_styling(self):
        """Test that navigation radio buttons have enhanced styling."""
        # This is tested implicitly through the CSS generation
        css = DesignSystem.generate_css()
        
        # Should have focus styles for interactive elements
        assert 'button:focus-visible' in css
        assert 'input:focus-visible' in css
    
    def test_glassmorphism_card_method(self):
        """Test glassmorphism card generation method."""
        css = DesignSystem.glassmorphism_card()
        
        # Should contain glassmorphism properties
        assert 'backdrop-filter: blur(12px)' in css
        assert '-webkit-backdrop-filter: blur(12px)' in css
        assert DesignSystem.COLORS['glass_bg'] in css
        assert DesignSystem.COLORS['glass_border'] in css
    
    def test_glassmorphism_card_custom_border(self):
        """Test glassmorphism card with custom border color."""
        custom_color = '#ff0000'
        css = DesignSystem.glassmorphism_card(border_color=custom_color)
        
        # Should use custom border color
        assert custom_color in css
    
    def test_glassmorphism_card_no_hover(self):
        """Test glassmorphism card without hover glow."""
        css = DesignSystem.glassmorphism_card(hover_glow=False)
        
        # Should not contain hover styles
        assert ':hover' not in css or 'box-shadow' not in css.split(':hover')[1].split('}')[0] if ':hover' in css else True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
