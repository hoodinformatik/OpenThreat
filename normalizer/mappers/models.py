
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, ValidationInfo, field_validator, ConfigDict, constr


CVEId = constr(pattern=r"^CVE-\d{4}-\d{4,}$")
CWEId = constr(pattern=r"^CWE-\d+$")


class Reference(BaseModel):
    url: HttpUrl
    type: Literal["advisory", "patch", "blog", "exploit", "vendor", "nvd", "other"] = "other"


class Vulnerability(BaseModel):
    """Normalized vulnerability record used across all sources."""
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    cve_id: CVEId
    title: str
    description: Optional[str] = None
    cvss_score: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    cvss_vector: Optional[str] = None
    severity: Optional[Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]] = "UNKNOWN"

    published_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None

    exploited_in_the_wild: bool = False
    cisa_due_date: Optional[date] = None

    cwe_ids: List[CWEId] = Field(default_factory=list)
    affected_products: List[str] = Field(default_factory=list)
    references: List[Reference] = Field(default_factory=list)

    attck_techniques: List[str] = Field(default_factory=list)
    source_tags: List[str] = Field(default_factory=list)


    @field_validator("published_at", "modified_at", mode="before")
    @classmethod
    def _coerce_datetime(cls, v: object, info: ValidationInfo) -> Optional[datetime]:
        if v in (None, "", 0):
            return None
        if isinstance(v, datetime):
            return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        if isinstance(v, date):
            return datetime(v.year, v.month, v.day, tzinfo=timezone.utc)
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return None
            try:
                if len(s) == 10 and s.count("-") == 2:
                    y, m, d = map(int, s.split("-"))
                    return datetime(y, m, d, tzinfo=timezone.utc)
                from datetime import datetime as _dt
                for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
                    try:
                        return _dt.strptime(s, fmt).replace(tzinfo=timezone.utc)
                    except Exception:
                        pass
                # Try fromisoformat last
                dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except Exception:
                return None
        return None


class Technique(BaseModel):
    id: str  # STIX id
    name: str
    external_id: Optional[str] = None  # e.g., T1190
    description: Optional[str] = None
    revoked: bool = False
    deprecated: bool = False
    source_tags: List[str] = Field(default_factory=lambda: ["MITRE"])


class IOC(BaseModel):
    indicator: str
    type: Literal["url", "domain", "ip", "sha256", "md5", "sha1", "other"] = "other"
    status: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    threat: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    reporter: Optional[str] = None
    source_tags: List[str] = Field(default_factory=list)

    @field_validator("first_seen", "last_seen", mode="before")
    @classmethod
    def _dt(cls, v):
        if not v:
            return None
        try:
            from datetime import datetime as _dt
            return _dt.fromisoformat(str(v).replace("Z", "+00:00"))
        except Exception:
            return None
