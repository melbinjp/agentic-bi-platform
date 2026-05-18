"""
Reusable UI Components Module

This module provides reusable UI component functions for the Streamlit frontend.
Components include status badges, metric cards, and expandable sections with
glassmorphism styling and smooth animations.

Requirements: 6.1, 6.2, 8.2
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import re
import streamlit as st
try:
    from frontend.design_system import DesignSystem
except ModuleNotFoundError:
    from design_system import DesignSystem

from html import escape as html_escape



def _clean_html(html_str: str) -> str:
    """
    Cleans leading whitespace from lines of an HTML string to prevent
    Streamlit/Markdown parsing issues, while preserving formatting
    inside <pre>...</pre> elements.
    """
    if not html_str:
        return ""
    cleaned_lines = []
    in_pre = False
    for line in html_str.split("\n"):
        if "<pre" in line:
            in_pre = True
        if in_pre:
            cleaned_lines.append(line.rstrip())
        else:
            cleaned_lines.append(line.strip())
        if "</pre>" in line:
            in_pre = False
    return "\n".join(cleaned_lines)


def status_badge(status: str, size: str = 'md') -> str:
    """
    Generate HTML for status badge with icon and color-coded styling.
    
    Args:
        status: Status string (running, completed, failed, queued, pending, aborted)
        size: Badge size ('sm', 'md', 'lg')
        
    Returns:
        HTML string with styled status badge
        
    Examples:
        >>> status_badge('running')
        '<span class="status-badge status-running">⚡ Running</span>'
        
        >>> status_badge('completed', size='lg')
        '<span class="status-badge status-completed" style="...">✅ Completed</span>'
    """
    # Get icon and color from design system
    icon = DesignSystem.get_status_icon(status)
    color = DesignSystem.get_status_color(status)
    
    # Size mapping
    size_styles = {
        'sm': {
            'padding': '2px 6px',
            'font_size': '11px',
            'gap': '3px',
        },
        'md': {
            'padding': '4px 8px',
            'font_size': '12px',
            'gap': '4px',
        },
        'lg': {
            'padding': '6px 12px',
            'font_size': '14px',
            'gap': '6px',
        },
    }
    
    style = size_styles.get(size, size_styles['md'])
    
    # Capitalize status for display
    status_display = status.capitalize()
    
    # ARIA label for accessibility (Requirement 10.4, 10.7)
    aria_label = f"Status: {status_display}"
    
    # Generate HTML with inline styles for size customization and ARIA attributes
    html = f"""<span class="status-badge status-{status.lower()}" role="status" aria-label="{aria_label}" style="display: inline-flex; align-items: center; gap: {style['gap']}; padding: {style['padding']}; border-radius: {DesignSystem.RADIUS['sm']}; font-size: {style['font_size']}; font-weight: {DesignSystem.TYPOGRAPHY['font_weight']['semibold']}; color: {color}; transition: all {DesignSystem.ANIMATION['duration_fast']} {DesignSystem.ANIMATION['easing']};"><span aria-hidden="true">{icon}</span> {status_display}</span>"""
    
    return _clean_html(html)


def metric_card(
    title: str,
    value: str,
    delta: Optional[str] = None,
    icon: Optional[str] = None
) -> str:
    """
    Generate HTML for glassmorphism metric card with optional delta and icon.
    
    Args:
        title: Metric title/label
        value: Metric value (can be number, text, or formatted string)
        delta: Optional delta indicator (e.g., "+12%", "-5", "↑ 3.2x")
        icon: Optional emoji icon to display
        
    Returns:
        HTML string with styled metric card
        
    Examples:
        >>> metric_card("Total Cost", "$45.23")
        '<div class="metric-box">...</div>'
        
        >>> metric_card("QA Score", "8/10", delta="+2", icon="📊")
        '<div class="metric-box">...</div>'
    """
    colors = DesignSystem.COLORS
    spacing = DesignSystem.SPACING
    radius = DesignSystem.RADIUS
    typo = DesignSystem.TYPOGRAPHY
    anim = DesignSystem.ANIMATION
    
    # Determine delta color (green for positive, red for negative)
    delta_html = ""
    if delta:
        # Check if delta indicates positive or negative change
        is_positive = any(char in delta for char in ['+', '↑', '⬆'])
        is_negative = any(char in delta for char in ['-', '↓', '⬇'])
        
        if is_positive:
            delta_color = colors['success']
        elif is_negative:
            delta_color = colors['error']
        else:
            delta_color = colors['neutral_400']
        
        delta_html = f"""
        <div style="
            font-size: {typo['font_size']['sm']};
            color: {delta_color};
            font-weight: {typo['font_weight']['semibold']};
            margin-top: {spacing['xs']};
        " aria-label="Change: {delta}">
            {delta}
        </div>
        """
    
    # Icon HTML with aria-hidden for decorative icons (Requirement 10.7)
    icon_html = ""
    if icon:
        icon_html = f"""
        <div style="
            font-size: {typo['font_size']['xxl']};
            margin-bottom: {spacing['xs']};
            opacity: 0.8;
        " aria-hidden="true">
            {icon}
        </div>
        """
    
    # ARIA label for accessibility (Requirement 10.4)
    aria_label = f"{title}: {value}"
    if delta:
        aria_label += f", {delta}"
    
    # Generate metric card HTML with semantic article element (Requirement 10.3)
    html = f"""
    <article class="metric-box" role="region" aria-label="{aria_label}" style="background: {colors['neutral_800']}; border-radius: {radius['md']}; padding: {spacing['md']} {spacing['lg']}; text-align: center; border: 1px solid {colors['neutral_600']}; transition: all {anim['duration_normal']} {anim['easing']};">
        {icon_html}
        <div class="metric-value" style="font-size: {typo['font_size']['xxxl']}; font-weight: {typo['font_weight']['bold']}; color: {colors['primary_light']}; line-height: {typo['line_height']['tight']};">
            {value}
        </div>
        <div class="metric-label" style="font-size: {typo['font_size']['sm']}; color: {colors['neutral_400']}; text-transform: uppercase; letter-spacing: 0.5px; margin-top: {spacing['xs']};">
            {title}
        </div>
        {delta_html}
    </article>
    """
    
    return _clean_html(html)


def _apply_inline_formatting(text: str) -> str:
    """Helper to apply bold, italic, link, and inline code formatting to plain text strings."""
    # Handle bold (**text**)
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    # Handle italic (*text*)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    # Handle links ([text](url)) with custom sky-blue text and interactive underlines
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank" style="color: #38bdf8; text-decoration: none; border-bottom: 1px dashed rgba(56, 189, 248, 0.4); transition: border-bottom 0.2s;">\1</a>', text)
    # Handle inline code (`code`) with distinct translucent backgrounds and monospaced font family
    text = re.sub(r'`(.*?)`', r'<code style="font-family: Consolas, Monaco, monospace; background: rgba(0, 0, 0, 0.3); padding: 2px 6px; border-radius: 4px; color: #f8f8f2; font-size: 0.9em; border: 1px solid rgba(255, 255, 255, 0.05);">\1</code>', text)
    return text


def _compile_html_table(rows: List[str]) -> str:
    """Compiles markdown table rows into a highly aesthetic, responsive glassmorphic HTML table."""
    if not rows:
        return ""
    
    colors = DesignSystem.COLORS
    radius = DesignSystem.RADIUS
    
    html_out = []
    html_out.append(f'<div style="overflow-x: auto; margin: 16px 0; border-radius: {radius["md"]}; border: 1px solid {colors["glass_border"]}; background: rgba(30, 30, 46, 0.4); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);">')
    html_out.append('<table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; color: rgba(255, 255, 255, 0.85);">')
    
    is_first = True
    
    for row in rows:
        stripped = row.strip()
        # Skip markdown separator rows (e.g. |---|:---|)
        if re.match(r'^\|[\s\-\:\|]+$', stripped):
            continue
            
        cells = [c.strip() for c in stripped.split("|")[1:-1]]
        
        if is_first:
            html_out.append(f'<thead style="background: rgba(56, 189, 248, 0.15); border-bottom: 2px solid rgba(56, 189, 248, 0.3);">')
            html_out.append('<tr>')
            for cell in cells:
                formatted_cell = _apply_inline_formatting(cell)
                html_out.append(f'<th style="padding: 12px 16px; font-weight: 600; color: #38bdf8;">{formatted_cell}</th>')
            html_out.append('</tr>')
            html_out.append('</thead>')
            html_out.append('<tbody>')
            is_first = False
        else:
            html_out.append(f'<tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.05); background: rgba(255, 255, 255, 0.01); transition: background 0.2s;">')
            for cell in cells:
                formatted_cell = _apply_inline_formatting(cell)
                html_out.append(f'<td style="padding: 12px 16px; line-height: 1.5; vertical-align: middle;">{formatted_cell}</td>')
            html_out.append('</tr>')
            
    if not is_first:
        html_out.append('</tbody>')
        
    html_out.append('</table>')
    html_out.append('</div>')
    
    return "\n".join(html_out)


def _markdown_to_html(md: str) -> str:
    """
    Lightweight, robust Markdown-to-HTML converter for rendering reports 
    inside HTML elements where standard markdown engines fail. Supports tables.
    """
    if not md:
        return ""
    
    lines = md.split("\n")
    html_lines = []
    in_list = False
    in_code = False
    in_table = False
    table_rows = []
    
    for line in lines:
        stripped = line.strip()
        
        # Check if this line is part of a markdown table
        is_table_row = stripped.startswith("|") and stripped.endswith("|")
        
        if is_table_row:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            if in_code:
                html_lines.append('</code></pre>')
                in_code = False
            
            if not in_table:
                in_table = True
                table_rows = []
            
            table_rows.append(stripped)
            continue
        else:
            if in_table:
                html_lines.append(_compile_html_table(table_rows))
                in_table = False
                table_rows = []
        
        # Handle code block toggle
        if stripped.startswith("```"):
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            if in_code:
                html_lines.append('</code></pre>')
                in_code = False
            else:
                html_lines.append('<pre style="background: rgba(0, 0, 0, 0.4); padding: 12px; border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.1); overflow-x: auto; margin: 12px 0;"><code style="font-family: Consolas, Monaco, monospace; color: #f8f8f2; font-size: 13px;">')
                in_code = True
            continue
            
        if in_code:
            html_lines.append(html_escape(line))
            continue
            
        # Handle lists
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                html_lines.append('<ul style="margin: 8px 0; padding-left: 24px; list-style-type: disc;">')
                in_list = True
            item_text = stripped[2:]
            item_text = _apply_inline_formatting(item_text)
            html_lines.append(f'<li style="margin: 4px 0; color: rgba(255, 255, 255, 0.85);">{item_text}</li>')
            continue
        else:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
                
        # Handle horizontal rule (three or more dashes)
        if re.match(r'^---+$', stripped):
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            if in_code:
                html_lines.append('</code></pre>')
                in_code = False
            html_lines.append('<hr style="border: 0; border-top: 1px solid rgba(255, 255, 255, 0.1); margin: 16px 0;">')
            continue
                
        # Handle Headings
        if stripped.startswith("### "):
            title = stripped[4:]
            html_lines.append(f'<h4 style="color: #38bdf8; margin-top: 16px; margin-bottom: 8px; font-weight: 600; font-size: 15px;">{title}</h4>')
        elif stripped.startswith("## "):
            title = stripped[3:]
            html_lines.append(f'<h3 style="color: #38bdf8; margin-top: 20px; margin-bottom: 10px; font-weight: 600; font-size: 18px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 4px;">{title}</h3>')
        elif stripped.startswith("# "):
            title = stripped[2:]
            html_lines.append(f'<h2 style="color: #38bdf8; margin-top: 24px; margin-bottom: 12px; font-weight: 700; font-size: 22px;">{title}</h2>')
        elif not stripped:
            html_lines.append('<div style="height: 8px;"></div>')
        else:
            text = _apply_inline_formatting(stripped)
            html_lines.append(f'<p style="margin: 8px 0; color: rgba(255, 255, 255, 0.85); line-height: 1.6;">{text}</p>')
            
    if in_table:
        html_lines.append(_compile_html_table(table_rows))
    if in_list:
        html_lines.append('</ul>')
    if in_code:
        html_lines.append('</code></pre>')
        
    return "\n".join(html_lines)


def expandable_section(
    title: str,
    content: str,
    expanded: bool = False
) -> str:
    """
    Generate HTML for expandable section with smooth animation.
    
    This function creates a collapsible section with a header and content area.
    The expansion/collapse is handled by CSS transitions for smooth animation.
    
    Args:
        title: Section header title
        content: Section content (can be HTML or plain text)
        expanded: Whether section should be expanded by default
        
    Returns:
        HTML string with styled expandable section
        
    Examples:
        >>> expandable_section("Research Report", "<p>Content here</p>")
        '<details class="expandable-section">...</details>'
        
        >>> expandable_section("Strategy", "Strategy content", expanded=True)
        '<details class="expandable-section" open>...</details>'
    """
    colors = DesignSystem.COLORS
    spacing = DesignSystem.SPACING
    radius = DesignSystem.RADIUS
    typo = DesignSystem.TYPOGRAPHY
    anim = DesignSystem.ANIMATION
    
    # Determine if section should be open
    open_attr = "open" if expanded else ""
    
    # ARIA label for accessibility (Requirement 10.4)
    aria_label = f"Expandable section: {title}"
    
    # Render content (convert markdown to HTML if it isn't HTML already)
    content_is_html = content.strip().startswith("<")
    parsed_content = content if content_is_html else _markdown_to_html(content)
    
    # Generate expandable section HTML using semantic <details> and <summary> (Requirement 10.3)
    html = f"""
    <details class="expandable-section" {open_attr} aria-label="{aria_label}" style="background: {colors['glass_bg']}; backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid {colors['glass_border']}; border-radius: {radius['lg']}; margin: {spacing['md']} 0; overflow: hidden; transition: all {anim['duration_normal']} {anim['easing']}; color: {colors['neutral_300']}; line-height: {typo['line_height']['relaxed']};">
        <summary style="padding: {spacing['md']} {spacing['lg']}; font-size: {typo['font_size']['lg']}; font-weight: {typo['font_weight']['semibold']}; color: {colors['neutral_100']}; cursor: pointer; list-style: none; display: flex; align-items: center; justify-content: space-between; transition: all {anim['duration_fast']} {anim['easing']}; user-select: none;" role="button" aria-expanded="{str(expanded).lower()}">
            <span>{title}</span>
            <span class="expand-icon" aria-hidden="true" style="font-size: {typo['font_size']['md']}; transition: transform {anim['duration_normal']} {anim['easing']};">▼</span>
        </summary>

