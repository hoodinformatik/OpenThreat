"""
Authentication endpoints for user registration, login, and management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import logging

from ..database import get_db
from ..models import User, UserRole, EmailVerification
from ..schemas.auth import (
    UserCreate, UserLogin, Token, UserResponse,
    UserUpdate, PasswordChange, UserRoleUpdate
)
from ..schemas.email_verification import (
    EmailVerificationRequest, EmailVerificationConfirm,
    EmailChangeRequest, EmailChangeConfirm, VerificationResponse
)
from ..utils.auth import (
    verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..dependencies.auth import get_current_user, require_admin
from ..services.email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    **Requirements:**
    - Unique email and username
    - Strong password (8+ chars, uppercase, lowercase, digit)
    
    **Default role:** VIEWER
    
    **Returns:**
    - User profile information
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Check if email was verified
    email_verified = db.query(EmailVerification).filter(
        EmailVerification.email == user_data.email,
        EmailVerification.verification_type == "registration",
        EmailVerification.is_used == True
    ).first()
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        role=UserRole.VIEWER,  # Default role
        is_active=True,
        is_verified=bool(email_verified)  # Set to True if email was verified
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"New user registered: {new_user.username} ({new_user.email})")
    
    return new_user


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login with username and password.
    
    **Returns:**
    - JWT access token
    - Token type (bearer)
    - Expiration time in seconds
    
    **Security:**
    - Account lockout after 5 failed attempts (30 minutes)
    - Failed login attempts are tracked
    """
    # Get user by username
    user = db.query(User).filter(User.username == credentials.username).first()
    
    if not user:
        logger.warning(f"Login attempt with non-existent username: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        logger.warning(f"Login attempt on locked account: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is locked until {user.locked_until.isoformat()}. Too many failed login attempts."
        )
    
    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        # Increment failed login attempts
        user.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
            logger.warning(f"Account locked due to failed attempts: {user.username}")
        
        db.commit()
        
        logger.warning(f"Failed login attempt for user: {user.username} (attempt {user.failed_login_attempts})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login attempt on inactive account: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact administrator."
        )
    
    # Reset failed login attempts on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    
    # Create access token
    token_data = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value
    }
    
    access_token = create_access_token(token_data)
    
    logger.info(f"User logged in: {user.username}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile.
    
    **Requires:** Valid JWT token
    
    **Returns:**
    - User profile information
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile.
    
    **Requires:** Valid JWT token
    
    **Updatable fields:**
    - email (must be unique)
    
    **Returns:**
    - Updated user profile
    """
    # Update email if provided
    if user_update.email and user_update.email != current_user.email:
        # Check if new email already exists
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        current_user.email = user_update.email
        current_user.is_verified = False  # Re-verify email
    
    current_user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"User profile updated: {current_user.username}")
    
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password.
    
    **Requires:** Valid JWT token
    
    **Requirements:**
    - Correct old password
    - Strong new password (8+ chars, uppercase, lowercase, digit)
    
    **Returns:**
    - Success message
    """
    # Verify old password
    if not verify_password(password_data.old_password, current_user.hashed_password):
        logger.warning(f"Failed password change attempt: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    logger.info(f"Password changed successfully: {current_user.username}")
    
    return {"message": "Password changed successfully"}


@router.delete("/me")
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete own user account.
    
    **Requires:** Valid JWT token
    
    **Warning:** This action is permanent and cannot be undone!
    
    **Returns:**
    - Success message
    """
    username = current_user.username
    
    # Delete user account
    db.delete(current_user)
    db.commit()
    
    logger.info(f"User account deleted: {username}")
    
    return {"message": "Account deleted successfully"}


# Admin endpoints
@router.get("/users", response_model=list[UserResponse], dependencies=[Depends(require_admin)])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all users (Admin only).
    
    **Requires:** Admin role
    
    **Returns:**
    - List of user profiles
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.put("/users/{user_id}/role", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def update_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    db: Session = Depends(get_db)
):
    """
    Update user role (Admin only).
    
    **Requires:** Admin role
    
    **Available roles:**
    - VIEWER: Read-only access
    - ANALYST: Can create and update
    - ADMIN: Full access
    
    **Returns:**
    - Updated user profile
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.role = role_update.role
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    
    logger.info(f"User role updated: {user.username} -> {role_update.role.value}")
    
    return user


@router.put("/users/{user_id}/deactivate", dependencies=[Depends(require_admin)])
async def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    """
    Deactivate user account (Admin only).
    
    **Requires:** Admin role
    
    **Returns:**
    - Success message
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = False
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    logger.info(f"User deactivated: {user.username}")
    
    return {"message": f"User {user.username} deactivated successfully"}


@router.put("/users/{user_id}/activate", dependencies=[Depends(require_admin)])
async def activate_user(user_id: int, db: Session = Depends(get_db)):
    """
    Activate user account (Admin only).
    
    **Requires:** Admin role
    
    **Returns:**
    - Success message
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    user.failed_login_attempts = 0
    user.locked_until = None
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    logger.info(f"User activated: {user.username}")
    
    return {"message": f"User {user.username} activated successfully"}


# ============================================================================
# EMAIL VERIFICATION ENDPOINTS
# ============================================================================

@router.post("/send-verification-code", response_model=VerificationResponse)
async def send_verification_code(
    request: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Send verification code to email for registration.
    
    **Public endpoint** - No authentication required.
    
    **Use case:** Before registration, verify email ownership.
    
    **Returns:**
    - Confirmation message
    - Email address
    - Expiry time (15 minutes)
    """
    # Check if email is already registered
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate verification code
    code = EmailVerification.generate_code()
    expires_at = EmailVerification.get_expiry_time()
    
    # Store verification code
    verification = EmailVerification(
        user_id=None,  # No user yet
        email=request.email,
        code=code,
        verification_type="registration",
        expires_at=expires_at
    )
    
    db.add(verification)
    db.commit()
    
    # Send email
    await email_service.send_verification_code(
        email=request.email,
        code=code,
        verification_type="registration"
    )
    
    logger.info(f"Verification code sent to {request.email}")
    
    return VerificationResponse(
        message="Verification code sent successfully",
        email=request.email,
        expires_in_minutes=15
    )


@router.post("/verify-email", response_model=dict)
async def verify_email(
    request: EmailVerificationConfirm,
    db: Session = Depends(get_db)
):
    """
    Verify email with code (used during registration).
    
    **Public endpoint** - No authentication required.
    
    **Returns:**
    - Success message
    - Verification token (to be used in registration)
    """
    # Find verification code
    verification = db.query(EmailVerification).filter(
        EmailVerification.email == request.email,
        EmailVerification.code == request.code,
        EmailVerification.verification_type == "registration",
        EmailVerification.is_used == False
    ).order_by(EmailVerification.created_at.desc()).first()
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    
    if verification.is_expired():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired"
        )
    
    # Mark as used
    verification.is_used = True
    verification.verified_at = datetime.now(timezone.utc)
    db.commit()
    
    logger.info(f"Email verified: {request.email}")
    
    return {
        "message": "Email verified successfully",
        "email": request.email,
        "verified": True
    }


@router.post("/request-email-change", response_model=VerificationResponse)
async def request_email_change(
    request: EmailChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request email change - sends verification code to NEW email.
    
    **Requires:** Authentication
    
    **Returns:**
    - Confirmation message
    - New email address
    - Expiry time (15 minutes)
    """
    # Check if new email is already in use
    existing_user = db.query(User).filter(
        User.email == request.new_email,
        User.id != current_user.id
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already in use"
        )
    
    # Generate verification code
    code = EmailVerification.generate_code()
    expires_at = EmailVerification.get_expiry_time()
    
    # Store verification code
    verification = EmailVerification(
        user_id=current_user.id,
        email=request.new_email,
        code=code,
        verification_type="email_change",
        expires_at=expires_at
    )
    
    db.add(verification)
    db.commit()
    
    # Send email to NEW address
    await email_service.send_verification_code(
        email=request.new_email,
        code=code,
        verification_type="email_change"
    )
    
    logger.info(f"Email change requested by user {current_user.username}: {request.new_email}")
    
    return VerificationResponse(
        message="Verification code sent to new email address",
        email=request.new_email,
        expires_in_minutes=15
    )


@router.post("/confirm-email-change", response_model=dict)
async def confirm_email_change(
    request: EmailChangeConfirm,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirm email change with verification code.
    
    **Requires:** Authentication
    
    **Returns:**
    - Success message
    - New email address
    """
    # Find verification code
    verification = db.query(EmailVerification).filter(
        EmailVerification.user_id == current_user.id,
        EmailVerification.email == request.new_email,
        EmailVerification.code == request.code,
        EmailVerification.verification_type == "email_change",
        EmailVerification.is_used == False
    ).order_by(EmailVerification.created_at.desc()).first()
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    
    if verification.is_expired():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired"
        )
    
    # Update user email
    current_user.email = request.new_email
    current_user.is_verified = True
    current_user.updated_at = datetime.now(timezone.utc)
    
    # Mark verification as used
    verification.is_used = True
    verification.verified_at = datetime.now(timezone.utc)
    
    db.commit()
    
    logger.info(f"Email changed for user {current_user.username}: {request.new_email}")
    
    return {
        "message": "Email changed successfully",
        "new_email": request.new_email
    }
