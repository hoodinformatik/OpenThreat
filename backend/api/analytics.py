"""
Site analytics endpoints for visitor statistics.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import Date, cast, func
from sqlalchemy.orm import Session
from user_agents import parse

from ..database import get_db
from ..models import PageView

router = APIRouter()


class PageViewCreate(BaseModel):
    """Request model for tracking a page view."""

    path: str
    referrer: Optional[str] = None
    visitor_id: Optional[str] = None


class AnalyticsResponse(BaseModel):
    """Response model for analytics data."""

    total_views: int
    unique_visitors: int
    views_today: int
    views_this_week: int
    views_this_month: int
    views_this_year: int
    top_pages: list
    views_by_day: list
    views_by_country: list
    views_by_device: list
    views_by_browser: list
    recent_views: list


def get_device_type(user_agent_string: str) -> str:
    """Parse user agent to determine device type."""
    try:
        user_agent = parse(user_agent_string)
        if user_agent.is_mobile:
            return "mobile"
        elif user_agent.is_tablet:
            return "tablet"
        else:
            return "desktop"
    except Exception:
        return "unknown"


def get_browser_and_os(user_agent_string: str) -> tuple[str, str]:
    """Parse user agent to get browser and OS."""
    try:
        user_agent = parse(user_agent_string)
        browser = f"{user_agent.browser.family}"
        os = f"{user_agent.os.family}"
        return browser, os
    except Exception:
        return "unknown", "unknown"


@router.post("/analytics/track")
async def track_page_view(
    page_view: PageViewCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Track a page view for analytics.

    This endpoint is called by the frontend to record page visits.
    """
    # Get user agent info
    user_agent_string = request.headers.get("user-agent", "")
    device_type = get_device_type(user_agent_string)
    browser, os = get_browser_and_os(user_agent_string)

    # Get country from headers (set by reverse proxy/CDN)
    country = request.headers.get("cf-ipcountry") or request.headers.get(
        "x-country-code"
    )
    city = request.headers.get("cf-ipcity")

    # Create page view record
    db_page_view = PageView(
        path=page_view.path[:500],  # Limit path length
        referrer=page_view.referrer[:1000] if page_view.referrer else None,
        visitor_id=page_view.visitor_id,
        country=country,
        city=city,
        device_type=device_type,
        browser=browser,
        os=os,
    )

    db.add(db_page_view)
    db.commit()

    return {"status": "ok"}


@router.get("/analytics/stats", response_model=AnalyticsResponse)
async def get_analytics_stats(
    days: int = 30,
    db: Session = Depends(get_db),
):
    """
    Get site analytics statistics.

    Returns comprehensive visitor statistics including:
    - Total views and unique visitors
    - Views by time period (today, week, month, year)
    - Top pages
    - Views by day (for charts)
    - Geographic distribution
    - Device and browser breakdown
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)
    year_start = today_start.replace(month=1, day=1)
    days_ago = now - timedelta(days=days)

    # Total views
    total_views = db.query(func.count(PageView.id)).scalar() or 0

    # Unique visitors (by visitor_id)
    unique_visitors = (
        db.query(func.count(func.distinct(PageView.visitor_id)))
        .filter(PageView.visitor_id.isnot(None))
        .scalar()
        or 0
    )

    # Views today
    views_today = (
        db.query(func.count(PageView.id))
        .filter(PageView.created_at >= today_start)
        .scalar()
        or 0
    )

    # Views this week
    views_this_week = (
        db.query(func.count(PageView.id))
        .filter(PageView.created_at >= week_start)
        .scalar()
        or 0
    )

    # Views this month
    views_this_month = (
        db.query(func.count(PageView.id))
        .filter(PageView.created_at >= month_start)
        .scalar()
        or 0
    )

    # Views this year
    views_this_year = (
        db.query(func.count(PageView.id))
        .filter(PageView.created_at >= year_start)
        .scalar()
        or 0
    )

    # Top pages (last N days)
    top_pages_query = (
        db.query(PageView.path, func.count(PageView.id).label("count"))
        .filter(PageView.created_at >= days_ago)
        .group_by(PageView.path)
        .order_by(func.count(PageView.id).desc())
        .limit(10)
        .all()
    )
    top_pages = [{"path": path, "views": count} for path, count in top_pages_query]

    # Views by day (last N days)
    views_by_day_query = (
        db.query(
            cast(PageView.created_at, Date).label("date"),
            func.count(PageView.id).label("count"),
        )
        .filter(PageView.created_at >= days_ago)
        .group_by(cast(PageView.created_at, Date))
        .order_by(cast(PageView.created_at, Date))
        .all()
    )
    views_by_day = [
        {"date": str(date), "views": count} for date, count in views_by_day_query
    ]

    # Views by country
    views_by_country_query = (
        db.query(PageView.country, func.count(PageView.id).label("count"))
        .filter(PageView.country.isnot(None))
        .filter(PageView.created_at >= days_ago)
        .group_by(PageView.country)
        .order_by(func.count(PageView.id).desc())
        .limit(10)
        .all()
    )
    views_by_country = [
        {"country": country or "Unknown", "views": count}
        for country, count in views_by_country_query
    ]

    # Views by device type
    views_by_device_query = (
        db.query(PageView.device_type, func.count(PageView.id).label("count"))
        .filter(PageView.device_type.isnot(None))
        .filter(PageView.created_at >= days_ago)
        .group_by(PageView.device_type)
        .order_by(func.count(PageView.id).desc())
        .all()
    )
    views_by_device = [
        {"device": device or "Unknown", "views": count}
        for device, count in views_by_device_query
    ]

    # Views by browser
    views_by_browser_query = (
        db.query(PageView.browser, func.count(PageView.id).label("count"))
        .filter(PageView.browser.isnot(None))
        .filter(PageView.created_at >= days_ago)
        .group_by(PageView.browser)
        .order_by(func.count(PageView.id).desc())
        .limit(8)
        .all()
    )
    views_by_browser = [
        {"browser": browser or "Unknown", "views": count}
        for browser, count in views_by_browser_query
    ]

    # Recent views (last 20)
    recent_views_query = (
        db.query(PageView).order_by(PageView.created_at.desc()).limit(20).all()
    )
    recent_views = [
        {
            "path": pv.path,
            "country": pv.country,
            "device": pv.device_type,
            "browser": pv.browser,
            "created_at": pv.created_at.isoformat() if pv.created_at else None,
        }
        for pv in recent_views_query
    ]

    return AnalyticsResponse(
        total_views=total_views,
        unique_visitors=unique_visitors,
        views_today=views_today,
        views_this_week=views_this_week,
        views_this_month=views_this_month,
        views_this_year=views_this_year,
        top_pages=top_pages,
        views_by_day=views_by_day,
        views_by_country=views_by_country,
        views_by_device=views_by_device,
        views_by_browser=views_by_browser,
        recent_views=recent_views,
    )
