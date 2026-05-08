import os

from fastapi import APIRouter, Depends, HTTPException, status
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
async def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if AuthService.get_user_by_email(db, body.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = AuthService.create_user(db, body.email, body.password, body.full_name)
    token = AuthService.create_access_token({"sub": user.id})
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = AuthService.get_user_by_email(db, body.email)
    if not user or not AuthService.verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = AuthService.create_access_token({"sub": user.id})
    return TokenResponse(access_token=token)


PASSWORD_RESET_TOKEN_MODE = os.getenv("PASSWORD_RESET_TOKEN_MODE", "console")


@router.post("/forgot-password/request")
async def forgot_password_request(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = AuthService.get_user_by_email(db, body.email)
    if user:
        token = AuthService.create_password_reset_token(db, user)
        if PASSWORD_RESET_TOKEN_MODE == "console":
            print(f"Password reset token for {user.email}: {token}")

    return {"detail": "If that account exists, a password reset token has been issued."}


@router.post("/forgot-password/confirm")
async def forgot_password_confirm(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    if len(body.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters",
        )

    user = AuthService.reset_password_with_token(db, body.token, body.new_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    return {"detail": "Password updated successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user
