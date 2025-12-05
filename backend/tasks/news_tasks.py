"""
Celery tasks for news fetching and processing.

This module handles background tasks for:
- Fetching articles from RSS feeds
- Processing articles with LLM
- Initializing default news sources
"""

import logging
from datetime import datetime, timezone

from backend.celery_app import celery_app as celery
from backend.database import get_db
from backend.services.news_service import get_news_service

logger = logging.getLogger(__name__)


@celery.task(name="tasks.fetch_news_articles", bind=True, max_retries=3)
def fetch_news_articles_task(self) -> dict:
    """
    Fetch articles from all active news sources.

    This task should run periodically (e.g., every 30 minutes).

    Returns:
        Dict with fetch statistics
    """
    db = next(get_db())
    try:
        logger.info("Starting news fetch task")

        news_service = get_news_service()
        stats = news_service.fetch_all_sources(db)

        logger.info(
            f"News fetch complete: {stats['sources_processed']} sources, "
            f"{stats['total_new']} new articles"
        )

        return {
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **stats,
        }

    except Exception as e:
        logger.error(f"News fetch task failed: {e}")

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    finally:
        db.close()


@celery.task(name="tasks.process_news_with_llm")
def process_news_with_llm_task(batch_size: int = 10) -> dict:
    """
    Process unprocessed news articles with LLM.

    Args:
        batch_size: Number of articles to process in this batch

    Returns:
        Dict with processing statistics
    """
    db = next(get_db())
    try:
        from backend.models import NewsArticle

        logger.info(f"Starting LLM news processing (batch_size={batch_size})")

        # Get unprocessed articles
        articles = (
            db.query(NewsArticle)
            .filter(NewsArticle.llm_processed == False)
            .order_by(NewsArticle.published_at.desc())
            .limit(batch_size)
            .all()
        )

        if not articles:
            logger.info("No unprocessed news articles found")
            return {
                "status": "success",
                "processed": 0,
                "message": "No articles to process",
            }

        news_service = get_news_service()
        processed = 0
        errors = 0

        for article in articles:
            try:
                success = news_service.process_article_with_llm(db, article)
                if success:
                    processed += 1
                else:
                    errors += 1
            except Exception as e:
                logger.error(f"Error processing article {article.id}: {e}")
                errors += 1

        logger.info(
            f"LLM news processing complete: {processed} processed, {errors} errors"
        )

        return {
            "status": "success",
            "processed": processed,
            "errors": errors,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"LLM news processing task failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    finally:
        db.close()


@celery.task(name="tasks.initialize_news_sources")
def initialize_news_sources_task() -> dict:
    """
    Initialize default news sources if not already present.

    This task should run once on startup.

    Returns:
        Dict with initialization status
    """
    db = next(get_db())
    try:
        logger.info("Initializing default news sources")

        news_service = get_news_service()
        added = news_service.initialize_default_sources(db)

        logger.info(f"News sources initialized: {added} new sources added")

        return {
            "status": "success",
            "sources_added": added,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"News source initialization failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    finally:
        db.close()


@celery.task(name="tasks.fetch_single_news_source", bind=True, max_retries=3)
def fetch_single_news_source_task(self, source_id: int) -> dict:
    """
    Fetch articles from a single news source.

    Args:
        source_id: ID of the news source to fetch

    Returns:
        Dict with fetch statistics
    """
    db = next(get_db())
    try:
        from backend.models import NewsSource

        source = db.query(NewsSource).filter(NewsSource.id == source_id).first()
        if not source:
            return {
                "status": "error",
                "message": f"Source {source_id} not found",
            }

        logger.info(f"Fetching articles from source: {source.name}")

        news_service = get_news_service()
        stats = news_service.fetch_and_store_articles(db, source)

        logger.info(f"Fetched {stats['new']} new articles from {source.name}")

        return {
            "status": "success",
            "source_id": source_id,
            "source_name": source.name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **stats,
        }

    except Exception as e:
        logger.error(f"Failed to fetch source {source_id}: {e}")
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    finally:
        db.close()
