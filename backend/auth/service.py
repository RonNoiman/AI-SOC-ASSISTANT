import os
import hashlib
import secrets
from datetime import datetime, timedelta

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database.models import User, PasswordResetToken

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
PASSWORD_RESET_EXPIRE_MINUTES = 15

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
        to_encode = {k: str(v) for k, v in data.items()}
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> dict | None:
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            return None

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create_user(db: Session, email: str, password: str, full_name: str) -> User:
        user = User(
            email=email,
            hashed_password=AuthService.hash_password(password),
            full_name=full_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_password(db: Session, user: User, password: str) -> User:
        user.hashed_password = AuthService.hash_password(password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def _hash_reset_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def create_password_reset_token(db: Session, user: User) -> str:
        now = datetime.utcnow()
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        ).update({"used_at": now}, synchronize_session=False)

        raw_token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=AuthService._hash_reset_token(raw_token),
            expires_at=now + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES),
        )
        db.add(reset_token)
        db.commit()
        return raw_token

    @staticmethod
    def get_valid_password_reset_token(db: Session, token: str) -> PasswordResetToken | None:
        token_hash = AuthService._hash_reset_token(token)
        reset_token = (
            db.query(PasswordResetToken)
            .filter(PasswordResetToken.token_hash == token_hash)
            .first()
        )
        if not reset_token:
            return None
        if reset_token.used_at is not None:
            return None
        if reset_token.expires_at < datetime.utcnow():
            return None
        return reset_token

    @staticmethod
    def reset_password_with_token(db: Session, token: str, new_password: str) -> User | None:
        reset_token = AuthService.get_valid_password_reset_token(db, token)
        if not reset_token:
            return None

        user = reset_token.user
        user.hashed_password = AuthService.hash_password(new_password)
        reset_token.used_at = datetime.utcnow()
        db.add(user)
        db.add(reset_token)
        db.commit()
        db.refresh(user)
        return user
