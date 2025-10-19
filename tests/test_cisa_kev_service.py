"""
Tests for CISA KEV service.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.services.cisa_kev_service import CISAKEVService, get_cisa_kev_service
from backend.models import Vulnerability


class TestCISAKEVService:
    """Test CISA KEV service functionality."""
    
    @pytest.fixture
    def kev_service(self):
        """Create KEV service instance."""
        return CISAKEVService()
    
    @pytest.fixture
    def mock_nvd_response(self):
        """Mock NVD API response with KEV data."""
        return {
            "resultsPerPage": 2,
            "startIndex": 0,
            "totalResults": 2,
            "vulnerabilities": [
                {
                    "cve": {
                        "id": "CVE-2024-1234",
                        "descriptions": [
                            {
                                "lang": "en",
                                "value": "Test vulnerability"
                            }
                        ]
                    }
                },
                {
                    "cve": {
                        "id": "CVE-2024-5678",
                        "descriptions": [
                            {
                                "lang": "en",
                                "value": "Another test vulnerability"
                            }
                        ]
                    }
                }
            ]
        }
    
    def test_service_initialization(self, kev_service):
        """Test that service initializes correctly."""
        assert kev_service is not None
        assert kev_service.NVD_API_BASE == "https://services.nvd.nist.gov/rest/json/cves/2.0"
        assert kev_service.nvd_service is not None
    
    def test_get_cisa_kev_service(self):
        """Test service factory function."""
        service = get_cisa_kev_service()
        assert isinstance(service, CISAKEVService)
    
    @patch('backend.services.cisa_kev_service.requests.get')
    def test_fetch_kev_cves_success(self, mock_get, kev_service, mock_nvd_response):
        """Test successful KEV CVE fetching from NVD API."""
        mock_response = Mock()
        mock_response.json.return_value = mock_nvd_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = kev_service.fetch_kev_cves()
        
        assert len(result) == 2
        assert result[0]["cve"]["id"] == "CVE-2024-1234"
        assert result[1]["cve"]["id"] == "CVE-2024-5678"
        
        # Verify API was called with correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "hasKev" in call_args[0][0]
        assert "resultsPerPage=2000" in call_args[0][0]
    
    @patch('backend.services.cisa_kev_service.requests.get')
    def test_fetch_kev_cves_api_error(self, mock_get, kev_service):
        """Test handling of API errors."""
        mock_get.side_effect = Exception("API Error")
        
        result = kev_service.fetch_kev_cves()
        
        assert result == []
    
    @patch('backend.services.cisa_kev_service.requests.get')
    def test_fetch_kev_cves_pagination(self, mock_get, kev_service):
        """Test pagination handling."""
        # First page
        first_response = Mock()
        first_response.json.return_value = {
            "resultsPerPage": 1,
            "startIndex": 0,
            "totalResults": 2,
            "vulnerabilities": [{"cve": {"id": "CVE-2024-1111"}}]
        }
        first_response.raise_for_status = Mock()
        
        # Second page
        second_response = Mock()
        second_response.json.return_value = {
            "resultsPerPage": 1,
            "startIndex": 1,
            "totalResults": 2,
            "vulnerabilities": [{"cve": {"id": "CVE-2024-2222"}}]
        }
        second_response.raise_for_status = Mock()
        
        mock_get.side_effect = [first_response, second_response]
        
        result = kev_service.fetch_kev_cves()
        
        assert len(result) == 2
        assert result[0]["cve"]["id"] == "CVE-2024-1111"
        assert result[1]["cve"]["id"] == "CVE-2024-2222"
    
    def test_update_exploited_vulnerabilities_no_data(self, kev_service):
        """Test update when no KEV data is available."""
        mock_db = Mock()
        
        with patch.object(kev_service, 'fetch_kev_cves', return_value=[]):
            result = kev_service.update_exploited_vulnerabilities(mock_db)
        
        assert result["status"] == "error"
        assert result["updated"] == 0
        assert "Failed to fetch" in result["message"]
    
    def test_update_exploited_vulnerabilities_success(self, kev_service, mock_nvd_response):
        """Test successful vulnerability update."""
        mock_db = Mock()
        
        # Create mock vulnerabilities
        mock_vuln1 = Mock(spec=Vulnerability)
        mock_vuln1.cve_id = "CVE-2024-1234"
        mock_vuln1.exploited_in_the_wild = False
        mock_vuln1.sources = []
        mock_vuln1.cvss_score = 7.5
        mock_vuln1.severity = "HIGH"
        mock_vuln1.published_at = Mock()
        mock_vuln1.published_at.isoformat.return_value = "2024-01-01T00:00:00"
        
        mock_vuln2 = Mock(spec=Vulnerability)
        mock_vuln2.cve_id = "CVE-2024-5678"
        mock_vuln2.exploited_in_the_wild = False
        mock_vuln2.sources = []
        mock_vuln2.cvss_score = 9.8
        mock_vuln2.severity = "CRITICAL"
        mock_vuln2.published_at = Mock()
        mock_vuln2.published_at.isoformat.return_value = "2024-01-01T00:00:00"
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [mock_vuln1, mock_vuln2]
        mock_db.query.return_value = mock_query
        
        with patch.object(kev_service, 'fetch_kev_cves', return_value=mock_nvd_response["vulnerabilities"]):
            result = kev_service.update_exploited_vulnerabilities(mock_db)
        
        assert result["status"] == "success"
        assert result["updated"] == 2
        assert result["not_found"] == 0
        assert result["total_kev_entries"] == 2
        
        # Verify vulnerabilities were marked as exploited
        assert mock_vuln1.exploited_in_the_wild == True
        assert mock_vuln2.exploited_in_the_wild == True
        
        # Verify CISA source was added
        assert "cisa_kev" in mock_vuln1.sources
        assert "cisa_kev" in mock_vuln2.sources
        
        # Verify commit was called
        mock_db.commit.assert_called()
    
    def test_update_exploited_vulnerabilities_not_found(self, kev_service, mock_nvd_response):
        """Test update when CVEs are not found in database."""
        mock_db = Mock()
        
        # Mock database query to return None (CVE not found)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        with patch.object(kev_service, 'fetch_kev_cves', return_value=mock_nvd_response["vulnerabilities"]):
            result = kev_service.update_exploited_vulnerabilities(mock_db)
        
        assert result["status"] == "success"
        assert result["updated"] == 0
        assert result["not_found"] == 2
    
    def test_update_exploited_vulnerabilities_partial_success(self, kev_service, mock_nvd_response):
        """Test update with some CVEs found and some not found."""
        mock_db = Mock()
        
        # Create one mock vulnerability
        mock_vuln = Mock(spec=Vulnerability)
        mock_vuln.cve_id = "CVE-2024-1234"
        mock_vuln.exploited_in_the_wild = False
        mock_vuln.sources = []
        mock_vuln.cvss_score = 7.5
        mock_vuln.severity = "HIGH"
        mock_vuln.published_at = Mock()
        mock_vuln.published_at.isoformat.return_value = "2024-01-01T00:00:00"
        
        # Mock database query - first found, second not found
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [mock_vuln, None]
        mock_db.query.return_value = mock_query
        
        with patch.object(kev_service, 'fetch_kev_cves', return_value=mock_nvd_response["vulnerabilities"]):
            result = kev_service.update_exploited_vulnerabilities(mock_db)
        
        assert result["status"] == "success"
        assert result["updated"] == 1
        assert result["not_found"] == 1