{parsed_content}

    </details>
    
    <style>
        .expandable-section:hover {{
            border-color: {colors['primary']};
        }}
        
        .expandable-section summary:hover {{
            color: {colors['primary_light']};
        }}
        
        .expandable-section summary::-webkit-details-marker {{
            display: none;
        }}
        
        .expandable-section[open] summary .expand-icon {{
            transform: rotate(180deg);
        }}

        .expandable-section > *:not(summary) {{
            padding: 0 {spacing['lg']};
            margin-top: {spacing['sm']};
            margin-bottom: {spacing['sm']};
            animation: fadeIn {anim['duration_normal']} {anim['easing']};
        }}

        .expandable-section > *:last-child {{
            padding-bottom: {spacing['lg']};
        }}
        
        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(-10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
    </style>
    """
    
    return _clean_html(html)



def render_agent_timeline(
    agent_tasks: List[Dict[str, Any]],
    job_status: str,
    layout: str = 'horizontal'
) -> str:
    """
    Render agent execution timeline with status, model, cost, and time.
    
    Displays agent cards in horizontal or vertical flow with glassmorphism styling.
    Shows agent icon, name, status badge, model used, execution time, and cost per card.
    Includes animations for running (pulsing), completed (checkmark), and failed (shake) states.
    Supports expandable cards showing agent output preview and decisions.
    Visualizes collaboration indicators (arrows/lines) between agents when collaboration events exist.
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 3.1, 3.3, 12.1, 12.2, 12.5
    
    Args:
        agent_tasks: List of agent task dictionaries with keys:
            - agent: str (agent role name)
            - status: str (running, completed, failed, queued)
            - model_used: str (LLM model identifier)
            - execution_time: float (seconds) or execution_time_ms: int (milliseconds)
            - cost_usd: float
            - output_preview: str (optional, for expandable cards)
            - decisions: List[Dict] (optional, autonomous decisions made)
            - collaborations: List[Dict] (optional, inter-agent requests)
        job_status: Overall job status
        layout: Timeline orientation ('horizontal' or 'vertical')
        
    Returns:
        HTML string with styled agent timeline
        
    Examples:
        >>> tasks = [
        ...     {
        ...         'agent': 'research',
        ...         'status': 'completed',
        ...         'model_used': 'gpt-4',
        ...         'execution_time': 12.5,
        ...         'cost_usd': 0.45
        ...     }
        ... ]
        >>> html = render_agent_timeline(tasks, 'running')
    """
    colors = DesignSystem.COLORS
    spacing = DesignSystem.SPACING
    radius = DesignSystem.RADIUS
    typo = DesignSystem.TYPOGRAPHY
    anim = DesignSystem.ANIMATION
    
    # Agent icon mapping
    agent_icons = {
        'orchestrator': '🎯',
        'research': '🔍',
        'strategy': '💡',
        'planner': '📋',
        'critic': '⚖️',
        'qa': '✓',
        'memory': '🧠',
    }
    
    # Determine layout direction
    flex_direction = 'row' if layout == 'horizontal' else 'column'
    
    # Build agent cards HTML
    cards_html = []
    
    for idx, task in enumerate(agent_tasks):
        agent_role = task.get('agent') or 'unknown'
        agent_name = html_escape(str(agent_role))
        status = html_escape(str(task.get('status') or 'queued'))
        model_used = html_escape(str(task.get('model_used') or 'N/A'))
        
        # Handle both execution_time (seconds) and execution_time_ms (milliseconds)
        execution_time = task.get('execution_time')
        if execution_time is None:
            execution_time_ms = task.get('execution_time_ms', 0)
            execution_time = execution_time_ms / 1000.0 if execution_time_ms else 0
        
        cost_usd = task.get('cost_usd', 0.0)
        output_preview = task.get('output_preview', '')
        decisions = task.get('decisions', [])
        collaborations = task.get('collaborations', [])
        
        # Get agent icon
        icon = agent_icons.get(agent_role.lower(), '🤖')
        
        # Get status color and icon
        status_color = DesignSystem.get_status_color(status)
        status_icon = DesignSystem.get_status_icon(status)
        
        # Determine animation class based on status
        animation_class = ''
        border_color = colors['neutral_600']
        
        if status.lower() == 'running':
            # Check if job is failing - if so, hide pulsing animation
            if job_status.lower() not in ['failed', 'aborted']:
                animation_class = 'animate-pulse'
            border_color = colors['warning']
        elif status.lower() == 'completed':
            animation_class = 'animate-checkmark'
            border_color = colors['success']
        elif status.lower() == 'failed':
            animation_class = 'animate-shake'
            border_color = colors['error']
        
        # Format execution time
        if execution_time >= 60:
            time_display = f"{execution_time / 60:.1f}m"
        else:
            time_display = f"{execution_time:.1f}s"
        
        # Format cost
        cost_display = f"${cost_usd:.4f}"
        
        # Build expandable content if available
        expandable_content = ''
        if output_preview or decisions or collaborations:
            expandable_parts = []
            
            # Output preview
            if output_preview:
                preview_str = str(output_preview)
                preview_text = preview_str[:200]
                if len(preview_str) > 200:
                    preview_text += '...'
                escaped_preview = html_escape(preview_text)
                expandable_parts.append(f"""
                <div style="margin-bottom: {spacing['md']};">
                    <div style="
                        font-size: {typo['font_size']['sm']};
                        color: {colors['neutral_400']};
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        margin-bottom: {spacing['xs']};
                    ">Output Preview</div>
                    <div style="
                        font-size: {typo['font_size']['sm']};
                        color: {colors['neutral_300']};
                        line-height: {typo['line_height']['relaxed']};
                        font-family: {typo['font_family']['mono']};
                        background: {colors['neutral_900']};
                        padding: {spacing['sm']};
                        border-radius: {radius['sm']};
                    ">{escaped_preview}</div>
                </div>
                """)
            
            # Decisions
            if decisions:
                decisions_html = []
                for decision in decisions:
                    decision_type = decision.get('type') or 'decision'
                    rationale = decision.get('rationale') or ''
                    escaped_type = html_escape(str(decision_type))
                    escaped_rationale = html_escape(str(rationale))
                    decisions_html.append(f"""
                    <div style="
                        background: {colors['neutral_900']};
                        padding: {spacing['sm']};
                        border-radius: {radius['sm']};
                        margin-bottom: {spacing['xs']};
                        border-left: 3px solid {colors['primary']};
                    ">
                        <div style="
                            font-size: {typo['font_size']['xs']};
                            color: {colors['primary_light']};
                            font-weight: {typo['font_weight']['semibold']};
                            text-transform: uppercase;
                            margin-bottom: {spacing['xs']};
                        ">{escaped_type}</div>
                        <div style="
                            font-size: {typo['font_size']['sm']};
                            color: {colors['neutral_300']};
                            line-height: {typo['line_height']['normal']};
                        ">{escaped_rationale}</div>
                    </div>
                    """)
                
                expandable_parts.append(f"""
                <div style="margin-bottom: {spacing['md']};">
                    <div style="
                        font-size: {typo['font_size']['sm']};
                        color: {colors['neutral_400']};
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        margin-bottom: {spacing['xs']};
                    ">Decisions Made</div>
                    {''.join(decisions_html)}
                </div>
                """)
            
            # Collaborations
            if collaborations:
                collab_html = []
                for collab in collaborations:
                    requested_agent = collab.get('requested_agent') or 'unknown'
                    reason = collab.get('reason') or ''
                    collab_icon = agent_icons.get(str(requested_agent).lower(), '🤖')
                    escaped_agent = html_escape(str(requested_agent))
                    escaped_reason = html_escape(str(reason))
                    collab_html.append(f"""
                    <div style="
                        background: {colors['neutral_900']};
                        padding: {spacing['sm']};
                        border-radius: {radius['sm']};
                        margin-bottom: {spacing['xs']};
                        border-left: 3px solid {colors['info']};
                    ">
                        <div style="
                            font-size: {typo['font_size']['xs']};
                            color: {colors['info']};
                            font-weight: {typo['font_weight']['semibold']};
                            margin-bottom: {spacing['xs']};
                        ">{collab_icon} Requested {escaped_agent}</div>
                        <div style="
                            font-size: {typo['font_size']['sm']};
                            color: {colors['neutral_300']};
                            line-height: {typo['line_height']['normal']};
                        ">{escaped_reason}</div>
                    </div>
                    """)
                
                expandable_parts.append(f"""
                <div style="margin-bottom: {spacing['md']};">
                    <div style="
                        font-size: {typo['font_size']['sm']};
                        color: {colors['neutral_400']};
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        margin-bottom: {spacing['xs']};
                    ">Collaborations</div>
                    {''.join(collab_html)}
                </div>
                """)
            
            expandable_content = f"""
            <details class="agent-expandable" style="margin-top: {spacing['md']};">
                <summary style="
                    font-size: {typo['font_size']['sm']};
                    color: {colors['primary_light']};
                    cursor: pointer;
                    list-style: none;
                    user-select: none;
                    font-weight: {typo['font_weight']['semibold']};
                ">
                    <span>▼ View Details</span>
                </summary>
                <div style="margin-top: {spacing['sm']};">
                    {''.join(expandable_parts)}
                </div>
            </details>
            """
        
        # Build agent card
        card_html = f"""
        <div class="agent-card {animation_class}" style="
            background: linear-gradient(135deg, {colors['neutral_800']} 0%, {colors['neutral_700']} 100%);
            border: 2px solid {border_color};
            border-radius: {radius['lg']};
            padding: {spacing['md']} {spacing['lg']};
            margin: {spacing['sm']};
            transition: all {anim['duration_normal']} {anim['easing']};
            position: relative;
            overflow: hidden;
            min-width: 280px;
            max-width: 350px;
        ">
            <!-- Top bar indicator -->
            <div style="
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, {status_color}, {colors['primary_light']});
            "></div>
            
            <!-- Agent header -->
            <div style="
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: {spacing['md']};
            ">
                <div style="display: flex; align-items: center; gap: {spacing['sm']};">
                    <span style="font-size: {typo['font_size']['xxl']};">{icon}</span>
                    <div>
                        <div style="
                            font-size: {typo['font_size']['lg']};
                            font-weight: {typo['font_weight']['semibold']};
                            color: {colors['neutral_100']};
                            text-transform: capitalize;
                        ">{agent_name}</div>
                        <div style="
                            font-size: {typo['font_size']['xs']};
                            color: {colors['neutral_400']};
                        ">{model_used}</div>
                    </div>
                </div>
                <div style="
                    display: inline-flex;
                    align-items: center;
                    gap: {spacing['xs']};
                    padding: {spacing['xs']} {spacing['sm']};
                    border-radius: {radius['sm']};
                    font-size: {typo['font_size']['sm']};
                    font-weight: {typo['font_weight']['semibold']};
                    color: {status_color};
                ">
                    {status_icon} {status.capitalize()}
                </div>
            </div>
            
            <!-- Metrics -->
            <div style="
                display: flex;
                justify-content: space-between;
                gap: {spacing['md']};
                padding-top: {spacing['sm']};
                border-top: 1px solid {colors['neutral_600']};
            ">
                <div style="text-align: center;">
                    <div style="
                        font-size: {typo['font_size']['lg']};
                        font-weight: {typo['font_weight']['bold']};
                        color: {colors['primary_light']};
                    ">{time_display}</div>
                    <div style="
                        font-size: {typo['font_size']['xs']};
                        color: {colors['neutral_400']};
                        text-transform: uppercase;
                    ">Time</div>
                </div>
                <div style="text-align: center;">
                    <div style="
                        font-size: {typo['font_size']['lg']};
                        font-weight: {typo['font_weight']['bold']};
                        color: {colors['success']};
                    ">{cost_display}</div>
                    <div style="
                        font-size: {typo['font_size']['xs']};
                        color: {colors['neutral_400']};
                        text-transform: uppercase;
                    ">Cost</div>
                </div>
            </div>
            
            {expandable_content}
        </div>
        """
        
        cards_html.append(card_html)
        
        # Add collaboration arrow if next agent has collaboration with current agent
        if idx < len(agent_tasks) - 1:
            next_task = agent_tasks[idx + 1]
            next_collaborations = next_task.get('collaborations', [])
            
            # Check if next agent collaborated with current agent
            has_collaboration = any(
                collab.get('requested_agent', '').lower() == agent_name.lower()
                for collab in next_collaborations
            )
            
            if has_collaboration:
                # Add collaboration arrow
                arrow_html = f"""
                <div style="
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 {spacing['sm']};
                    color: {colors['info']};
                    font-size: {typo['font_size']['xl']};
                ">
                    {'→' if layout == 'horizontal' else '↓'}
                </div>
                """
                cards_html.append(arrow_html)
            else:
                # Add regular connector
                connector_html = f"""
                <div style="
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 {spacing['sm']};
                    color: {colors['neutral_600']};
                    font-size: {typo['font_size']['md']};
                ">
                    {'→' if layout == 'horizontal' else '↓'}
                </div>
                """
                cards_html.append(connector_html)
    
    # Build timeline container
    timeline_html = f"""
    <div class="agent-timeline" style="
        display: flex;
        flex-direction: {flex_direction};
        align-items: {'center' if layout == 'horizontal' else 'stretch'};
        gap: {spacing['sm']};
        padding: {spacing['lg']};
        background: {colors['neutral_900']};
        border-radius: {radius['lg']};
        overflow-x: {'auto' if layout == 'horizontal' else 'visible'};
        overflow-y: {'visible' if layout == 'horizontal' else 'auto'};
    ">
        {''.join(cards_html)}
    </div>
    
    <style>
        .agent-card:hover {{
            border-color: {colors['primary']};
            transform: translateX(4px);
            box-shadow: {DesignSystem.SHADOWS['glow']};
        }}
        
        .agent-expandable summary {{
            transition: color {anim['duration_fast']} {anim['easing']};
        }}
        
        .agent-expandable summary:hover {{
            color: {colors['primary']};
        }}
        
        .agent-expandable summary::-webkit-details-marker {{
            display: none;
        }}
        
        .agent-expandable[open] summary span::before {{
            content: '▲ ';
        }}
        
        .agent-expandable:not([open]) summary span::before {{
            content: '▼ ';
        }}
    </style>
    """
    
    return _clean_html(timeline_html)


def skeleton_timeline(count: int = 5) -> str:
    """
    Generate skeleton loading screen for agent timeline.
    
    Args:
        count: Number of skeleton cards to display
        
    Returns:
        HTML string with skeleton timeline
        
    Requirements: 7.6
    """
    colors = DesignSystem.COLORS
    spacing = DesignSystem.SPACING
    radius = DesignSystem.RADIUS
    
    skeleton_cards = []
    for _ in range(count):
        skeleton_cards.append(f"""
        <div class="skeleton-card" style="
            min-width: 280px;
            height: 200px;
            background: linear-gradient(90deg, {colors['neutral_800']} 25%, {colors['neutral_700']} 50%, {colors['neutral_800']} 75%);
            background-size: 200% 100%;
            animation: loading 1.5s ease-in-out infinite;
            border-radius: {radius['lg']};
            border: 1px solid {colors['neutral_600']};
        "></div>
        """)
    
    html = f"""
    <div class="skeleton-timeline" style="
        display: flex;
        gap: {spacing['md']};
        padding: {spacing['lg']};
        overflow-x: auto;
    ">
        {''.join(skeleton_cards)}
    </div>
    """
    
    return _clean_html(html)


def skeleton_log_panel(count: int = 10) -> str:
    """
    Generate skeleton loading screen for log panel.
    
    Args:
        count: Number of skeleton log entries to display
        
    Returns:
        HTML string with skeleton log panel
        
    Requirements: 7.6
    """
    colors = DesignSystem.COLORS
    spacing = DesignSystem.SPACING
    radius = DesignSystem.RADIUS
    
    skeleton_logs = []
    for i in range(count):
        # Vary the width for more realistic appearance
        width = 100 if i % 3 == 0 else (80 if i % 3 == 1 else 90)
        skeleton_logs.append(f"""
        <div class="skeleton-log" style="
            height: 20px;
            width: {width}%;
            margin: {spacing['sm']} 0;
            background: linear-gradient(90deg, {colors['neutral_800']} 25%, {colors['neutral_700']} 50%, {colors['neutral_800']} 75%);
            background-size: 200% 100%;
            animation: loading 1.5s ease-in-out infinite;
            border-radius: {radius['sm']};
        "></div>
        """)
    
    html = f"""
    <div style="
        background: {colors['neutral_900']};
        border-radius: {radius['md']};
        padding: {spacing['md']};
        border: 1px solid {colors['neutral_600']};
    ">
        {''.join(skeleton_logs)}
    </div>
    """
    
    return _clean_html(html)


def skeleton_report() -> str:
    """
    Generate skeleton loading screen for final report.
    
    Returns:
        HTML string with skeleton report
        
    Requirements: 7.6
    """
    colors = DesignSystem.COLORS
    spacing = DesignSystem.SPACING
    radius = DesignSystem.RADIUS
    
    html = f"""
    <div>
        <!-- Skeleton metric cards -->
        <div style="
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: {spacing['md']};
            margin-bottom: {spacing['lg']};
        ">
            <div class="skeleton" style="
                height: 120px;
                border-radius: {radius['md']};
            "></div>
            <div class="skeleton" style="
                height: 120px;
                border-radius: {radius['md']};
            "></div>
            <div class="skeleton" style="
                height: 120px;
                border-radius: {radius['md']};
            "></div>
        </div>
        
        <!-- Skeleton report sections -->
        <div class="skeleton-report" style="
            height: 400px;
            background: linear-gradient(90deg, {colors['neutral_800']} 25%, {colors['neutral_700']} 50%, {colors['neutral_800']} 75%);
            background-size: 200% 100%;
            animation: loading 1.5s ease-in-out infinite;
            border-radius: {radius['lg']};
            border: 1px solid {colors['neutral_600']};
            margin-bottom: {spacing['md']};
        "></div>
        
        <div class="skeleton-report" style="
            height: 300px;
            background: linear-gradient(90deg, {colors['neutral_800']} 25%, {colors['neutral_700']} 50%, {colors['neutral_800']} 75%);
            background-size: 200% 100%;
            animation: loading 1.5s ease-in-out infinite;
            border-radius: {radius['lg']};
            border: 1px solid {colors['neutral_600']};
        "></div>
    </div>
    """
    
    return _clean_html(html)


def render_job_card(job: Dict[str, Any], on_inspect_callback: Optional[callable] = None) -> str:
    """
    Generate HTML for a glassmorphism job card with hover effects and quick actions.
    
    Displays job preview information including company name, status, cost, timestamp,
    and quick action buttons (Inspect, Cancel, Delete).
    
    Requirements: 8.1, 8.2, 8.7
    
    Args:
        job: Job dictionary with keys:
            - job_id: str
            - status: str (running, completed, failed, aborted)
            - company: str (company name or truncated description)
            - created_at: str (ISO timestamp)
            - completed_at: str (ISO timestamp, optional)
            - total_cost_usd: float
        on_inspect_callback: Optional callback function for inspect button
        
    Returns:
        HTML string with styled job card
        
    Examples:
        >>> job = {
        ...     'job_id': 'job-123',
        ...     'status': 'completed',
        ...     'company': 'Acme Corp',
        ...     'created_at': '2024-01-15T10:30:00',
        ...     'total_cost_usd': 2.45
        ... }
        >>> html = render_job_card(job)
    """
    colors = DesignSystem.COLORS
    spacing = DesignSystem.SPACING
    radius = DesignSystem.RADIUS
    typo = DesignSystem.TYPOGRAPHY
    anim = DesignSystem.ANIMATION
    
    # Extract job data
    job_id = job.get('job_id', 'N/A')
    status = job.get('status', 'pending')
    company = job.get('company', 'Unknown Company')
    created_at = job.get('created_at', '')
    completed_at = job.get('completed_at', '')
    cost_usd = job.get('total_cost_usd', 0.0)
    
    # Truncate company name if too long
    if len(company) > 50:
        company_display = company[:47] + "..."
    else:
        company_display = company
    company_display_escaped = html_escape(company_display)
    
    # Truncate job ID for display
    job_id_display = job_id[:16] + "..." if len(job_id) > 16 else job_id
    job_id_display_escaped = html_escape(job_id_display)
    
    # Format timestamp
    try:
        from datetime import datetime
        created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        time_display = created_dt.strftime('%b %d, %Y %H:%M')
    except:
        time_display = created_at[:19] if created_at else 'N/A'
    time_display_escaped = html_escape(time_display)
    
    # Get status color and icon
    status_color = DesignSystem.get_status_color(status)
    status_icon = DesignSystem.get_status_icon(status)
    
    # Format cost
    cost_display = f"${cost_usd:.4f}"
    
    # Generate unique IDs for buttons (to be used with Streamlit)
    inspect_id = f"inspect_{job_id}"
    cancel_id = f"cancel_{job_id}"
    delete_id = f"delete_{job_id}"
    
    # Build job card HTML
    html = f"""
    <div class="job-card glass-card" style="
        background: {colors['glass_bg']};
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid {colors['glass_border']};
        border-radius: {radius['lg']};
        padding: {spacing['lg']};
        transition: all {anim['duration_normal']} {anim['easing']};
        position: relative;
        overflow: hidden;
        cursor: pointer;
    ">
        <!-- Status indicator bar -->
        <div style="
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: {status_color};
        "></div>
        
        <!-- Card header -->
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: {spacing['md']};
        ">
            <div style="flex: 1;">
                <div style="
                    font-size: {typo['font_size']['lg']};
                    font-weight: {typo['font_weight']['semibold']};
                    color: {colors['neutral_100']};
                    margin-bottom: {spacing['xs']};
                ">{company_display_escaped}</div>
                <div style="
                    font-size: {typo['font_size']['xs']};
                    color: {colors['neutral_400']};
                    font-family: {typo['font_family']['mono']};
                ">{job_id_display_escaped}</div>
            </div>
            <div style="
                display: inline-flex;
                align-items: center;
                gap: {spacing['xs']};
                padding: {spacing['xs']} {spacing['sm']};
                border-radius: {radius['sm']};
                font-size: {typo['font_size']['sm']};
                font-weight: {typo['font_weight']['semibold']};
                color: {status_color};
                background: rgba({','.join(str(int(status_color.lstrip('#')[i:i+2], 16)) for i in (0, 2, 4))}, 0.1);
            ">
                {status_icon} {status.capitalize()}
            </div>
        </div>
        
        <!-- Card body -->
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: {spacing['md']} 0;
            border-top: 1px solid {colors['neutral_600']};
            border-bottom: 1px solid {colors['neutral_600']};
        ">
            <div>
                <div style="
                    font-size: {typo['font_size']['xs']};
                    color: {colors['neutral_400']};
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: {spacing['xs']};
                ">Created</div>
                <div style="
                    font-size: {typo['font_size']['sm']};
                    color: {colors['neutral_200']};
                ">{time_display_escaped}</div>
            </div>
            <div style="text-align: right;">
                <div style="
                    font-size: {typo['font_size']['xs']};
                    color: {colors['neutral_400']};
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: {spacing['xs']};
                ">Cost</div>
                <div style="
                    font-size: {typo['font_size']['lg']};
                    font-weight: {typo['font_weight']['bold']};
                    color: {colors['success']};
                ">{cost_display}</div>
            </div>
        </div>
        
        <!-- Card footer with action buttons (rendered by Streamlit) -->
        <div class="job-card-actions" data-job-id="{job_id}" style="margin-top: {spacing['md']};"></div>
    </div>
    
    <style>
        .job-card:hover {{
            border-color: {colors['primary']};
            box-shadow: {DesignSystem.SHADOWS['glow']};
            transform: translateY(-4px);
        }}
    </style>
    """
    
    return html.strip()


def render_final_report(report: Dict[str, Any]) -> None:
    """
    Render interactive final report with expandable sections and export options.
    
    Displays key metrics in glassmorphism metric cards, expandable sections for
    research, strategy, execution plan, and QA, with prominent Critic verdict badge.
    Implements kanban-style execution plan layout and interactive source links.
    
    Args:
        report: Report dictionary with keys:
            - job_id: str
            - research: Dict (report, sources)
            - strategy: Dict (report, critic_verdict, critic_score)
            - execution_plan: Dict (phase_30_days, phase_60_days, phase_90_days)
            - qa: Dict (score, passed, gaps)
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8
    
    Examples:
        >>> report = {
        ...     'job_id': 'job-123',
        ...     'research': {'report': '# Research', 'sources': ['https://example.com']},
        ...     'strategy': {'report': '# Strategy', 'critic_verdict': 'APPROVED', 'critic_score': 9},
        ...     'execution_plan': {'phase_30_days': [], 'phase_60_days': [], 'phase_90_days': []},
        ...     'qa': {'score': 8, 'passed': True, 'gaps': []}
        ... }
        >>> render_final_report(report)
    """
    colors = DesignSystem.COLORS
    spacing = DesignSystem.SPACING
    
    # Extract report data with safe defaults
    job_id = report.get('job_id', 'N/A')
    research = report.get('research', {})
    strategy = report.get('strategy', {})
    execution_plan = report.get('execution_plan', {})
    qa = report.get('qa', {})
    
    # Extract nested data
    research_report = research.get('report', '')
    research_sources = research.get('sources', [])
    
    strategy_report = strategy.get('report', '')
    critic_verdict = strategy.get('critic_verdict', 'PENDING')
    critic_score = strategy.get('critic_score', 0)
    
    phase_30 = execution_plan.get('phase_30_days', [])
    phase_60 = execution_plan.get('phase_60_days', [])
    phase_90 = execution_plan.get('phase_90_days', [])
    
    qa_score = qa.get('score', 0)
    qa_passed = qa.get('passed', False)
    qa_gaps = qa.get('gaps', [])
    
    # Calculate metrics
    total_sources = len(research_sources)
    total_tasks = len(phase_30) + len(phase_60) + len(phase_90)
    
    # Render header
    st.markdown(f"## 📊 Final Report - {job_id}")
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Render key metrics in glassmorphism cards
    st.markdown("### Key Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        qa_icon = "✅" if qa_passed else "⚠️"
        st.markdown(
            metric_card(
                title="QA Score",
                value=f"{qa_score}/10",
                icon=qa_icon
            ),
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            metric_card(
                title="Research Sources",
                value=str(total_sources),
                icon="🔍"
            ),
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            metric_card(
                title="Total Tasks",
                value=str(total_tasks),
                icon="📋"
            ),
            unsafe_allow_html=True
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Render Critic Verdict Badge
    st.markdown("### Critic Verdict")
    
    verdict_class = f"verdict-{critic_verdict}"
    verdict_html = f"""
    <div style="margin: {spacing['md']} 0;">
        <span class="{verdict_class} verdict-badge">
            {critic_verdict}
        </span>
        <span style="margin-left: {spacing['md']}; color: {colors['neutral_300']};">
            Score: <strong style="color: {colors['primary_light']};">{critic_score}/10</strong>
        </span>
    </div>
    """
    st.markdown(verdict_html, unsafe_allow_html=True)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Render Research Section
    st.markdown("### 🔍 Research")
    
    if research_report:
        with st.expander("Research Report", expanded=False):
            st.markdown(research_report)
            
            # Add sources if available
            if research_sources:
                st.markdown("<br><strong>Sources:</strong>", unsafe_allow_html=True)
                for source in research_sources:
                    domain = _extract_domain(source)
                    st.markdown(f"- [🔗 {domain}]({source})")
    else:
        st.info("No research report available")
    
    # Render Strategy Section
    st.markdown("### 🎯 Strategy")
    
    if strategy_report:
        with st.expander("Strategy Report", expanded=False):
            st.markdown(strategy_report)
    else:
        st.info("No strategy report available")
    
    # Render Execution Plan Section (Kanban-style)
    st.markdown("### 📅 Execution Plan")
    
    if total_tasks > 0:
        # Create kanban-style layout with columns
        kanban_html = _render_kanban_layout(phase_30, phase_60, phase_90)
        st.markdown(kanban_html, unsafe_allow_html=True)
    else:
        st.info("No execution plan available")
    
    # Render QA Section
    st.markdown("### ✅ Quality Assurance")
    
    qa_content = f"""
    <div style="margin-bottom: {spacing['md']};">
        <p><strong>Score:</strong> {qa_score}/10</p>
        <p><strong>Status:</strong> {'✅ Passed' if qa_passed else '⚠️ Failed'}</p>
    </div>
    """
    
    # Add QA gaps if available
    if qa_gaps:
        qa_content += "<div style='margin-top: " + spacing['md'] + ";'><strong>Identified Gaps:</strong><ul>"
        for gap in qa_gaps:
            severity = _determine_severity(gap)
            severity_icon = "🔴" if severity == "error" else "🟡"
            severity_color = colors['error'] if severity == "error" else colors['warning']
            
            qa_content += f"""
            <li style="margin: {spacing['xs']} 0; color: {severity_color};">
                {severity_icon} {gap}
            </li>
            """
        qa_content += "</ul></div>"
        
    with st.expander("QA Report", expanded=False):
        st.markdown(qa_content, unsafe_allow_html=True)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Render Export Buttons
    st.markdown("### 📥 Export Report")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Export as JSON
        json_data = json.dumps(report, indent=2)
        st.download_button(
            label="📄 Export JSON",
            data=json_data,
            file_name=f"report_{job_id}.json",
            mime="application/json"
        )
    
    with col2:
        # Export as Markdown
        markdown_data = _generate_markdown_export(report)
        st.download_button(
            label="📝 Export Markdown",
            data=markdown_data,
            file_name=f"report_{job_id}.md",
            mime="text/markdown"
        )
    
    with col3:
        # PDF export placeholder (requires additional library)
        st.button("📕 Export PDF", disabled=True, help="PDF export coming soon")


def _extract_domain(url: str) -> str:
    """
    Extract domain name from URL for display.
    
    Args:
        url: Full URL string
        
    Returns:
        Domain name (e.g., "example.com")
    """
    import re
    match = re.search(r'https?://([^/]+)', url)
    if match:
        return match.group(1)
    return url


def _determine_severity(gap: str) -> str:
    """
    Determine severity level of a QA gap based on keywords.
    
    Args:
        gap: QA gap description string
        
    Returns:
        Severity level: "error" or "warning"
    """
    error_keywords = ['critical', 'error', 'fail', 'missing', 'invalid', 'broken']
    gap_lower = gap.lower()
    
    for keyword in error_keywords:
        if keyword in gap_lower:
            return "error"
    
    return "warning"


def _render_kanban_layout(
    phase_30: List[Dict[str, Any]],
    phase_60: List[Dict[str, Any]],
    phase_90: List[Dict[str, Any]]
) -> str:
    """
    Render execution plan in kanban-style layout with three columns.
    
    Args:
        phase_30: List of tasks for 30-day phase
        phase_60: List of tasks for 60-day phase
        phase_90: List of tasks for 90-day phase
        
    Returns:
        HTML string with kanban layout
    """
    colors = DesignSystem.COLORS
    spacing = DesignSystem.SPACING
    radius = DesignSystem.RADIUS
    
    # Priority color mapping
    priority_colors = {
        'high': colors['error'],
        'medium': colors['warning'],
        'low': colors['info']
    }
    
    kanban_html = f"""<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: {spacing['lg']}; margin: {spacing['lg']} 0;">"""
    
    # Render each phase column
    phases = [
        ("30 Days", phase_30),
        ("60 Days", phase_60),
        ("90 Days", phase_90)
    ]
    
    for phase_name, tasks in phases:
        kanban_html += f"""<div style="background: {colors['neutral_800']}; border: 1px solid {colors['neutral_600']}; border-radius: {radius['lg']}; padding: {spacing['md']};"><h4 style="color: {colors['primary_light']}; margin-bottom: {spacing['md']}; text-align: center;">{phase_name}</h4>"""
        
        if tasks:
            for task in tasks:
                task_name = task.get('task', 'Unnamed task')
                owner = task.get('owner', 'Unassigned')
                kpi = task.get('kpi', 'N/A')
                priority = task.get('priority', 'medium').lower()
                priority_color = priority_colors.get(priority, colors['neutral_400'])
                
                kanban_html += f"""
                <div style="background: {colors['neutral_700']}; border-left: 3px solid {priority_color}; border-radius: {radius['sm']}; padding: {spacing['sm']}; margin-bottom: {spacing['sm']};">
                    <div style="font-weight: 600; color: {colors['neutral_100']}; margin-bottom: {spacing['xs']};">{task_name}</div>
                    <div style="font-size: 12px; color: {colors['neutral_400']}; margin-bottom: {spacing['xs']};">👤 {owner}</div>
                    <div style="font-size: 11px; color: {colors['neutral_400']};">📊 KPI: {kpi}</div>
                    <div style="font-size: 11px; color: {priority_color}; margin-top: {spacing['xs']}; font-weight: 600;">Priority: {priority.upper()}</div>
                </div>
                """
        else:
            kanban_html += f"""<div style="text-align: center; color: {colors['neutral_400']}; padding: {spacing['lg']};">No tasks</div>"""
        
        kanban_html += "</div>"
    
    kanban_html += "</div>"
    
    return _clean_html(kanban_html)


