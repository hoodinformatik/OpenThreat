"""
Tests for middleware components.
"""

import pytest
from fastapi import status
from unittest.mock import Mock, patch


@pytest.mark.unit
class TestRateLimiting:
    """Test rate limiting middleware."""
    
    def test_rate_limit_allows_normal_requests(self, client):
        """Test that normal requests are allowed."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
    
    def test_rate_limit_exempts_health_checks(self, client):
        """Test that health checks are exempt from rate limiting."""
        # Make many requests to health endpoint
        for _ in range(100):
            response = client.get("/health")
            assert response.status_code == status.HTTP_200_OK
    
    def test_rate_limit_headers_present(self, client):
        """Test that rate limit headers are present."""
        response = client.get("/api/v1/vulnerabilities")
        
        # Check for rate limit headers
        assert "X-RateLimit-Limit-Minute" in response.headers
        assert "X-RateLimit-Limit-Hour" in response.headers


@pytest.mark.unit
class TestLogging:
    """Test logging configuration."""
    
    def test_sensitive_data_filtering(self):
        """Test that sensitive data is filtered from logs."""
        from backend.config.logging_config import LogConfig
        
        # Test password filtering with proper format
        message = "User password='secret123' logged in"
        filtered = LogConfig.filter_sensitive_data(message)
        assert "secret123" not in filtered
        assert "***REDACTED***" in filtered
        
        # Test API key filtering with proper format
        message = "api_key='sk-1234567890'"
        filtered = LogConfig.filter_sensitive_data(message)
        assert "sk-1234567890" not in filtered
        assert "***REDACTED***" in filtered
    
    def test_logger_creation(self):
        """Test logger creation."""
        from backend.config.logging_config import get_logger
        
        logger = get_logger("test")
        assert logger is not None
        assert logger.name == "test"


@pytest.mark.api
class TestMetrics:
    """Test Prometheus metrics."""
    
    def test_metrics_endpoint_exists(self, client):
        """Test that metrics endpoint exists."""
        response = client.get("/metrics")
        assert response.status_code == status.HTTP_200_OK
    
    def test_metrics_format(self, client):
        """Test that metrics are in Prometheus format."""
        response = client.get("/metrics")
        
        # Check content type
        assert "text/plain" in response.headers.get("content-type", "")
        
        # Check for some expected metrics
        content = response.text
        assert "http_requests_total" in content or "vulnerabilities_total" in content
