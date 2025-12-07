"""
Tech Stack API endpoints for CVE vulnerability scanning.

Allows users to upload dependency files (package.json, requirements.txt, etc.)
and get a list of known CVEs affecting their tech stack.
"""

import base64
import json
import logging
import secrets
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import TechStack, TechStackMatch
from ..services.techstack_service import get_techstack_service

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Pydantic Schemas
# =============================================================================


class PackageInfo(BaseModel):
    """Single package information."""

    name: str
    version: Optional[str] = None
    ecosystem: str = "npm"
    dev: bool = False


class TechStackCreate(BaseModel):
    """Request to create a tech stack from manual input."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    packages: List[PackageInfo]
    session_id: Optional[str] = None


class TechStackCreateEncoded(BaseModel):
    """Request with base64-encoded payload to bypass WAF restrictions."""

    encoded: str = Field(..., description="Base64-encoded JSON payload")


class VulnerabilityInfo(BaseModel):
    """Vulnerability information in scan results."""

    cve_id: str
    severity: Optional[str]
    cvss_score: Optional[float]
    title: Optional[str]
    description: Optional[str]
    match_type: str
    match_confidence: float
    exploited: bool


class PackageWithVulns(BaseModel):
    """Package with its vulnerabilities."""

    name: str
    version: Optional[str]
    ecosystem: str
    dev: bool = False
    status: str = "safe"  # "safe", "vulnerable"
    vulnerabilities: List[VulnerabilityInfo]


class TechStackResponse(BaseModel):
    """Tech stack scan response."""

    id: int
    name: str
    description: Optional[str]
    source_type: Optional[str]
    package_count: int
    vulnerable_count: int
    safe_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    last_scanned_at: Optional[str]
    created_at: str
    packages: List[PackageWithVulns]  # All packages with their status
    session_id: Optional[str] = None


class TechStackSummary(BaseModel):
    """Summary of a tech stack."""

    id: int
    name: str
    source_type: Optional[str]
    package_count: int
    vulnerable_count: int
    critical_count: int
    high_count: int
    created_at: str


class SupportedFormatsResponse(BaseModel):
    """List of supported file formats."""

    formats: List[dict]


# =============================================================================
# API Endpoints
# =============================================================================


@router.get("/techstack/formats", response_model=SupportedFormatsResponse)
async def get_supported_formats():
    """
    Get list of supported dependency file formats.

    Returns information about which file types can be parsed.
    """
    formats = [
        {
            "filename": "package.json",
            "ecosystem": "npm",
            "language": "JavaScript/TypeScript",
            "description": "Node.js package manifest",
        },
        {
            "filename": "package-lock.json",
            "ecosystem": "npm",
            "language": "JavaScript/TypeScript",
            "description": "Node.js lockfile with exact versions",
        },
        {
            "filename": "requirements.txt",
            "ecosystem": "pypi",
            "language": "Python",
            "description": "Python pip requirements",
        },
        {
            "filename": "Pipfile",
            "ecosystem": "pypi",
            "language": "Python",
            "description": "Pipenv manifest",
        },
        {
            "filename": "pyproject.toml",
            "ecosystem": "pypi",
            "language": "Python",
            "description": "Python project manifest (Poetry/PEP 621)",
        },
        {
            "filename": "Gemfile",
            "ecosystem": "rubygems",
            "language": "Ruby",
            "description": "Ruby Bundler manifest",
        },
        {
            "filename": "Gemfile.lock",
            "ecosystem": "rubygems",
            "language": "Ruby",
            "description": "Ruby Bundler lockfile",
        },
        {
            "filename": "composer.json",
            "ecosystem": "packagist",
            "language": "PHP",
            "description": "PHP Composer manifest",
        },
        {
            "filename": "pom.xml",
            "ecosystem": "maven",
            "language": "Java",
            "description": "Maven project file",
        },
        {
            "filename": "go.mod",
            "ecosystem": "go",
            "language": "Go",
            "description": "Go module file",
        },
        {
            "filename": "Cargo.toml",
            "ecosystem": "cargo",
            "language": "Rust",
            "description": "Rust Cargo manifest",
        },
    ]

    return {"formats": formats}


@router.post("/techstack/scan", response_model=TechStackResponse)
async def scan_dependency_file(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Upload and scan a dependency file for vulnerabilities.

    Supports:
    - package.json, package-lock.json (npm)
    - requirements.txt, Pipfile, pyproject.toml (Python)
    - Gemfile, Gemfile.lock (Ruby)
    - composer.json (PHP)
    - pom.xml (Java/Maven)
    - go.mod (Go)
    - Cargo.toml (Rust)

    Returns a list of packages with known CVE vulnerabilities.
    """
    # Validate file size (max 5MB)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400, detail="File too large. Maximum size is 5MB."
        )

    # Decode content
    try:
        content_str = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text.")

    # Get filename
    filename = file.filename or "unknown"

    # Parse file
    service = get_techstack_service()
    try:
        packages, ecosystem = service.parse_file(content_str, filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to parse file {filename}: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    if not packages:
        raise HTTPException(
            status_code=400,
            detail="No packages found in the file. Please check the file format.",
        )

    # Generate session ID if not provided
    if not session_id:
        session_id = secrets.token_hex(32)

    # Create tech stack name
    stack_name = name or f"Scan of {filename}"

    # Create tech stack and scan
    try:
        tech_stack = service.create_tech_stack(
            db=db,
            name=stack_name,
            packages=packages,
            source_type=filename,
            session_id=session_id,
        )
    except Exception as e:
        logger.error(f"Failed to create tech stack: {e}")
        raise HTTPException(status_code=500, detail="Failed to scan packages.")

    # Get results
    results = service.get_tech_stack_results(db, tech_stack.id)

    if not results:
        raise HTTPException(status_code=500, detail="Failed to retrieve scan results.")

    # Format response
    return _format_tech_stack_response(results, session_id)


@router.post("/techstack/scan/manual", response_model=TechStackResponse)
async def scan_manual_packages(
    request: TechStackCreate,
    db: Session = Depends(get_db),
):
    """
    Scan a manually provided list of packages for vulnerabilities.

    Useful for:
    - Quick checks without uploading files
    - API integrations
    - Testing specific packages
    """
    if not request.packages:
        raise HTTPException(status_code=400, detail="At least one package is required.")

    if len(request.packages) > 500:
        raise HTTPException(
            status_code=400, detail="Maximum 500 packages allowed per scan."
        )

    # Convert to internal format
    packages = [
        {
            "name": pkg.name,
            "version": pkg.version,
            "ecosystem": pkg.ecosystem,
            "dev": pkg.dev,
        }
        for pkg in request.packages
    ]

    # Generate session ID if not provided
    session_id = request.session_id or secrets.token_hex(32)

    # Create tech stack and scan
    service = get_techstack_service()
    try:
        tech_stack = service.create_tech_stack(
            db=db,
            name=request.name,
            description=request.description,
            packages=packages,
            source_type="manual",
            session_id=session_id,
        )
    except Exception as e:
        logger.error(f"Failed to create tech stack: {e}")
        raise HTTPException(status_code=500, detail="Failed to scan packages.")

    # Get results
    results = service.get_tech_stack_results(db, tech_stack.id)

    if not results:
        raise HTTPException(status_code=500, detail="Failed to retrieve scan results.")

    return _format_tech_stack_response(results, session_id)


@router.post("/techstack/scan/manual/encoded", response_model=TechStackResponse)
async def scan_manual_packages_encoded(
    request: TechStackCreateEncoded,
    db: Session = Depends(get_db),
):
    """
    Scan packages with base64-encoded payload to bypass WAF restrictions.

    The encoded field should contain a base64-encoded JSON with:
    - name: string (scan name)
    - packages: array of {name, version, ecosystem, dev}
    """
    # Decode and parse the payload
    try:
        decoded = base64.b64decode(request.encoded).decode("utf-8")
        payload = json.loads(decoded)
    except Exception as e:
        logger.error(f"Failed to decode payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid encoded payload")

    # Validate required fields
    if "packages" not in payload or not payload["packages"]:
        raise HTTPException(status_code=400, detail="At least one package is required.")

    if len(payload["packages"]) > 500:
        raise HTTPException(
            status_code=400, detail="Maximum 500 packages allowed per scan."
        )

    # Convert to internal format
    packages = [
        {
            "name": pkg.get("name", ""),
            "version": pkg.get("version"),
            "ecosystem": pkg.get("ecosystem", "npm"),
            "dev": pkg.get("dev", False),
        }
        for pkg in payload["packages"]
    ]

    # Generate session ID
    session_id = payload.get("session_id") or secrets.token_hex(32)

    # Create tech stack and scan
    service = get_techstack_service()
    try:
        tech_stack = service.create_tech_stack(
            db=db,
            name=payload.get("name", "Scan"),
            description=payload.get("description"),
            packages=packages,
            source_type="manual",
            session_id=session_id,
        )
    except Exception as e:
        logger.error(f"Failed to create tech stack: {e}")
        raise HTTPException(status_code=500, detail="Failed to scan packages.")

    # Get results
    results = service.get_tech_stack_results(db, tech_stack.id)

    if not results:
        raise HTTPException(status_code=500, detail="Failed to retrieve scan results.")

    return _format_tech_stack_response(results, session_id)


@router.get("/techstack/scan/check", response_model=TechStackResponse)
async def scan_packages_get(
    data: str = Query(..., description="Base64-encoded JSON with name and packages"),
    db: Session = Depends(get_db),
):
    """
    Scan packages for vulnerabilities using GET request.

    This endpoint accepts a base64-encoded JSON payload to work with
    CDN/WAF configurations that may block POST requests.

    The 'data' parameter should be a base64-encoded JSON object with:
    - name: string (scan name)
    - packages: array of {name, version, ecosystem, dev}
    """
    # Decode and parse the data
    try:
        decoded = base64.b64decode(data).decode("utf-8")
        payload = json.loads(decoded)
    except Exception as e:
        logger.error(f"Failed to decode scan data: {e}")
        raise HTTPException(
            status_code=400, detail="Invalid data format. Expected base64-encoded JSON."
        )

    # Validate payload
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid payload format.")

    name = payload.get("name", "Scan")
    packages_data = payload.get("packages", [])

    if not packages_data:
        raise HTTPException(status_code=400, detail="At least one package is required.")

    if len(packages_data) > 500:
        raise HTTPException(
            status_code=400, detail="Maximum 500 packages allowed per scan."
        )

    # Convert to internal format
    packages = []
    for pkg in packages_data:
        if not isinstance(pkg, dict) or "name" not in pkg:
            continue
        packages.append(
            {
                "name": pkg.get("name"),
                "version": pkg.get("version"),
                "ecosystem": pkg.get("ecosystem", "npm"),
                "dev": pkg.get("dev", False),
            }
        )

    if not packages:
        raise HTTPException(status_code=400, detail="No valid packages found.")

    # Generate session ID
    session_id = secrets.token_hex(32)

    # Create tech stack and scan
    service = get_techstack_service()
    try:
        tech_stack = service.create_tech_stack(
            db=db,
            name=name,
            description=None,
            packages=packages,
            source_type="manual",
            session_id=session_id,
        )
    except Exception as e:
        logger.error(f"Failed to create tech stack: {e}")
        raise HTTPException(status_code=500, detail="Failed to scan packages.")

    # Get results
    results = service.get_tech_stack_results(db, tech_stack.id)

    if not results:
        raise HTTPException(status_code=500, detail="Failed to retrieve scan results.")

    return _format_tech_stack_response(results, session_id)


@router.get("/techstack/{tech_stack_id}", response_model=TechStackResponse)
async def get_tech_stack(
    tech_stack_id: int,
    session_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get a previously scanned tech stack by ID.

    Requires the session_id that was used when creating the scan.
    """
    # Get tech stack
    tech_stack = db.query(TechStack).filter(TechStack.id == tech_stack_id).first()

    if not tech_stack:
        raise HTTPException(status_code=404, detail="Tech stack not found.")

    # Verify ownership (for anonymous users)
    if tech_stack.session_id and tech_stack.session_id != session_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    # Get results
    service = get_techstack_service()
    results = service.get_tech_stack_results(db, tech_stack_id)

    if not results:
        raise HTTPException(status_code=404, detail="Tech stack not found.")

    return _format_tech_stack_response(results, tech_stack.session_id)


@router.post("/techstack/{tech_stack_id}/rescan", response_model=TechStackResponse)
async def rescan_tech_stack(
    tech_stack_id: int,
    session_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Rescan a tech stack for new vulnerabilities.

    Useful when new CVEs have been added to the database.
    """
    # Get tech stack
    tech_stack = db.query(TechStack).filter(TechStack.id == tech_stack_id).first()

    if not tech_stack:
        raise HTTPException(status_code=404, detail="Tech stack not found.")

    # Verify ownership
    if tech_stack.session_id and tech_stack.session_id != session_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    # Rescan
    service = get_techstack_service()
    service.scan_tech_stack(db, tech_stack)
    db.commit()

    # Get updated results
    results = service.get_tech_stack_results(db, tech_stack_id)

    return _format_tech_stack_response(results, tech_stack.session_id)


@router.get("/techstack/session/{session_id}", response_model=List[TechStackSummary])
async def list_session_tech_stacks(
    session_id: str,
    db: Session = Depends(get_db),
):
    """
    List all tech stacks for a session.

    Returns a summary of each tech stack without full vulnerability details.
    """
    tech_stacks = (
        db.query(TechStack)
        .filter(TechStack.session_id == session_id)
        .order_by(TechStack.created_at.desc())
        .limit(50)
        .all()
    )

    return [
        TechStackSummary(
            id=ts.id,
            name=ts.name,
            source_type=ts.source_type,
            package_count=ts.package_count,
            vulnerable_count=ts.vulnerable_count,
            critical_count=ts.critical_count,
            high_count=ts.high_count,
            created_at=ts.created_at.isoformat() if ts.created_at else "",
        )
        for ts in tech_stacks
    ]


@router.delete("/techstack/{tech_stack_id}")
async def delete_tech_stack(
    tech_stack_id: int,
    session_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Delete a tech stack and its scan results.
    """
    # Get tech stack
    tech_stack = db.query(TechStack).filter(TechStack.id == tech_stack_id).first()

    if not tech_stack:
        raise HTTPException(status_code=404, detail="Tech stack not found.")

    # Verify ownership
    if tech_stack.session_id and tech_stack.session_id != session_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    # Delete
    db.delete(tech_stack)
    db.commit()

    return {"message": "Tech stack deleted successfully."}


# =============================================================================
# Helper Functions
# =============================================================================


def _format_tech_stack_response(
    results: dict, session_id: Optional[str]
) -> TechStackResponse:
    """Format tech stack results for API response including all packages."""
    # Build a map of vulnerable packages with their vulnerabilities
    vulnerable_packages = {}
    medium_count = 0
    low_count = 0

    for pkg in results.get("packages", []):
        vulns = []
        for v in pkg.get("vulnerabilities", []):
            vulns.append(
                VulnerabilityInfo(
                    cve_id=v["cve_id"],
                    severity=v.get("severity"),
                    cvss_score=v.get("cvss_score"),
                    title=v.get("title"),
                    description=v.get("description"),
                    match_type=v.get("match_type", "unknown"),
                    match_confidence=v.get("match_confidence", 0.5),
                    exploited=v.get("exploited", False),
                )
            )
            # Count medium and low severity
            severity = v.get("severity", "").upper()
            if severity == "MEDIUM":
                medium_count += 1
            elif severity == "LOW":
                low_count += 1

        vulnerable_packages[pkg["name"].lower()] = {
            "name": pkg["name"],
            "version": pkg.get("version"),
            "ecosystem": pkg.get("ecosystem", "unknown"),
            "dev": pkg.get("dev", False),
            "vulnerabilities": vulns,
        }

    # Build complete package list from all_packages
    all_packages_list = []
    all_packages = results.get("all_packages", [])

    for pkg in all_packages:
        pkg_name = pkg.get("name", "")
        pkg_name_lower = pkg_name.lower()

        if pkg_name_lower in vulnerable_packages:
            # Package has vulnerabilities
            vuln_pkg = vulnerable_packages[pkg_name_lower]
            all_packages_list.append(
                PackageWithVulns(
                    name=pkg_name,
                    version=vuln_pkg.get("version") or pkg.get("version"),
                    ecosystem=pkg.get(
                        "ecosystem", vuln_pkg.get("ecosystem", "unknown")
                    ),
                    dev=pkg.get("dev", False),
                    status="vulnerable",
                    vulnerabilities=vuln_pkg["vulnerabilities"],
                )
            )
        else:
            # Package is safe
            all_packages_list.append(
                PackageWithVulns(
                    name=pkg_name,
                    version=pkg.get("version"),
                    ecosystem=pkg.get("ecosystem", "unknown"),
                    dev=pkg.get("dev", False),
                    status="safe",
                    vulnerabilities=[],
                )
            )

    # Sort: vulnerable first (by number of vulns), then safe alphabetically
    all_packages_list.sort(
        key=lambda p: (
            0 if p.status == "vulnerable" else 1,
            -len(p.vulnerabilities) if p.status == "vulnerable" else 0,
            p.name.lower(),
        )
    )

    package_count = results.get("package_count", len(all_packages_list))
    vulnerable_count = results.get("vulnerable_count", 0)
    safe_count = package_count - vulnerable_count

    return TechStackResponse(
        id=results["id"],
        name=results["name"],
        description=results.get("description"),
        source_type=results.get("source_type"),
        package_count=package_count,
        vulnerable_count=vulnerable_count,
        safe_count=safe_count,
        critical_count=results.get("critical_count", 0),
        high_count=results.get("high_count", 0),
        medium_count=medium_count,
        low_count=low_count,
        last_scanned_at=(
            results["last_scanned_at"].isoformat()
            if results.get("last_scanned_at")
            else None
        ),
        created_at=(
            results["created_at"].isoformat() if results.get("created_at") else ""
        ),
        packages=all_packages_list,
        session_id=session_id,
    )
