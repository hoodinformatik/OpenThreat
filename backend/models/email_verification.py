"""
Email verification model for user email confirmation.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta
import secrets
import string

from backend.database import Base


class EmailVerification(Base):
    """
    Email verification codes for user registration and email changes.
    """
    __tablename__ = "email_verifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    code = Column(String(6), nullable=False)
    
    # Type: 'registration' or 'email_change'
    verification_type = Column(String(20), nullable=False)
    
    # Status
    is_used = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", backref="email_verifications")
    
    @staticmethod
    def generate_code() -> str:
        """Generate a 6-digit verification code."""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    @staticmethod
    def get_expiry_time() -> datetime:
        """Get expiry time (15 minutes from now)."""
        return datetime.now(timezone.utc) + timedelta(minutes=15)
    
    def is_expired(self) -> bool:
        """Check if code is expired."""
        return datetime.now(timezone.utc) > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if code is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired()
