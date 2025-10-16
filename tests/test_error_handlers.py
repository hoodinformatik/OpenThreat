"""
Tests for error handlers.
"""

import pytest
from fastapi import status

from backend.utils.error_handlers import (
    OpenThreatException,
    DatabaseError,
    NotFoundError,
    ValidationError,
    ExternalServiceError
)


@pytest.mark.unit
class TestCustomExceptions:
    """Test custom exception classes."""
    
    def test_openthreat_exception(self):
        """Test base OpenThreat exception."""
        exc = OpenThreatException(
            message="Test error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"key": "value"}
        )
        
        assert exc.message == "Test error"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.details == {"key": "value"}
    
    def test_database_error(self):
        """Test database error exception."""
        exc = DatabaseError("Database connection failed")
        
        assert exc.message == "Database connection failed"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_not_found_error(self):
        """Test not found error exception."""
        exc = NotFoundError("CVE", "CVE-2024-1234")
        
        assert "CVE" in exc.message
        assert "CVE-2024-1234" in exc.message
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.details["resource"] == "CVE"
        assert exc.details["identifier"] == "CVE-2024-1234"
    
    def test_validation_error(self):
        """Test validation error exception."""
        exc = ValidationError("Invalid input", field="cve_id")
        
        assert exc.message == "Invalid input"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.details["field"] == "cve_id"
    
    def test_external_service_error(self):
        """Test external service error exception."""
        exc = ExternalServiceError("NVD", "API timeout")
        
        assert "NVD" in exc.message
        assert "API timeout" in exc.message
        assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert exc.details["service"] == "NVD"


@pytest.mark.unit
class TestErrorResponses:
    """Test error response handling."""
    
    def test_not_found_response(self, client):
        """Test 404 error response format."""
        response = client.get("/api/v1/vulnerabilities/CVE-FAKE-9999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        # FastAPI default format uses "detail"
        assert "detail" in data or "error" in data
    
    def test_validation_error_response(self, client):
        """Test validation error response format."""
        response = client.get("/api/v1/vulnerabilities?page=-1")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "error" in data
        assert "details" in data
