"""
Notifications Demo - Interactive demonstration of the notification system

This demo showcases all notification types and features implemented in Task 8.
Run with: streamlit run frontend/notifications_demo.py
"""

import streamlit as st
try:
    from frontend.design_system import DesignSystem
except ModuleNotFoundError:
    from design_system import DesignSystem

try:
    from frontend.notifications import (
        show_toast,
        show_connection_error,
        show_timeout_error,
        show_validation_error,
        show_job_not_found,
    )
except ModuleNotFoundError:
    from notifications import (
        show_toast,
        show_connection_error,
        show_timeout_error,
        show_validation_error,
        show_job_not_found,
    )


st.set_page_config(
    page_title="Notifications Demo",
    page_icon="🔔",
    layout="wide",
)

# Inject design system CSS
st.markdown(DesignSystem.generate_css(), unsafe_allow_html=True)

st.title("🔔 Notification System Demo")
st.markdown("Interactive demonstration of all notification types and features")

st.divider()

# Toast Notifications Section
st.header("1. Toast Notifications")
st.markdown("Auto-dismissing notifications that appear at the top-right of the screen")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("✅ Success Toast", use_container_width=True):
        show_toast("Job submitted successfully!", "success")

with col2:
    if st.button("⚠️ Warning Toast", use_container_width=True):
        show_toast("Falling back to polling mode", "warning")

with col3:
    if st.button("❌ Error Toast", use_container_width=True):
        show_toast("Failed to connect to backend", "error")

with col4:
    if st.button("ℹ️ Info Toast", use_container_width=True):
        show_toast("Processing your request...", "info")

st.markdown("---")

# Toast with Action Button
st.subheader("Toast with Action Button")
st.markdown("Error toasts can include retry buttons for failed actions")

if st.button("🔄 Error Toast with Retry", use_container_width=True):
    show_toast(
        "Failed to submit job",
        "error",
        action_button={
            "label": "Retry",
            "action": "alert('Retry clicked!')"
        }
    )

st.markdown("---")

# Custom Duration
st.subheader("Custom Duration")
st.markdown("Toasts can have custom auto-dismiss durations")

duration = st.slider("Duration (seconds)", 1, 10, 5)
if st.button(f"⏱️ Toast with {duration}s duration", use_container_width=True):
    show_toast(f"This toast will dismiss after {duration} seconds", "info", duration=duration)

st.divider()

# Connection Error Banner
st.header("2. Connection Error Banner")
st.markdown("Prominent banner displayed when backend is unreachable")

if st.button("🔴 Show Connection Error", use_container_width=True):
    show_connection_error("http://localhost:8000/api/v1", retry_callback="alert('Retry clicked!')")

st.divider()

# Timeout Error Message
st.header("3. Timeout Error Message")
st.markdown("Displayed when requests exceed timeout duration")

timeout_seconds = st.number_input("Timeout (seconds)", 5, 60, 10)
if st.button("⏱️ Show Timeout Error", use_container_width=True):
    show_timeout_error("Job submission", timeout_seconds, retry_callback="alert('Retry clicked!')")

st.divider()

# Inline Validation Error
st.header("4. Inline Validation Errors")
st.markdown("Displayed below form fields with validation errors")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Without Correction Hint")
    if st.button("❌ Show Basic Validation Error", use_container_width=True):
        show_validation_error("Business Brief", "Field is required")

with col2:
    st.subheader("With Correction Hint")
    if st.button("💡 Show Validation Error with Hint", use_container_width=True):
        show_validation_error(
            "Email",
            "Invalid email format",
            correction_hint="Please enter a valid email address (e.g., user@example.com)"
        )

st.divider()

# Job Not Found Message
st.header("5. Job Not Found Message")
st.markdown("Displayed when a requested job ID doesn't exist")

job_id = st.text_input("Job ID", "job123")
if st.button("🔍 Show Job Not Found", use_container_width=True):
    show_job_not_found(job_id)

st.divider()

# Real-World Scenarios
st.header("6. Real-World Scenarios")
st.markdown("Common use cases for notifications in the application")

