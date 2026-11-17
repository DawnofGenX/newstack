"""Routes: /health, /token, /me."""

from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from .auth import decode_token, issue_token, load_users

router = APIRouter()

oauth2 = OAuth2PasswordBearer(tokenUrl="/token", auto_error=False)


def current_user(token: str | None = Depends(oauth2)) -> dict:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = decode_token(token)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return claims


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/token")
async def login(request: Request) -> dict[str, str]:
    content_type = request.headers.get("content-type", "")
    username = None
    password = None
    if "application/json" in content_type:
        try:
            data = await request.json()
        except (ValueError, TypeError):
            data = {}
        if isinstance(data, dict):
            username = data.get("username")
            password = data.get("password")
    else:
        try:
            form = await request.form()
        except (ValueError, TypeError, RuntimeError):
            form = {}
        username = form.get("username") if hasattr(form, "get") else username
        password = form.get("password") if hasattr(form, "get") else password

    users = load_users()
    if not isinstance(username, str) or not isinstance(password, str) or users.get(username) != password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="bad credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": issue_token(username), "token_type": "bearer"}


@router.get("/me")
def me(claims: Annotated[dict, Depends(current_user)]) -> dict:
    return {"user": claims.get("sub"), "claims": claims}