def _generate_markdown_export(report: Dict[str, Any]) -> str:
    """
    Generate markdown export of the report.
    
    Args:
        report: Report dictionary
        
    Returns:
        Markdown-formatted report string
    """
    job_id = report.get('job_id', 'N/A')
    research = report.get('research', {})
    strategy = report.get('strategy', {})
    execution_plan = report.get('execution_plan', {})
    qa = report.get('qa', {})
    
    markdown = f"""# Final Report - {job_id}

## Research

{research.get('report', 'No research report available')}

### Sources

"""
    
    sources = research.get('sources', [])
    if sources:
        for source in sources:
            markdown += f"- {source}\n"
    else:
        markdown += "No sources available\n"
    
    markdown += f"""
## Strategy

{strategy.get('report', 'No strategy report available')}

**Critic Verdict:** {strategy.get('critic_verdict', 'PENDING')}
**Critic Score:** {strategy.get('critic_score', 0)}/10

## Execution Plan

### 30-Day Phase

"""
    
    phase_30 = execution_plan.get('phase_30_days', [])
    if phase_30:
        for task in phase_30:
            markdown += f"- **{task.get('task', 'Unnamed')}** (Owner: {task.get('owner', 'Unassigned')}, KPI: {task.get('kpi', 'N/A')}, Priority: {task.get('priority', 'medium')})\n"
    else:
        markdown += "No tasks\n"
    
    markdown += "\n### 60-Day Phase\n\n"
    
    phase_60 = execution_plan.get('phase_60_days', [])
    if phase_60:
        for task in phase_60:
            markdown += f"- **{task.get('task', 'Unnamed')}** (Owner: {task.get('owner', 'Unassigned')}, KPI: {task.get('kpi', 'N/A')}, Priority: {task.get('priority', 'medium')})\n"
    else:
        markdown += "No tasks\n"
    
    markdown += "\n### 90-Day Phase\n\n"
    
    phase_90 = execution_plan.get('phase_90_days', [])
    if phase_90:
        for task in phase_90:
            markdown += f"- **{task.get('task', 'Unnamed')}** (Owner: {task.get('owner', 'Unassigned')}, KPI: {task.get('kpi', 'N/A')}, Priority: {task.get('priority', 'medium')})\n"
    else:
        markdown += "No tasks\n"
    
    markdown += f"""
## Quality Assurance

**Score:** {qa.get('score', 0)}/10
**Status:** {'Passed' if qa.get('passed', False) else 'Failed'}

### Identified Gaps

"""
    
    gaps = qa.get('gaps', [])
    if gaps:
        for gap in gaps:
            markdown += f"- {gap}\n"
    else:
        markdown += "No gaps identified\n"
    
    return markdown



