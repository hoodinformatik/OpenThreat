"""
Tests for CISA KEV Celery task.
"""
import pytest
from unittest.mock import Mock, patch
from backend.tasks.data_tasks import fetch_cisa_kev_task


class TestCISAKEVTask:
    """Test CISA KEV Celery task."""
    
    @patch('backend.tasks.data_tasks.get_cisa_kev_service')
    @patch('backend.tasks.data_tasks.get_db')
    def test_fetch_cisa_kev_task_success(self, mock_get_db, mock_get_service):
        """Test successful KEV fetch task."""
        # Mock database
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        # Mock service
        mock_service = Mock()
        mock_service.update_exploited_vulnerabilities.return_value = {
            "status": "success",
            "total_kev_entries": 100,
            "updated": 95,
            "not_found": 5,
            "timestamp": "2024-01-01T00:00:00"
        }
        mock_get_service.return_value = mock_service
        
        # Execute task
        result = fetch_cisa_kev_task()
        
        # Verify result
        assert result["status"] == "success"
        assert result["updated"] == 95
        assert result["not_found"] == 5
        assert result["total_kev_entries"] == 100
        
        # Verify service was called
        mock_service.update_exploited_vulnerabilities.assert_called_once_with(mock_db)
        
        # Verify database was closed
        mock_db.close.assert_called_once()
    
    @patch('backend.tasks.data_tasks.get_cisa_kev_service')
    @patch('backend.tasks.data_tasks.get_db')
    def test_fetch_cisa_kev_task_failure(self, mock_get_db, mock_get_service):
        """Test KEV fetch task failure handling."""
        # Mock database
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        # Mock service to raise exception
        mock_service = Mock()
        mock_service.update_exploited_vulnerabilities.side_effect = Exception("API Error")
        mock_get_service.return_value = mock_service
        
        # Execute task and expect exception
        with pytest.raises(Exception):
            fetch_cisa_kev_task()
        
        # Verify database rollback was called
        mock_db.rollback.assert_called_once()
        
        # Verify database was closed
        mock_db.close.assert_called_once()
    
    @patch('backend.tasks.data_tasks.get_cisa_kev_service')
    @patch('backend.tasks.data_tasks.get_db')
    def test_fetch_cisa_kev_task_warning(self, mock_get_db, mock_get_service):
        """Test KEV fetch task with warnings."""
        # Mock database
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        # Mock service with warning status
        mock_service = Mock()
        mock_service.update_exploited_vulnerabilities.return_value = {
            "status": "error",
            "message": "Failed to fetch CISA KEV data",
            "updated": 0,
            "not_found": 0
        }
        mock_get_service.return_value = mock_service
        
        # Execute task
        result = fetch_cisa_kev_task()
        
        # Verify result contains warning
        assert result["status"] == "error"
        assert result["updated"] == 0
        assert "Failed to fetch" in result["message"]
