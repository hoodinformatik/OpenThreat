"""
Simple script to query the database and show statistics.
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
os.environ["DATABASE_URL"] = f"sqlite:///{PROJECT_ROOT}/openthreat.db"

from backend.database import SessionLocal
from backend.models import Vulnerability, IngestionRun
from sqlalchemy import func

db = SessionLocal()

print("""
╔══════════════════════════════════════════════════════════╗
║              OpenThreat Database Statistics              ║
╚══════════════════════════════════════════════════════════╝
""")

# Total vulnerabilities
total = db.query(func.count(Vulnerability.id)).scalar()
print(f"📊 Total Vulnerabilities: {total:,}")

# Exploited vulnerabilities
exploited = db.query(func.count(Vulnerability.id)).filter(
    Vulnerability.exploited_in_the_wild == True
).scalar()
print(f"🔥 Exploited in the Wild: {exploited:,}")

# By severity
print("\n📈 By Severity:")
severities = db.query(
    Vulnerability.severity,
    func.count(Vulnerability.id)
).group_by(Vulnerability.severity).all()

for severity, count in sorted(severities, key=lambda x: x[1], reverse=True):
    print(f"   {severity or 'UNKNOWN':12} {count:,}")

# Top 10 by priority score
print("\n🎯 Top 10 by Priority Score:")
top_vulns = db.query(Vulnerability).order_by(
    Vulnerability.priority_score.desc()
).limit(10).all()

for i, vuln in enumerate(top_vulns, 1):
    print(f"   {i:2}. {vuln.cve_id:15} {vuln.priority_score:.3f} - {vuln.title[:50]}")

# Recent ingestion runs
print("\n📥 Recent Ingestion Runs:")
runs = db.query(IngestionRun).order_by(
    IngestionRun.started_at.desc()
).limit(5).all()

for run in runs:
    status_emoji = "✅" if run.status == "success" else "❌"
    print(f"   {status_emoji} {run.source:20} {run.started_at.strftime('%Y-%m-%d %H:%M')} - Inserted: {run.records_inserted:,}, Updated: {run.records_updated:,}")

print()
db.close()
