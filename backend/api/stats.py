"""
Statistics and dashboard endpoints.
"""

import json
from datetime import datetime, timedelta, timezone

import redis
from fastapi import APIRouter, Depends
from sqlalchemy import case, desc, func
from sqlalchemy.orm import Session

from ..database import REDIS_URL, get_db
from ..models import IngestionRun, Vulnerability
from ..schemas import StatsResponse

router = APIRouter()

# Redis connection for caching
redis_client = redis.from_url(REDIS_URL, decode_responses=True)
STATS_CACHE_KEY = "dashboard:stats"
STATS_CACHE_TTL = 300  # 5 minutes


@router.get("/stats", response_model=StatsResponse)
async def get_statistics(db: Session = Depends(get_db)):
    """
    Get overall statistics for the dashboard (cached for 5 minutes).

    Returns:
    - Total vulnerabilities
    - Exploited vulnerabilities
    - Breakdown by severity
    - Recent updates count
    - Last update timestamp
    """
    # Try to get from cache first
    try:
        cached = redis_client.get(STATS_CACHE_KEY)
        if cached:
            data = json.loads(cached)
            return StatsResponse(**data)
    except Exception as e:
        print(f"Cache read error: {e}")

    # Cache miss - calculate stats with optimized single query
    try:
        # Use a single aggregation query instead of multiple COUNT queries
        stats_query = (
            db.query(
                func.count(Vulnerability.id).label("total"),
                func.sum(
                    case((Vulnerability.exploited_in_the_wild == True, 1), else_=0)
                ).label("exploited"),
                func.sum(
                    case((Vulnerability.severity == "CRITICAL", 1), else_=0)
                ).label("critical"),
                func.sum(case((Vulnerability.severity == "HIGH", 1), else_=0)).label(
                    "high"
                ),
                func.sum(
                    case(
                        (
                            Vulnerability.updated_at
                            >= datetime.now(timezone.utc) - timedelta(days=7),
                            1,
                        ),
                        else_=0,
                    )
                ).label("recent"),
            )
            .filter(Vulnerability.cve_id.like("CVE-%"))
            .one()
        )

        total = stats_query.total or 0
        exploited = stats_query.exploited or 0
        critical = stats_query.critical or 0
        high = stats_query.high or 0
        recent = stats_query.recent or 0

        # Severity breakdown - separate query but still fast
        severity_counts = (
            db.query(Vulnerability.severity, func.count(Vulnerability.id))
            .filter(Vulnerability.cve_id.like("CVE-%"))
            .group_by(Vulnerability.severity)
            .all()
        )

        by_severity = {
            severity or "UNKNOWN": count for severity, count in severity_counts
        }

        # Last update timestamp
        last_run = (
            db.query(IngestionRun)
            .filter(IngestionRun.status == "success")
            .order_by(desc(IngestionRun.completed_at))
            .first()
        )

        last_update = last_run.completed_at if last_run else None

        result = StatsResponse(
            total_vulnerabilities=total,
            exploited_vulnerabilities=exploited,
            critical_vulnerabilities=critical,
            high_vulnerabilities=high,
            by_severity=by_severity,
            recent_updates=recent,
            last_update=last_update,
        )

        # Cache the result
        try:
            redis_client.setex(
                STATS_CACHE_KEY,
                STATS_CACHE_TTL,
                json.dumps(result.model_dump(), default=str),
            )
        except Exception as e:
            print(f"Cache write error: {e}")

        return result

    except Exception as e:
        print(f"Stats calculation error: {e}")
        # Return empty stats on error
        return StatsResponse(
            total_vulnerabilities=0,
            exploited_vulnerabilities=0,
            critical_vulnerabilities=0,
            high_vulnerabilities=0,
            by_severity={},
            recent_updates=0,
            last_update=None,
        )


@router.get("/stats/top-vendors")
async def get_top_vendors(limit: int = 20, db: Session = Depends(get_db)):
    """
    Get top vendors by vulnerability count.

    **Query Parameters:**
    - `limit`: Number of vendors to return (default: 20)
    """

    # This is a complex query - get all vendors and count
    vulnerabilities = (
        db.query(Vulnerability.vendors).filter(Vulnerability.vendors.isnot(None)).all()
    )

    vendor_counts = {}
    for (vendors,) in vulnerabilities:
        if vendors:
            for vendor in vendors:
                vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1

    # Sort and limit
    top_vendors = sorted(vendor_counts.items(), key=lambda x: x[1], reverse=True)[
        :limit
    ]

    return {
        "vendors": [{"name": vendor, "count": count} for vendor, count in top_vendors]
    }


@router.get("/stats/severity-distribution")
async def get_severity_distribution(db: Session = Depends(get_db)):
    """
    Get vulnerability distribution by severity.

    Returns counts and percentages for each severity level.
    """
    total = db.query(func.count(Vulnerability.id)).scalar() or 1

    severity_counts = (
        db.query(Vulnerability.severity, func.count(Vulnerability.id))
        .group_by(Vulnerability.severity)
        .all()
    )

    distribution = []
    for severity, count in severity_counts:
        distribution.append(
            {
                "severity": severity or "UNKNOWN",
                "count": count,
                "percentage": round((count / total) * 100, 2),
            }
        )

    # Sort by severity priority
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}
    distribution.sort(key=lambda x: severity_order.get(x["severity"], 5))

    return {"distribution": distribution, "total": total}


@router.get("/stats/timeline")
async def get_vulnerability_timeline(days: int = 30, db: Session = Depends(get_db)):
    """
    Get vulnerability publication timeline.

    Returns daily counts of published vulnerabilities for the last N days.

    **Query Parameters:**
    - `days`: Number of days to include (default: 30)
    """
    from sqlalchemy import Date, cast, func

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    timeline = (
        db.query(
            cast(Vulnerability.published_at, Date).label("date"),
            func.count(Vulnerability.id).label("count"),
        )
        .filter(Vulnerability.published_at >= cutoff)
        .group_by(cast(Vulnerability.published_at, Date))
        .order_by(cast(Vulnerability.published_at, Date))
        .all()
    )

    return {
        "timeline": [{"date": str(date), "count": count} for date, count in timeline]
    }


@router.get("/stats/ingestion-history")
async def get_ingestion_history(limit: int = 10, db: Session = Depends(get_db)):
    """
    Get recent ingestion run history.

    **Query Parameters:**
    - `limit`: Number of runs to return (default: 10)
    """
    runs = (
        db.query(IngestionRun)
        .order_by(desc(IngestionRun.started_at))
        .limit(limit)
        .all()
    )

    return {
        "runs": [
            {
                "id": run.id,
                "source": run.source,
                "status": run.status,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": (
                    run.completed_at.isoformat() if run.completed_at else None
                ),
                "duration_seconds": run.duration_seconds,
                "records_fetched": run.records_fetched,
                "records_inserted": run.records_inserted,
                "records_updated": run.records_updated,
                "records_failed": run.records_failed,
            }
            for run in runs
        ]
    }
