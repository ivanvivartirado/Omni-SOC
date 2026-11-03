from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_session
from app.core.deps import client_ip, current_user
from app.core.security import (
    ACCESS_COOKIE,
    CSRF_COOKIE,
    REFRESH_COOKIE,
    create_token,
    decode_token,
    hash_password,
    needs_rehash,
    new_csrf_token,
    validate_password_strength,
    verify_password,
)
from app.models import User
from app.services import login_guard
from app.services.audit import audit

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=1, max_length=256)


class PasswordChangeIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=12, max_length=256)


def user_out(user: User) -> dict[str, object]:
    return {"id": user.id, "username": user.username, "full_name": user.full_name, "role": user.role}


def set_session_cookies(response: Response, user: User) -> None:
    settings = get_settings()
    access, access_exp = create_token(user.id, user.role, user.token_version, "access")
    refresh, refresh_exp = create_token(user.id, user.role, user.token_version, "refresh")
    common = {"secure": settings.cookie_secure, "samesite": "strict"}
    response.set_cookie(ACCESS_COOKIE, access, httponly=True, path="/api", expires=access_exp, **common)
    response.set_cookie(REFRESH_COOKIE, refresh, httponly=True, path="/api/auth", expires=refresh_exp, **common)
    response.set_cookie(CSRF_COOKIE, new_csrf_token(), httponly=False, path="/", expires=refresh_exp, **common)


def clear_session_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/api")
    response.delete_cookie(REFRESH_COOKIE, path="/api/auth")
    response.delete_cookie(CSRF_COOKIE, path="/")


@router.post("/login")
async def login(
    body: LoginIn, request: Request, response: Response, session: AsyncSession = Depends(get_session)
) -> dict[str, object]:
    settings = request.app.state.settings
    ip = client_ip(request)
    username = body.username.lower()

    wait = await login_guard.retry_after(session, username, ip, settings)
    if wait:
        await audit(session, request, "login_blocked", username=username, details={"retry_after": wait})
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Demasiados intentos fallidos. Espera antes de reintentar.",
            headers={"Retry-After": str(wait)},
        )

    user = await session.scalar(select(User).where(User.username == username))
    ok = verify_password(body.password, user.password_hash if user else None) and user is not None and user.is_active
    await login_guard.record_attempt(session, username, ip, ok)
    if not ok or user is None:
        await audit(session, request, "login_failed", username=username)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario o contraseña incorrectos")

    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(body.password)
    user.last_login_at = datetime.now(UTC)
    await audit(session, request, "login_success", user=user)
    set_session_cookies(response, user)
    return user_out(user)


@router.post("/refresh")
async def refresh(request: Request, response: Response, session: AsyncSession = Depends(get_session)) -> dict[str, object]:
    payload = decode_token(request.cookies.get(REFRESH_COOKIE, ""), "refresh")
    user = await session.get(User, int(payload["sub"])) if payload else None
    if not payload or not user or not user.is_active or user.token_version != payload.get("ver"):
        clear_session_cookies(response)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sesión caducada")
    set_session_cookies(response, user)
    return user_out(user)


@router.post("/logout")
async def logout(
    request: Request, response: Response, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)
) -> dict[str, str]:
    db_user = await session.get(User, user.id)
    if db_user:
        db_user.token_version += 1  # invalida todos los tokens emitidos
    await audit(session, request, "logout", user=user)
    clear_session_cookies(response)
    return {"status": "ok"}


@router.get("/me")
async def me(user: User = Depends(current_user)) -> dict[str, object]:
    return user_out(user)


@router.post("/password")
async def change_password(
    body: PasswordChangeIn,
    request: Request,
    response: Response,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    db_user = await session.get(User, user.id)
    assert db_user is not None
    if not verify_password(body.current_password, db_user.password_hash):
        await audit(session, request, "password_change_failed", user=user)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La contraseña actual no es correcta")
    if err := validate_password_strength(body.new_password):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, err)
    db_user.password_hash = hash_password(body.new_password)
    db_user.token_version += 1
    await audit(session, request, "password_changed", user=user, commit=False)
    await session.commit()
    set_session_cookies(response, db_user)
    return {"status": "ok"}
