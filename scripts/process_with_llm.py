"""
CLI tool to process CVEs with LLM and generate simple titles/descriptions.

Usage:
    python scripts/process_with_llm.py --all                    # Process all unprocessed CVEs
    python scripts/process_with_llm.py --cve CVE-2024-1234      # Process specific CVE
    python scripts/process_with_llm.py --limit 10               # Process 10 CVEs
    python scripts/process_with_llm.py --reprocess              # Reprocess all CVEs
"""
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from backend.database import SessionLocal
from backend.models import Vulnerability
from backend.llm_service import get_llm_service


def process_vulnerabilities(
    session: Session,
    cve_id: str = None,
    limit: int = None,
    reprocess: bool = False
):
    """Process vulnerabilities with LLM."""
    
    llm = get_llm_service(enabled=True)
    
    if not llm.enabled:
        print("❌ LLM service is not available. Please install and start Ollama.")
        print("   Install: https://ollama.ai/download")
        print("   Run: ollama pull llama3.2:3b")
        return
    
    # Build query
    query = session.query(Vulnerability)
    
    if cve_id:
        query = query.filter(Vulnerability.cve_id == cve_id)
    elif not reprocess:
        query = query.filter(Vulnerability.llm_processed == False)
    
    if limit:
        query = query.limit(limit)
    
    vulnerabilities = query.all()
    
    if not vulnerabilities:
        print("✅ No vulnerabilities to process")
        return
    
    print(f"🤖 Processing {len(vulnerabilities)} CVEs with LLM...")
    print(f"   Model: {llm.model}")
    print()
    
    processed = 0
    errors = 0
    
    for vuln in vulnerabilities:
        try:
            print(f"Processing {vuln.cve_id}...", end=" ")
            
            # Generate summary
            summary = llm.generate_cve_summary(
                cve_id=vuln.cve_id,
                original_title=vuln.title,
                description=vuln.description or "",
                cvss_score=vuln.cvss_score,
                severity=vuln.severity,
                vendors=vuln.vendors,
                products=vuln.products,
                published_at=vuln.published_at
            )
            
            # Update database
            vuln.simple_title = summary['simple_title']
            vuln.simple_description = summary['simple_description']
            vuln.llm_processed = True
            vuln.llm_processed_at = datetime.now(timezone.utc)
            
            session.commit()
            
            print("✅")
            print(f"  Title: {summary['simple_title']}")
            print(f"  Desc:  {summary['simple_description'][:80]}...")
            print()
            
            processed += 1
            
        except Exception as e:
            print(f"❌ Error: {e}")
            errors += 1
            session.rollback()
    
    print()
    print(f"✅ Processed: {processed}")
    if errors:
        print(f"❌ Errors: {errors}")


def main():
    parser = argparse.ArgumentParser(description="Process CVEs with LLM")
    parser.add_argument("--cve", help="Process specific CVE ID")
    parser.add_argument("--limit", type=int, help="Limit number of CVEs to process")
    parser.add_argument("--all", action="store_true", help="Process all unprocessed CVEs")
    parser.add_argument("--reprocess", action="store_true", help="Reprocess all CVEs (including already processed)")
    parser.add_argument("--model", default="llama3.2:3b", help="Ollama model to use")
    
    args = parser.parse_args()
    
    if not any([args.cve, args.limit, args.all, args.reprocess]):
        parser.print_help()
        return
    
    session = SessionLocal()
    
    try:
        process_vulnerabilities(
            session=session,
            cve_id=args.cve,
            limit=args.limit,
            reprocess=args.reprocess
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
