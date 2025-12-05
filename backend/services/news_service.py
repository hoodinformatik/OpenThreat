"""
News Service - Fetch and process security news from RSS feeds.

This service handles:
1. Fetching RSS/Atom feeds from configured sources
2. Parsing and storing articles
3. LLM processing for summaries and categorization
4. CVE extraction from article content
"""

import html
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

import requests
from sqlalchemy.orm import Session

from backend.models import NewsArticle, NewsSource

logger = logging.getLogger(__name__)

# Default security news sources
DEFAULT_NEWS_SOURCES = [
    {
        "name": "Heise Security",
        "url": "https://www.heise.de/security/feed.xml",
        "description": "German IT security news from Heise",
        "icon_url": "https://www.heise.de/favicon.ico",
    },
    {
        "name": "NCSC UK",
        "url": "https://www.ncsc.gov.uk/api/1/services/v1/report-rss-feed.xml",
        "description": "UK National Cyber Security Centre advisories",
        "icon_url": "https://www.ncsc.gov.uk/favicon.ico",
    },
    {
        "name": "The Hacker News",
        "url": "https://feeds.feedburner.com/TheHackersNews",
        "description": "Cybersecurity news and analysis",
        "icon_url": "https://thehackernews.com/favicon.ico",
    },
    {
        "name": "Krebs on Security",
        "url": "https://krebsonsecurity.com/feed/",
        "description": "In-depth security news and investigation by Brian Krebs",
        "icon_url": "https://krebsonsecurity.com/favicon.ico",
    },
    {
        "name": "Bleeping Computer",
        "url": "https://www.bleepingcomputer.com/feed/",
        "description": "Technology news and security updates",
        "icon_url": "https://www.bleepingcomputer.com/favicon.ico",
    },
]


