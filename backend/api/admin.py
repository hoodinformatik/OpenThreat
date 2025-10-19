"""
Admin-only endpoints for system management.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import require_admin
from ..models import User, Vulnerability

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stats")
async def get_system_stats(
    current_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    """
    Get system statistics (Admin only).

    **Requires:** Admin role

    **Returns:**
    - Total users
    - Total vulnerabilities
    - System health metrics
    """
    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    total_vulns = db.query(func.count(Vulnerability.id)).scalar()

    logger.info(f"Admin {current_user.username} accessed system stats")

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": total_users - active_users,
        },
        "vulnerabilities": {"total": total_vulns},
        "system": {"status": "healthy"},
    }


@router.delete("/vulnerabilities/{vuln_id}")
async def delete_vulnerability(
    vuln_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Delete a vulnerability (Admin only).

    **Requires:** Admin role

    **Warning:** This is a destructive operation!

    **Returns:**
    - Success message
    """
    vuln = db.query(Vulnerability).filter(Vulnerability.id == vuln_id).first()

    if not vuln:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vulnerability not found"
        )

    cve_id = vuln.cve_id
    db.delete(vuln)
    db.commit()

    logger.warning(f"Admin {current_user.username} deleted vulnerability {cve_id}")

    return {
        "message": f"Vulnerability {cve_id} deleted successfully",
        "deleted_by": current_user.username,
    }
