"""
Tests for vulnerability API endpoints.
"""

import pytest
from fastapi import status


@pytest.mark.api
class TestVulnerabilityEndpoints:
    """Test vulnerability API endpoints."""
    
    def test_list_vulnerabilities_empty(self, client):
        """Test listing vulnerabilities when database is empty."""
        response = client.get("/api/v1/vulnerabilities")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
    
    def test_list_vulnerabilities(self, client, sample_vulnerability):
        """Test listing vulnerabilities."""
        response = client.get("/api/v1/vulnerabilities")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["cve_id"] == "CVE-2024-TEST"
    
    def test_list_vulnerabilities_pagination(self, client, multiple_vulnerabilities):
        """Test vulnerability pagination."""
        # First page
        response = client.get("/api/v1/vulnerabilities?page=1&page_size=10")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 20
        assert len(data["items"]) == 10
        assert data["page"] == 1
        assert data["total_pages"] == 2
        
        # Second page
        response = client.get("/api/v1/vulnerabilities?page=2&page_size=10")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 10
        assert data["page"] == 2
    
    def test_filter_by_severity(self, client, multiple_vulnerabilities):
        """Test filtering by severity."""
        response = client.get("/api/v1/vulnerabilities?severity=CRITICAL")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 5  # 20 vulns, every 4th is CRITICAL
        
        for item in data["items"]:
            assert item["severity"] == "CRITICAL"
    
    def test_filter_by_exploited(self, client, multiple_vulnerabilities):
        """Test filtering by exploitation status."""
        response = client.get("/api/v1/vulnerabilities?exploited=true")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 4  # Every 5th vulnerability is exploited
        
        for item in data["items"]:
            assert item["exploited_in_the_wild"] is True
    
    def test_get_vulnerability_by_id(self, client, sample_vulnerability):
        """Test getting a specific vulnerability."""
        response = client.get("/api/v1/vulnerabilities/CVE-2024-TEST")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["cve_id"] == "CVE-2024-TEST"
        assert data["title"] == "Test Vulnerability"
        assert data["severity"] == "HIGH"
        assert data["cvss_score"] == 7.5
    
    def test_get_nonexistent_vulnerability(self, client):
        """Test getting a vulnerability that doesn't exist."""
        response = client.get("/api/v1/vulnerabilities/CVE-9999-FAKE")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_list_exploited_vulnerabilities(self, client, sample_exploited_vulnerability):
        """Test listing exploited vulnerabilities."""
        response = client.get("/api/v1/vulnerabilities/exploited")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["exploited_in_the_wild"] is True
        assert data["items"][0]["cve_id"] == "CVE-2024-EXPLOITED"
    
    def test_sorting(self, client, multiple_vulnerabilities):
        """Test sorting vulnerabilities."""
        # Sort by CVSS score descending
        response = client.get("/api/v1/vulnerabilities?sort_by=cvss_score&sort_order=desc")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check that scores are in descending order
        scores = [item["cvss_score"] for item in data["items"]]
        assert scores == sorted(scores, reverse=True)
    
    def test_invalid_page_number(self, client):
        """Test invalid page number."""
        response = client.get("/api/v1/vulnerabilities?page=0")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_invalid_page_size(self, client):
        """Test invalid page size."""
        response = client.get("/api/v1/vulnerabilities?page_size=1000")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.api
class TestStatsEndpoints:
    """Test statistics API endpoints."""
    
    def test_get_stats_empty(self, client):
        """Test getting stats when database is empty."""
        response = client.get("/api/v1/stats")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_vulnerabilities"] == 0
        assert data["exploited_vulnerabilities"] == 0
    
    def test_get_stats(self, client, multiple_vulnerabilities):
        """Test getting statistics."""
        response = client.get("/api/v1/stats")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_vulnerabilities"] == 20
        assert data["exploited_vulnerabilities"] == 4
        assert "by_severity" in data
        assert data["by_severity"]["CRITICAL"] == 5
        assert data["by_severity"]["HIGH"] == 5


@pytest.mark.api
class TestSearchEndpoints:
    """Test search API endpoints."""
    
    def test_search_by_cve_id(self, client, sample_vulnerability):
        """Test searching by CVE ID."""
        response = client.get("/api/v1/search?q=CVE-2024-TEST")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1
        assert any(item["cve_id"] == "CVE-2024-TEST" for item in data["items"])
    
    def test_search_by_title(self, client, sample_vulnerability):
        """Test searching by title."""
        response = client.get("/api/v1/search?q=Test+Vulnerability")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1
    
    def test_search_no_results(self, client):
        """Test search with no results."""
        response = client.get("/api/v1/search?q=NONEXISTENT")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []


@pytest.mark.api
class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "version" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "OpenThreat API"
        assert "version" in data
        assert "endpoints" in data
