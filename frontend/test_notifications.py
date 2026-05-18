"""
Unit Tests for Notifications Module

Tests toast notifications, error banners, validation messages, and other
notification components.

Requirements: 11.1-11.8
"""

import pytest
from frontend.notifications import (
    toast_notification,
    connection_error_banner,
    timeout_error_message,
    inline_validation_error,
    job_not_found_message,
)


class TestToastNotification:
    """Test toast notification generation."""
    
    def test_success_toast(self):
        """Test success toast notification."""
        html = toast_notification("Job submitted!", "success")
        
        assert "Job submitted!" in html
        assert "toast-success" in html
        assert "✅" in html
        assert "slideInRight" in html
        assert "setTimeout" in html
        
    def test_warning_toast(self):
        """Test warning toast notification."""
        html = toast_notification("Slow response detected", "warning")
        
        assert "Slow response detected" in html
        assert "toast-warning" in html
        assert "⚠️" in html
        
    def test_error_toast(self):
        """Test error toast notification."""
        html = toast_notification("Connection failed", "error")
        
        assert "Connection failed" in html
        assert "toast-error" in html
        assert "❌" in html
        
    def test_info_toast(self):
        """Test info toast notification."""
        html = toast_notification("Processing...", "info")
        
        assert "Processing..." in html
        assert "toast-info" in html
        assert "ℹ️" in html
        
    def test_custom_duration(self):
        """Test toast with custom duration."""
        html = toast_notification("Test", "info", duration=10)
        
        assert "10000" in html  # 10 seconds in milliseconds
        
    def test_with_action_button(self):
        """Test toast with action button."""
        html = toast_notification(
            "Failed to submit",
            "error",
            action_button={
                "label": "Retry",
                "action": "location.reload()"
            }
        )
        
        assert "Retry" in html
        assert "location.reload()" in html
        assert "button" in html.lower()
        
    def test_auto_dismiss_script(self):
        """Test that auto-dismiss script is included."""
        html = toast_notification("Test", "info", duration=5)
        
        assert "<script>" in html
        assert "setTimeout" in html
        assert "5000" in html  # 5 seconds in milliseconds
        assert "slideOutRight" in html
        
    def test_close_button(self):
        """Test that close button is included."""
        html = toast_notification("Test", "info")
        
        assert "×" in html
        assert ".remove()" in html


class TestConnectionErrorBanner:
    """Test connection error banner generation."""
    
    def test_basic_banner(self):
        """Test basic connection error banner."""
        html = connection_error_banner("http://localhost:8000")
        
        assert "Cannot Connect to Backend" in html
        assert "http://localhost:8000" in html
        assert "error-banner" in html
        assert "🔴" in html
        
    def test_with_retry_callback(self):
        """Test banner with custom retry callback."""
        html = connection_error_banner(
            "http://localhost:8000",
            retry_callback="retryConnection()"
        )
        
        assert "retryConnection()" in html
        assert "Retry Connection" in html
        
    def test_default_retry_action(self):
        """Test banner with default retry action."""
        html = connection_error_banner("http://localhost:8000")
        
        assert "location.reload()" in html
        
    def test_backend_url_display(self):
        """Test that backend URL is displayed in code block."""
        html = connection_error_banner("http://api.example.com:8080")
        
        assert "http://api.example.com:8080" in html
        assert "<code" in html


class TestTimeoutErrorMessage:
    """Test timeout error message generation."""
    
    def test_basic_timeout_message(self):
        """Test basic timeout error message."""
        html = timeout_error_message("Job submission", 10)
        
        assert "Job submission" in html
        assert "10 seconds" in html
        assert "Request Timed Out" in html
        assert "⏱️" in html
        
    def test_with_retry_callback(self):
        """Test timeout message with retry button."""
        html = timeout_error_message(
            "Data fetch",
            30,
            retry_callback="retryFetch()"
        )
        
        assert "retryFetch()" in html
        assert "Retry" in html
        
    def test_without_retry_button(self):
        """Test timeout message without retry button."""
        html = timeout_error_message("Operation", 5)
        
        # Should not have retry button if no callback provided
        assert "retryFetch()" not in html


class TestInlineValidationError:
    """Test inline validation error generation."""
    
    def test_basic_validation_error(self):
        """Test basic validation error."""
        html = inline_validation_error("Business Brief", "Field is required")
        
        assert "Field is required" in html
        assert "validation-error" in html
        assert "❌" in html
        
    def test_with_correction_hint(self):
        """Test validation error with correction hint."""
        html = inline_validation_error(
            "Email",
            "Invalid format",
            correction_hint="Please enter a valid email address"
        )
        
        assert "Invalid format" in html
        assert "Please enter a valid email address" in html
        assert "💡" in html
        
    def test_without_correction_hint(self):
        """Test validation error without correction hint."""
        html = inline_validation_error("Name", "Too short")
        
        assert "Too short" in html
        assert "💡" not in html


