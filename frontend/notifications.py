"""
Notifications Module - Toast and Error Handling System

This module provides a toast notification system and error handling components
for the Streamlit frontend. Includes success, warning, error, and info toasts
with auto-dismiss functionality, as well as connection error banners and
inline validation messages.

Requirements: 11.1-11.8
"""

from typing import Optional, Literal
import streamlit as st
try:
    from frontend.design_system import DesignSystem
except ModuleNotFoundError:
    from design_system import DesignSystem

from html import escape as html_escape


NotificationType = Literal['success', 'warning', 'error', 'info']

ALLOWED_ACTIONS = {
    'location.reload()',
    'window.location.reload()',
    'history.back()',
    'void(0)',
    'retryConnection()',
    'retryFetch()',
    'retryOperation()',
}


def clean_html(html: str) -> str:
    """Clean HTML lines to prevent Streamlit/Markdown parser from rendering it as code blocks."""
    return "\n".join(line.strip() for line in html.splitlines() if line.strip())


def toast_notification(
    message: str,
    notification_type: NotificationType = 'info',
    duration: int = 5,
    action_button: Optional[dict] = None
) -> str:
    """
    Generate HTML for toast notification with auto-dismiss.
    
    Creates a styled toast notification that appears at the top-right of the screen
    and automatically dismisses after the specified duration. Supports action buttons
    for interactive notifications (e.g., retry buttons on errors).
    
    Requirements: 11.6
    
    Args:
        message: Notification message text
        notification_type: Type of notification ('success', 'warning', 'error', 'info')
        duration: Auto-dismiss duration in seconds (default: 5)
        action_button: Optional action button config with keys:
            - label: str (button text)
            - action: str (JavaScript action or callback)
            
    Returns:
        HTML string with styled toast notification and auto-dismiss script
        
    Examples:
        >>> toast_notification("Job submitted successfully!", "success")
        '<div class="toast toast-success">...</div>'
        
        >>> toast_notification("Failed to connect", "error", action_button={
        ...     "label": "Retry",
        ...     "action": "location.reload()"
        ... })
        '<div class="toast toast-error">...</div>'
    """
    colors = DesignSystem.COLORS
    spacing = DesignSystem.SPACING
    radius = DesignSystem.RADIUS
    typo = DesignSystem.TYPOGRAPHY
    anim = DesignSystem.ANIMATION
    shadows = DesignSystem.SHADOWS
    
    # Map notification type to colors and icons
    type_config = {
        'success': {
            'color': colors['success'],
            'bg': colors['success_bg'],
            'icon': '✅',
            'shadow': shadows['glow_success'],
        },
        'warning': {
            'color': colors['warning'],
            'bg': colors['neutral_800'],
            'icon': '⚠️',
            'shadow': shadows['md'],
        },
        'error': {
            'color': colors['error'],
            'bg': colors['error_bg'],
            'icon': '❌',
            'shadow': shadows['glow_error'],
        },
        'info': {
            'color': colors['info'],
            'bg': colors['neutral_800'],
            'icon': 'ℹ️',
            'shadow': shadows['md'],
        },
    }
    
    config = type_config.get(notification_type, type_config['info'])
    
    # Generate unique ID for this toast
    import time
    toast_id = f"toast-{int(time.time() * 1000)}"
    
    # Action button HTML - sanitize actions to avoid arbitrary JS injection
    action_html = ""
    if action_button:
        raw_label = action_button.get('label', 'Action')
        raw_action = action_button.get('action', '')

        # Allow only a small set of safe actions. Any unknown action falls back to reload.
        action = raw_action if raw_action in ALLOWED_ACTIONS else 'location.reload()'
        label = html_escape(raw_label)

        action_html = f"""
        <button onclick="{action}" style="
            background: {config['color']};
            color: white;
            border: none;
            border-radius: {radius['sm']};
            padding: {spacing['xs']} {spacing['sm']};
            font-size: {typo['font_size']['sm']};
            font-weight: {typo['font_weight']['semibold']};
            cursor: pointer;
            margin-left: {spacing['sm']};
            transition: all {anim['duration_fast']} {anim['easing']};
        " onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">
            {label}
        </button>
        """
    
    slide_in_pct = min(10.0, (0.5 / duration) * 100.0) if duration > 0.5 else 10.0
    slide_out_pct = max(90.0, ((duration - 0.5) / duration) * 100.0) if duration > 0.5 else 90.0

    # Generate toast HTML with pure CSS animations and high z-index
    html = f"""
    <div id="{toast_id}" class="toast toast-{notification_type}" style="
        position: fixed;
        top: calc(3.75rem + {spacing['lg']});
        right: {spacing['lg']};
        z-index: 99999999;
        pointer-events: auto !important;
        background: {config['bg']};
        border: 2px solid {config['color']};
        border-radius: {radius['lg']};
        padding: {spacing['md']} {spacing['lg']};
        box-shadow: {config['shadow']};
        display: flex;
        align-items: center;
        gap: {spacing['md']};
        min-width: 300px;
        max-width: 500px;
        animation: toastAutoDismiss-{toast_id} {duration}s ease-in-out forwards;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
    ">
        <span style="font-size: {typo['font_size']['xl']};">{config['icon']}</span>
        <div style="flex: 1;">
            <div style="
                font-size: {typo['font_size']['md']};
                font-weight: {typo['font_weight']['semibold']};
                color: {colors['neutral_100']};
                line-height: {typo['line_height']['normal']};
            ">{message}</div>
        </div>
        {action_html}
        <button onclick="this.parentElement.remove()" style="
            background: transparent;
            border: none;
            color: {colors['neutral_400']};
            font-size: {typo['font_size']['lg']};
            cursor: pointer;
            padding: 0;
            margin-left: {spacing['sm']};
            transition: color {anim['duration_fast']} {anim['easing']};
        " onmouseover="this.style.color='{colors['neutral_100']}'" onmouseout="this.style.color='{colors['neutral_400']}'">
            ×
        </button>
    </div>
    
    <style>
        /* Prevent Streamlit parent containers from clipping the fixed toast */
        div[data-testid="column"]:has(#{toast_id}),
        div[data-testid="stHorizontalBlock"]:has(#{toast_id}),
        div[data-testid="stExpander"]:has(#{toast_id}),
        div.stTabs:has(#{toast_id}),
        div[data-testid="stSidebar"]:has(#{toast_id}) {{
            overflow: visible !important;
            pointer-events: none !important;
        }}

        div.element-container:has(#{toast_id}) {{
            overflow: visible !important;
            height: 0 !important;
            min-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            pointer-events: none !important;
        }}

        /* slideInRight slideOutRight compatibility */
        @keyframes slideInRight {{
            from {{
                transform: translateX(400px);
                opacity: 0;
            }}
            to {{
                transform: translateX(0);
                opacity: 1;
            }}
        }}
        
        @keyframes slideOutRight {{
            from {{
                transform: translateX(0);
                opacity: 1;
            }}
            to {{
                transform: translateX(400px);
                opacity: 0;
            }}
        }}

        @keyframes toastAutoDismiss-{toast_id} {{
            0% {{
                transform: translateX(400px);
                opacity: 0;
            }}
            {slide_in_pct}% {{
                transform: translateX(0);
                opacity: 1;
            }}
            {slide_out_pct}% {{
                transform: translateX(0);
                opacity: 1;
            }}
            100% {{
                transform: translateX(400px);
                opacity: 0;
                visibility: hidden;
                pointer-events: none;
                height: 0;
                padding: 0;
                margin: 0;
                border: none;
            }}
        }}
    </style>
    
    <script>
        /* Auto-dismiss fallback after {duration} seconds for JS environments */
        setTimeout(function() {{
            var toast = document.getElementById('{toast_id}');
            if (toast) {{
                toast.remove();
            }}
        }}, {duration * 1000});
    </script>
    """
    
    return clean_html(html)


