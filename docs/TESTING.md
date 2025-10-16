# Testing Guide for OpenThreat

## 🧪 Overview

OpenThreat uses pytest for testing with comprehensive coverage of API endpoints, business logic, and error handling.

---

## 📦 Setup

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

---

## 🚀 Running Tests

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=backend --cov-report=html
```

### Run Specific Test Types

```bash
# Unit tests only
pytest -m unit

# API tests only
pytest -m api

# Integration tests only
pytest -m integration

# Slow tests
pytest -m slow
```

### Run Specific Test File

```bash
pytest tests/test_api_vulnerabilities.py
```

### Run Specific Test

```bash
pytest tests/test_api_vulnerabilities.py::TestVulnerabilityEndpoints::test_list_vulnerabilities
```

---

## 📊 Coverage Reports

After running tests with coverage, open the HTML report:

```bash
# Windows
start htmlcov/index.html

# Linux/Mac
open htmlcov/index.html
```

**Coverage Goals:**
- Overall: >70%
- Critical paths: >90%
- API endpoints: >85%

---

## 🏗️ Test Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── test_api_vulnerabilities.py    # API endpoint tests
├── test_error_handlers.py         # Error handling tests
├── test_services.py               # Service layer tests
└── test_models.py                 # Model tests
```

---

## 🔧 Writing Tests

### Test Naming Convention

```python
def test_<what>_<condition>_<expected>():
    """Test that <what> <condition> results in <expected>."""
    pass
```

### Example Test

```python
import pytest
from fastapi import status

@pytest.mark.api
def test_get_vulnerability_returns_404_when_not_found(client):
    """Test that getting a non-existent vulnerability returns 404."""
    response = client.get("/api/v1/vulnerabilities/CVE-FAKE-9999")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "error" in data
```

---

## 🎯 Test Fixtures

### Available Fixtures

#### `client`
FastAPI test client with database override.

```python
def test_endpoint(client):
    response = client.get("/api/v1/vulnerabilities")
    assert response.status_code == 200
```

#### `db_session`
Fresh database session for each test.

```python
def test_database(db_session):
    vuln = Vulnerability(cve_id="CVE-2024-TEST")
    db_session.add(vuln)
    db_session.commit()
```

#### `sample_vulnerability`
Pre-created test vulnerability.

```python
def test_with_sample(client, sample_vulnerability):
    response = client.get(f"/api/v1/vulnerabilities/{sample_vulnerability.cve_id}")
    assert response.status_code == 200
```

#### `multiple_vulnerabilities`
20 test vulnerabilities for pagination/filtering tests.

```python
def test_pagination(client, multiple_vulnerabilities):
    response = client.get("/api/v1/vulnerabilities?page=1&page_size=10")
    assert len(response.json()["items"]) == 10
```

---

## 🔍 Test Categories

### Unit Tests (`@pytest.mark.unit`)
Test individual functions and classes in isolation.

```python
@pytest.mark.unit
def test_priority_calculation():
    score = calculate_priority_score(cvss=9.8, exploited=True)
    assert score > 0.9
```

### API Tests (`@pytest.mark.api`)
Test API endpoints and responses.

```python
@pytest.mark.api
def test_list_vulnerabilities(client):
    response = client.get("/api/v1/vulnerabilities")
    assert response.status_code == 200
```

### Integration Tests (`@pytest.mark.integration`)
Test multiple components working together.

```python
@pytest.mark.integration
def test_full_vulnerability_workflow(client, db_session):
    # Create, read, update, delete
    pass
```

### Slow Tests (`@pytest.mark.slow`)
Tests that take >1 second.

```python
@pytest.mark.slow
def test_bulk_import():
    # Import 10,000 vulnerabilities
    pass
```

---

## 🐛 Debugging Tests

### Run with Verbose Output

```bash
pytest -vv
```

### Show Print Statements

```bash
pytest -s
```

### Stop on First Failure

```bash
pytest -x
```

### Run Last Failed Tests

```bash
pytest --lf
```

### Debug with PDB

```bash
pytest --pdb
```

---

## 📈 Continuous Integration

Tests run automatically on:
- Every push to main
- Every pull request
- Nightly builds

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pip install -r requirements.txt -r requirements-test.txt
          pytest --cov=backend
```

---

## ✅ Best Practices

### DO:
- ✅ Write tests for new features
- ✅ Test edge cases
- ✅ Use descriptive test names
- ✅ Keep tests independent
- ✅ Use fixtures for common setup
- ✅ Test error conditions

### DON'T:
- ❌ Test implementation details
- ❌ Write tests that depend on each other
- ❌ Use real external APIs in tests
- ❌ Commit failing tests
- ❌ Skip tests without good reason

---

## 🎓 Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Test-Driven Development](https://en.wikipedia.org/wiki/Test-driven_development)

---

## 📧 Questions?

If you have questions about testing, please:
- Check existing tests for examples
- Read the pytest documentation
- Ask in GitHub Discussions
- Email: hoodinformatik@gmail.com
