"""
Pydantic schemas for waitlist functionality.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class WaitlistJoin(BaseModel):
    """Schema for joining the waitlist."""

    email: EmailStr


class WaitlistResponse(BaseModel):
    """Schema for waitlist entry response."""

    id: int
    email: str
    is_verified: bool
    created_at: datetime
    verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True