def connection_error_banner(
    backend_url: str,
    retry_callback: Optional[str] = None
) -> str:
    """
    Generate HTML for connection error banner.
    
    Displays a prominent banner at the top of the page when the backend
    is unreachable. Includes retry button and backend URL information.
    
    Requirements: 11.1
    
    Args:
        backend_url: Backend URL that failed to connect
        retry_callback: Optional JavaScript callback for retry button
            
    Returns:
        HTML string with styled connection error banner
        
    Examples:
        >>> connection_error_banner("http://localhost:8000")
        '<div class="error-banner">...</div>'
    """
    colors = DesignSystem.COLORS
    spacing = DesignSystem.SPACING
    radius = DesignSystem.RADIUS
    typo = DesignSystem.TYPOGRAPHY
    shadows = DesignSystem.SHADOWS
    
    # Default retry action is page reload; sanitize callbacks
    retry_action = retry_callback if (retry_callback in ALLOWED_ACTIONS) else "location.reload()"
    
    html = f"""
    <div class="error-banner" style="
        background: linear-gradient(135deg, {colors['error_bg']} 0%, {colors['error_dark']} 100%);
        border: 2px solid {colors['error']};
        border-radius: {radius['lg']};
        padding: {spacing['lg']};
        margin-bottom: {spacing['lg']};
        box-shadow: {shadows['glow_error']};
        display: flex;
        align-items: center;
        gap: {spacing['md']};
    ">
        <span style="font-size: {typo['font_size']['xxxl']};">🔴</span>
        <div style="flex: 1;">
            <div style="
                font-size: {typo['font_size']['xl']};
                font-weight: {typo['font_weight']['bold']};
                color: {colors['neutral_100']};
                margin-bottom: {spacing['xs']};
            ">Cannot Connect to Backend</div>
            <div style="
                font-size: {typo['font_size']['md']};
                color: {colors['neutral_300']};
                line-height: {typo['line_height']['normal']};
            ">
                Unable to reach the backend API at <code style="
                    background: {colors['neutral_900']};
                    padding: 2px 6px;
                    border-radius: {radius['sm']};
                    font-family: {typo['font_family']['mono']};
                    font-size: {typo['font_size']['sm']};
                ">{backend_url}</code>
            </div>
            <div style="
                font-size: {typo['font_size']['sm']};
                color: {colors['neutral_400']};
                margin-top: {spacing['xs']};
            ">
                Please check your connection and ensure the backend service is running.
            </div>
        </div>
        <button onclick="{retry_action}" style="
            background: {colors['error']};
            color: white;
            border: none;
            border-radius: {radius['md']};
            padding: {spacing['sm']} {spacing['lg']};
            font-size: {typo['font_size']['md']};
            font-weight: {typo['font_weight']['semibold']};
            cursor: pointer;
            transition: all {DesignSystem.ANIMATION['duration_normal']} {DesignSystem.ANIMATION['easing']};
            white-space: nowrap;
        " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
            🔄 Retry Connection
        </button>
    </div>
    """
    
    return clean_html(html)


