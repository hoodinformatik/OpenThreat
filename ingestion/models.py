
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

    model_config = ConfigDict(extra="forbid", frozen=False, str_strip_whitespace=True)

    cve_id: CVEId = Field(..., description="Canonical CVE identifier")
    title: str = Field(..., min_length=3)
    description: Optional[str] = Field(default=None, max_length=20_000)
    cvss_score: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    cvss_vector: Optional[str] = None
    severity: Optional[Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]] = "UNKNOWN"

    published_at: Optional[datetime] = Field(default=None, description="First seen/published time (UTC)")
    modified_at: Optional[datetime] = Field(default=None, description="Last modified time (UTC)")

    exploited_in_the_wild: bool = Field(default=False)
    cisa_due_date: Optional[date] = None

    cwe_ids: List[CWEId] = Field(default_factory=list)
    affected_products: List[str] = Field(default_factory=list, description="List of strings vendor:product[:version]")
    references: List[Reference] = Field(default_factory=list)

    attck_techniques: List[str] = Field(default_factory=list)
    source_tags: List[str] = Field(default_factory=list)

    score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Computed priority score (0..1)")

    @field_validator("published_at", "modified_at", mode="before")
    @classmethod
    def _coerce_datetime(cls, v: object, info: ValidationInfo) -> Optional[datetime]:
        if v in (None, "", 0):
            return None
        if isinstance(v, datetime):
            # Ensure timezone-aware UTC
            return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        if isinstance(v, date):
            # Convert date to midnight UTC datetime
            return datetime(v.year, v.month, v.day, tzinfo=timezone.utc)
        if isinstance(v, str):
            # Try ISO strings; if only a date string, set midnight UTC
            try:
                if len(v) == 10 and v.count("-") == 2:
                    y, m, d = map(int, v.split("-"))
                    return datetime(y, m, d, tzinfo=timezone.utc)
                # fallback to fromisoformat (may not parse Z)
                try:
                    dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
                except Exception:
                    # last resort: parse YYYY-MM-DDTHH:MM:SS.mmmZ variants
                    from datetime import datetime as _dt
                    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
                        try:
                            dt = _dt.strptime(v, fmt).replace(tzinfo=timezone.utc)
                            break
                        except Exception:
                            dt = None
                    if dt is None:
                        raise
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                raise
        return None

    @field_validator("affected_products", mode="before")
    @classmethod
    def _clean_products(cls, v: object) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        return []


class CisaKevItem(BaseModel):
    cveID: CVEId
    vendorProject: Optional[str] = None
    product: Optional[str] = None
    vulnerabilityName: Optional[str] = None
    dateAdded: Optional[str] = None
    shortDescription: Optional[str] = None
    requiredAction: Optional[str] = None
    dueDate: Optional[str] = None
    knownRansomwareCampaignUse: Optional[str] = None
    notes: Optional[str] = None
    cwes: List[CWEId] = Field(default_factory=list)

    def to_vulnerability(self) -> Vulnerability:
        # Build references from notes (semicolon separated URLs)
        refs: List[Reference] = []
        if self.notes:
            for raw in self.notes.split(";"):
                url = raw.strip()
                if not url:
                    continue
                rtype: Literal["advisory", "patch", "blog", "exploit", "vendor", "nvd", "other"] = "other"
                if "nvd.nist.gov" in url:
                    rtype = "nvd"
                elif "advisories" in url or "advisory" in url:
                    rtype = "advisory"
                elif "patch" in url or "kb" in url:
                    rtype = "patch"
                elif "blog" in url:
                    rtype = "blog"
                elif "exploit" in url or "poc" in url:
                    rtype = "exploit"
                elif "3ds.com" in url or "vendor" in url:
                    rtype = "vendor"
                try:
                    refs.append(Reference(url=url, type=rtype))
                except Exception:
                    # Skip invalid URLs silently; upstream feed sometimes has typos
                    pass

        affected = []
        if self.vendorProject or self.product:
            vendor = (self.vendorProject or "").strip()
            product = (self.product or "").strip()
            label = ":".join([x for x in (vendor, product) if x])
            if label:
                affected.append(label)

        v = Vulnerability(
            cve_id=self.cveID,
            title=self.vulnerabilityName or self.cveID,
            description=self.shortDescription,
            published_at=self.dateAdded,  # validator converts to UTC datetime
            cisa_due_date=(
                date.fromisoformat(self.dueDate) if self.dueDate and len(self.dueDate) == 10 else None
            ),
            exploited_in_the_wild=True,
            cwe_ids=self.cwes or [],
            affected_products=affected,
            references=refs,
            source_tags=["CISA"],
        )
        return v


class CisaKevFeed(BaseModel):
    title: str
    catalogVersion: str
    dateReleased: str
    count: int
    vulnerabilities: List[CisaKevItem]

    @field_validator("count")
    @classmethod
    def _non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("count must be non-negative")
        return v

    def to_vulnerabilities(self) -> List[Vulnerability]:
        return [item.to_vulnerability() for item in self.vulnerabilities]