class NewsService:
    """Service for fetching and processing security news."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "OpenThreat/1.0 (Security News Aggregator)"}
        )

    def initialize_default_sources(self, db: Session) -> int:
        """
        Initialize default news sources in the database.

        Args:
            db: Database session

        Returns:
            Number of sources added
        """
        added = 0
        for source_data in DEFAULT_NEWS_SOURCES:
            existing = (
                db.query(NewsSource)
                .filter(NewsSource.url == source_data["url"])
                .first()
            )

            if not existing:
                source = NewsSource(
                    name=source_data["name"],
                    url=source_data["url"],
                    description=source_data.get("description"),
                    icon_url=source_data.get("icon_url"),
                    is_default=True,
                    is_active=True,
                )
                db.add(source)
                added += 1
                logger.info(f"Added default news source: {source_data['name']}")

        if added > 0:
            db.commit()

        return added

    def fetch_feed(self, url: str, timeout: int = 30) -> Optional[str]:
        """
        Fetch RSS/Atom feed content.

        Args:
            url: Feed URL
            timeout: Request timeout in seconds

        Returns:
            Feed XML content or None on error
        """
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch feed {url}: {e}")
            return None

    def parse_rss_feed(self, xml_content: str) -> List[Dict[str, Any]]:
        """
        Parse RSS 2.0 feed.

        Args:
            xml_content: RSS XML content

        Returns:
            List of article dicts
        """
        articles = []
        try:
            root = ElementTree.fromstring(xml_content)

            # Handle RSS 2.0
            channel = root.find("channel")
            if channel is not None:
                for item in channel.findall("item"):
                    article = self._parse_rss_item(item)
                    if article:
                        articles.append(article)

            # Handle Atom
            else:
                # Check for Atom namespace (with prefix)
                ns_prefixed = {"atom": "http://www.w3.org/2005/Atom"}
                for entry in root.findall("atom:entry", ns_prefixed):
                    article = self._parse_atom_entry(entry, ns_prefixed, "atom:")
                    if article:
                        articles.append(article)

                # Try with default namespace (xmlns without prefix - like Heise)
                if not articles:
                    # ElementTree requires {namespace}tag format for default namespace
                    atom_ns = "{http://www.w3.org/2005/Atom}"
                    for entry in root.findall(f"{atom_ns}entry"):
                        article = self._parse_atom_entry_with_ns(entry, atom_ns)
                        if article:
                            articles.append(article)

                # Try without any namespace
                if not articles:
                    for entry in root.findall("entry"):
                        article = self._parse_atom_entry(entry, {}, "")
                        if article:
                            articles.append(article)

        except ElementTree.ParseError as e:
            logger.error(f"Failed to parse feed XML: {e}")

        return articles

    def _parse_rss_item(self, item: ElementTree.Element) -> Optional[Dict[str, Any]]:
        """Parse a single RSS item."""
        title = item.findtext("title")
        link = item.findtext("link")

        if not title or not link:
            return None

        # Parse publication date
        pub_date = None
        pub_date_str = item.findtext("pubDate")
        if pub_date_str:
            pub_date = self._parse_date(pub_date_str)

        # Get description/summary
        description = item.findtext("description") or ""
        # Clean HTML from description
        description = self._clean_html(description)

        # Get author
        author = item.findtext("author") or item.findtext("dc:creator")

        # Get categories
        categories = [cat.text for cat in item.findall("category") if cat.text]

        return {
            "title": self._clean_html(title),
            "url": link.strip(),
            "summary": description[:2000],  # Limit length
            "author": author,
            "published_at": pub_date,
            "categories": categories if categories else None,
        }

    def _parse_atom_entry(
        self, entry: ElementTree.Element, ns: Dict[str, str], prefix: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Parse a single Atom entry with namespace prefix."""
        title_elem = entry.find(f"{prefix}title", ns) if ns else entry.find("title")
        title = title_elem.text if title_elem is not None else None

        # Get link (prefer alternate)
        link = None
        for link_elem in (
            entry.findall(f"{prefix}link", ns) if ns else entry.findall("link")
        ):
            rel = link_elem.get("rel", "alternate")
            if rel == "alternate":
                link = link_elem.get("href")
                break
            elif not link:
                link = link_elem.get("href")

        if not title or not link:
            return None

        # Parse publication date
        pub_date = None
        published = (
            entry.find(f"{prefix}published", ns) if ns else entry.find("published")
        )
        updated = entry.find(f"{prefix}updated", ns) if ns else entry.find("updated")
        pub_date_str = (
            published.text
            if published is not None
            else updated.text if updated is not None else None
        )
        if pub_date_str:
            pub_date = self._parse_date(pub_date_str)

        # Get summary/content
        summary_elem = (
            entry.find(f"{prefix}summary", ns) if ns else entry.find("summary")
        )
        content_elem = (
            entry.find(f"{prefix}content", ns) if ns else entry.find("content")
        )
        summary = (
            summary_elem.text
            if summary_elem is not None
            else content_elem.text if content_elem is not None else ""
        )
        summary = self._clean_html(summary or "")

        # Get author
        author_elem = (
            entry.find(f"{prefix}author/{prefix}name", ns)
            if ns
            else entry.find("author/name")
        )
        author = author_elem.text if author_elem is not None else None

        return {
            "title": self._clean_html(title),
            "url": link.strip(),
            "summary": summary[:2000],
            "author": author,
            "published_at": pub_date,
            "categories": None,
        }

    def _parse_atom_entry_with_ns(
        self, entry: ElementTree.Element, ns: str
    ) -> Optional[Dict[str, Any]]:
        """Parse Atom entry with default namespace (like Heise feeds)."""
        title_elem = entry.find(f"{ns}title")
        title = title_elem.text if title_elem is not None else None

        # Get link (prefer alternate)
        link = None
        for link_elem in entry.findall(f"{ns}link"):
            rel = link_elem.get("rel", "alternate")
            if rel == "alternate":
                link = link_elem.get("href")
                break
            elif not link:
                link = link_elem.get("href")

        if not title or not link:
            return None

        # Parse publication date - prefer published over updated
        pub_date = None
        published = entry.find(f"{ns}published")
        updated = entry.find(f"{ns}updated")
        pub_date_str = (
            published.text
            if published is not None
            else updated.text if updated is not None else None
        )
        if pub_date_str:
            pub_date = self._parse_date(pub_date_str)

        # Get summary/content
        summary_elem = entry.find(f"{ns}summary")
        content_elem = entry.find(f"{ns}content")
        summary = (
            summary_elem.text
            if summary_elem is not None
            else content_elem.text if content_elem is not None else ""
        )
        summary = self._clean_html(summary or "")

        # Get author
        author_elem = entry.find(f"{ns}author/{ns}name")
        author = author_elem.text if author_elem is not None else None

        return {
            "title": self._clean_html(title),
            "url": link.strip(),
            "summary": summary[:2000],
            "author": author,
            "published_at": pub_date,
            "categories": None,
        }

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats."""
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",  # RFC 822
            "%a, %d %b %Y %H:%M:%S %Z",  # RFC 822 with timezone name
            "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO 8601 with milliseconds UTC (Heise)
            "%Y-%m-%dT%H:%M:%S.%f%z",  # ISO 8601 with milliseconds and timezone
            "%Y-%m-%dT%H:%M:%S%z",  # ISO 8601
            "%Y-%m-%dT%H:%M:%SZ",  # ISO 8601 UTC
            "%Y-%m-%d %H:%M:%S",  # Simple datetime
            "%Y-%m-%d",  # Simple date
        ]

        # Clean up timezone
        date_str = date_str.strip()
        date_str = re.sub(r"\s+GMT$", " +0000", date_str)
        date_str = re.sub(r"\s+UTC$", " +0000", date_str)

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue

        logger.debug(f"Could not parse date: {date_str}")
        return None

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags and decode entities."""
        if not text:
            return ""
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Decode HTML entities
        text = html.unescape(text)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def fetch_and_store_articles(
        self, db: Session, source: NewsSource, limit: int = 50
    ) -> Dict[str, int]:
        """
        Fetch articles from a source and store new ones.

        Args:
            db: Database session
            source: News source to fetch from
            limit: Maximum articles to process

        Returns:
            Dict with fetch statistics
        """
        stats = {"fetched": 0, "new": 0, "errors": 0}

        # Fetch feed
        xml_content = self.fetch_feed(source.url)
        if not xml_content:
            source.last_fetch_status = "error"
            source.last_fetch_error = "Failed to fetch feed"
            source.last_fetched_at = datetime.now(timezone.utc)
            db.commit()
            return stats

        # Parse feed
        articles = self.parse_rss_feed(xml_content)
        stats["fetched"] = len(articles)

        # Store new articles one by one to handle duplicates gracefully
        for article_data in articles[:limit]:
            try:
                # Check if article already exists
                existing = (
                    db.query(NewsArticle)
                    .filter(NewsArticle.url == article_data["url"])
                    .first()
                )

                if existing:
                    continue

                # Create new article
                article = NewsArticle(
                    source_id=source.id,
                    title=article_data["title"],
                    url=article_data["url"],
                    author=article_data.get("author"),
                    original_summary=article_data.get("summary"),
                    published_at=article_data.get("published_at"),
                    categories=article_data.get("categories"),
                    fetched_at=datetime.now(timezone.utc),
                )

                # Extract CVEs from title and summary
                cves = self._extract_cves(
                    f"{article_data['title']} {article_data.get('summary', '')}"
                )
                if cves:
                    article.related_cves = cves

                db.add(article)
                db.flush()  # Flush to catch duplicates early
                stats["new"] += 1

            except Exception as e:
                db.rollback()  # Rollback on error to continue with next article
                logger.error(f"Error storing article: {e}")
                stats["errors"] += 1

        # Update source stats
        source.last_fetched_at = datetime.now(timezone.utc)
        source.last_fetch_status = "success"
        source.last_fetch_error = None
        source.total_articles = (
            db.query(NewsArticle).filter(NewsArticle.source_id == source.id).count()
        )

        db.commit()

        logger.info(
            f"Fetched {stats['fetched']} articles from {source.name}, "
            f"{stats['new']} new, {stats['errors']} errors"
        )

        return stats

    def _extract_cves(self, text: str) -> Optional[List[str]]:
        """Extract CVE IDs from text."""
        if not text:
            return None

        pattern = r"CVE-\d{4}-\d{4,7}"
        cves = list(set(re.findall(pattern, text, re.IGNORECASE)))
        return cves if cves else None

    def fetch_all_sources(self, db: Session) -> Dict[str, Any]:
        """
        Fetch articles from all active sources.

        Args:
            db: Database session

        Returns:
            Dict with overall statistics
        """
        sources = db.query(NewsSource).filter(NewsSource.is_active == True).all()

        total_stats = {
            "sources_processed": 0,
            "total_fetched": 0,
            "total_new": 0,
            "total_errors": 0,
        }

        for source in sources:
            try:
                stats = self.fetch_and_store_articles(db, source)
                total_stats["sources_processed"] += 1
                total_stats["total_fetched"] += stats["fetched"]
                total_stats["total_new"] += stats["new"]
                total_stats["total_errors"] += stats["errors"]
            except Exception as e:
                logger.error(f"Error processing source {source.name}: {e}")
                total_stats["total_errors"] += 1

        return total_stats

    def process_article_with_llm(self, db: Session, article: NewsArticle) -> bool:
        """
        Process an article with LLM to generate summary and extract info.

        Args:
            db: Database session
            article: Article to process

        Returns:
            True if successful
        """
        try:
            from backend.llm_service import get_llm_service

            llm = get_llm_service()
            if not llm.enabled:
                return False

            # Build prompt for article summarization
            content = article.original_summary or article.title

            prompt = f"""You are a cybersecurity analyst summarizing security news.

Article Title: {article.title}

Article Content:
{content[:1500]}

Tasks:
1. Write a 2-3 sentence summary focusing on the security implications
2. List 2-3 key takeaways as bullet points
3. Rate relevance to cybersecurity (0.0-1.0)
4. Identify categories: vulnerability, malware, breach, ransomware, apt, policy, tool, other

Respond in this exact JSON format:
{{
    "summary": "Your summary here",
    "key_points": ["Point 1", "Point 2"],
    "relevance": 0.8,
    "categories": ["vulnerability", "malware"]
}}

JSON Response:"""

            response = llm.client.generate(
                model=llm.model,
                prompt=prompt,
                options={"temperature": 0.3, "num_predict": 300},
            )

            # Parse JSON response
            import json

            response_text = response["response"].strip()

            # Try to extract JSON from response
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())

                article.llm_summary = result.get("summary")
                article.llm_key_points = result.get("key_points")
                article.llm_relevance_score = result.get("relevance")
                article.categories = result.get("categories")
                article.llm_processed = True
                article.llm_processed_at = datetime.now(timezone.utc)

                db.commit()
                logger.info(f"Processed article with LLM: {article.title[:50]}...")
                return True

        except Exception as e:
            logger.error(f"Error processing article with LLM: {e}")

        return False


# Singleton instance
_news_service = None


def get_news_service() -> NewsService:
    """Get or create news service instance."""
    global _news_service
    if _news_service is None:
        _news_service = NewsService()
    return _news_service
