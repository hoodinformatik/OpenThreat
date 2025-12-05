"""
News API endpoints for security news aggregation.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, HttpUrl
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_user, require_admin
from ..models import NewsArticle, NewsSource, User
from ..services.news_service import get_news_service

router = APIRouter()


# Pydantic schemas
class NewsSourceCreate(BaseModel):
    """Schema for creating a news source."""

    name: str
    url: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    fetch_interval_minutes: int = 30


class NewsSourceUpdate(BaseModel):
    """Schema for updating a news source."""

    name: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None
    is_active: Optional[bool] = None
    fetch_interval_minutes: Optional[int] = None


class NewsSourceResponse(BaseModel):
    """Schema for news source response."""

    id: int
    name: str
    url: str
    description: Optional[str]
    icon_url: Optional[str]
    source_type: str
    is_active: bool
    is_default: bool
    fetch_interval_minutes: int
    last_fetched_at: Optional[datetime]
    last_fetch_status: Optional[str]
    total_articles: int
    created_at: datetime

    class Config:
        from_attributes = True


class NewsArticleResponse(BaseModel):
    """Schema for news article response."""

    id: int
    source_id: int
    source_name: Optional[str] = None
    title: str
    url: str
    author: Optional[str]
    original_summary: Optional[str]
    llm_summary: Optional[str]
    llm_key_points: Optional[List[str]]
    llm_relevance_score: Optional[float]
    llm_processed: bool
    categories: Optional[List[str]]
    related_cves: Optional[List[str]]
    published_at: Optional[datetime]
    fetched_at: datetime

    class Config:
        from_attributes = True


class NewsArticleListResponse(BaseModel):
    """Schema for paginated article list."""

    articles: List[NewsArticleResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# Source endpoints
@router.get("/news/sources", response_model=List[NewsSourceResponse])
async def list_news_sources(
    active_only: bool = False,
    db: Session = Depends(get_db),
):
    """
    List all news sources.

    **Query Parameters:**
    - `active_only`: Only return active sources (default: false)
    """
    query = db.query(NewsSource)

    if active_only:
        query = query.filter(NewsSource.is_active == True)

    sources = query.order_by(NewsSource.name).all()
    return sources


@router.post("/news/sources", response_model=NewsSourceResponse)
async def create_news_source(
    source: NewsSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Create a new news source.

    **Requires:** ADMIN role
    """
    # Check if URL already exists
    existing = db.query(NewsSource).filter(NewsSource.url == source.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Source URL already exists")

    new_source = NewsSource(
        name=source.name,
        url=source.url,
        description=source.description,
        icon_url=source.icon_url,
        fetch_interval_minutes=source.fetch_interval_minutes,
        is_active=True,
        is_default=False,
    )

    db.add(new_source)
    db.commit()
    db.refresh(new_source)

    return new_source


@router.put("/news/sources/{source_id}", response_model=NewsSourceResponse)
async def update_news_source(
    source_id: int,
    update: NewsSourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Update a news source.

    **Requires:** ADMIN role
    """
    source = db.query(NewsSource).filter(NewsSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # Update fields
    if update.name is not None:
        source.name = update.name
    if update.description is not None:
        source.description = update.description
    if update.icon_url is not None:
        source.icon_url = update.icon_url
    if update.is_active is not None:
        source.is_active = update.is_active
    if update.fetch_interval_minutes is not None:
        source.fetch_interval_minutes = update.fetch_interval_minutes

    db.commit()
    db.refresh(source)

    return source


@router.delete("/news/sources/{source_id}")
async def delete_news_source(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Delete a news source and all its articles.

    **Requires:** ADMIN role
    """
    source = db.query(NewsSource).filter(NewsSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    if source.is_default:
        raise HTTPException(status_code=400, detail="Cannot delete default sources")

    db.delete(source)
    db.commit()

    return {"status": "deleted", "source_id": source_id}


@router.post("/news/sources/{source_id}/fetch")
async def fetch_source_articles(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Manually trigger article fetch for a source.

    **Requires:** ADMIN role
    """
    source = db.query(NewsSource).filter(NewsSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    news_service = get_news_service()
    stats = news_service.fetch_and_store_articles(db, source)

    return {
        "status": "success",
        "source": source.name,
        "stats": stats,
    }


@router.post("/news/sources/initialize")
async def initialize_default_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Initialize default news sources.

    **Requires:** ADMIN role
    """
    news_service = get_news_service()
    added = news_service.initialize_default_sources(db)

    return {
        "status": "success",
        "sources_added": added,
    }


# Article endpoints
@router.get("/news/articles", response_model=NewsArticleListResponse)
async def list_news_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_id: Optional[int] = None,
    category: Optional[str] = None,
    has_cve: Optional[bool] = None,
    llm_processed: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    List news articles with pagination and filtering.

    **Query Parameters:**
    - `page`: Page number (default: 1)
    - `page_size`: Items per page (default: 20, max: 100)
    - `source_id`: Filter by source ID
    - `category`: Filter by category
    - `has_cve`: Filter articles that mention CVEs
    - `llm_processed`: Filter by LLM processing status
    - `search`: Search in title
    """
    query = db.query(NewsArticle)

    # Apply filters
    if source_id:
        query = query.filter(NewsArticle.source_id == source_id)

    if category:
        query = query.filter(NewsArticle.categories.contains([category]))

    if has_cve is not None:
        if has_cve:
            query = query.filter(NewsArticle.related_cves.isnot(None))
        else:
            query = query.filter(NewsArticle.related_cves.is_(None))

    if llm_processed is not None:
        query = query.filter(NewsArticle.llm_processed == llm_processed)

    if search:
        query = query.filter(NewsArticle.title.ilike(f"%{search}%"))

    # Get total count
    total = query.count()

    # Apply pagination with proper sorting
    # Use COALESCE to fall back to fetched_at if published_at is NULL
    offset = (page - 1) * page_size
    articles = (
        query.order_by(
            desc(func.coalesce(NewsArticle.published_at, NewsArticle.fetched_at))
        )
        .offset(offset)
        .limit(page_size)
        .all()
    )

    # Add source names
    result = []
    for article in articles:
        article_dict = {
            "id": article.id,
            "source_id": article.source_id,
            "source_name": article.source.name if article.source else None,
            "title": article.title,
            "url": article.url,
            "author": article.author,
            "original_summary": article.original_summary,
            "llm_summary": article.llm_summary,
            "llm_key_points": article.llm_key_points,
            "llm_relevance_score": article.llm_relevance_score,
            "llm_processed": article.llm_processed,
            "categories": article.categories,
            "related_cves": article.related_cves,
            "published_at": article.published_at,
            "fetched_at": article.fetched_at,
        }
        result.append(NewsArticleResponse(**article_dict))

    return NewsArticleListResponse(
        articles=result,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(articles)) < total,
    )


@router.get("/news/articles/{article_id}", response_model=NewsArticleResponse)
async def get_news_article(
    article_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a single news article by ID.
    """
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return NewsArticleResponse(
        id=article.id,
        source_id=article.source_id,
        source_name=article.source.name if article.source else None,
        title=article.title,
        url=article.url,
        author=article.author,
        original_summary=article.original_summary,
        llm_summary=article.llm_summary,
        llm_key_points=article.llm_key_points,
        llm_relevance_score=article.llm_relevance_score,
        llm_processed=article.llm_processed,
        categories=article.categories,
        related_cves=article.related_cves,
        published_at=article.published_at,
        fetched_at=article.fetched_at,
    )


@router.post("/news/articles/{article_id}/process")
async def process_article_with_llm(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Process an article with LLM to generate summary.

    **Requires:** ADMIN role
    """
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    news_service = get_news_service()
    success = news_service.process_article_with_llm(db, article)

    if success:
        db.refresh(article)
        return {
            "status": "success",
            "article_id": article_id,
            "llm_summary": article.llm_summary,
            "llm_key_points": article.llm_key_points,
        }
    else:
        raise HTTPException(status_code=500, detail="LLM processing failed")


@router.post("/news/fetch-all")
async def fetch_all_news(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Fetch articles from all active sources.

    **Requires:** ADMIN role
    """
    news_service = get_news_service()
    stats = news_service.fetch_all_sources(db)

    return {
        "status": "success",
        "stats": stats,
    }


@router.get("/news/stats")
async def get_news_stats(
    db: Session = Depends(get_db),
):
    """
    Get news aggregation statistics.
    """
    from sqlalchemy import func

    total_sources = db.query(NewsSource).count()
    active_sources = db.query(NewsSource).filter(NewsSource.is_active == True).count()
    total_articles = db.query(NewsArticle).count()
    processed_articles = (
        db.query(NewsArticle).filter(NewsArticle.llm_processed == True).count()
    )

    # Articles with CVEs
    articles_with_cves = (
        db.query(NewsArticle).filter(NewsArticle.related_cves.isnot(None)).count()
    )

    # Recent articles (last 24h)
    from datetime import timedelta

    recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_articles = (
        db.query(NewsArticle).filter(NewsArticle.fetched_at >= recent_cutoff).count()
    )

    return {
        "total_sources": total_sources,
        "active_sources": active_sources,
        "total_articles": total_articles,
        "processed_articles": processed_articles,
        "articles_with_cves": articles_with_cves,
        "recent_articles_24h": recent_articles,
    }
