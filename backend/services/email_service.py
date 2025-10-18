"""
Email service for sending verification codes.
For development: Logs codes to console.
For production: Use SMTP or email service (SendGrid, AWS SES, etc.)
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending verification codes."""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.smtp_enabled = os.getenv("SMTP_ENABLED", "false").lower() == "true"
        
    async def send_verification_code(
        self,
        email: str,
        code: str,
        verification_type: str = "registration"
    ) -> bool:
        """
        Send verification code to email.
        
        Args:
            email: Recipient email address
            code: 6-digit verification code
            verification_type: 'registration' or 'email_change'
            
        Returns:
            True if sent successfully
        """
        subject = self._get_subject(verification_type)
        message = self._get_message(code, verification_type)
        
        if self.environment == "development" or not self.smtp_enabled:
            # Development mode: Log to console
            logger.info("=" * 60)
            logger.info(f"📧 EMAIL VERIFICATION CODE")
            logger.info(f"To: {email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Code: {code}")
            logger.info(f"Type: {verification_type}")
            logger.info(f"Message:\n{message}")
            logger.info("=" * 60)
            print(f"\n🔐 VERIFICATION CODE for {email}: {code}\n")
            return True
        else:
            # Production mode: Send actual email
            return await self._send_smtp_email(email, subject, message)
    
    def _get_subject(self, verification_type: str) -> str:
        """Get email subject based on verification type."""
        if verification_type == "registration":
            return "OpenThreat - Verify Your Email Address"
        elif verification_type == "email_change":
            return "OpenThreat - Confirm Email Change"
        return "OpenThreat - Verification Code"
    
    def _get_message(self, code: str, verification_type: str) -> str:
        """Get email message based on verification type."""
        if verification_type == "registration":
            return f"""
Welcome to OpenThreat!

Your verification code is: {code}

This code will expire in 15 minutes.

If you didn't create an account, please ignore this email.

Best regards,
OpenThreat Team
"""
        elif verification_type == "email_change":
            return f"""
Email Change Request

Your verification code is: {code}

This code will expire in 15 minutes.

If you didn't request this change, please secure your account immediately.

Best regards,
OpenThreat Team
"""
        return f"Your verification code is: {code}"
    
    async def _send_smtp_email(
        self,
        email: str,
        subject: str,
        message: str
    ) -> bool:
        """
        Send email via SMTP.
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_username = os.getenv("SMTP_USERNAME")
            smtp_password = os.getenv("SMTP_PASSWORD")
            from_email = os.getenv("SMTP_FROM_EMAIL", smtp_username)
            from_name = os.getenv("SMTP_FROM_NAME", "OpenThreat")
            
            if not smtp_username or not smtp_password:
                logger.error("SMTP credentials not configured")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


# Singleton instance
email_service = EmailService()