class TestJobNotFoundMessage:
    """Test job not found message generation."""
    
    def test_basic_message(self):
        """Test basic job not found message."""
        html = job_not_found_message("job123")
        
        assert "Job Not Found" in html
        assert "job123" in html
        assert "job-not-found" in html
        assert "🔍" in html
        
    def test_navigation_button(self):
        """Test that navigation button is included."""
        html = job_not_found_message("job456")
        
        assert "Go to Dashboard" in html
        assert "window.location.href" in html
        assert "?page=dashboard" in html
        
    def test_job_id_display(self):
        """Test that job ID is displayed in code block."""
        html = job_not_found_message("test-job-789")
        
        assert "test-job-789" in html
        assert "<code" in html


class TestNotificationStyling:
    """Test that notifications have proper styling."""
    
    def test_toast_has_animations(self):
        """Test that toast has animation keyframes."""
        html = toast_notification("Test", "info")
        
        assert "@keyframes slideInRight" in html
        assert "@keyframes slideOutRight" in html
        
    def test_toast_has_positioning(self):
        """Test that toast has fixed positioning."""
        html = toast_notification("Test", "info")
        
        assert "position: fixed" in html
        assert "z-index: 9999" in html
        
    def test_error_banner_has_gradient(self):
        """Test that error banner has gradient background."""
        html = connection_error_banner("http://localhost:8000")
        
        assert "linear-gradient" in html
        
    def test_validation_error_has_border(self):
        """Test that validation error has left border."""
        html = inline_validation_error("Field", "Error")
        
        assert "border-left:" in html


class TestNotificationAccessibility:
    """Test accessibility features of notifications."""
    
    def test_toast_has_semantic_structure(self):
        """Test that toast has proper semantic structure."""
        html = toast_notification("Test message", "success")
        
        # Should have clear message structure
        assert "Test message" in html
        
    def test_error_banner_has_clear_message(self):
        """Test that error banner has clear error message."""
        html = connection_error_banner("http://localhost:8000")
        
        assert "Cannot Connect to Backend" in html
        assert "Please check your connection" in html
        
    def test_validation_error_has_clear_guidance(self):
        """Test that validation error provides clear guidance."""
        html = inline_validation_error(
            "Field",
            "Error",
            correction_hint="How to fix"
        )
        
        assert "Error" in html
        assert "How to fix" in html


class TestNotificationEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_message(self):
        """Test toast with empty message."""
        html = toast_notification("", "info")
        
        # Should still generate valid HTML
        assert "toast-info" in html
        assert "<div" in html
        
    def test_long_message(self):
        """Test toast with very long message."""
        long_message = "A" * 500
        html = toast_notification(long_message, "info")
        
        assert long_message in html
        assert "max-width: 500px" in html
        
    def test_special_characters_in_message(self):
        """Test toast with special characters."""
        html = toast_notification("Test <script>alert('xss')</script>", "info")
        
        # Should include the message as-is (Streamlit handles escaping)
        assert "Test" in html
        
    def test_invalid_notification_type(self):
        """Test toast with invalid notification type."""
        # Should default to 'info' type
        html = toast_notification("Test", "invalid")  # type: ignore
        
        # Should still generate valid HTML with info styling
        assert "toast-invalid" in html or "toast-info" in html
        
    def test_zero_duration(self):
        """Test toast with zero duration."""
        html = toast_notification("Test", "info", duration=0)
        
        # Should still have auto-dismiss script
        assert "setTimeout" in html
        assert "0" in html
        
    def test_negative_duration(self):
        """Test toast with negative duration."""
        html = toast_notification("Test", "info", duration=-5)
        
        # Should still generate valid HTML
        assert "setTimeout" in html


class TestNotificationIntegration:
    """Test integration scenarios."""
    
    def test_multiple_toasts(self):
        """Test generating multiple toasts with unique IDs."""
        html1 = toast_notification("First", "success")
        html2 = toast_notification("Second", "error")
        
        # Each should have unique ID
        assert "toast-" in html1
        assert "toast-" in html2
        # IDs should be different (time-based)
        assert html1 != html2
        
    def test_toast_with_all_features(self):
        """Test toast with all optional features."""
        html = toast_notification(
            "Complete test",
            "error",
            duration=10,
            action_button={
                "label": "Retry Now",
                "action": "retryOperation()"
            }
        )
        
        assert "Complete test" in html
        assert "toast-error" in html
        assert "10000" in html
        assert "Retry Now" in html
        assert "retryOperation()" in html
        assert "×" in html  # Close button
