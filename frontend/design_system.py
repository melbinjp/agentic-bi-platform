"""
Design System Module - Glassmorphism Foundations

This module provides centralized design tokens, CSS generation, and theming
for the Streamlit frontend redesign. It implements a modern glassmorphism
design pattern with transparency, backdrop blur, and smooth animations.

Requirements: 1.1, 1.2, 1.3, 1.5, 1.6, 1.7, 1.8, 10.2
"""

from typing import Dict, Optional
import streamlit as st


class DesignSystem:
    """
    Centralized design system with glassmorphism foundations.
    
    Provides design tokens for colors, spacing, typography, shadows, and
    CSS generation methods for consistent styling across the application.
    """
    
    # Color Palette - Modern dark theme with vibrant accents
    COLORS: Dict[str, str] = {
        # Primary colors
        'primary': '#6c63ff',
        'primary_light': '#8b84ff',
        'primary_dark': '#4d45cc',
        'primary_glow': 'rgba(108, 99, 255, 0.3)',
        
        # Semantic colors
        'success': '#10b981',
        'success_dark': '#059669',
        'success_bg': '#064e3b',
        'warning': '#f59e0b',
        'warning_dark': '#d97706',
        'error': '#ef4444',
        'error_dark': '#dc2626',
        'error_bg': '#7f1d1d',
        'info': '#60a5fa',
        
        # Neutral colors (dark theme)
        'neutral_900': '#0f0f1a',  # Darkest background
        'neutral_800': '#1e1e2e',  # Card background
        'neutral_700': '#2a2a3e',  # Elevated surface
        'neutral_600': '#3a3a5e',  # Border color
        'neutral_500': '#4a4a6e',  # Subtle border
        'neutral_400': '#6b7280',  # Muted text
        'neutral_300': '#9ca3af',  # Secondary text
        'neutral_200': '#d1d5db',  # Primary text
        'neutral_100': '#f3f4f6',  # Bright text
        
        # Glass effect colors
        'glass_bg': 'rgba(30, 30, 46, 0.7)',
        'glass_border': 'rgba(255, 255, 255, 0.1)',
        'glass_highlight': 'rgba(255, 255, 255, 0.05)',
    }
    
    # Spacing Scale (8px base unit)
    SPACING: Dict[str, str] = {
        'xs': '4px',
        'sm': '8px',
        'md': '16px',
        'lg': '24px',
        'xl': '32px',
        'xxl': '48px',
        'xxxl': '64px',
    }
    
    # Border Radius
    RADIUS: Dict[str, str] = {
        'sm': '6px',
        'md': '10px',
        'lg': '16px',
        'xl': '24px',
        'full': '9999px',
    }
    
    # Shadows
    SHADOWS: Dict[str, str] = {
        'sm': '0 2px 8px rgba(0, 0, 0, 0.1)',
        'md': '0 4px 16px rgba(0, 0, 0, 0.15)',
        'lg': '0 8px 32px rgba(0, 0, 0, 0.2)',
        'xl': '0 12px 48px rgba(0, 0, 0, 0.3)',
        'glow': '0 0 20px rgba(108, 99, 255, 0.3)',
        'glow_success': '0 0 20px rgba(16, 185, 129, 0.3)',
        'glow_error': '0 0 20px rgba(239, 68, 68, 0.3)',
    }
    
    # Typography
    TYPOGRAPHY: Dict[str, Dict[str, str]] = {
        'font_family': {
            'primary': "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            'mono': "'Courier New', 'Consolas', monospace",
        },
        'font_size': {
            'xs': '11px',
            'sm': '12px',
            'base': '14px',
            'md': '16px',
            'lg': '18px',
            'xl': '20px',
            'xxl': '24px',
            'xxxl': '32px',
        },
        'font_weight': {
            'light': '300',
            'normal': '400',
            'medium': '500',
            'semibold': '600',
            'bold': '700',
        },
        'line_height': {
            'tight': '1.2',
            'normal': '1.5',
            'relaxed': '1.75',
        },
    }
    
    # Animation Timing
    ANIMATION: Dict[str, str] = {
        'duration_fast': '150ms',
        'duration_normal': '250ms',
        'duration_slow': '400ms',
        'easing': 'cubic-bezier(0.4, 0, 0.2, 1)',
        'easing_bounce': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
    }
    
    @staticmethod
    @st.cache_data(show_spinner=False)
    def generate_css() -> str:
        """
        Generate complete CSS stylesheet with glassmorphism effects.
        
        Cached to avoid regenerating CSS on every page load.
        
        Returns:
            str: Complete CSS stylesheet as a string
        """
        colors = DesignSystem.COLORS
        spacing = DesignSystem.SPACING
        radius = DesignSystem.RADIUS
        shadows = DesignSystem.SHADOWS
        typo = DesignSystem.TYPOGRAPHY
        anim = DesignSystem.ANIMATION
        
        css = f"""
<style>
/* Import Inter font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Global Styles */
html, body, [class*="css"] {{
    font-family: {typo['font_family']['primary']};
    color: {colors['neutral_200']};
    background-color: {colors['neutral_900']};
}}

/* Glassmorphism Card Base */
.glass-card {{
    background: {colors['glass_bg']};
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid {colors['glass_border']};
    border-radius: {radius['lg']};
    box-shadow: {shadows['md']};
    transition: all {anim['duration_normal']} {anim['easing']};
}}

.glass-card:hover {{
    border-color: {colors['primary']};
    box-shadow: {shadows['glow']};
    transform: translateY(-2px);
}}

/* Agent Card */
.agent-card {{
    background: linear-gradient(135deg, {colors['neutral_800']} 0%, {colors['neutral_700']} 100%);
    border: 1px solid {colors['neutral_600']};
    border-radius: {radius['lg']};
    padding: {spacing['md']} {spacing['lg']};
    margin: {spacing['sm']} 0;
    transition: all {anim['duration_normal']} {anim['easing']};
    position: relative;
    overflow: hidden;
}}

.agent-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, {colors['primary']}, {colors['primary_light']});
    opacity: 0;
    transition: opacity {anim['duration_normal']} {anim['easing']};
}}

.agent-card:hover {{
    border-color: {colors['primary']};
    transform: translateX(4px);
    box-shadow: {shadows['glow']};
}}

.agent-card:hover::before {{
    opacity: 1;
}}

/* Status Badges */
.status-badge {{
    display: inline-flex;
    align-items: center;
    gap: {spacing['xs']};
    padding: {spacing['xs']} {spacing['sm']};
    border-radius: {radius['sm']};
    font-size: {typo['font_size']['sm']};
    font-weight: {typo['font_weight']['semibold']};
    transition: all {anim['duration_fast']} {anim['easing']};
}}

.status-running {{
    color: {colors['warning']};
    font-weight: {typo['font_weight']['semibold']};
}}

.status-completed {{
    color: {colors['success']};
    font-weight: {typo['font_weight']['semibold']};
}}

.status-failed {{
    color: {colors['error']};
    font-weight: {typo['font_weight']['semibold']};
}}

.status-queued {{
    color: {colors['neutral_400']};
    font-weight: {typo['font_weight']['medium']};
}}

.status-pending {{
    color: {colors['neutral_400']};
    font-weight: {typo['font_weight']['medium']};
}}

.status-aborted {{
    color: {colors['neutral_300']};
    font-weight: {typo['font_weight']['medium']};
}}

/* Metric Box */
.metric-box {{
    background: {colors['neutral_800']};
    border-radius: {radius['md']};
    padding: {spacing['md']} {spacing['lg']};
    text-align: center;
    border: 1px solid {colors['neutral_600']};
    transition: all {anim['duration_normal']} {anim['easing']};
}}

.metric-box:hover {{
    border-color: {colors['primary']};
    box-shadow: {shadows['glow']};
    transform: scale(1.02);
}}

.metric-value {{
    font-size: {typo['font_size']['xxxl']};
    font-weight: {typo['font_weight']['bold']};
    color: {colors['primary_light']};
    line-height: {typo['line_height']['tight']};
}}

.metric-label {{
    font-size: {typo['font_size']['sm']};
    color: {colors['neutral_400']};
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: {spacing['xs']};
}}

/* Log Panel */
.log-panel {{
    background: {colors['neutral_900']};
    border-radius: {radius['md']};
    padding: {spacing['md']};
    max-height: 400px;
    overflow-y: auto;
    font-family: {typo['font_family']['mono']};
    border: 1px solid {colors['neutral_600']};
}}

.log-entry {{
    font-family: {typo['font_family']['mono']};
    font-size: {typo['font_size']['sm']};
    margin: {spacing['xs']} 0;
    padding: {spacing['xs']} {spacing['sm']};
    border-radius: {radius['sm']};
    transition: background {anim['duration_fast']} {anim['easing']};
}}

.log-entry:hover {{
    background: {colors['neutral_800']};
}}

.log-INFO {{
    color: {colors['info']};
}}

.log-WARN {{
    color: {colors['warning']};
}}

.log-ERROR {{
    color: {colors['error']};
    font-weight: {typo['font_weight']['semibold']};
}}

/* Verdict Badges */
.verdict-badge {{
    display: inline-block;
    padding: {spacing['xs']} {spacing['md']};
    border-radius: {radius['sm']};
    font-weight: {typo['font_weight']['bold']};
    font-size: {typo['font_size']['sm']};
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.verdict-APPROVED {{
    background: {colors['success_bg']};
    color: {colors['success']};
    border: 1px solid {colors['success_dark']};
}}

.verdict-REJECTED {{
    background: {colors['error_bg']};
    color: {colors['error']};
    border: 1px solid {colors['error_dark']};
}}

/* Animations */
@keyframes pulse {{
    0%, 100% {{
        opacity: 1;
        transform: scale(1);
    }}
    50% {{
        opacity: 0.7;
        transform: scale(1.05);
    }}
}}

@keyframes checkmark {{
    0% {{
        transform: scale(0) rotate(0deg);
        opacity: 0;
    }}
    50% {{
        transform: scale(1.2) rotate(180deg);
        opacity: 1;
    }}
    100% {{
        transform: scale(1) rotate(360deg);
        opacity: 1;
    }}
}}

@keyframes shake {{
    0%, 100% {{
        transform: translateX(0);
    }}
    10%, 30%, 50%, 70%, 90% {{
        transform: translateX(-4px);
    }}
    20%, 40%, 60%, 80% {{
        transform: translateX(4px);
    }}
}}

@keyframes fadeIn {{
    from {{
        opacity: 0;
        transform: translateY(10px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

.animate-pulse {{
    animation: pulse 2s {anim['easing']} infinite;
}}

.animate-checkmark {{
    animation: checkmark {anim['duration_slow']} {anim['easing_bounce']} forwards;
}}

.animate-shake {{
    animation: shake 0.5s {anim['easing']} forwards;
}}

.animate-fadeIn {{
    animation: fadeIn {anim['duration_normal']} {anim['easing']} forwards;
}}

/* Scrollbar Styling */
.log-panel::-webkit-scrollbar {{
    width: 8px;
}}

.log-panel::-webkit-scrollbar-track {{
    background: {colors['neutral_800']};
    border-radius: {radius['sm']};
}}

.log-panel::-webkit-scrollbar-thumb {{
    background: {colors['neutral_600']};
    border-radius: {radius['sm']};
    transition: background {anim['duration_fast']} {anim['easing']};
}}

.log-panel::-webkit-scrollbar-thumb:hover {{
    background: {colors['primary']};
}}

/* Button Styles */
.btn-primary {{
    background: linear-gradient(135deg, {colors['primary']} 0%, {colors['primary_dark']} 100%);
    color: white;
    border: none;
    border-radius: {radius['md']};
    padding: {spacing['sm']} {spacing['lg']};
    font-weight: {typo['font_weight']['semibold']};
    cursor: pointer;
    transition: all {anim['duration_normal']} {anim['easing']};
    box-shadow: {shadows['md']};
}}

.btn-primary:hover {{
    transform: translateY(-2px);
    box-shadow: {shadows['glow']};
}}

.btn-secondary {{
    background: {colors['neutral_700']};
    color: {colors['neutral_200']};
    border: 1px solid {colors['neutral_600']};
    border-radius: {radius['md']};
    padding: {spacing['sm']} {spacing['lg']};
    font-weight: {typo['font_weight']['medium']};
    cursor: pointer;
    transition: all {anim['duration_normal']} {anim['easing']};
}}

.btn-secondary:hover {{
    border-color: {colors['primary']};
    background: {colors['neutral_600']};
}}

/* Card Grid Layout */
.card-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: {spacing['lg']};
    margin: {spacing['lg']} 0;
}}

/* Divider */
.divider {{
    height: 1px;
    background: linear-gradient(90deg, transparent, {colors['neutral_600']}, transparent);
    margin: {spacing['lg']} 0;
}}

/* Loading Skeleton */
.skeleton {{
    background: linear-gradient(90deg, {colors['neutral_800']} 25%, {colors['neutral_700']} 50%, {colors['neutral_800']} 75%);
    background-size: 200% 100%;
    animation: loading 1.5s ease-in-out infinite;
    border-radius: {radius['sm']};
}}

@keyframes loading {{
    0% {{
        background-position: 200% 0;
    }}
    100% {{
        background-position: -200% 0;
    }}
}}

/* Skeleton Screens for Loading States */
.skeleton-timeline {{
    display: flex;
    gap: {spacing['md']};
    padding: {spacing['lg']};
    overflow-x: auto;
}}

.skeleton-card {{
    min-width: 280px;
    height: 200px;
    background: linear-gradient(90deg, {colors['neutral_800']} 25%, {colors['neutral_700']} 50%, {colors['neutral_800']} 75%);
    background-size: 200% 100%;
    animation: loading 1.5s ease-in-out infinite;
    border-radius: {radius['lg']};
    border: 1px solid {colors['neutral_600']};
}}

.skeleton-log {{
    height: 20px;
    margin: {spacing['sm']} 0;
    background: linear-gradient(90deg, {colors['neutral_800']} 25%, {colors['neutral_700']} 50%, {colors['neutral_800']} 75%);
    background-size: 200% 100%;
    animation: loading 1.5s ease-in-out infinite;
    border-radius: {radius['sm']};
}}

.skeleton-report {{
    height: 400px;
    background: linear-gradient(90deg, {colors['neutral_800']} 25%, {colors['neutral_700']} 50%, {colors['neutral_800']} 75%);
    background-size: 200% 100%;
    animation: loading 1.5s ease-in-out infinite;
    border-radius: {radius['lg']};
    border: 1px solid {colors['neutral_600']};
}}

/* Responsive Grid Layouts */
@media (max-width: 375px) {{
    /* Mobile - Single column */
    .card-grid {{
        grid-template-columns: 1fr;
    }}
    
    .agent-timeline {{
        flex-direction: column;
    }}
    
    .agent-card {{
        min-width: 100%;
    }}
    
    .job-card-grid {{
        grid-template-columns: 1fr !important;
    }}
}}

@media (min-width: 376px) and (max-width: 768px) {{
    /* Tablet - Two columns */
    .card-grid {{
        grid-template-columns: repeat(2, 1fr);
    }}
    
    .job-card-grid {{
        grid-template-columns: repeat(2, 1fr) !important;
    }}
}}

@media (min-width: 769px) and (max-width: 1280px) {{
    /* Desktop small - Three columns */
    .card-grid {{
        grid-template-columns: repeat(3, 1fr);
    }}
    
    .job-card-grid {{
        grid-template-columns: repeat(2, 1fr) !important;
    }}
}}

@media (min-width: 1281px) and (max-width: 1920px) {{
    /* Desktop medium - Four columns */
    .card-grid {{
        grid-template-columns: repeat(4, 1fr);
    }}
    
    .job-card-grid {{
        grid-template-columns: repeat(3, 1fr) !important;
    }}
}}

@media (min-width: 1921px) {{
    /* Desktop large - Five columns */
    .card-grid {{
        grid-template-columns: repeat(5, 1fr);
    }}
    
    .job-card-grid {{
        grid-template-columns: repeat(4, 1fr) !important;
    }}
}}

/* Focus Styles for Accessibility */
*:focus {{
    outline: 2px solid {colors['primary']};
    outline-offset: 2px;
}}

*:focus:not(:focus-visible) {{
    outline: none;
}}

*:focus-visible {{
    outline: 2px solid {colors['primary']};
    outline-offset: 2px;
    box-shadow: 0 0 0 4px {colors['primary_glow']};
}}

button:focus-visible,
a:focus-visible,
input:focus-visible,
textarea:focus-visible,
select:focus-visible {{
    outline: 2px solid {colors['primary']};
    outline-offset: 2px;
    box-shadow: 0 0 0 4px {colors['primary_glow']};
}}

/* Keyboard Navigation Hints */
.keyboard-shortcut {{
    display: inline-block;
    padding: 2px 6px;
    background: {colors['neutral_700']};
    border: 1px solid {colors['neutral_600']};
    border-radius: {radius['sm']};
    font-family: {typo['font_family']['mono']};
    font-size: {typo['font_size']['xs']};
    color: {colors['neutral_300']};
    margin-left: {spacing['xs']};
}}

/* Reduced Motion Support */
@media (prefers-reduced-motion: reduce) {{
    *,
    *::before,
    *::after {{
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }}
    
    .animate-pulse,
    .animate-checkmark,
    .animate-shake,
    .animate-fadeIn {{
        animation: none !important;
    }}
}}

/* Utility Classes */
.text-primary {{ color: {colors['primary']}; }}
.text-success {{ color: {colors['success']}; }}
.text-warning {{ color: {colors['warning']}; }}
.text-error {{ color: {colors['error']}; }}
.text-muted {{ color: {colors['neutral_400']}; }}

.bg-primary {{ background-color: {colors['primary']}; }}
.bg-success {{ background-color: {colors['success']}; }}
.bg-warning {{ background-color: {colors['warning']}; }}
.bg-error {{ background-color: {colors['error']}; }}

.font-bold {{ font-weight: {typo['font_weight']['bold']}; }}
.font-semibold {{ font-weight: {typo['font_weight']['semibold']}; }}
.font-medium {{ font-weight: {typo['font_weight']['medium']}; }}

.text-xs {{ font-size: {typo['font_size']['xs']}; }}
.text-sm {{ font-size: {typo['font_size']['sm']}; }}
.text-base {{ font-size: {typo['font_size']['base']}; }}
.text-lg {{ font-size: {typo['font_size']['lg']}; }}
.text-xl {{ font-size: {typo['font_size']['xl']}; }}

.rounded-sm {{ border-radius: {radius['sm']}; }}
.rounded-md {{ border-radius: {radius['md']}; }}
.rounded-lg {{ border-radius: {radius['lg']}; }}
.rounded-xl {{ border-radius: {radius['xl']}; }}

.shadow-sm {{ box-shadow: {shadows['sm']}; }}
.shadow-md {{ box-shadow: {shadows['md']}; }}
.shadow-lg {{ box-shadow: {shadows['lg']}; }}
.shadow-glow {{ box-shadow: {shadows['glow']}; }}

/* Glassmorphism Native Expander Overrides */
div[data-testid="stExpander"] {{
    background: {colors['glass_bg']} !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid {colors['glass_border']} !important;
    border-radius: {radius['lg']} !important;
    margin: {spacing['md']} 0 !important;
    box-shadow: {shadows['md']} !important;
    transition: all {anim['duration_normal']} {anim['easing']} !important;
}}

div[data-testid="stExpander"]:hover {{
    border-color: {colors['primary']} !important;
    box-shadow: {shadows['glow']} !important;
}}

div[data-testid="stExpander"] summary {{
    background: transparent !important;
    padding: {spacing['md']} {spacing['lg']} !important;
    color: {colors['neutral_100']} !important;
    font-weight: {typo['font_weight']['semibold']} !important;
}}

div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
    border-top: 1px solid {colors['glass_border']} !important;
    padding: {spacing['md']} {spacing['lg']} !important;
    background: rgba(0, 0, 0, 0.2) !important;
}}
</style>
"""
        return css
    
    @staticmethod
    def glassmorphism_card(
        border_color: Optional[str] = None,
        hover_glow: bool = True,
        padding: str = 'md'
    ) -> str:
        """
        Generate glassmorphism card CSS with customizable properties.
        
        Args:
            border_color: Optional custom border color (hex or rgba)
            hover_glow: Whether to show glow effect on hover
            padding: Padding size key from SPACING dict
            
        Returns:
            str: CSS string for glassmorphism card styling
        """
        colors = DesignSystem.COLORS
        spacing = DesignSystem.SPACING
        radius = DesignSystem.RADIUS
        shadows = DesignSystem.SHADOWS
        anim = DesignSystem.ANIMATION
        
        border = border_color or colors['glass_border']
        padding_value = spacing.get(padding, spacing['md'])
        
        hover_styles = ""
        if hover_glow:
            hover_styles = f"""
    border-color: {colors['primary']};
    box-shadow: {shadows['glow']};
    transform: translateY(-2px);
"""
        
        css = f"""
background: {colors['glass_bg']};
backdrop-filter: blur(12px);
-webkit-backdrop-filter: blur(12px);
border: 1px solid {border};
border-radius: {radius['lg']};
padding: {padding_value};
box-shadow: {shadows['md']};
transition: all {anim['duration_normal']} {anim['easing']};
"""
        
        if hover_glow:
            css += f"""
/* Hover state */
:hover {{
{hover_styles}}}
"""
        
        return css
    
    @staticmethod
    def get_status_color(status: str) -> str:
        """
        Get color for a given status.
        
        Args:
            status: Status string (running, completed, failed, queued, aborted)
            
        Returns:
            str: Hex color code
        """
        status_colors = {
            'running': DesignSystem.COLORS['warning'],
            'completed': DesignSystem.COLORS['success'],
            'failed': DesignSystem.COLORS['error'],
            'queued': DesignSystem.COLORS['neutral_400'],
            'pending': DesignSystem.COLORS['neutral_400'],
            'aborted': DesignSystem.COLORS['neutral_300'],
        }
        return status_colors.get(status.lower(), DesignSystem.COLORS['neutral_400'])
    
    @staticmethod
    def get_status_icon(status: str) -> str:
        """
        Get emoji icon for a given status.
        
        Args:
            status: Status string (running, completed, failed, queued, aborted)
            
        Returns:
            str: Emoji icon
        """
        status_icons = {
            'running': '⚡',
            'completed': '✅',
            'failed': '❌',
            'queued': '⏳',
            'pending': '⏳',
            'aborted': '🛑',
        }
        return status_icons.get(status.lower(), '•')
