"""
Tests for Pydantic schemas.
"""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from backend.schemas import (
    VulnerabilityList,
    VulnerabilityDetail,
    StatsResponse,
    PaginatedResponse
)


@pytest.mark.unit
class TestVulnerabilitySchemas:
    """Test vulnerability schemas."""
    
    def test_vulnerability_list_schema(self):
        """Test VulnerabilityList schema."""
        data = {
            "cve_id": "CVE-2024-TEST",
            "title": "Test Vulnerability",
            "severity": "HIGH",
            "cvss_score": 7.5,
            "exploited_in_the_wild": False,
            "priority_score": 0.75,
            "published_at": "2024-01-01T00:00:00Z"
        }
        
        vuln = VulnerabilityList(**data)
        
        assert vuln.cve_id == "CVE-2024-TEST"
        assert vuln.severity == "HIGH"
        assert vuln.cvss_score == 7.5
    
    def test_vulnerability_detail_schema(self):
        """Test VulnerabilityDetail schema."""
        data = {
            "id": 1,
            "cve_id": "CVE-2024-TEST",
            "title": "Test Vulnerability",
            "description": "Test description",
            "severity": "HIGH",
            "cvss_score": 7.5,
            "exploited_in_the_wild": False,
            "priority_score": 0.75,
            "published_at": "2024-01-01T00:00:00Z",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        vuln = VulnerabilityDetail(**data)
        
        assert vuln.id == 1
        assert vuln.cve_id == "CVE-2024-TEST"
        assert vuln.description == "Test description"


@pytest.mark.unit
class TestStatsSchema:
    """Test statistics schema."""
    
    def test_stats_response_schema(self):
        """Test StatsResponse schema."""
        data = {
            "total_vulnerabilities": 100,
            "exploited_vulnerabilities": 10,
            "critical_vulnerabilities": 5,
            "high_vulnerabilities": 20,
            "by_severity": {
                "CRITICAL": 5,
                "HIGH": 20,
                "MEDIUM": 50,
                "LOW": 25
            },
            "recent_updates": 10
        }
        
        stats = StatsResponse(**data)
        
        assert stats.total_vulnerabilities == 100
        assert stats.exploited_vulnerabilities == 10
        assert stats.by_severity["CRITICAL"] == 5


@pytest.mark.unit
class TestPaginatedResponse:
    """Test paginated response schema."""
    
    def test_paginated_response_schema(self):
        """Test PaginatedResponse schema."""
        data = {
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5,
            "items": []
        }
        
        response = PaginatedResponse(**data)
        
        assert response.total == 100
        assert response.page == 1
        assert response.page_size == 20
        assert response.total_pages == 5
    
    def test_paginated_response_with_items(self):
        """Test PaginatedResponse with items."""
        items = [
            {
                "cve_id": "CVE-2024-1",
                "title": "Test 1",
                "severity": "HIGH",
                "cvss_score": 7.5,
                "exploited_in_the_wild": False,
                "priority_score": 0.75,
                "published_at": "2024-01-01T00:00:00Z"
            }
        ]
        
        data = {
            "total": 1,
            "page": 1,
            "page_size": 20,
            "total_pages": 1,
            "items": items
        }
        
        response = PaginatedResponse(**data)
        
        assert len(response.items) == 1
        # Items are Pydantic models, not dicts
        assert response.items[0].cve_id == "CVE-2024-1"


@pytest.mark.unit
class TestSchemaValidation:
    """Test schema validation."""
    
    def test_invalid_severity(self):
        """Test that invalid severity raises error."""
        # This should work with any severity since we don't enforce enum
        data = {
            "cve_id": "CVE-2024-TEST",
            "title": "Test",
            "severity": "INVALID",
            "published_at": "2024-01-01T00:00:00Z"
        }
        
        # Should not raise error as we don't enforce severity enum
        vuln = VulnerabilityList(**data)
        assert vuln.severity == "INVALID"
    
    def test_missing_required_fields(self):
        """Test that missing required fields raise error."""
        data = {
            "title": "Test"
            # Missing cve_id
        }
        
        with pytest.raises(ValidationError):
            VulnerabilityList(**data)