def timeout_error_message(
    operation: str,
    timeout_seconds: int,
    retry_callback: Optional[str] = None
) -> str:
    """
    Generate HTML for timeout error message.
    
    Displays a timeout error message when a request takes too long.
    Includes information about the operation and timeout duration.
    
    Requirements: 11.8
    
    Args:
        operation: Description of the operation that timed out
        timeout_seconds: Timeout duration in seconds
        retry_callback: Optional JavaScript callback for retry button
            
    Returns:
        HTML string with styled timeout error message
        
    Examples:
        >>> timeout_error_message("Job submission", 10)
        '<div class="timeout-error">...</div>'
    """
    colors = DesignSystem.COLORS
    spacing = DesignSystem.SPACING
    radius = DesignSystem.RADIUS
    typo = DesignSystem.TYPOGRAPHY
    
    retry_button = ""
    if retry_callback:
        # sanitize retry callback
        retry_cb = retry_callback if retry_callback in ALLOWED_ACTIONS else 'location.reload()'
        retry_button = f"""
        <button onclick="{retry_cb}" style="
            background: {colors['warning']};
            color: white;
            border: none;
            border-radius: {radius['sm']};
            padding: {spacing['xs']} {spacing['md']};
            font-size: {typo['font_size']['sm']};
            font-weight: {typo['font_weight']['semibold']};
            cursor: pointer;
            margin-top: {spacing['sm']};
            transition: all {DesignSystem.ANIMATION['duration_fast']} {DesignSystem.ANIMATION['easing']};
        " onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">
            🔄 Retry
        </button>
        """
    
    html = f"""
    <div class="timeout-error" style="
        background: {colors['neutral_800']};
        border: 2px solid {colors['warning']};
        border-left: 4px solid {colors['warning']};
        border-radius: {radius['md']};
        padding: {spacing['md']};
        margin: {spacing['md']} 0;
    ">
        <div style="display: flex; align-items: start; gap: {spacing['sm']};">
            <span style="font-size: {typo['font_size']['xl']};">⏱️</span>
            <div style="flex: 1;">
                <div style="
                    font-size: {typo['font_size']['md']};
                    font-weight: {typo['font_weight']['semibold']};
                    color: {colors['warning']};
                    margin-bottom: {spacing['xs']};
                ">Request Timed Out</div>
                <div style="
                    font-size: {typo['font_size']['sm']};
                    color: {colors['neutral_300']};
                    line-height: {typo['line_height']['normal']};
                ">
                    {operation} took longer than {timeout_seconds} seconds. 
                    The backend may be busy or experiencing high load.
                </div>
                {retry_button}
            </div>
        </div>
    </div>
    """
    
    return clean_html(html)