def render_log_panel(
    logs: List[Dict[str, Any]],
    filters: Optional[Dict[str, Any]] = None,
    search_query: Optional[str] = None,
    auto_scroll: bool = True
) -> str:
    """
    Render scrollable log panel with filtering, search, and expandable structured data.
    
    Displays logs in monospace font with color-coded log levels (INFO: blue, WARN: orange, ERROR: red).
    Implements filter chips for log level and agent name with active state styling.
    Implements search input with text highlighting for matches.
    Adds relative timestamps ("2s ago") with absolute time on hover.
    Implements auto-scroll to latest entry with manual scroll lock detection.
    Adds expandable structured data display for JSON logs.
    Adds distinct visual styling for agent decision logs vs execution logs.
    Implements visual grouping for related log entries from same agent/phase.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8
    
    Args:
        logs: List of log dictionaries with keys:
            - timestamp: str (ISO format)
            - level: str (INFO, WARN, ERROR)
            - agent: str (agent name or 'system')
            - message: str
            - structured_data: Dict (optional, expandable JSON)
            - is_decision: bool (optional, marks autonomous decisions)
        filters: Active filters {'level': ['INFO', 'ERROR'], 'agent': ['research']}
        search_query: Text search string
        auto_scroll: Whether to scroll to latest entry
        
    Returns:
        HTML string with styled log panel
        
    Examples:
        >>> logs = [
        ...     {
        ...         'timestamp': '2024-01-15T10:30:00Z',
        ...         'level': 'INFO',
        ...         'agent': 'research',
        ...         'message': 'Starting research phase',
        ...         'is_decision': False
        ...     }
        ... ]
        >>> html = render_log_panel(logs)
    """
    colors = DesignSystem.COLORS
    spacing = DesignSystem.SPACING
    radius = DesignSystem.RADIUS
    typo = DesignSystem.TYPOGRAPHY
    anim = DesignSystem.ANIMATION
    
    # Initialize filters if not provided
    if filters is None:
        filters = {}
    
    # Filter logs based on active filters
    filtered_logs = logs
    
    # Apply level filter
    if 'level' in filters and filters['level']:
        filtered_logs = [log for log in filtered_logs if log.get('level', 'INFO') in filters['level']]
    
    # Apply agent filter
    if 'agent' in filters and filters['agent']:
        filtered_logs = [log for log in filtered_logs if log.get('agent', 'system') in filters['agent']]
    
    # Apply search query
    if search_query:
        search_lower = search_query.lower()
        filtered_logs = [
            log for log in filtered_logs
            if search_lower in log.get('message', '').lower()
            or search_lower in log.get('agent', '').lower()
        ]
    
    # Log level color mapping
    level_colors = {
        'INFO': colors['info'],
        'WARN': colors['warning'],
        'ERROR': colors['error'],
        'DEBUG': colors['neutral_400'],
    }
    
    # Build log entries HTML
    log_entries_html = []
    previous_agent = None
    
    for idx, log in enumerate(filtered_logs):
        timestamp = log.get('timestamp') or ''
        level = html_escape(str(log.get('level') or 'INFO'))
        agent = html_escape(str(log.get('agent') or 'system'))
        message = log.get('message') or ''
        structured_data = log.get('structured_data', None)
        is_decision = log.get('is_decision', False)
        
        # Get level color
        level_color = level_colors.get(level, colors['neutral_400'])
        
        # Format timestamp
        relative_time = _format_relative_time(timestamp)
        absolute_time = _format_absolute_time(timestamp)
        
        # Always escape HTML and highlight search matches in message
        highlighted_message = _highlight_search_matches(message, search_query)
        
        # Determine if this is a new agent group (for visual grouping)
        is_new_group = agent != previous_agent
        previous_agent = agent
        
        # Add group separator if new agent
        group_separator = ""
        if is_new_group and idx > 0:
            group_separator = f"""
            <div style="
                height: 1px;
                background: linear-gradient(90deg, transparent, {colors['neutral_600']}, transparent);
                margin: {spacing['sm']} 0;
            "></div>
            """
        
        # Determine background color based on decision vs execution
        if is_decision:
            bg_color = colors['neutral_700']
            border_left = f"3px solid {colors['primary']}"
            decision_badge = f"""
            <span style="
                display: inline-block;
                background: {colors['primary']};
                color: white;
                font-size: {typo['font_size']['xs']};
                padding: 2px 6px;
                border-radius: {radius['sm']};
                margin-left: {spacing['xs']};
                font-weight: {typo['font_weight']['semibold']};
            ">DECISION</span>
            """
        else:
            bg_color = 'transparent'
            border_left = f"2px solid {level_color}"
            decision_badge = ""
        
        # Build structured data expandable section
        structured_data_html = ""
        if structured_data:
            structured_json = json.dumps(structured_data, indent=2)
            structured_data_html = f"""
            <details class="log-structured-data" style="margin-top: {spacing['xs']};">
                <summary style="
                    font-size: {typo['font_size']['xs']};
                    color: {colors['primary_light']};
                    cursor: pointer;
                    list-style: none;
                    user-select: none;
                    font-weight: {typo['font_weight']['semibold']};
                ">
                    <span>▼ View Structured Data</span>
                </summary>
                <pre style="
                    background: {colors['neutral_900']};
                    padding: {spacing['sm']};
                    border-radius: {radius['sm']};
                    margin-top: {spacing['xs']};
                    overflow-x: auto;
                    font-size: {typo['font_size']['xs']};
                    color: {colors['neutral_300']};
                    border: 1px solid {colors['neutral_600']};
                "><code>{structured_json}</code></pre>
            </details>
            """
        
        # Build log entry
        log_entry_html = f"""
        {group_separator}
        <div class="log-entry" style="
            font-family: {typo['font_family']['mono']};
            font-size: {typo['font_size']['sm']};
            margin: {spacing['xs']} 0;
            padding: {spacing['sm']};
            border-radius: {radius['sm']};
            background: {bg_color};
            border-left: {border_left};
            transition: background {anim['duration_fast']} {anim['easing']};
        ">
            <div style="
                display: flex;
                align-items: center;
                gap: {spacing['sm']};
                margin-bottom: {spacing['xs']};
            ">
                <span 
                    class="log-timestamp" 
                    title="{absolute_time}"
                    style="
                        color: {colors['neutral_400']};
                        font-size: {typo['font_size']['xs']};
                        cursor: help;
                    "
                >
                    {relative_time}
                </span>
                <span style="
                    color: {level_color};
                    font-weight: {typo['font_weight']['semibold']};
                    font-size: {typo['font_size']['xs']};
                ">
                    [{level}]
                </span>
                <span style="
                    color: {colors['neutral_300']};
                    font-size: {typo['font_size']['xs']};
                    text-transform: capitalize;
                ">
                    {agent}
                </span>
                {decision_badge}
            </div>
            <div style="
                color: {colors['neutral_200']};
                line-height: {typo['line_height']['relaxed']};
                word-wrap: break-word;
            ">
                {highlighted_message}
            </div>
            {structured_data_html}
        </div>
        """
        
        log_entries_html.append(log_entry_html)
    
    # Build complete log panel HTML
    log_panel_html = f"""
    <div class="log-panel" style="
        background: {colors['neutral_900']};
        border-radius: {radius['md']};
        padding: {spacing['md']};
        max-height: 500px;
        overflow-y: auto;
        font-family: {typo['font_family']['mono']};
        border: 1px solid {colors['neutral_600']};
        {'scroll-behavior: smooth;' if auto_scroll else ''}
    ">
        {''.join(log_entries_html) if log_entries_html else f'<div style="text-align: center; color: {colors["neutral_400"]}; padding: {spacing["lg"]};">No logs to display</div>'}
    </div>
    
    <style>
        .log-entry:hover {{
            background: {colors['neutral_800']} !important;
        }}
        
        .log-structured-data summary {{
            transition: color {anim['duration_fast']} {anim['easing']};
        }}
        
        .log-structured-data summary:hover {{
            color: {colors['primary']};
        }}
        
        .log-structured-data summary::-webkit-details-marker {{
            display: none;
        }}
        
        .log-structured-data[open] summary span::before {{
            content: '▲ ';
        }}
        
        .log-structured-data:not([open]) summary span::before {{
            content: '▼ ';
        }}
        
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
    </style>
    """
    
    return _clean_html(log_panel_html)





