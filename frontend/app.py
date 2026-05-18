"""
Streamlit Frontend - Business Intelligence Platform Dashboard

Assignment requirement: Frontend Requirements
  - Workflow visualization
  - Agent execution timeline
  - Logs panel
  - Streaming responses
  - Status dashboard
"""

import time
import json
import requests
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional
from html import escape as html_escape
import re

# ─── Config ──────────────────────────────────────────────────────────────────
import os

# Import design system
from design_system import DesignSystem

# Import notifications system
from notifications import (
    show_toast,
    show_connection_error,
    show_timeout_error,
    show_validation_error,
    show_job_not_found,
)

# Import component library
from components import (
    status_badge as component_status_badge,
    metric_card,
    expandable_section,
    render_agent_timeline,
    skeleton_timeline,
    skeleton_log_panel,
    skeleton_report,
    _clean_html,
)

# Import API client
from api_client import APIClient

# Import stream manager
from stream_manager import StreamManager

# Try to import SSE client, fallback to polling if not available
try:
    import sseclient
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False


def _backend_url() -> str:
    """Read backend URL from Streamlit secrets first, then environment."""
    try:
        configured_url = st.secrets.get("BACKEND_URL")
    except Exception:
        configured_url = None
    configured_url = configured_url or os.getenv("BACKEND_URL", "http://localhost:8000/api/v1")
    return configured_url.rstrip("/")


BACKEND_URL = _backend_url()
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "2"))
SSE_TIMEOUT = int(os.getenv("SSE_TIMEOUT", "300"))  # 5 minutes default
ENABLE_SSE = os.getenv("ENABLE_SSE", "true").lower() == "true"
ENABLE_ANIMATIONS = os.getenv("ENABLE_ANIMATIONS", "true").lower() == "true"
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
STALE_JOB_HOURS = float(os.getenv("STALE_JOB_HOURS", "0.6"))

# Initialize API client
api_client = APIClient(BACKEND_URL, timeout=10, max_retries=MAX_RETRIES)