def inline_validation_error(
    field_name: str,
    error_message: str,
    correction_hint: Optional[str] = None
) -> str:
    """
    Generate HTML for inline validation error message.
    
    Displays validation error below form fields with correction guidance.
    
    Requirements: 11.3
    
    Args:
        field_name: Name of the field with validation error
        error_message: Error message text
        correction_hint: Optional hint for correcting the error
            
    Returns:
        HTML string with styled inline validation error
        
    Examples:
        >>> inline_validation_error("Business Brief", "Field is required")
        '<div class="validation-error">...</div>'
        
        >>> inline_validation_error(
        ...     "Business Brief",
        ...     "Too short",
        ...     "Please enter at least 50 characters"
        ... )
        '<div class="validation-error">...</div>'
    """
    colors = DesignSystem.COLORS
    spacing = DesignSystem.SPACING
    radius = DesignSystem.RADIUS
    typo = DesignSystem.TYPOGRAPHY
    
    hint_html = ""
    if correction_hint:
        hint_html = f"""
        <div style="
            font-size: {typo['font_size']['xs']};
            color: {colors['neutral_400']};
            margin-top: {spacing['xs']};
            font-style: italic;
        ">
            💡 {correction_hint}
        </div>
        """
    
    html = f"""
    <div class="validation-error" style="
        background: {colors['error_bg']};
        border-left: 3px solid {colors['error']};
        border-radius: {radius['sm']};
        padding: {spacing['sm']};
        margin-top: {spacing['xs']};
        margin-bottom: {spacing['sm']};
    ">
        <div style="
            font-size: {typo['font_size']['sm']};
            font-weight: {typo['font_weight']['semibold']};
            color: {colors['error']};
        ">
            ❌ {error_message}
        </div>
        {hint_html}
    </div>
    """
    
    return clean_html(html)


def job_not_found_message(job_id: str) -> str:
    """
    Generate HTML for "Job not found" error message.
    
    Displays when a requested job ID doesn't exist in the system.
    Includes navigation back to dashboard.
    
    Requirements: 11.2
    
    Args:
        job_id: The job ID that was not found
            
    Returns:
        HTML string with styled job not found message
        
    Examples:
        >>> job_not_found_message("job123")
        '<div class="job-not-found">...</div>'
    """
    colors = DesignSystem.COLORS
    spacing = DesignSystem.SPACING
    radius = DesignSystem.RADIUS
    typo = DesignSystem.TYPOGRAPHY
    shadows = DesignSystem.SHADOWS
    
    html = f"""
    <div class="job-not-found" style="
        background: {colors['neutral_800']};
        border: 2px solid {colors['neutral_600']};
        border-radius: {radius['lg']};
        padding: {spacing['xxl']};
        margin: {spacing['xl']} auto;
        max-width: 600px;
        text-align: center;
        box-shadow: {shadows['md']};
    ">
        <div style="font-size: 64px; margin-bottom: {spacing['md']};">🔍</div>
        <div style="
            font-size: {typo['font_size']['xxl']};
            font-weight: {typo['font_weight']['bold']};
            color: {colors['neutral_100']};
            margin-bottom: {spacing['sm']};
        ">Job Not Found</div>
        <div style="
            font-size: {typo['font_size']['md']};
            color: {colors['neutral_400']};
            line-height: {typo['line_height']['relaxed']};
            margin-bottom: {spacing['md']};
        ">
            The job with ID <code style="
                background: {colors['neutral_900']};
                padding: 2px 8px;
                border-radius: {radius['sm']};
                font-family: {typo['font_family']['mono']};
                color: {colors['primary_light']};
            ">{job_id}</code> could not be found.
        </div>
        <div style="
            font-size: {typo['font_size']['sm']};
            color: {colors['neutral_500']};
            margin-bottom: {spacing['lg']};
        ">
            The job may have been deleted, or the ID may be incorrect.
        </div>
        <button onclick="window.location.href='?page=dashboard'" style="
            background: linear-gradient(135deg, {colors['primary']} 0%, {colors['primary_dark']} 100%);
            color: white;
            border: none;
            border-radius: {radius['md']};
            padding: {spacing['sm']} {spacing['xl']};
            font-size: {typo['font_size']['md']};
            font-weight: {typo['font_weight']['semibold']};
            cursor: pointer;
            transition: all {DesignSystem.ANIMATION['duration_normal']} {DesignSystem.ANIMATION['easing']};
            box-shadow: {shadows['md']};
        " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='{shadows['glow']}'" 
           onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='{shadows['md']}'">
            📊 Go to Dashboard
        </button>
    </div>
    """
    
    return clean_html(html)


