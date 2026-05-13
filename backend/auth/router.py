import os

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database.connection import get_db
from auth.service import AuthService
from auth.middleware import get_current_user
from database.models import User

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str | None
    role: str

    class Config:
        from_attributes = True


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    if AuthService.get_user_by_email(db, body.email):
        AuthService.log_security_event(
            db,
            event_type="register_attempt",
            status="failed",
            email=body.email,
            ip_address=request.client.host if request.client else None,
            details="Email already registered",
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    password_error = AuthService.validate_password_strength(body.password)
    if password_error:
        AuthService.log_security_event(
            db,
            event_type="register_attempt",
            status="failed",
            email=body.email,
            ip_address=request.client.host if request.client else None,
            details=password_error,
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=password_error)

    user = AuthService.create_user(db, body.email, body.password, body.full_name)
    AuthService.log_security_event(
        db,
        event_type="register_attempt",
        status="success",
        email=user.email,
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    token = AuthService.create_access_token({"sub": user.id})
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = AuthService.get_user_by_email(db, body.email)
    if not user:
        AuthService.log_security_event(
            db,
            event_type="login_attempt",
            status="failed",
            email=body.email,
            ip_address=request.client.host if request.client else None,
            details="Unknown email",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if AuthService.is_user_locked(user):
        AuthService.log_security_event(
            db,
            event_type="login_attempt",
            status="blocked",
            email=user.email,
            user_id=user.id,
            ip_address=request.client.host if request.client else None,
            details="Account currently locked",
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account locked after too many failed login attempts. Try again later.",
        )

    if not AuthService.verify_password(body.password, user.hashed_password):
        _, locked = AuthService.register_failed_login(db, user)
        detail = "Invalid credentials"
        if locked:
            detail = "Account locked after 5 failed login attempts. Try again in 15 minutes."
        AuthService.log_security_event(
            db,
            event_type="login_attempt",
            status="locked" if locked else "failed",
            email=user.email,
            user_id=user.id,
            ip_address=request.client.host if request.client else None,
            details=detail,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

    AuthService.reset_login_attempts(db, user)
    AuthService.log_security_event(
        db,
        event_type="login_attempt",
        status="success",
        email=user.email,
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )

    token = AuthService.create_access_token({"sub": user.id})
    return TokenResponse(access_token=token)


PASSWORD_RESET_TOKEN_MODE = os.getenv("PASSWORD_RESET_TOKEN_MODE", "console")


@router.post("/forgot-password/request")
async def forgot_password_request(body: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    user = AuthService.get_user_by_email(db, body.email)
    if user:
        token = AuthService.create_password_reset_token(db, user)
        if PASSWORD_RESET_TOKEN_MODE == "console":
            print(f"Password reset token for {user.email}: {token}")
        AuthService.log_security_event(
            db,
            event_type="password_reset_request",
            status="success",
            email=user.email,
            user_id=user.id,
            ip_address=request.client.host if request.client else None,
        )
    else:
        AuthService.log_security_event(
            db,
            event_type="password_reset_request",
            status="ignored",
            email=body.email,
            ip_address=request.client.host if request.client else None,
            details="No matching account",
        )

    return {"detail": "If that account exists, a password reset token has been issued."}


@router.post("/forgot-password/confirm")
async def forgot_password_confirm(body: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    password_error = AuthService.validate_password_strength(body.new_password)
    if password_error:
        AuthService.log_security_event(
            db,
            event_type="password_reset_confirm",
            status="failed",
            ip_address=request.client.host if request.client else None,
            details=password_error,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=password_error,
        )

    user = AuthService.reset_password_with_token(db, body.token, body.new_password)
    if not user:
        AuthService.log_security_event(
            db,
            event_type="password_reset_confirm",
            status="failed",
            ip_address=request.client.host if request.client else None,
            details="Invalid or expired reset token",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    AuthService.log_security_event(
        db,
        event_type="password_reset_confirm",
        status="success",
        email=user.email,
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return {"detail": "Password updated successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user
