"""
Authentication endpoints for user registration, login, and management.
Integrates with Supabase Auth for secure user authentication.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from loguru import logger
from typing import Dict, Any

from app.schemas.auth import (
    UserSignup,
    UserLogin,
    UserLoginResponse,
    PasswordReset,
    PasswordChange,
    UserProfile,
    UserProfileUpdate,
    MessageResponse,
    TokenRefresh,
    TokenResponse
)
from app.core.security import get_current_user
from app.db.supabase import get_supabase_client
from supabase import Client

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserSignup, supabase: Client = Depends(get_supabase_client)):
    """
    Register a new user account.
    
    Creates a new user in Supabase Auth and sends verification email.
    """
    try:
        # Sign up user with Supabase Auth
        response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "full_name": user_data.full_name,
                    "phone": user_data.phone,
                    **user_data.metadata
                }
            }
        })
        
        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account"
            )
        
        logger.info(f"New user registered: {user_data.email}")
        
        return MessageResponse(
            message="Account created successfully",
            detail="Please check your email to verify your account"
        )
        
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=UserLoginResponse)
async def login(credentials: UserLogin, supabase: Client = Depends(get_supabase_client)):
    """
    Authenticate user and return access token.
    
    Validates credentials against Supabase Auth and returns JWT tokens.
    """
    try:
        # Sign in with Supabase Auth
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        
        if response.user is None or response.session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        logger.info(f"User logged in: {credentials.email}")
        
        return UserLoginResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            token_type="bearer",
            expires_in=response.session.expires_in or 3600,
            user={
                "id": response.user.id,
                "email": response.user.email,
                "email_verified": response.user.email_confirmed_at is not None,
                "metadata": response.user.user_metadata
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Logout current user and invalidate session.
    
    Requires valid authentication token.
    """
    try:
        supabase.auth.sign_out()
        logger.info(f"User logged out: {current_user.get('email')}")
        
        return MessageResponse(
            message="Logged out successfully"
        )
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    supabase: Client = Depends(get_supabase_client)
):
    """
    Refresh access token using refresh token.
    
    Returns a new access token without requiring re-authentication.
    """
    try:
        response = supabase.auth.refresh_session(token_data.refresh_token)
        
        if response.session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        return TokenResponse(
            access_token=response.session.access_token,
            token_type="bearer",
            expires_in=response.session.expires_in or 3600
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )


@router.post("/password-reset", response_model=MessageResponse)
async def request_password_reset(
    reset_data: PasswordReset,
    supabase: Client = Depends(get_supabase_client)
):
    """
    Request password reset email.
    
    Sends password reset link to user's email address.
    """
    try:
        supabase.auth.reset_password_email(reset_data.email)
        
        logger.info(f"Password reset requested for: {reset_data.email}")
        
        return MessageResponse(
            message="Password reset email sent",
            detail="Please check your email for reset instructions"
        )
        
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        # Return success even on error to prevent email enumeration
        return MessageResponse(
            message="If the email exists, a reset link has been sent"
        )


@router.post("/password-change", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Change password for authenticated user.
    
    Requires current password verification.
    """
    try:
        # Update password
        response = supabase.auth.update_user({
            "password": password_data.new_password
        })
        
        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update password"
            )
        
        logger.info(f"Password changed for user: {current_user.get('email')}")
        
        return MessageResponse(
            message="Password updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to change password"
        )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get current user's profile information.
    
    Returns authenticated user's profile data.
    """
    try:
        user = supabase.auth.get_user()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        metadata = user.user.user_metadata or {}
        
        return UserProfile(
            id=user.user.id,
            email=user.user.email,
            full_name=metadata.get("full_name"),
            phone=metadata.get("phone"),
            email_verified=user.user.email_confirmed_at is not None,
            phone_verified=user.user.phone_confirmed_at is not None,
            avatar_url=metadata.get("avatar_url"),
            metadata=metadata,
            created_at=user.user.created_at,
            updated_at=user.user.updated_at,
            last_sign_in_at=user.user.last_sign_in_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.patch("/me", response_model=UserProfile)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Update current user's profile.
    
    Allows updating user metadata and profile information.
    """
    try:
        update_data = {}
        
        if profile_data.metadata:
            update_data["data"] = profile_data.metadata
        else:
            update_data["data"] = {}
        
        if profile_data.full_name is not None:
            update_data["data"]["full_name"] = profile_data.full_name
        if profile_data.phone is not None:
            update_data["data"]["phone"] = profile_data.phone
        if profile_data.avatar_url is not None:
            update_data["data"]["avatar_url"] = profile_data.avatar_url
        
        response = supabase.auth.update_user(update_data)
        
        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update profile"
            )
        
        logger.info(f"Profile updated for user: {current_user.get('email')}")
        
        metadata = response.user.user_metadata or {}
        
        return UserProfile(
            id=response.user.id,
            email=response.user.email,
            full_name=metadata.get("full_name"),
            phone=metadata.get("phone"),
            email_verified=response.user.email_confirmed_at is not None,
            phone_verified=response.user.phone_confirmed_at is not None,
            avatar_url=metadata.get("avatar_url"),
            metadata=metadata,
            created_at=response.user.created_at,
            updated_at=response.user.updated_at,
            last_sign_in_at=response.user.last_sign_in_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update profile"
        )