st.set_page_config(
    page_title="AI Business Intelligence Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Styling ─────────────────────────────────────────────────────────────────
# Inject design system CSS
st.markdown(DesignSystem.generate_css(), unsafe_allow_html=True)

# Add keyboard navigation support
st.markdown("""
<script>
document.addEventListener('keydown', function(event) {
    // Alt+1: New Analysis
    if (event.altKey && event.key === '1') {
        event.preventDefault();
        const newAnalysisRadio = document.querySelector('input[value="🚀 New Analysis"]');
        if (newAnalysisRadio) {
            newAnalysisRadio.click();
        }
    }
    // Alt+2: Job Dashboard
    else if (event.altKey && event.key === '2') {
        event.preventDefault();
        const dashboardRadio = document.querySelector('input[value="📊 Job Dashboard"]');
        if (dashboardRadio) {
            dashboardRadio.click();
        }
    }
    // Alt+3: Job Inspector
    else if (event.altKey && event.key === '3') {
        event.preventDefault();
        const inspectorRadio = document.querySelector('input[value="🔍 Job Inspector"]');
        if (inspectorRadio) {
            inspectorRadio.click();
        }
    }
});
</script>
""", unsafe_allow_html=True)


# ─── Helper Functions ─────────────────────────────────────────────────────────
# BUG A FIX: All _render_* helpers defined HERE, before any page code calls them.

def api(method: str, path: str, **kwargs):
    """Make API request with error handling using centralized APIClient."""
    clean_path = "/" + path.lstrip("/")
    try:
        return api_client.request(method, clean_path, **kwargs)
    except requests.Timeout:
        show_timeout_error(
            operation=f"{method} {clean_path}",
            timeout_seconds=api_client.timeout,
            retry_callback="location.reload()"
        )
        return None
    except requests.ConnectionError:
        show_connection_error(api_client.backend_url, retry_callback="location.reload()")
        return None
    except requests.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 404:
                show_job_not_found(clean_path.split("/")[-1])
                return None
        show_toast(f"API error: {str(e)}", "error", action_button={
            "label": "Retry",
            "action": "location.reload()"
        })
        return None


def status_badge(status: str) -> str:
    """Generate status badge HTML using components library."""
    from components import status_badge as comp_status_badge
    return comp_status_badge(status)


def _render_agent_timeline(agent_tasks: list, job_status: str):
    """Render agent execution timeline with status badges and animations."""
    agent_icons = {
        "orchestrator": "🎯", "research": "🔍", "strategy": "🧠",
        "critic": "⚖️", "planner": "📅", "qa": "✅", "memory": "💾",
    }

    if not agent_tasks:
        st.info("No agent tasks yet — pipeline hasn't started.")
        return

    cols = st.columns(len(agent_tasks))
    for i, task in enumerate(agent_tasks):
        role = task.get("agent", "")
        status = task.get("status", "queued")
        icon = agent_icons.get(role, "🤖")
        
        # Get status color from design system
        border_color = DesignSystem.get_status_color(status)
        
        # Add animation classes based on status
        animation_class = ""
        if status == "running":
            animation_class = "animate-pulse"
        elif status == "completed":
            animation_class = "animate-checkmark"
        elif status == "failed":
            animation_class = "animate-shake"
        
        model_line = (
            f'<div style="font-size:11px;color:{DesignSystem.COLORS["neutral_400"]}">Model: {task["model_used"]}</div>'
            if task.get("model_used") else ""
        )
        
        with cols[i]:
            st.markdown(f"""
<div class="agent-card {animation_class}" style="border-color: {border_color}">
  <div style="font-size:24px">{icon}</div>
  <div style="font-weight:600;text-transform:capitalize">{role}</div>
  <div>{status_badge(status)}</div>
  {model_line}
</div>""", unsafe_allow_html=True)

    st.markdown(f"**Job Status:** {status_badge(job_status)}", unsafe_allow_html=True)


def _render_logs_panel(logs: list):
    """Render scrollable log panel with design system styling using premium components."""
    from components import render_log_panel
    log_panel_html = render_log_panel(
        logs,
        filters=None,
        search_query=None,
        auto_scroll=True
    )
    st.markdown(log_panel_html, unsafe_allow_html=True)


def _render_final_report(report: dict):
    """Render the assembled final report with clean formatting using premium components."""
    if not report:
        return
    from components import render_final_report
    render_final_report(report)


def _enrich_agent_data_with_logs(agent_data: list, log_data: list) -> list:
    """
    Enrich agent task data with decisions, collaborations, memory retrievals, 
    and model router selections extracted from workflow logs.
    
    Args:
        agent_data: List of agent task dictionaries from /agents endpoint
        log_data: List of log dictionaries from /logs endpoint
        
    Returns:
        Enriched agent data with additional fields:
            - decisions: List of autonomous decisions made by the agent
            - collaborations: List of inter-agent collaboration requests
            - memory_retrievals: List of memory system retrievals
            - model_selections: List of model router selections
            - output_preview: Preview of agent output
            - cost_usd: Calculated cost based on tokens and model
    """
    enriched_data = []
    
    for agent_task in agent_data:
        agent_role = agent_task.get('agent') or ''
        
        # Initialize enrichment fields
        enriched_task = agent_task.copy()
        enriched_task['decisions'] = []
        enriched_task['collaborations'] = []
        enriched_task['memory_retrievals'] = []
        enriched_task['model_selections'] = []
        enriched_task['output_preview'] = ''
        
        # Calculate cost if not present (rough estimation based on tokens)
        if 'cost_usd' not in enriched_task:
            tokens = enriched_task.get('tokens_used') or 0
            model = enriched_task.get('model_used') or ''
            # Rough cost estimation: $0.01 per 1000 tokens (adjust based on model)
            if 'gpt-4' in (model or '').lower():
                cost_per_1k = 0.03
            elif 'gpt-3.5' in (model or '').lower():
                cost_per_1k = 0.002
            else:
                cost_per_1k = 0.01
            enriched_task['cost_usd'] = (tokens / 1000.0) * cost_per_1k
        
        # Extract relevant logs for this agent
        agent_logs = [log for log in log_data if (log.get('agent') or '').lower() == (agent_role or '').lower()]
        
        for log in agent_logs:
            event_type = log.get('event_type', '')
            message = log.get('message', '')
            details = log.get('details', {})
            
            # Extract decisions (look for decision-related event types)
            if event_type in ['decision', 'strategy_selection', 'quality_verdict', 'agent_decision']:
                decision = {
                    'type': event_type,
                    'rationale': message,
                    'timestamp': log.get('timestamp', '')
                }
                if details:
                    decision['details'] = details
                enriched_task['decisions'].append(decision)
            
            # Extract collaborations (look for collaboration event types)
            elif event_type in ['collaboration_request', 'agent_collaboration', 'request_help']:
                collaboration = {
                    'requested_agent': details.get('requested_agent', 'unknown') if details else 'unknown',
                    'reason': message,
                    'timestamp': log.get('timestamp', '')
                }
                enriched_task['collaborations'].append(collaboration)
            
            # Extract memory retrievals
            elif event_type in ['memory_retrieval', 'vector_search', 'memory_lookup']:
                memory_retrieval = {
                    'query': details.get('query', message) if details else message,
                    'results_count': details.get('results_count', 0) if details else 0,
                    'timestamp': log.get('timestamp', '')
                }
                enriched_task['memory_retrievals'].append(memory_retrieval)
            
            # Extract model router selections
            elif event_type in ['model_selection', 'model_router', 'llm_selection']:
                model_selection = {
                    'selected_model': details.get('model', enriched_task.get('model_used', 'unknown')) if details else enriched_task.get('model_used', 'unknown'),
                    'reason': message,
                    'timestamp': log.get('timestamp', '')
                }
                enriched_task['model_selections'].append(model_selection)
            
            # Extract output preview from completion events
            elif event_type in ['agent_completed', 'task_completed', 'output_generated']:
                if details and 'output' in details:
                    output = details['output']
                    enriched_task['output_preview'] = output[:200] if isinstance(output, str) else str(output)[:200]
                elif message and len(message) > 50:
                    enriched_task['output_preview'] = message[:200]
        
        # If no output preview found, use the last message from this agent
        if not enriched_task['output_preview'] and agent_logs:
            last_log = agent_logs[-1]
            enriched_task['output_preview'] = last_log.get('message', '')[:200]
        
        enriched_data.append(enriched_task)
    
    return enriched_data


def _process_logs_for_display(log_data: list) -> list:
    """
    Process log data to add display-specific fields like is_decision flag
    and structured_data for expandable JSON display.
    
    Args:
        log_data: List of log dictionaries from /logs endpoint
        
    Returns:
        Processed log data with additional display fields:
            - is_decision: Boolean flag for decision logs
            - structured_data: JSON data for expandable display
    """
    processed_logs = []
    
    for log in log_data:
        processed_log = log.copy()
        
        # Determine if this is a decision log
        event_type = log.get('event_type', '')
        decision_event_types = [
            'decision', 'strategy_selection', 'quality_verdict', 
            'agent_decision', 'critic_verdict', 'model_selection',
            'collaboration_request'
        ]
        processed_log['is_decision'] = event_type in decision_event_types
        
        # Add structured data if details exist
        details = log.get('details')
        if details and isinstance(details, dict):
            processed_log['structured_data'] = details
        
        processed_logs.append(processed_log)
    
    return processed_logs


# Check for programmatic page navigation requests before widget rendering
if "next_page" in st.session_state and st.session_state["next_page"]:
    st.session_state["navigation_radio"] = st.session_state["next_page"]
    del st.session_state["next_page"]


# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    # Enhanced sidebar with glassmorphism styling
    st.markdown(f"""
    <div style="
        background: {DesignSystem.COLORS['glass_bg']};
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid {DesignSystem.COLORS['glass_border']};
        border-radius: {DesignSystem.RADIUS['lg']};
        padding: {DesignSystem.SPACING['lg']};
        margin-bottom: {DesignSystem.SPACING['md']};
        text-align: center;
    ">
        <div style="
            font-size: {DesignSystem.TYPOGRAPHY['font_size']['xxl']};
            font-weight: {DesignSystem.TYPOGRAPHY['font_weight']['bold']};
            color: {DesignSystem.COLORS['primary_light']};
            margin-bottom: {DesignSystem.SPACING['xs']};
        ">🤖 AI-BI Platform</div>
        <div style="
            font-size: {DesignSystem.TYPOGRAPHY['font_size']['sm']};
            color: {DesignSystem.COLORS['neutral_400']};
            text-transform: uppercase;
            letter-spacing: 1px;
        ">Multi-Agent Business Intelligence</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Navigation")
    
    # Enhanced navigation with icons and keyboard shortcuts
    # Custom styling for navigation items
    st.markdown(f"""
    <style>
    /* Enhanced navigation radio buttons */
    div[data-testid="stRadio"] > div {{
        gap: {DesignSystem.SPACING['sm']};
    }}
    
    div[data-testid="stRadio"] label {{
        background: {DesignSystem.COLORS['neutral_800']};
        border: 1px solid {DesignSystem.COLORS['neutral_600']};
        border-radius: {DesignSystem.RADIUS['md']};
        padding: {DesignSystem.SPACING['md']};
        transition: all {DesignSystem.ANIMATION['duration_normal']} {DesignSystem.ANIMATION['easing']};
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: {DesignSystem.SPACING['sm']};
    }}
    
    div[data-testid="stRadio"] label:hover {{
        background: {DesignSystem.COLORS['neutral_700']};
        border-color: {DesignSystem.COLORS['primary']};
        transform: translateX(4px);
    }}
    
    div[data-testid="stRadio"] label[data-checked="true"] {{
        background: linear-gradient(135deg, {DesignSystem.COLORS['primary_dark']} 0%, {DesignSystem.COLORS['primary']} 100%);
        border-color: {DesignSystem.COLORS['primary_light']};
        box-shadow: {DesignSystem.SHADOWS['glow']};
    }}
    
    /* Navigation item text */
    div[data-testid="stRadio"] label span {{
        font-size: {DesignSystem.TYPOGRAPHY['font_size']['md']};
        font-weight: {DesignSystem.TYPOGRAPHY['font_weight']['medium']};
    }}
    </style>
    """, unsafe_allow_html=True)
    
    page = st.radio(
        "Navigate",
        ["🚀 New Analysis", "📊 Job Dashboard", "🔍 Job Inspector"],
        label_visibility="collapsed",
        key="navigation_radio"
    )
    
    # Display keyboard shortcuts hint
    st.markdown(f"""
    <div style="
        font-size: {DesignSystem.TYPOGRAPHY['font_size']['xs']};
        color: {DesignSystem.COLORS['neutral_400']};
        margin-top: {DesignSystem.SPACING['sm']};
        padding: {DesignSystem.SPACING['sm']};
        background: {DesignSystem.COLORS['neutral_800']};
        border-radius: {DesignSystem.RADIUS['sm']};
    ">
        <strong>Keyboard Shortcuts:</strong><br>
        <span class="keyboard-shortcut">Alt+1</span> New Analysis<br>
        <span class="keyboard-shortcut">Alt+2</span> Job Dashboard<br>
        <span class="keyboard-shortcut">Alt+3</span> Job Inspector
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Connection status indicator with glassmorphism
    health = api("GET", "/health")
    
    if health:
        status_color = DesignSystem.COLORS['success']
        status_icon = '🟢'
        status_text = 'Backend Online'
        status_detail = 'All systems operational'
    else:
        status_color = DesignSystem.COLORS['error']
        status_icon = '🔴'
        status_text = 'Backend Offline'
        status_detail = 'Cannot connect to API'
        # Show connection error banner when backend is offline
        show_connection_error(BACKEND_URL, retry_callback="location.reload()")
    
    st.markdown(f"""
    <div style="
        background: {DesignSystem.COLORS['glass_bg']};
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid {DesignSystem.COLORS['glass_border']};
        border-radius: {DesignSystem.RADIUS['md']};
        padding: {DesignSystem.SPACING['md']};
        margin-bottom: {DesignSystem.SPACING['md']};
    ">
        <div style="
            display: flex;
            align-items: center;
            gap: {DesignSystem.SPACING['sm']};
            margin-bottom: {DesignSystem.SPACING['xs']};
        ">
            <span style="font-size: {DesignSystem.TYPOGRAPHY['font_size']['lg']};">{status_icon}</span>
            <div>
                <div style="
                    font-size: {DesignSystem.TYPOGRAPHY['font_size']['md']};
                    font-weight: {DesignSystem.TYPOGRAPHY['font_weight']['semibold']};
                    color: {status_color};
                ">{status_text}</div>
                <div style="
                    font-size: {DesignSystem.TYPOGRAPHY['font_size']['xs']};
                    color: {DesignSystem.COLORS['neutral_400']};
                ">{status_detail}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Backend URL info (hidden for security)
    st.caption("Backend: " + BACKEND_URL.split("//")[1].split("/")[0] if "//" in BACKEND_URL else "localhost")


# ─── Page: New Analysis ───────────────────────────────────────────────────────
# Enhanced with glassmorphism styling, example prompts, character count, validation,
# cost/time estimation, and StreamManager integration

if "🚀" in page:
    st.title("🚀 New Business Analysis")
    
    # Glassmorphism container for form
    st.markdown(f"""
    <div style="
        background: {DesignSystem.COLORS['glass_bg']};
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid {DesignSystem.COLORS['glass_border']};
        border-radius: {DesignSystem.RADIUS['lg']};
        padding: {DesignSystem.SPACING['lg']};
        margin-bottom: {DesignSystem.SPACING['lg']};
    ">
        <p style="
            color: {DesignSystem.COLORS['neutral_300']};
            font-size: {DesignSystem.TYPOGRAPHY['font_size']['md']};
            line-height: {DesignSystem.TYPOGRAPHY['line_height']['relaxed']};
            margin-bottom: {DesignSystem.SPACING['md']};
        ">
            Give the agent team one clear business brief. Our AI agents will analyze your business context, 
            research the market, develop a strategic plan, and provide actionable recommendations.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Example prompts removed per request
    
    # Initialize session state for draft
    if 'draft_brief' not in st.session_state:
        st.session_state['draft_brief'] = ""
    
    with st.form("analysis_form"):
        business_brief = st.text_area(
            "Business Brief",
            value=st.session_state.get('draft_brief', ''),
            placeholder=(
                "Describe your business context, product, target market, goals, constraints, and any specific "
                "questions you'd like answered. The more detail you provide, the better our agents can help."
            ),
            help=(
                "Include: company context, product/service details, target audience, business goals, "
                "budget constraints, timeline, geography, competitors, or specific strategic questions."
            ),
            height=220,
            key="business_brief_input"
        )
        
        # Character count and validation feedback
        char_count = len(business_brief.strip())
        min_chars = 50
        max_chars = 5000
        
        # Color-coded character count
        if char_count < min_chars:
            count_color = DesignSystem.COLORS['error']
            count_message = f"{char_count}/{max_chars} characters (minimum {min_chars})"
        elif char_count > max_chars:
            count_color = DesignSystem.COLORS['error']
            count_message = f"{char_count}/{max_chars} characters (exceeds maximum)"
        else:
            count_color = DesignSystem.COLORS['success']
            count_message = f"{char_count}/{max_chars} characters"
        
        st.markdown(f"""
        <div style="
            font-size: {DesignSystem.TYPOGRAPHY['font_size']['sm']};
            color: {count_color};
            margin-top: {DesignSystem.SPACING['xs']};
            text-align: right;
        ">
            {count_message}
        </div>
        """, unsafe_allow_html=True)
        
        # Cost and time estimation (only show when input provided)
        if char_count >= min_chars:
            # Rough estimation based on character count
            # Assume ~1000 chars = 1 minute processing, $0.10 cost
            estimated_time_min = max(2, int(char_count / 500))
            estimated_cost = max(0.50, char_count / 1000 * 0.10)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div style="
                    background: {DesignSystem.COLORS['neutral_800']};
                    border: 1px solid {DesignSystem.COLORS['neutral_600']};
                    border-radius: {DesignSystem.RADIUS['md']};
                    padding: {DesignSystem.SPACING['md']};
                    text-align: center;
                ">
                    <div style="
                        font-size: {DesignSystem.TYPOGRAPHY['font_size']['xxl']};
                        font-weight: {DesignSystem.TYPOGRAPHY['font_weight']['bold']};
                        color: {DesignSystem.COLORS['primary_light']};
                    ">~{estimated_time_min} min</div>
                    <div style="
                        font-size: {DesignSystem.TYPOGRAPHY['font_size']['sm']};
                        color: {DesignSystem.COLORS['neutral_400']};
                        text-transform: uppercase;
                    ">Estimated Time</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="
                    background: {DesignSystem.COLORS['neutral_800']};
                    border: 1px solid {DesignSystem.COLORS['neutral_600']};
                    border-radius: {DesignSystem.RADIUS['md']};
                    padding: {DesignSystem.SPACING['md']};
                    text-align: center;
                ">
                    <div style="
                        font-size: {DesignSystem.TYPOGRAPHY['font_size']['xxl']};
                        font-weight: {DesignSystem.TYPOGRAPHY['font_weight']['bold']};
                        color: {DesignSystem.COLORS['success']};
                    ">${estimated_cost:.2f}</div>
                    <div style="
                        font-size: {DesignSystem.TYPOGRAPHY['font_size']['sm']};
                        color: {DesignSystem.COLORS['neutral_400']};
                        text-transform: uppercase;
                    ">Estimated Cost</div>
                </div>
                """, unsafe_allow_html=True)
        
        submitted = st.form_submit_button("🧠 Run Analysis", use_container_width=True, type="primary")

    if submitted:
        # Validate input
        if char_count < min_chars:
            show_validation_error(
                "Business Brief",
                f"Please enter at least {min_chars} characters",
                correction_hint=f"Current: {char_count} characters. Add {min_chars - char_count} more."
            )
        elif char_count > max_chars:
            show_validation_error(
                "Business Brief",
                f"Input exceeds maximum length of {max_chars} characters",
                correction_hint=f"Current: {char_count} characters. Remove {char_count - max_chars} characters."
            )
        else:
            # Save draft to session state
            st.session_state['draft_brief'] = business_brief.strip()
            
            brief = business_brief.strip()
            with st.spinner("Submitting job to agent pipeline..."):
                try:
                    result = api("POST", "/analyze", json={
                        "company_description": brief[:2000],
                        "product_details": brief[:2000],
                        "target_audience": "Infer the target audience from the business brief.",
                        "goals": "Infer the business goals from the brief and produce practical milestones.",
                        "constraints": "Infer constraints from the business brief. If none are stated, call that out.",
                    })
                    if result:
                        st.session_state["active_job_id"] = result["job_id"]
                        st.session_state["job_submitted"] = True
                        # Clear draft after successful submission
                        st.session_state['draft_brief'] = ""
                        # Show success toast
                        show_toast(f"Job submitted successfully! ID: {result['job_id'][:8]}...", "success")
                        st.rerun()  # Trigger rerun to start monitoring
                    else:
                        # Show error toast with retry button
                        show_toast(
                            "Failed to submit job. Please check the backend connection.",
                            "error",
                            action_button={
                                "label": "Retry",
                                "action": "location.reload()"
                            }
                        )
                except Exception as e:
                    show_toast(f"Error submitting job: {str(e)}", "error", action_button={
                        "label": "Retry",
                        "action": "location.reload()"
                    })

    # Show live progress for the active job (persists across reruns via session_state)
    active_job_id = st.session_state.get("active_job_id")
    if active_job_id and st.session_state.get("job_submitted"):
        # Show success toast for job submission
        show_toast(f"Job submitted successfully! ID: {active_job_id[:8]}...", "success")
        # Clear the flag to prevent showing toast on every rerun
        st.session_state["job_submitted"] = False
        st.markdown("---")
        
        # Connection status indicator
        connection_status_placeholder = st.empty()
        
        st.subheader("⚡ Live Agent Progress")

        # Show skeleton timeline initially
        progress_placeholder = st.empty()
        with progress_placeholder.container():
            from components import skeleton_timeline
            st.markdown(skeleton_timeline(5), unsafe_allow_html=True)
        
        log_placeholder = st.empty()
        with log_placeholder.container():
            from components import skeleton_log_panel
            st.markdown("### 📋 Workflow Logs")
            st.markdown(skeleton_log_panel(10), unsafe_allow_html=True)

        cancel_col, _ = st.columns([1, 4])
        with cancel_col:
            if st.button("🛑 Cancel Job", type="secondary"):
                try:
                    cancel_result = api("POST", f"/cancel/{active_job_id}")
                    if cancel_result:
                        show_toast(f"Job {active_job_id[:8]}... cancelled successfully", "success")
                        time.sleep(1)
                        st.rerun()
                    else:
                        show_toast("Failed to cancel job", "error", action_button={
                            "label": "Retry",
                            "action": "location.reload()"
                        })
                except Exception as e:
                    show_toast(f"Error cancelling job: {str(e)}", "error")

        # Import StreamManager
        from stream_manager import StreamManager
        
        # Initialize StreamManager
        stream_manager = StreamManager(BACKEND_URL, active_job_id)
        
        # Display initial connection status
        with connection_status_placeholder.container():
            st.markdown(_clean_html(f"""
            <div style="
                display: inline-flex;
                align-items: center;
                gap: {DesignSystem.SPACING['xs']};
                padding: {DesignSystem.SPACING['xs']} {DesignSystem.SPACING['sm']};
                background: {DesignSystem.COLORS['neutral_800']};
                border: 1px solid {DesignSystem.COLORS['neutral_600']};
                border-radius: {DesignSystem.RADIUS['sm']};
                font-size: {DesignSystem.TYPOGRAPHY['font_size']['sm']};
                margin-bottom: {DesignSystem.SPACING['md']};
            ">
                <span style="color: {DesignSystem.COLORS['info']};">🔄</span>
                <span style="color: {DesignSystem.COLORS['neutral_300']};">Connecting...</span>
            </div>
            """), unsafe_allow_html=True)
        
        # Stream events using StreamManager
        terminal_statuses = ("completed", "failed", "aborted")
        
        # Track if we've shown the polling fallback warning
        polling_warning_shown = False
        
        try:
            for event in stream_manager.connect_stream():
                # Update connection status indicator
                conn_status = stream_manager.get_connection_status()
                
                # Show warning toast when falling back to polling (only once)
                if conn_status == 'polling' and not polling_warning_shown:
                    show_toast("Streaming unavailable. Using polling for updates.", "warning", duration=3)
                    polling_warning_shown = True
                
                if conn_status == 'streaming':
                    status_icon = '🟢'
                    status_text = 'Live Stream'
                    status_color = DesignSystem.COLORS['success']
                elif conn_status == 'polling':
                    status_icon = '🟡'
                    status_text = 'Polling'
                    status_color = DesignSystem.COLORS['warning']
                else:
                    status_icon = '🔴'
                    status_text = 'Disconnected'
                    status_color = DesignSystem.COLORS['error']
                
                with connection_status_placeholder.container():
                    st.markdown(_clean_html(f"""
                    <div style="
                        display: inline-flex;
                        align-items: center;
                        gap: {DesignSystem.SPACING['xs']};
                        padding: {DesignSystem.SPACING['xs']} {DesignSystem.SPACING['sm']};
                        background: {DesignSystem.COLORS['neutral_800']};
                        border: 1px solid {DesignSystem.COLORS['neutral_600']};
                        border-radius: {DesignSystem.RADIUS['sm']};
                        font-size: {DesignSystem.TYPOGRAPHY['font_size']['sm']};
                        margin-bottom: {DesignSystem.SPACING['md']};
                    ">
                        <span>{status_icon}</span>
                        <span style="color: {status_color}; font-weight: {DesignSystem.TYPOGRAPHY['font_weight']['semibold']};">{status_text}</span>
                    </div>
                    """), unsafe_allow_html=True)
                
                # Handle different event types
                event_type = event.get('type')
                
                if event_type in ['log', 'status', 'agent_update']:
                    # Fetch latest status to update displays
                    try:
                        status_data = api("GET", f"/status/{active_job_id}")
                        agent_data = api("GET", f"/agents/{active_job_id}") or []
                        log_data = api("GET", f"/logs/{active_job_id}") or []
                        
                        # Update agent timeline using new component
                        with progress_placeholder.container():
                            from components import render_agent_timeline
                            timeline_html = render_agent_timeline(
                                agent_data,
                                status_data["status"] if status_data else "pending",
                                layout='horizontal'
                            )
                            st.markdown(timeline_html, unsafe_allow_html=True)
                        
                        # Update log panel using new component (show last 50 entries)
                        with log_placeholder.container():
                            from components import render_log_panel
                            st.markdown("### 📋 Workflow Logs")
                            log_panel_html = render_log_panel(
                                log_data[-50:],
                                filters=None,
                                search_query=None,
                                auto_scroll=True
                            )
                            st.markdown(log_panel_html, unsafe_allow_html=True)
                    except Exception as e:
                        show_toast(f"Error fetching job status: {str(e)}", "error")
                
                elif event_type == 'done':
                    # Job completed, exit streaming loop
                    st.session_state["job_submitted"] = False
                    break
                
                elif event_type == 'error':
                    # Error occurred during streaming
                    error_msg = event.get('data', {}).get('message', 'Unknown error')
                    show_toast(f"Streaming error: {error_msg}", "error", action_button={
                        "label": "Retry",
                        "action": "location.reload()"
                    })
                    st.session_state["job_submitted"] = False
                    break
        
        except Exception as e:
            show_toast(f"Unexpected error during monitoring: {str(e)}", "error", action_button={
                "label": "Retry",
                "action": "location.reload()"
            })
            st.session_state["job_submitted"] = False

        # Render final report — always on same run after loop exits
        try:
            final_status = api("GET", f"/status/{active_job_id}")
            if final_status and final_status.get("final_report"):
                st.divider()
                st.subheader("📄 Final Report")
                _render_final_report(final_status["final_report"])
            elif final_status and final_status["status"] == "failed":
                show_toast("Analysis failed. Check the logs panel for details.", "error")
        except Exception as e:
            show_toast(f"Error fetching final report: {str(e)}", "error")


# ─── Page: Job Dashboard ──────────────────────────────────────────────────────

elif "📊" in page:
    st.title("📊 Job Dashboard")
    
    # Initialize session state for filters and pagination
    if 'dashboard_page' not in st.session_state:
        st.session_state['dashboard_page'] = 1
    if 'dashboard_status_filter' not in st.session_state:
        st.session_state['dashboard_status_filter'] = 'all'
    if 'dashboard_sort' not in st.session_state:
        st.session_state['dashboard_sort'] = 'date_desc'
    if 'dashboard_search' not in st.session_state:
        st.session_state['dashboard_search'] = ''
    
    try:
        # Fetch all jobs
        all_jobs = api("GET", "/jobs")
        
        if all_jobs:
            # Calculate aggregate statistics
            total_jobs = len(all_jobs)
            completed_jobs = sum(1 for job in all_jobs if job.get('status') == 'completed')
            failed_jobs = sum(1 for job in all_jobs if job.get('status') == 'failed')
            success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
            total_cost = sum(job.get('total_cost_usd', 0) for job in all_jobs)
            
            # Display aggregate statistics in metric cards
            st.markdown("### 📈 Overview")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                from components import metric_card
                import streamlit.components.v1 as components_html
                components_html.html(metric_card(
                    "Total Jobs",
                    str(total_jobs),
                    icon="📊"
                ), height=140)
            
            with col2:
                from components import metric_card
                import streamlit.components.v1 as components_html
                components_html.html(metric_card(
                    "Success Rate",
                    f"{success_rate:.1f}%",
                    delta=f"+{completed_jobs}" if completed_jobs > 0 else "0",
                    icon="✅"
                ), height=140)
            
            with col3:
                from components import metric_card
                import streamlit.components.v1 as components_html
                components_html.html(metric_card(
                    "Failed Jobs",
                    str(failed_jobs),
                    delta=f"-{failed_jobs}" if failed_jobs > 0 else "0",
                    icon="❌"
                ), height=140)
            
            with col4:
                from components import metric_card
                import streamlit.components.v1 as components_html
                components_html.html(metric_card(
                    "Total Cost",
                    f"${total_cost:.2f}",
                    icon="💰"
                ), height=140)
            
            st.markdown("---")
            
            # Filters and controls
            st.markdown("### 🔍 Filter & Sort")
            
            filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([2, 2, 2, 1])
            
            with filter_col1:
                # Status filter
                status_options = ['all', 'completed', 'running', 'failed', 'aborted', 'pending']
                status_filter = st.selectbox(
                    "Status",
                    options=status_options,
                    index=status_options.index(st.session_state['dashboard_status_filter']),
                    key='status_filter_select'
                )
                st.session_state['dashboard_status_filter'] = status_filter
            
            with filter_col2:
                # Sort dropdown
                sort_options = {
                    'date_desc': 'Date (Newest First)',
                    'date_asc': 'Date (Oldest First)',
                    'cost_desc': 'Cost (High to Low)',
                    'cost_asc': 'Cost (Low to High)',
                    'status': 'Status'
                }
                sort_option = st.selectbox(
                    "Sort By",
                    options=list(sort_options.keys()),
                    format_func=lambda x: sort_options[x],
                    index=list(sort_options.keys()).index(st.session_state['dashboard_sort']),
                    key='sort_select'
                )
                st.session_state['dashboard_sort'] = sort_option
            
            with filter_col3:
                # Search input
                search_query = st.text_input(
                    "Search",
                    value=st.session_state['dashboard_search'],
                    placeholder="Search by company or job ID...",
                    key='search_input'
                )
                st.session_state['dashboard_search'] = search_query
            
            with filter_col4:
                # Refresh button
                if st.button("🔄 Refresh", use_container_width=True):
                    st.rerun()
                # Toggle to show/hide stale (ghost) running jobs
                show_stale = st.checkbox(
                    "Show stale/ghost jobs",
                    value=False,
                    help=f"Show jobs older than {STALE_JOB_HOURS} hours that are still marked running/pending",
                    key='show_stale_jobs'
                )
            
            # Apply filters
            filtered_jobs = all_jobs

            # Hide stale/ghost jobs by default
            if not st.session_state.get('show_stale_jobs', False):
                from datetime import datetime as _dt
                safe_jobs = []
                for job in filtered_jobs:
                    status_j = (job.get('status') or '').lower()
                    created_at = job.get('created_at', '')
                    is_stale = False
                    if status_j in ('running', 'pending') and created_at:
                        try:
                            created_dt = _dt.fromisoformat(created_at.replace('Z', '+00:00'))
                            # compare to now (UTC)
                            try:
                                now = _dt.utcnow()
                                created_naive = created_dt.replace(tzinfo=None) if created_dt.tzinfo else created_dt
                                age_hours = (now - created_naive).total_seconds() / 3600.0
                                if age_hours > STALE_JOB_HOURS:
                                    is_stale = True
                            except Exception:
                                # If timezone math fails, keep the job
                                is_stale = False
                        except Exception:
                            is_stale = False

                    if not is_stale:
                        safe_jobs.append(job)

                filtered_jobs = safe_jobs
            
            # Status filter
            if status_filter != 'all':
                filtered_jobs = [job for job in filtered_jobs if job.get('status') == status_filter]
            
            # Search filter with debouncing (Requirement 10.2)
            if search_query:
                from performance_utils import debounce_search
                if 'debounced_search_query' not in st.session_state:
                    st.session_state['debounced_search_query'] = ''
                
                if debounce_search(search_query, delay=0.3):
                    st.session_state['debounced_search_query'] = search_query
                
                stable_query = st.session_state['debounced_search_query']
                if stable_query:
                    search_lower = stable_query.lower()
                    filtered_jobs = [
                        job for job in filtered_jobs
                        if search_lower in (job.get('company') or '').lower() or
                           search_lower in (job.get('job_id') or '').lower()
                    ]
            
            # Apply sorting
            if sort_option == 'date_desc':
                filtered_jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            elif sort_option == 'date_asc':
                filtered_jobs.sort(key=lambda x: x.get('created_at', ''))
            elif sort_option == 'cost_desc':
                filtered_jobs.sort(key=lambda x: x.get('total_cost_usd', 0), reverse=True)
            elif sort_option == 'cost_asc':
                filtered_jobs.sort(key=lambda x: x.get('total_cost_usd', 0))
            elif sort_option == 'status':
                # Sort by status priority: running > pending > completed > failed > aborted
                status_priority = {'running': 0, 'pending': 1, 'completed': 2, 'failed': 3, 'aborted': 4}
                filtered_jobs.sort(key=lambda x: status_priority.get(x.get('status', 'pending'), 5))
            
            # Pagination
            jobs_per_page = 20
            total_pages = (len(filtered_jobs) + jobs_per_page - 1) // jobs_per_page
            current_page = st.session_state['dashboard_page']
            
            # Ensure current page is valid
            if current_page > total_pages:
                current_page = max(1, total_pages)
                st.session_state['dashboard_page'] = current_page
            
            # Calculate pagination slice
            start_idx = (current_page - 1) * jobs_per_page
            end_idx = min(start_idx + jobs_per_page, len(filtered_jobs))
            page_jobs = filtered_jobs[start_idx:end_idx]
            
            st.markdown("---")
            
            # Display results count
            st.markdown(f"**Showing {start_idx + 1}-{end_idx} of {len(filtered_jobs)} jobs**")
            
            if page_jobs:
                # Render job cards in responsive grid
                st.markdown(f"""
                <style>
                .job-card-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                    gap: {DesignSystem.SPACING['lg']};
                    margin: {DesignSystem.SPACING['lg']} 0;
                }}
                
                .job-card {{
                    background: {DesignSystem.COLORS['glass_bg']};
                    backdrop-filter: blur(12px);
                    -webkit-backdrop-filter: blur(12px);
                    border: 1px solid {DesignSystem.COLORS['glass_border']};
                    border-radius: {DesignSystem.RADIUS['lg']};
                    padding: {DesignSystem.SPACING['lg']};
                    transition: all {DesignSystem.ANIMATION['duration_normal']} {DesignSystem.ANIMATION['easing']};
                    position: relative;
                    overflow: hidden;
                }}
                
                .job-card:hover {{
                    border-color: {DesignSystem.COLORS['primary']};
                    box-shadow: {DesignSystem.SHADOWS['glow']};
                    transform: translateY(-4px);
                }}
                
                .job-card-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    margin-bottom: {DesignSystem.SPACING['md']};
                }}
                
                .job-card-title {{
                    font-size: {DesignSystem.TYPOGRAPHY['font_size']['lg']};
                    font-weight: {DesignSystem.TYPOGRAPHY['font_weight']['semibold']};
                    color: {DesignSystem.COLORS['neutral_100']};
                    margin-bottom: {DesignSystem.SPACING['xs']};
                    line-height: {DesignSystem.TYPOGRAPHY['line_height']['tight']};
                }}
                
                .job-card-id {{
                    font-size: {DesignSystem.TYPOGRAPHY['font_size']['xs']};
                    color: {DesignSystem.COLORS['neutral_400']};
                    font-family: {DesignSystem.TYPOGRAPHY['font_family']['mono']};
                }}
                
                .job-card-meta {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding-top: {DesignSystem.SPACING['md']};
                    border-top: 1px solid {DesignSystem.COLORS['neutral_600']};
                    margin-top: {DesignSystem.SPACING['md']};
                }}
                
                .job-card-time {{
                    font-size: {DesignSystem.TYPOGRAPHY['font_size']['sm']};
                    color: {DesignSystem.COLORS['neutral_400']};
                }}
                
                .job-card-cost {{
                    font-size: {DesignSystem.TYPOGRAPHY['font_size']['md']};
                    font-weight: {DesignSystem.TYPOGRAPHY['font_weight']['semibold']};
                    color: {DesignSystem.COLORS['success']};
                }}
                
                .job-card-actions {{
                    display: flex;
                    gap: {DesignSystem.SPACING['sm']};
                    margin-top: {DesignSystem.SPACING['md']};
                }}
                </style>
                """, unsafe_allow_html=True)
                
                # Render cards in grid (3 per row)
                for i in range(0, len(page_jobs), 3):
                    cols = st.columns(3)
                    for j, col in enumerate(cols):
                        if i + j < len(page_jobs):
                            job = page_jobs[i + j]
                            
                            with col:
                                # Job card container
                                job_id = job.get('job_id', 'N/A')
                                status = job.get('status', 'pending')
                                company = job.get('company', 'Unknown Company')
                                created_at = job.get('created_at', '')
                                cost_usd = job.get('total_cost_usd', 0.0)
                                
                                # Truncate and escape company name to avoid rendering unintended HTML/CSS
                                company_display = company[:50] + "..." if len(company) > 50 else company
                                company_display_escaped = html_escape(company_display)

                                # Truncate and escape job id for display
                                job_id_display = job_id[:16] + "..." if len(job_id) > 16 else job_id
                                job_id_display_escaped = html_escape(job_id_display)

                                # Format timestamp (and escape)
                                try:
                                    from datetime import datetime
                                    created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                    time_display = created_dt.strftime('%b %d, %Y %H:%M')
                                except:
                                    time_display = created_at[:19] if created_at else 'N/A'
                                time_display_escaped = html_escape(time_display)

                                # Get status badge (HTML) - intentionally not escaped
                                status_html = status_badge(status)

                                # Render card (escaped fields only)
                                st.markdown(f"""
                                <div class="job-card">
                                    <div class="job-card-header">
                                        <div style="flex: 1;">
                                            <div class="job-card-title">{company_display_escaped}</div>
                                            <div class="job-card-id">{job_id_display_escaped}</div>
                                        </div>
                                        <div>
                                            {status_html}
                                        </div>
                                    </div>
                                    <div class="job-card-meta">
                                        <div class="job-card-time">🕒 {time_display_escaped}</div>
                                        <div class="job-card-cost">${cost_usd:.4f}</div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Action buttons
                                action_col1, action_col2, action_col3 = st.columns(3)
                                
                                # Sanitize job_id for Streamlit keys (avoid special chars)
                                def _sanitize_key(s: str) -> str:
                                    return re.sub(r"[^0-9a-zA-Z_]+", "_", s)

                                safe_key = _sanitize_key(job_id)

                                with action_col1:
                                    if st.button("🔍 Inspect", key=f"inspect_{safe_key}", use_container_width=True):
                                        st.session_state["inspect_job_id"] = job_id
                                        st.session_state["job_submitted"] = False
                                        st.session_state["next_page"] = "🔍 Job Inspector"
                                        st.rerun()

                                with action_col2:
                                    if status in ['running', 'pending']:
                                        if st.button("🛑 Cancel", key=f"cancel_{safe_key}", use_container_width=True):
                                            try:
                                                cancel_result = api("POST", f"/cancel/{job_id}")
                                                if cancel_result:
                                                    show_toast(f"Job {job_id[:8]}... cancelled successfully", "success")
                                                    time.sleep(1)
                                                    st.rerun()
                                                else:
                                                    show_toast("Failed to cancel job", "error", action_button={
                                                        "label": "Retry",
                                                        "action": "location.reload()"
                                                    })
                                            except Exception as e:
                                                show_toast(f"Error: {str(e)}", "error")
                                    else:
                                        st.button("🛑 Cancel", key=f"cancel_{safe_key}", disabled=True, use_container_width=True)

                                with action_col3:
                                    # Delete button (placeholder - backend doesn't have delete endpoint yet)
                                    st.button("🗑️ Delete", key=f"delete_{safe_key}", disabled=True, use_container_width=True)
                
                # Pagination controls
                if total_pages > 1:
                    st.markdown("---")
                    
                    pagination_cols = st.columns([1, 3, 1])
                    
                    with pagination_cols[0]:
                        if current_page > 1:
                            if st.button("⬅️ Previous", use_container_width=True):
                                st.session_state['dashboard_page'] = current_page - 1
                                st.rerun()
                        else:
                            st.button("⬅️ Previous", disabled=True, use_container_width=True)
                    
                    with pagination_cols[1]:
                        st.markdown(f"""
                        <div style="
                            text-align: center;
                            padding: {DesignSystem.SPACING['sm']};
                            font-size: {DesignSystem.TYPOGRAPHY['font_size']['md']};
                            color: {DesignSystem.COLORS['neutral_300']};
                        ">
                            Page {current_page} of {total_pages}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with pagination_cols[2]:
                        if current_page < total_pages:
                            if st.button("Next ➡️", use_container_width=True):
                                st.session_state['dashboard_page'] = current_page + 1
                                st.rerun()
                        else:
                            st.button("Next ➡️", disabled=True, use_container_width=True)
            else:
                st.info("No jobs match your filters. Try adjusting your search criteria.")
        else:
            st.info("No jobs yet. Submit your first analysis!")
    except Exception as e:
        # Show error toast for exceptions
        show_toast(f"Error loading jobs: {str(e)}", "error", action_button={
            "label": "Retry",
            "action": "location.reload()"
        })


# ─── Page: Job Inspector ──────────────────────────────────────────────────────

elif "🔍" in page:
    st.title("🔍 Job Inspector")

    default_id = st.session_state.get(
        "inspect_job_id",
        st.session_state.get("active_job_id", ""),
    )
    job_id_input = st.text_input(
        "Job ID",
        value=default_id,
        placeholder="Paste a job ID here",
    )

    if job_id_input:
        # Reset lazy loading when job_id_input changes (Requirement 10.8)
        if "last_inspected_job_id" not in st.session_state:
            st.session_state["last_inspected_job_id"] = ""
        
        if job_id_input != st.session_state["last_inspected_job_id"]:
            from performance_utils import reset_lazy_loading
            reset_lazy_loading()
            st.session_state["last_inspected_job_id"] = job_id_input

        try:
            # Show loading skeletons while fetching data
            timeline_placeholder = st.empty()
            logs_placeholder = st.empty()
            report_placeholder = st.empty()
            
            with timeline_placeholder.container():
                st.subheader("📈 Agent Timeline")
                from components import skeleton_timeline
                st.markdown(skeleton_timeline(5), unsafe_allow_html=True)
            
            with logs_placeholder.container():
                st.subheader("📋 Workflow Logs")
                from components import skeleton_log_panel
                st.markdown(skeleton_log_panel(10), unsafe_allow_html=True)
            
            with report_placeholder.container():
                st.subheader("📄 Final Report")
                from components import skeleton_report
                st.markdown(skeleton_report(), unsafe_allow_html=True)
            
            # Fetch data
            status_data = api("GET", f"/status/{job_id_input}")
            agent_data = api("GET", f"/agents/{job_id_input}") or []
            log_data = api("GET", f"/logs/{job_id_input}") or []
            
            # Clear skeletons
            timeline_placeholder.empty()
            logs_placeholder.empty()
            report_placeholder.empty()

            if status_data:
                # Enrich agent data with decisions, collaborations, and other details from logs
                enriched_agent_data = _enrich_agent_data_with_logs(agent_data, log_data)
                
                # Process logs to mark decision logs and add structured data
                processed_logs = _process_logs_for_display(log_data)
                
                tab1, tab2, tab3, tab4 = st.tabs(["📈 Timeline", "📋 Logs", "📄 Report", "🔬 Raw"])

                with tab1:
                    st.subheader("Agent Execution Timeline")
                    
                    # Display job status and metadata
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        from components import metric_card
                        st.markdown(metric_card(
                            "Job Status",
                            status_data["status"].upper(),
                            icon=DesignSystem.get_status_icon(status_data["status"])
                        ), unsafe_allow_html=True)
                    
                    with col2:
                        total_cost = sum(task.get('cost_usd', 0) for task in enriched_agent_data)
                        st.markdown(metric_card(
                            "Total Cost",
                            f"${total_cost:.4f}",
                            icon="💰"
                        ), unsafe_allow_html=True)
                    
                    with col3:
                        total_time = sum(task.get('execution_time_ms', 0) for task in enriched_agent_data) / 1000.0
                        time_display = f"{total_time / 60:.1f}m" if total_time >= 60 else f"{total_time:.1f}s"
                        st.markdown(metric_card(
                            "Total Time",
                            time_display,
                            icon="⏱️"
                        ), unsafe_allow_html=True)
                    
                    with col4:
                        agent_count = len(enriched_agent_data)
                        st.markdown(metric_card(
                            "Agents",
                            str(agent_count),
                            icon="🤖"
                        ), unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # Import render_agent_timeline from components
                    from components import render_agent_timeline
                    timeline_html = render_agent_timeline(
                        enriched_agent_data, 
                        status_data["status"], 
                        layout='horizontal'
                    )
                    st.markdown(timeline_html, unsafe_allow_html=True)
                    
                    # Display key insights section
                    st.markdown("---")
                    st.subheader("🔍 Key Insights")
                    
                    # Extract and display key insights from enriched data
                    insights_col1, insights_col2 = st.columns(2)
                    
                    with insights_col1:
                        # Count decisions
                        total_decisions = sum(len(task.get('decisions', [])) for task in enriched_agent_data)
                        if total_decisions > 0:
                            st.markdown(f"""
                            <div style="
                                background: {DesignSystem.COLORS['neutral_800']};
                                border-left: 3px solid {DesignSystem.COLORS['primary']};
                                padding: {DesignSystem.SPACING['md']};
                                border-radius: {DesignSystem.RADIUS['md']};
                                margin-bottom: {DesignSystem.SPACING['sm']};
                            ">
                                <div style="
                                    font-size: {DesignSystem.TYPOGRAPHY['font_size']['lg']};
                                    font-weight: {DesignSystem.TYPOGRAPHY['font_weight']['bold']};
                                    color: {DesignSystem.COLORS['primary_light']};
                                ">{total_decisions}</div>
                                <div style="
                                    font-size: {DesignSystem.TYPOGRAPHY['font_size']['sm']};
                                    color: {DesignSystem.COLORS['neutral_400']};
                                ">Autonomous Decisions Made</div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with insights_col2:
                        # Count collaborations
                        total_collaborations = sum(len(task.get('collaborations', [])) for task in enriched_agent_data)
                        if total_collaborations > 0:
                            st.markdown(f"""
                            <div style="
                                background: {DesignSystem.COLORS['neutral_800']};
                                border-left: 3px solid {DesignSystem.COLORS['info']};
                                padding: {DesignSystem.SPACING['md']};
                                border-radius: {DesignSystem.RADIUS['md']};
                                margin-bottom: {DesignSystem.SPACING['sm']};
                            ">
                                <div style="
                                    font-size: {DesignSystem.TYPOGRAPHY['font_size']['lg']};
                                    font-weight: {DesignSystem.TYPOGRAPHY['font_weight']['bold']};
                                    color: {DesignSystem.COLORS['info']};
                                ">{total_collaborations}</div>
                                <div style="
                                    font-size: {DesignSystem.TYPOGRAPHY['font_size']['sm']};
                                    color: {DesignSystem.COLORS['neutral_400']};
                                ">Agent Collaborations</div>
                            </div>
                            """, unsafe_allow_html=True)

                with tab2:
                    st.subheader("Workflow Logs")
                    
                    # Add filter controls
                    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 3])
                    
                    with filter_col1:
                        # Level filter
                        level_options = ['All'] + sorted(list(set(log.get('level', 'INFO') for log in processed_logs)))
                        selected_levels = st.multiselect(
                            "Filter by Level",
                            options=level_options,
                            default=['All'],
                            key='log_level_filter'
                        )
                    
                    with filter_col2:
                        # Agent filter
                        agent_options = ['All'] + sorted(list(set(log.get('agent', 'system') for log in processed_logs)))
                        selected_agents = st.multiselect(
                            "Filter by Agent",
                            options=agent_options,
                            default=['All'],
                            key='log_agent_filter'
                        )
                    
                    with filter_col3:
                        # Search input
                        search_query_log = st.text_input(
                            "Search Logs",
                            placeholder="Search messages...",
                            key='log_search_input'
                        )
                    
                    # Apply manual filtering first to support correct pagination size
                    filtered_logs = processed_logs
                    if search_query_log:
                        search_lower = search_query_log.lower()
                        filtered_logs = [log for log in filtered_logs if search_lower in (log.get('message') or '').lower()]
                    
                    if 'All' not in selected_levels:
                        filtered_logs = [log for log in filtered_logs if log.get('level', 'INFO') in selected_levels]
                        
                    if 'All' not in selected_agents:
                        filtered_logs = [log for log in filtered_logs if log.get('agent', 'system') in selected_agents]
                    
                    # Lazy loading
                    from performance_utils import lazy_load_logs, load_more_logs
                    visible_logs = lazy_load_logs(filtered_logs, chunk_size=50)
                    
                    # Import render_log_panel from components
                    from components import render_log_panel
                    log_panel_html = render_log_panel(
                        visible_logs, 
                        filters=None,  # Handled above
                        search_query=None,  # Handled above
                        auto_scroll=False
                    )
                    st.markdown(log_panel_html, unsafe_allow_html=True)
                    
                    # Render Load More button if there are more logs to display
                    if len(filtered_logs) > len(visible_logs):
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("🔄 Load More Logs", key="load_more_logs_inspector_btn", use_container_width=True):
                            load_more_logs(increment=50)
                            st.rerun()

                with tab3:
                    st.subheader("Final Report")
                    report = status_data.get("final_report")
                    if report:
                        # Import render_final_report from components
                        from components import render_final_report
                        render_final_report(report)
                    else:
                        st.info("Report not yet available")

                with tab4:
                    st.subheader("Raw JSON")
                    st.json(status_data)
            else:
                # Use job not found message instead of st.error
                show_job_not_found(job_id)
        except Exception as e:
            # Show error toast for exceptions
            show_toast(f"Error inspecting job: {str(e)}", "error", action_button={
                "label": "Retry",
                "action": "location.reload()"
            })
