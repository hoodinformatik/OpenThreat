"""
Pytest fixtures for OpenThreat tests.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database import get_db, Base
from backend.models import Vulnerability


# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database session for each test.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a test client with database session override.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_vulnerability(db_session):
    """
    Create a sample vulnerability for testing.
    """
    from datetime import datetime, timezone
    
    vuln = Vulnerability(
        cve_id="CVE-2024-TEST",
        title="Test Vulnerability",
        description="This is a test vulnerability",
        severity="HIGH",
        cvss_score=7.5,
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
        published_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        modified_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        exploited_in_the_wild=False,
        priority_score=0.75,
        sources=["nvd"],
        cwe_ids=["CWE-79"],
        references=[
            {
                "url": "https://example.com/advisory",
                "type": "advisory"
            }
        ]
    )
    
    db_session.add(vuln)
    db_session.commit()
    db_session.refresh(vuln)
    
    return vuln


@pytest.fixture
def sample_exploited_vulnerability(db_session):
    """
    Create a sample exploited vulnerability for testing.
    """
    from datetime import datetime, timezone
    
    vuln = Vulnerability(
        cve_id="CVE-2024-EXPLOITED",
        title="Exploited Vulnerability",
        description="This vulnerability is exploited in the wild",
        severity="CRITICAL",
        cvss_score=9.8,
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        published_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        modified_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        exploited_in_the_wild=True,
        priority_score=0.95,
        sources=["nvd", "cisa_kev"],
        cwe_ids=["CWE-89"],
        references=[
            {
                "url": "https://www.cisa.gov/known-exploited-vulnerabilities",
                "type": "kev"
            }
        ]
    )
    
    db_session.add(vuln)
    db_session.commit()
    db_session.refresh(vuln)
    
    return vuln


@pytest.fixture
def multiple_vulnerabilities(db_session):
    """
    Create multiple vulnerabilities for testing pagination and filtering.
    """
    from datetime import datetime, timezone
    
    vulnerabilities = []
    
    severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    
    for i in range(20):
        vuln = Vulnerability(
            cve_id=f"CVE-2024-{1000 + i}",
            title=f"Test Vulnerability {i}",
            description=f"Test description {i}",
            severity=severities[i % 4],
            cvss_score=3.0 + (i % 7),
            published_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            modified_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            exploited_in_the_wild=(i % 5 == 0),
            priority_score=0.5 + (i * 0.02),
            sources=["nvd"]
        )
        
        db_session.add(vuln)
        vulnerabilities.append(vuln)
    
    db_session.commit()
    
    return vulnerabilities
