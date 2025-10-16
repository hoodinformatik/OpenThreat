"""
Tests for database models.
"""

import pytest
from datetime import datetime, timezone

from backend.models import Vulnerability, IngestionRun


@pytest.mark.unit
class TestVulnerabilityModel:
    """Test Vulnerability model."""
    
    def test_create_vulnerability(self, db_session):
        """Test creating a vulnerability."""
        vuln = Vulnerability(
            cve_id="CVE-2024-MODEL-TEST",
            title="Model Test",
            description="Testing the model",
            severity="HIGH",
            cvss_score=7.5,
            published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            modified_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            priority_score=0.75
        )
        
        db_session.add(vuln)
        db_session.commit()
        
        assert vuln.id is not None
        assert vuln.cve_id == "CVE-2024-MODEL-TEST"
        assert vuln.severity == "HIGH"
    
    def test_vulnerability_with_sources(self, db_session):
        """Test vulnerability with multiple sources."""
        vuln = Vulnerability(
            cve_id="CVE-2024-SOURCES",
            title="Multi-source",
            description="Test",
            sources=["nvd", "cisa_kev", "bsi_cert"],
            published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            modified_at=datetime(2024, 1, 1, tzinfo=timezone.utc)
        )
        
        db_session.add(vuln)
        db_session.commit()
        
        assert len(vuln.sources) == 3
        assert "nvd" in vuln.sources
        assert "cisa_kev" in vuln.sources
    
    def test_vulnerability_with_cwe(self, db_session):
        """Test vulnerability with CWE IDs."""
        vuln = Vulnerability(
            cve_id="CVE-2024-CWE",
            title="CWE Test",
            description="Test",
            cwe_ids=["CWE-79", "CWE-89"],
            published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            modified_at=datetime(2024, 1, 1, tzinfo=timezone.utc)
        )
        
        db_session.add(vuln)
        db_session.commit()
        
        assert len(vuln.cwe_ids) == 2
        assert "CWE-79" in vuln.cwe_ids
    
    def test_vulnerability_with_references(self, db_session):
        """Test vulnerability with references."""
        vuln = Vulnerability(
            cve_id="CVE-2024-REFS",
            title="References Test",
            description="Test",
            references=[
                {"url": "https://example.com/1", "type": "advisory"},
                {"url": "https://example.com/2", "type": "patch"}
            ],
            published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            modified_at=datetime(2024, 1, 1, tzinfo=timezone.utc)
        )
        
        db_session.add(vuln)
        db_session.commit()
        
        assert len(vuln.references) == 2
        assert vuln.references[0]["type"] == "advisory"


@pytest.mark.unit
class TestIngestionRunModel:
    """Test IngestionRun model."""
    
    def test_create_ingestion_run(self, db_session):
        """Test creating an ingestion run."""
        run = IngestionRun(
            source="nvd",
            status="success",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc)
        )
        
        db_session.add(run)
        db_session.commit()
        
        assert run.id is not None
        assert run.source == "nvd"
        assert run.status == "success"
    
    def test_ingestion_run_with_error(self, db_session):
        """Test ingestion run with error."""
        run = IngestionRun(
            source="test",
            status="failed",
            error_message="Test error",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc)
        )
        
        db_session.add(run)
        db_session.commit()
        
        assert run.status == "failed"
        assert run.error_message == "Test error"
