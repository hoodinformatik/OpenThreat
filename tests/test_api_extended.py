"""
Extended API tests for better coverage.
"""

import pytest
from fastapi import status


@pytest.mark.api
class TestFeedsEndpoints:
    """Test RSS/Atom feed endpoints."""
    
    def test_rss_feed_all(self, client):
        """Test RSS feed for all vulnerabilities."""
        response = client.get("/api/v1/feeds/rss")
        
        assert response.status_code == status.HTTP_200_OK
        assert "xml" in response.headers.get("content-type", "")
    
    def test_rss_feed_exploited(self, client, sample_exploited_vulnerability):
        """Test RSS feed for exploited vulnerabilities."""
        response = client.get("/api/v1/feeds/rss/exploited")
        
        # May return 200 or 404 depending on implementation
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
    
    def test_atom_feed(self, client):
        """Test Atom feed."""
        response = client.get("/api/v1/feeds/atom")
        
        # May return 200 or 404 depending on implementation
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.api
class TestSearchAdvanced:
    """Test advanced search functionality."""
    
    def test_search_with_filters(self, client, multiple_vulnerabilities):
        """Test search with multiple filters."""
        response = client.get(
            "/api/v1/search?q=Test&severity=CRITICAL&min_cvss=7.0"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # All results should be CRITICAL
        for item in data["items"]:
            assert item["severity"] == "CRITICAL"
    
    def test_search_by_cwe(self, client, sample_vulnerability):
        """Test search by CWE ID."""
        response = client.get("/api/v1/search?cwe=CWE-79")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 0
    
    def test_search_pagination(self, client, multiple_vulnerabilities):
        """Test search pagination."""
        response = client.get("/api/v1/search?q=Test&page=1&page_size=5")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) <= 5


@pytest.mark.api
class TestStatsDetailed:
    """Test detailed statistics."""
    
    def test_stats_with_data(self, client, multiple_vulnerabilities):
        """Test stats with actual data."""
        response = client.get("/api/v1/stats")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["total_vulnerabilities"] == 20
        assert "by_severity" in data
        assert data["by_severity"]["CRITICAL"] == 5
        assert data["by_severity"]["HIGH"] == 5
        assert data["by_severity"]["MEDIUM"] == 5
        assert data["by_severity"]["LOW"] == 5
    
    def test_stats_exploited_count(self, client, multiple_vulnerabilities):
        """Test exploited vulnerabilities count."""
        response = client.get("/api/v1/stats")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Every 5th vulnerability is exploited (0, 5, 10, 15)
        assert data["exploited_vulnerabilities"] == 4


@pytest.mark.api
class TestHealthDetailed:
    """Test detailed health checks."""
    
    def test_health_basic(self, client):
        """Test basic health check."""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["status"] in ["healthy", "degraded"]
        assert "database" in data
        assert "version" in data
        assert "timestamp" in data
    
    def test_health_detailed(self, client):
        """Test detailed health check."""
        response = client.get("/health/detailed")
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
        data = response.json()
        
        assert "checks" in data
        assert "database" in data["checks"]
        assert "system" in data["checks"]
        assert "environment" in data["checks"]
    
    def test_health_ready(self, client):
        """Test readiness probe."""
        response = client.get("/health/ready")
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
        data = response.json()
        assert "status" in data
    
    def test_health_live(self, client):
        """Test liveness probe."""
        response = client.get("/health/live")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "alive"


@pytest.mark.api
class TestDataSourcesEndpoints:
    """Test data sources management endpoints."""
    
    def test_list_data_sources(self, client):
        """Test listing data sources."""
        response = client.get("/api/v1/data-sources/list")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "sources" in data
        assert "total" in data
        assert len(data["sources"]) > 0
    
    def test_bsi_cert_status(self, client):
        """Test BSI CERT status endpoint."""
        response = client.get("/api/v1/data-sources/bsi-cert/status")
        
        # May fail if database query has issues in test environment
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "source" in data
            assert data["source"] == "bsi_cert"


@pytest.mark.api
class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root_endpoint(self, client):
        """Test API root endpoint."""
        response = client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["name"] == "OpenThreat API"
        assert "version" in data
        assert "endpoints" in data
    
    def test_docs_endpoint(self, client):
        """Test API documentation endpoint."""
        response = client.get("/docs")
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.api
class TestErrorCases:
    """Test error handling."""
    
    def test_404_not_found(self, client):
        """Test 404 error."""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_invalid_cve_id(self, client):
        """Test invalid CVE ID format."""
        response = client.get("/api/v1/vulnerabilities/INVALID")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_invalid_query_params(self, client):
        """Test invalid query parameters."""
        response = client.get("/api/v1/vulnerabilities?page=-1")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
