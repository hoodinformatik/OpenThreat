"""
RSS/Atom feed endpoints.
"""
from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timezone
import html

from ..database import get_db
from ..models import Vulnerability

router = APIRouter()


def generate_rss_feed(vulnerabilities, title, description, base_url):
    """Generate RSS 2.0 feed XML."""
    items = []
    for vuln in vulnerabilities:
        pub_date = vuln.published_at.strftime("%a, %d %b %Y %H:%M:%S GMT") if vuln.published_at else ""
        
        # Escape XML special characters
        cve_id = html.escape(vuln.cve_id)
        vuln_title = html.escape(vuln.title or "")
        
        # Build description
        desc_parts = []
        if vuln.description:
            desc_parts.append(html.escape(vuln.description[:500]))
        if vuln.cvss_score:
            desc_parts.append(f"CVSS Score: {vuln.cvss_score}")
        if vuln.severity:
            desc_parts.append(f"Severity: {vuln.severity}")
        if vuln.exploited_in_the_wild:
            desc_parts.append("EXPLOITED IN THE WILD")
        
        item_desc = " | ".join(desc_parts)
        
        items.append(f"""
    <item>
      <title>{cve_id}: {vuln_title}</title>
      <link>{base_url}/vulnerabilities/{vuln.cve_id}</link>
      <guid>{base_url}/vulnerabilities/{vuln.cve_id}</guid>
      <pubDate>{pub_date}</pubDate>
      <description><![CDATA[{item_desc}]]></description>
    </item>""")
    
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    
    # Escape XML special characters
    title = html.escape(title)
    description = html.escape(description)
    
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{title}</title>
    <link>{base_url}</link>
    <description>{description}</description>
    <language>en-us</language>
    <lastBuildDate>{now}</lastBuildDate>
    <atom:link href="{base_url}/api/v1/feeds/rss" rel="self" type="application/rss+xml" />
    {''.join(items)}
  </channel>
</rss>"""
    
    return rss


@router.get("/feeds/rss")
async def rss_feed(
    request: Request,
    limit: int = 50,
    exploited_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    RSS feed of recent vulnerabilities.
    
    **Query Parameters:**
    - `limit`: Number of items (default: 50, max: 100)
    - `exploited_only`: Only include exploited vulnerabilities (default: false)
    """
    limit = min(limit, 100)
    
    # Get base URL from request
    base_url = str(request.base_url).rstrip('/')
    
    query = db.query(Vulnerability)
    
    if exploited_only:
        query = query.filter(Vulnerability.exploited_in_the_wild == True)
    
    vulnerabilities = query.order_by(
        desc(Vulnerability.published_at)
    ).limit(limit).all()
    
    title = "OpenThreat - Recent Vulnerabilities"
    if exploited_only:
        title = "OpenThreat - Exploited Vulnerabilities"
    
    rss_content = generate_rss_feed(
        vulnerabilities,
        title=title,
        description="Public Threat Intelligence Dashboard - Latest CVEs",
        base_url=base_url
    )
    
    return Response(content=rss_content, media_type="application/rss+xml")


@router.get("/feeds/exploited")
async def exploited_feed(
    request: Request,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    RSS feed of exploited vulnerabilities.
    
    Returns vulnerabilities with `exploited_in_the_wild = true`.
    """
    limit = min(limit, 100)
    
    # Get base URL from request
    base_url = str(request.base_url).rstrip('/')
    
    vulnerabilities = db.query(Vulnerability).filter(
        Vulnerability.exploited_in_the_wild == True
    ).order_by(
        desc(Vulnerability.priority_score)
    ).limit(limit).all()
    
    rss_content = generate_rss_feed(
        vulnerabilities,
        title="OpenThreat - Exploited Vulnerabilities",
        description="CVEs actively exploited in the wild",
        base_url=base_url
    )
    
    return Response(content=rss_content, media_type="application/rss+xml")


@router.get("/feeds/critical")
async def critical_feed(
    request: Request,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    RSS feed of critical vulnerabilities.
    
    Returns vulnerabilities with severity = CRITICAL.
    """
    limit = min(limit, 100)
    
    # Get base URL from request
    base_url = str(request.base_url).rstrip('/')
    
    vulnerabilities = db.query(Vulnerability).filter(
        Vulnerability.severity == "CRITICAL"
    ).order_by(
        desc(Vulnerability.published_at)
    ).limit(limit).all()
    
    rss_content = generate_rss_feed(
        vulnerabilities,
        title="OpenThreat - Critical Vulnerabilities",
        description="Critical severity CVEs",
        base_url=base_url
    )
    
    return Response(content=rss_content, media_type="application/rss+xml")