def _format_relative_time(timestamp: str) -> str:
    """
    Format timestamp as relative time (e.g., "2s ago", "5m ago").
    
    Args:
        timestamp: ISO format timestamp string
        
    Returns:
        Relative time string
    """
    if not timestamp or not isinstance(timestamp, str):
        return "unknown"
    
    try:
        # Parse ISO timestamp
        log_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now(log_time.tzinfo)
        
        # Calculate time difference
        delta = now - log_time
        seconds = delta.total_seconds()
        
        if seconds < 60:
            return f"{int(seconds)}s ago"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m ago"
        elif seconds < 86400:
            return f"{int(seconds / 3600)}h ago"
        else:
            return f"{int(seconds / 86400)}d ago"
    except Exception:
        return "unknown"


def _format_absolute_time(timestamp: str) -> str:
    """
    Format timestamp as absolute time for hover tooltip.
    
    Args:
        timestamp: ISO format timestamp string
        
    Returns:
        Formatted absolute time string
    """
    if not timestamp or not isinstance(timestamp, str):
        return "Unknown time"
    
    try:
        # Parse ISO timestamp
        log_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return log_time.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        return timestamp


def _highlight_search_matches(text: str, search_query: str) -> str:
    """
    Highlight search query matches in text.
    
    Args:
        text: Text to search in
        search_query: Search query string
        
    Returns:
        HTML string with highlighted matches
    """
    # Safeguard against NoneType/None values
    if text is None:
        text = ""
    else:
        text = str(text)
        
    # Always escape HTML in text first to prevent HTML injection and layout breakage
    text = html_escape(text)
    
    if not search_query:
        return text
    
    # Case-insensitive search and highlight
    pattern = re.compile(re.escape(search_query), re.IGNORECASE)
    highlighted = pattern.sub(
        lambda m: f'<mark style="background: {DesignSystem.COLORS["warning"]}; color: {DesignSystem.COLORS["neutral_900"]}; padding: 2px 4px; border-radius: 3px;">{m.group(0)}</mark>',
        text
    )
    
    return highlighted