scenario = st.selectbox(
    "Select a scenario",
    [
        "Job Submission Success",
        "Job Submission Failure",
        "Job Cancellation Success",
        "Job Cancellation Failure",
        "Export Success",
        "Polling Fallback Warning",
        "Slow Response Warning",
        "Form Validation Error",
        "Backend Unreachable",
        "Request Timeout",
    ]
)

if st.button("▶️ Run Scenario", use_container_width=True, type="primary"):
    if scenario == "Job Submission Success":
        show_toast("Job submitted successfully! ID: job_abc123", "success")
        
    elif scenario == "Job Submission Failure":
        show_toast(
            "Failed to submit job. Please check the backend connection.",
            "error",
            action_button={
                "label": "Retry",
                "action": "alert('Retrying job submission...')"
            }
        )
        
    elif scenario == "Job Cancellation Success":
        show_toast("Job job_abc123 cancelled successfully", "success")
        
    elif scenario == "Job Cancellation Failure":
        show_toast(
            "Failed to cancel job",
            "error",
            action_button={
                "label": "Retry",
                "action": "alert('Retrying cancellation...')"
            }
        )
        
    elif scenario == "Export Success":
        show_toast("Report exported successfully!", "success")
        
    elif scenario == "Polling Fallback Warning":
        show_toast("Streaming unavailable. Using polling for updates.", "warning", duration=3)
        
    elif scenario == "Slow Response Warning":
        show_toast("Backend is responding slowly. Please be patient.", "warning")
        
    elif scenario == "Form Validation Error":
        show_validation_error(
            "Business Brief",
            "Please enter at least 50 characters",
            correction_hint="Current: 25 characters. Add 25 more characters."
        )
        
    elif scenario == "Backend Unreachable":
        show_connection_error("http://localhost:8000/api/v1", retry_callback="alert('Retrying connection...')")
        
    elif scenario == "Request Timeout":
        show_timeout_error("Job submission", 10, retry_callback="alert('Retrying request...')")

st.divider()

# Multiple Toasts
st.header("7. Multiple Toasts")
st.markdown("Multiple toasts can be displayed simultaneously with unique IDs")

if st.button("🎉 Show Multiple Toasts", use_container_width=True):
    show_toast("First notification", "success")
    show_toast("Second notification", "info")
    show_toast("Third notification", "warning")
    st.info("Three toasts should appear at the top-right, stacked vertically")

st.divider()

# Implementation Notes
st.header("📝 Implementation Notes")

st.markdown("""
### Features
- ✅ Auto-dismiss after configurable duration (default: 5 seconds)
- ✅ Manual close button (×)
- ✅ Smooth slide-in/slide-out animations
- ✅ Four notification types: success, warning, error, info
- ✅ Optional action buttons for interactive notifications
- ✅ Fixed positioning at top-right of screen
- ✅ Glassmorphism styling with backdrop blur
- ✅ Color-coded borders and icons
- ✅ Unique IDs for multiple toasts

### Usage in app.py

```python
from frontend.notifications import show_toast, show_connection_error

# Success toast
show_toast("Job submitted successfully!", "success")

# Error toast with retry button
show_toast(
    "Failed to connect",
    "error",
    action_button={
        "label": "Retry",
        "action": "location.reload()"
    }
)

# Connection error banner
if not health:
    show_connection_error(BACKEND_URL, retry_callback="location.reload()")
```

### Requirements Mapping
- **11.1**: Connection error banner ✅
- **11.2**: Job not found message ✅
- **11.3**: Inline validation errors ✅
- **11.4**: Success toasts ✅
- **11.5**: Action failure prevention ✅
- **11.6**: Toast notification system ✅
- **11.7**: Warning toasts ✅
- **11.8**: Timeout messages ✅

### Testing
All notification components have been tested with 36 unit tests:
```bash
python -m pytest frontend/test_notifications.py -v
```
""")

st.divider()

st.success("✅ All notification types implemented and ready for integration!")