def show_toast(
    message: str,
    notification_type: NotificationType = 'info',
    duration: int = 5,
    action_button: Optional[dict] = None
) -> None:
    """
    Display a toast notification in Streamlit.
    
    Convenience function that renders a toast notification using st.markdown.
    
    Args:
        message: Notification message text
        notification_type: Type of notification ('success', 'warning', 'error', 'info')
        duration: Auto-dismiss duration in seconds (default: 5)
        action_button: Optional action button config
        
    Examples:
        >>> show_toast("Job submitted successfully!", "success")
        >>> show_toast("Connection failed", "error", action_button={
        ...     "label": "Retry",
        ...     "action": "location.reload()"
        ... })
    """
    html = toast_notification(message, notification_type, duration, action_button)
    st.markdown(html, unsafe_allow_html=True)


def show_connection_error(backend_url: str, retry_callback: Optional[str] = None) -> None:
    """
    Display a connection error banner in Streamlit.
    
    Convenience function that renders a connection error banner using st.markdown.
    
    Args:
        backend_url: Backend URL that failed to connect
        retry_callback: Optional JavaScript callback for retry button
        
    Examples:
        >>> show_connection_error("http://localhost:8000")
    """
    html = connection_error_banner(backend_url, retry_callback)
    st.markdown(html, unsafe_allow_html=True)


def show_timeout_error(
    operation: str,
    timeout_seconds: int,
    retry_callback: Optional[str] = None
) -> None:
    """
    Display a timeout error message in Streamlit.
    
    Convenience function that renders a timeout error message using st.markdown.
    
    Args:
        operation: Description of the operation that timed out
        timeout_seconds: Timeout duration in seconds
        retry_callback: Optional JavaScript callback for retry button
        
    Examples:
        >>> show_timeout_error("Job submission", 10)
    """
    html = timeout_error_message(operation, timeout_seconds, retry_callback)
    st.markdown(html, unsafe_allow_html=True)


def show_validation_error(
    field_name: str,
    error_message: str,
    correction_hint: Optional[str] = None
) -> None:
    """
    Display an inline validation error in Streamlit.
    
    Convenience function that renders an inline validation error using st.markdown.
    
    Args:
        field_name: Name of the field with validation error
        error_message: Error message text
        correction_hint: Optional hint for correcting the error
        
    Examples:
        >>> show_validation_error("Business Brief", "Field is required")
    """
    html = inline_validation_error(field_name, error_message, correction_hint)
    st.markdown(html, unsafe_allow_html=True)


def show_job_not_found(job_id: str) -> None:
    """
    Display a job not found message in Streamlit.
    
    Convenience function that renders a job not found message using st.markdown.
    
    Args:
        job_id: The job ID that was not found
        
    Examples:
        >>> show_job_not_found("job123")
    """
    html = job_not_found_message(job_id)
    st.markdown(html, unsafe_allow_html=True)
