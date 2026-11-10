from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import (
    COOKIE_NAME,
    create_access_token,
    get_current_user,
    verify_password,
)
from app.config import AUTH_COOKIE_SECURE, AUTH_TOKEN_EXPIRE_HOURS
from app.database import get_db
from app.models import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(
    data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    username = data.username.strip().lower()

    user = db.scalar(
        select(User).where(User.username == username)
    )

    if (
        user is None
        or not user.is_active
        or not verify_password(data.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
        )

    token = create_access_token(user.id)

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=int(timedelta(hours=AUTH_TOKEN_EXPIRE_HOURS).total_seconds()),
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )

    return {"username": user.username}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key=COOKIE_NAME,
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    return {"message": "Logged out successfully."}


@router.get("/me")
def current_account(user: User = Depends(get_current_user)):
    return {"username": user.username}
