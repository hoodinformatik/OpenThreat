"""
Pydantic schemas for email verification.
"""

from pydantic import BaseModel, EmailStr, Field


class EmailVerificationRequest(BaseModel):
    """Request to send verification code."""

    email: EmailStr


class EmailVerificationConfirm(BaseModel):
    """Confirm email with verification code."""

    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class EmailChangeRequest(BaseModel):
    """Request to change email address."""

    new_email: EmailStr


class EmailChangeConfirm(BaseModel):
    """Confirm email change with verification code."""

    new_email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class VerificationResponse(BaseModel):
    """Response after sending verification code."""

    message: str
    email: str
    expires_in_minutes: int = 15
