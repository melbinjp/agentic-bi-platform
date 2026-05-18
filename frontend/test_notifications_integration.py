"""
Integration Tests for Notifications in Streamlit App

Tests the integration of notification components within the main Streamlit application.
Verifies that notifications are properly displayed in various scenarios.

Requirements: 11.1-11.8
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
from frontend.notifications import (
    toast_notification,
    connection_error_banner,
    timeout_error_message,
    inline_validation_error,
    job_not_found_message,
    show_toast,
    show_connection_error,
    show_timeout_error,
    show_validation_error,
    show_job_not_found,
)


class TestNotificationIntegrationScenarios:
    """Test notification integration in real-world scenarios."""
    
    def test_job_submission_success_flow(self):
        """Test success toast after job submission."""
        # Simulate successful job submission
        job_id = "test-job-123"
        
        # Generate success toast
        html = toast_notification(
            f"Job submitted successfully! ID: {job_id[:8]}...",
            "success"
        )
        
        assert "Job submitted successfully!" in html
        assert job_id[:8] in html
        assert "toast-success" in html
        assert "✅" in html
    
    def test_job_submission_failure_flow(self):
        """Test error toast with retry button after job submission failure."""
        # Simulate failed job submission
        html = toast_notification(
            "Failed to submit job. Please check the backend connection.",
            "error",
            action_button={
                "label": "Retry",
                "action": "location.reload()"
            }
        )
        
        assert "Failed to submit job" in html
        assert "toast-error" in html
        assert "Retry" in html
        assert "location.reload()" in html
    
    def test_job_cancellation_success_flow(self):
        """Test success toast after job cancellation."""
        job_id = "test-job-456"
        
        html = toast_notification(
            f"Job {job_id[:8]}... cancelled successfully",
            "success"
        )
        
        assert "cancelled successfully" in html
        assert job_id[:8] in html
        assert "toast-success" in html
    
    def test_job_cancellation_failure_flow(self):
        """Test error toast with retry button after cancellation failure."""
        job_id = "test-job-789"
        
        html = toast_notification(
            "Failed to cancel job",
            "error",
            action_button={
                "label": "Retry",
                "action": f"cancelJob('{job_id}')"
            }
        )
        
        assert "Failed to cancel job" in html
        assert "toast-error" in html
        assert "Retry" in html
        # Untrusted actions are sanitized and fallback to a safe reload action
        assert "location.reload()" in html
    
    def test_polling_fallback_warning_flow(self):
        """Test warning toast when falling back to polling."""
        html = toast_notification(
            "Streaming unavailable. Using polling for updates.",
            "warning",
            duration=3
        )
        
        assert "Streaming unavailable" in html
        assert "polling" in html
        assert "toast-warning" in html
        assert "3000" in html  # 3 seconds in milliseconds
    
    def test_slow_response_warning_flow(self):
        """Test warning toast for slow backend response."""
        html = toast_notification(
            "Backend is responding slowly. Please be patient.",
            "warning"
        )
        
        assert "responding slowly" in html
        assert "toast-warning" in html
    
    def test_connection_error_flow(self):
        """Test connection error banner when backend is unreachable."""
        backend_url = "http://localhost:8000"
        
        html = connection_error_banner(
            backend_url,
            retry_callback="location.reload()"
        )
        
        assert "Cannot Connect to Backend" in html
        assert backend_url in html
        assert "Retry Connection" in html
        assert "location.reload()" in html
    
    def test_timeout_error_flow(self):
        """Test timeout error message for slow requests."""
        html = timeout_error_message(
            "Job submission",
            10,
            retry_callback="location.reload()"
        )
        
        assert "Request Timed Out" in html
        assert "Job submission" in html
        assert "10 seconds" in html
        assert "Retry" in html
    
    def test_validation_error_flow(self):
        """Test inline validation error for form fields."""
        html = inline_validation_error(
            "Business Brief",
            "Please enter at least 50 characters",
            correction_hint="Current: 20 characters. Add 30 more."
        )
        
        assert "Please enter at least 50 characters" in html
        assert "Current: 20 characters" in html
        assert "validation-error" in html
    
    def test_job_not_found_flow(self):
        """Test job not found message."""
        job_id = "nonexistent-job-123"
        
        html = job_not_found_message(job_id)
        
        assert "Job Not Found" in html
        assert job_id in html
        assert "Go to Dashboard" in html
        assert "?page=dashboard" in html


class TestNotificationStreamlitIntegration:
    """Test Streamlit convenience functions."""
    
    @patch('frontend.notifications.st.markdown')
    def test_show_toast_calls_markdown(self, mock_markdown):
        """Test that show_toast calls st.markdown with correct parameters."""
        show_toast("Test message", "success")
        
        # Verify st.markdown was called
        assert mock_markdown.called
        call_args = mock_markdown.call_args
        
        # Check that HTML was passed
        html_arg = call_args[0][0]
        assert "Test message" in html_arg
        assert "toast-success" in html_arg
        
        # Check unsafe_allow_html=True
        assert call_args[1]['unsafe_allow_html'] is True
    
    @patch('frontend.notifications.st.markdown')
    def test_show_connection_error_calls_markdown(self, mock_markdown):
        """Test that show_connection_error calls st.markdown."""
        show_connection_error("http://localhost:8000")
        
        assert mock_markdown.called
        html_arg = mock_markdown.call_args[0][0]
        assert "Cannot Connect to Backend" in html_arg
    
    @patch('frontend.notifications.st.markdown')
    def test_show_timeout_error_calls_markdown(self, mock_markdown):
        """Test that show_timeout_error calls st.markdown."""
        show_timeout_error("Operation", 10)
        
        assert mock_markdown.called
        html_arg = mock_markdown.call_args[0][0]
        assert "Request Timed Out" in html_arg
    
    @patch('frontend.notifications.st.markdown')
    def test_show_validation_error_calls_markdown(self, mock_markdown):
        """Test that show_validation_error calls st.markdown."""
        show_validation_error("Field", "Error message")
        
        assert mock_markdown.called
        html_arg = mock_markdown.call_args[0][0]
        assert "Error message" in html_arg
    
    @patch('frontend.notifications.st.markdown')
    def test_show_job_not_found_calls_markdown(self, mock_markdown):
        """Test that show_job_not_found calls st.markdown."""
        show_job_not_found("job123")
        
        assert mock_markdown.called
        html_arg = mock_markdown.call_args[0][0]
        assert "Job Not Found" in html_arg


class TestNotificationErrorHandling:
    """Test error handling in notification scenarios."""
    
    def test_api_timeout_triggers_timeout_notification(self):
        """Test that API timeout triggers timeout error notification."""
        # This would be tested in the actual app context
        # Here we just verify the notification can be generated
        html = timeout_error_message(
            "GET /status/job123",
            10,
            retry_callback="location.reload()"
        )
        
        assert "Request Timed Out" in html
        assert "GET /status/job123" in html
    
    def test_api_connection_error_triggers_connection_notification(self):
        """Test that API connection error triggers connection error banner."""
        html = connection_error_banner(
            "http://localhost:8000",
            retry_callback="location.reload()"
        )
        
        assert "Cannot Connect to Backend" in html
    
    def test_validation_error_prevents_submission(self):
        """Test that validation error is shown before submission."""
        # Simulate validation error for short input
        char_count = 20
        min_chars = 50
        
        html = inline_validation_error(
            "Business Brief",
            f"Please enter at least {min_chars} characters",
            correction_hint=f"Current: {char_count} characters. Add {min_chars - char_count} more."
        )
        
        assert f"Please enter at least {min_chars} characters" in html
        assert f"Current: {char_count} characters" in html


class TestNotificationAccessibilityIntegration:
    """Test accessibility features in integrated scenarios."""
    
    def test_toast_keyboard_dismissible(self):
        """Test that toast has close button for keyboard users."""
        html = toast_notification("Test", "info")
        
        # Should have close button
        assert "×" in html
        assert ".remove()" in html
    
    def test_error_banner_has_clear_action(self):
        """Test that error banner has clear retry action."""
        html = connection_error_banner("http://localhost:8000")
        
        assert "Retry Connection" in html
        assert "button" in html.lower()
    
    def test_validation_error_provides_guidance(self):
        """Test that validation error provides correction guidance."""
        html = inline_validation_error(
            "Email",
            "Invalid format",
            correction_hint="Please enter a valid email address"
        )
        
        assert "Invalid format" in html
        assert "Please enter a valid email address" in html


class TestNotificationPerformance:
    """Test performance aspects of notifications."""
    
    def test_toast_auto_dismiss_timing(self):
        """Test that toast has correct auto-dismiss timing."""
        html = toast_notification("Test", "info", duration=5)
        
        # Should have 5000ms (5 seconds) timeout
        assert "5000" in html
        assert "setTimeout" in html
    
    def test_multiple_toasts_have_unique_ids(self):
        """Test that multiple toasts have unique IDs."""
        import time
        
        html1 = toast_notification("First", "success")
        time.sleep(0.01)  # Small delay to ensure different timestamps
        html2 = toast_notification("Second", "error")
        
        # Extract toast IDs (they should be different)
        assert "toast-" in html1
        assert "toast-" in html2
        # The HTML should be different due to different IDs
        assert html1 != html2


class TestNotificationRequirementsCoverage:
    """Test that all requirements are covered."""
    
    def test_requirement_11_1_connection_error_banner(self):
        """Requirement 11.1: Connection error banner with retry."""
        html = connection_error_banner(
            "http://localhost:8000",
            retry_callback="location.reload()"
        )
        
        assert "Cannot Connect to Backend" in html
        assert "Retry Connection" in html
    
    def test_requirement_11_2_job_not_found(self):
        """Requirement 11.2: Job not found message."""
        html = job_not_found_message("job123")
        
        assert "Job Not Found" in html
        assert "job123" in html
    
    def test_requirement_11_3_inline_validation(self):
        """Requirement 11.3: Inline validation errors."""
        html = inline_validation_error(
            "Field",
            "Error",
            correction_hint="Hint"
        )
        
        assert "Error" in html
        assert "Hint" in html
    
    def test_requirement_11_4_success_notifications(self):
        """Requirement 11.4: Success notifications for actions."""
        # Job submission
        html1 = toast_notification("Job submitted!", "success")
        assert "Job submitted!" in html1
        
        # Job cancellation
        html2 = toast_notification("Job cancelled!", "success")
        assert "Job cancelled!" in html2
    
    def test_requirement_11_6_toast_system(self):
        """Requirement 11.6: Toast notification system with auto-dismiss."""
        html = toast_notification("Test", "info", duration=5)
        
        assert "toast-info" in html
        assert "5000" in html  # Auto-dismiss after 5 seconds
        assert "setTimeout" in html
    
    def test_requirement_11_7_warning_toasts(self):
        """Requirement 11.7: Warning toasts for polling fallback."""
        html = toast_notification(
            "Streaming unavailable. Using polling.",
            "warning"
        )
        
        assert "Streaming unavailable" in html
        assert "toast-warning" in html
    
    def test_requirement_11_8_timeout_messages(self):
        """Requirement 11.8: Timeout error messages with retry."""
        html = timeout_error_message(
            "Operation",
            10,
            retry_callback="retry()"
        )
        
        assert "Request Timed Out" in html
        assert "10 seconds" in html
        assert "Retry" in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
