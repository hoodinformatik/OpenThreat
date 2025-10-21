"""
Waitlist endpoints for beta launch signups with email verification.
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import WaitlistEntry
from ..schemas.waitlist import WaitlistJoin, WaitlistResponse
from ..services.email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter()


def generate_verification_token() -> str:
    """Generate a secure random token for email verification."""
    return secrets.token_urlsafe(32)


@router.post("/join", status_code=status.HTTP_201_CREATED)
async def join_waitlist(data: WaitlistJoin, db: Session = Depends(get_db)):
    """
    Join the waitlist - sends verification email with link.

    **Returns:**
    - Success message
    """
    # Check if email already exists
    existing_entry = (
        db.query(WaitlistEntry).filter(WaitlistEntry.email == data.email).first()
    )

    if existing_entry:
        if existing_entry.is_verified:
            return {
                "message": "This email is already on the waitlist!",
                "already_verified": True,
            }
        else:
            # Resend verification email
            verification_token = generate_verification_token()
            token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

            existing_entry.verification_token = verification_token
            existing_entry.token_expires_at = token_expires_at
            db.commit()

            logger.info(f"Resending verification email to: {data.email}")
    else:
        # Create new entry
        verification_token = generate_verification_token()
        token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        new_entry = WaitlistEntry(
            email=data.email,
            verification_token=verification_token,
            token_expires_at=token_expires_at,
            is_verified=False,
        )
        db.add(new_entry)
        db.commit()

        logger.info(f"New waitlist signup: {data.email}")

    # Send verification email
    try:
        verification_link = (
            f"https://open-threats.com/auth/verify?token={verification_token}"
        )

        await email_service.send_email(
            to_email=data.email,
            subject="🚀 Verify Your OpenThreat Waitlist Signup",
            html_content=f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9fafb;">
                    <div style="background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <h1 style="color: #2563eb; margin: 0;">🛡️ OpenThreat</h1>
                            <p style="color: #6b7280; font-size: 16px; margin-top: 8px;">Democratizing Threat Intelligence</p>
                        </div>

                        <div style="margin-bottom: 30px;">
                            <h2 style="color: #1f2937; margin-top: 0;">Verify Your Email</h2>
                            <p style="color: #4b5563; font-size: 16px; line-height: 1.6;">
                                Thanks for joining the OpenThreat waitlist! Please verify your email address by clicking the button below:
                            </p>
                        </div>

                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{verification_link}"
                               style="display: inline-block; background: #2563eb; color: white; padding: 14px 32px;
                                      text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                                Verify Email Address
                            </a>
                        </div>

                        <div style="background: #eff6ff; border-left: 4px solid #2563eb; padding: 16px; margin: 30px 0; border-radius: 4px;">
                            <p style="color: #1e40af; margin: 0; font-size: 14px; line-height: 1.6;">
                                <strong>Why OpenThreat?</strong><br>
                                • Real-time CVE tracking from CISA, NVD, BSI-CERT<br>
                                • AI-powered threat analysis with MITRE ATT&CK<br>
                                • Privacy-first approach - no tracking<br>
                                • 100% Open Source
                            </p>
                        </div>

                        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                            <p style="color: #9ca3af; font-size: 12px; margin: 0;">
                                This link expires in 24 hours. If you didn't request this, you can safely ignore this email.
                            </p>
                            <p style="color: #9ca3af; font-size: 12px; margin-top: 8px;">
                                Or copy this link: <span style="word-break: break-all;">{verification_link}</span>
                            </p>
                        </div>
                    </div>
                </body>
            </html>
            """,
            text_content=f"""
OpenThreat - Verify Your Email

Thanks for joining the OpenThreat waitlist!

Please verify your email address by clicking this link:
{verification_link}

Why OpenThreat?
• Real-time CVE tracking from CISA, NVD, BSI-CERT
• AI-powered threat analysis with MITRE ATT&CK mapping
• Privacy-first approach - no tracking
• 100% Open Source

This link expires in 24 hours.

If you didn't request this, you can safely ignore this email.
            """,
        )
        logger.info(f"Verification email sent to: {data.email}")
    except Exception as e:
        logger.error(f"Failed to send verification email to {data.email}: {e}")
        # Don't fail the request if email fails

    return {
        "message": "Verification email sent! Please check your inbox.",
        "already_verified": False,
    }


@router.get("/verify")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Verify email address via token from link.

    **Returns:**
    - Success message or error
    """
    # Find entry by token
    entry = (
        db.query(WaitlistEntry)
        .filter(WaitlistEntry.verification_token == token)
        .first()
    )

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid verification link."
        )

    if entry.is_verified:
        return {
            "message": "Email already verified!",
            "email": entry.email,
            "already_verified": True,
        }

    # Check if token expired
    if entry.token_expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link expired. Please request a new one.",
        )

    # Mark as verified
    entry.is_verified = True
    entry.verified_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(f"Waitlist entry verified: {entry.email}")

    return {
        "message": "Email verified successfully! You're on the waitlist.",
        "email": entry.email,
        "already_verified": False,
    }


@router.get("/count")
async def get_waitlist_count(db: Session = Depends(get_db)):
    """
    Get the current verified waitlist count (public endpoint).

    **Returns:**
    - Total number of verified people on the waitlist
    """
    count = db.query(WaitlistEntry).filter(WaitlistEntry.is_verified == True).count()
    return {"count": count}
