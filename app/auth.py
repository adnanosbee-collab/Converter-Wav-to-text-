from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import (
    AUTH_SECRET,
    AUTH_TOKEN_EXPIRE_HOURS,
)
from app.database import get_db
from app.models import User


password_hash = PasswordHash.recommended()

COOKIE_NAME = "wav_session"


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(user_id: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=AUTH_TOKEN_EXPIRE_HOURS
    )

    return jwt.encode(
        {"sub": user_id, "exp": expires_at},
        AUTH_SECRET,
        algorithm="HS256",
    )


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    token = request.cookies.get(COOKIE_NAME)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please log in.",
        )

    try:
        payload = jwt.decode(
            token,
            AUTH_SECRET,
            algorithms=["HS256"],
        )
        user_id = payload.get("sub")

        if not user_id:
            raise ValueError("Missing user ID")

    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired login session.",
        )

    user = db.get(User, user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is unavailable.",
        )

    return user
