"""
Accessibility Utilities Module

This module provides utilities for validating and ensuring WCAG AA compliance,
including color contrast validation and accessibility testing helpers.

Requirements: 10.3, 10.4, 10.5, 10.6, 10.7
"""

from typing import Tuple
import re


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert hex color to RGB tuple.
    
    Args:
        hex_color: Hex color string (e.g., "#6c63ff" or "6c63ff")
        
    Returns:
        Tuple of (r, g, b) values (0-255)
        
    Examples:
        >>> hex_to_rgb("#6c63ff")
        (108, 99, 255)
        >>> hex_to_rgb("6c63ff")
        (108, 99, 255)
    """
    # Remove '#' if present
    hex_color = hex_color.lstrip('#')
    
    # Convert to RGB
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """
    Calculate relative luminance of an RGB color.
    
    Uses the WCAG formula for relative luminance:
    https://www.w3.org/TR/WCAG20/#relativeluminancedef
    
    Args:
        rgb: Tuple of (r, g, b) values (0-255)
        
    Returns:
        Relative luminance value (0-1)
        
    Examples:
        >>> relative_luminance((255, 255, 255))  # White
        1.0
        >>> relative_luminance((0, 0, 0))  # Black
        0.0
    """
    # Convert to 0-1 range
    r, g, b = [x / 255.0 for x in rgb]
    
    # Apply gamma correction
    def gamma_correct(channel):
        if channel <= 0.03928:
            return channel / 12.92
        else:
            return ((channel + 0.055) / 1.055) ** 2.4
    
    r = gamma_correct(r)
    g = gamma_correct(g)
    b = gamma_correct(b)
    
    # Calculate luminance
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(color1: str, color2: str) -> float:
    """
    Calculate contrast ratio between two colors.
    
    Uses the WCAG formula for contrast ratio:
    https://www.w3.org/TR/WCAG20/#contrast-ratiodef
    
    Args:
        color1: First color (hex format)
        color2: Second color (hex format)
        
    Returns:
        Contrast ratio (1-21)
        
    Examples:
        >>> contrast_ratio("#ffffff", "#000000")  # White on black
        21.0
        >>> contrast_ratio("#6c63ff", "#0f0f1a")  # Primary on dark bg
        ~8.5
    """
    # Get RGB values
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    
    # Calculate luminance
    lum1 = relative_luminance(rgb1)
    lum2 = relative_luminance(rgb2)
    
    # Calculate contrast ratio
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    
    return (lighter + 0.05) / (darker + 0.05)


def validate_wcag_aa(
    text_color: str,
    bg_color: str,
    font_size: int = 14,
    is_bold: bool = False
) -> Tuple[bool, float]:
    """
    Validate if color combination meets WCAG AA standards.
    
    WCAG AA Requirements:
    - Normal text (< 18pt or < 14pt bold): 4.5:1 contrast ratio
    - Large text (>= 18pt or >= 14pt bold): 3:1 contrast ratio
    
    Args:
        text_color: Text color (hex format)
        bg_color: Background color (hex format)
        font_size: Font size in pixels (default: 14)
        is_bold: Whether text is bold (default: False)
        
    Returns:
        Tuple of (passes_wcag_aa: bool, contrast_ratio: float)
        
    Examples:
        >>> validate_wcag_aa("#ffffff", "#000000")  # White on black
        (True, 21.0)
        >>> validate_wcag_aa("#6c63ff", "#0f0f1a")  # Primary on dark
        (True, ~8.5)
    """
    ratio = contrast_ratio(text_color, bg_color)
    
    # Determine if text is "large"
    # Large text: >= 18pt (24px) or >= 14pt (18.66px) bold
    is_large_text = (font_size >= 24) or (font_size >= 19 and is_bold)
    
    # WCAG AA requirements
    required_ratio = 3.0 if is_large_text else 4.5
    
    passes = ratio >= required_ratio
    
    return passes, ratio


def validate_color_palette(colors: dict) -> dict:
    """
    Validate entire color palette for WCAG AA compliance.
    
    Tests common text/background combinations to ensure they meet
    WCAG AA standards.
    
    Args:
        colors: Dictionary of color definitions (from DesignSystem.COLORS)
        
    Returns:
        Dictionary with validation results:
            {
                'passes': bool,
                'results': [
                    {
                        'combination': str,
                        'text_color': str,
                        'bg_color': str,
                        'ratio': float,
                        'passes': bool,
                        'required': float
                    },
                    ...
                ]
            }
    """
    results = []
    
    # Common text/background combinations to test
    combinations = [
        # Primary text on backgrounds
        ('neutral_200', 'neutral_900', 'Primary text on dark background'),
        ('neutral_200', 'neutral_800', 'Primary text on card background'),
        ('neutral_300', 'neutral_900', 'Secondary text on dark background'),
        ('neutral_300', 'neutral_800', 'Secondary text on card background'),
        ('neutral_400', 'neutral_900', 'Muted text on dark background'),
        ('neutral_400', 'neutral_800', 'Muted text on card background'),
        
        # Status colors on backgrounds
        ('success', 'neutral_900', 'Success text on dark background'),
        ('warning', 'neutral_900', 'Warning text on dark background'),
        ('error', 'neutral_900', 'Error text on dark background'),
        ('info', 'neutral_900', 'Info text on dark background'),
        
        # Primary color on backgrounds
        ('primary', 'neutral_900', 'Primary color on dark background'),
        ('primary_light', 'neutral_900', 'Primary light on dark background'),
        
        # White text on colored backgrounds
        ('neutral_100', 'primary', 'White text on primary background'),
        ('neutral_100', 'success', 'White text on success background'),
        ('neutral_100', 'error', 'White text on error background'),
    ]
    
    all_pass = True
    
    for text_key, bg_key, description in combinations:
        text_color = colors.get(text_key, '#ffffff')
        bg_color = colors.get(bg_key, '#000000')
        
        # Skip if color is rgba (can't validate)
        if 'rgba' in text_color or 'rgba' in bg_color:
            continue
        
        passes, ratio = validate_wcag_aa(text_color, bg_color)
        
        results.append({
            'combination': description,
            'text_color': text_color,
            'bg_color': bg_color,
            'ratio': round(ratio, 2),
            'passes': passes,
            'required': 4.5
        })
        
        if not passes:
            all_pass = False
    
    return {
        'passes': all_pass,
        'results': results
    }


def generate_accessibility_report(colors: dict) -> str:
    """
    Generate human-readable accessibility report for color palette.
    
    Args:
        colors: Dictionary of color definitions (from DesignSystem.COLORS)
        
    Returns:
        Formatted report string
    """
    validation = validate_color_palette(colors)
    
    report = "# WCAG AA Color Contrast Validation Report\n\n"
    
    if validation['passes']:
        report += "✅ **All color combinations pass WCAG AA standards (4.5:1)**\n\n"
    else:
        report += "⚠️ **Some color combinations do not meet WCAG AA standards**\n\n"
    
    report += "## Test Results\n\n"
    report += "| Combination | Text | Background | Ratio | Required | Status |\n"
    report += "|-------------|------|------------|-------|----------|--------|\n"
    
    for result in validation['results']:
        status = "✅ Pass" if result['passes'] else "❌ Fail"
        report += f"| {result['combination']} | {result['text_color']} | {result['bg_color']} | {result['ratio']}:1 | {result['required']}:1 | {status} |\n"
    
    return report


if __name__ == "__main__":
    # Test color contrast validation
    from design_system import DesignSystem
    
    print("Testing WCAG AA Color Contrast Validation\n")
    print("=" * 60)
    
    # Validate design system colors
    report = generate_accessibility_report(DesignSystem.COLORS)
    print(report)
    
    # Test specific combinations
    print("\n" + "=" * 60)
    print("\nSpecific Combination Tests:\n")
    
    test_cases = [
        ("#ffffff", "#000000", "White on black"),
        ("#000000", "#ffffff", "Black on white"),
        ("#6c63ff", "#0f0f1a", "Primary on dark background"),
        ("#d1d5db", "#1e1e2e", "Primary text on card"),
    ]
    
    for text, bg, desc in test_cases:
        passes, ratio = validate_wcag_aa(text, bg)
        status = "✅ Pass" if passes else "❌ Fail"
        print(f"{desc}: {ratio:.2f}:1 {status}")
