from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import ACCESS_COOKIE, decode_token
from app.models import ROLE_RANK, Role, User


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "desconocida"


async def user_from_token(session: AsyncSession, token: str | None) -> User | None:
    if not token:
        return None
    payload = decode_token(token, "access")
    if not payload:
        return None
    user = await session.get(User, int(payload["sub"]))
    if not user or not user.is_active or user.token_version != payload.get("ver"):
        return None
    return user


async def current_user(request: Request, session: AsyncSession = Depends(get_session)) -> User:
    user = await user_from_token(session, request.cookies.get(ACCESS_COOKIE))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No autenticado")
    return user


def require_role(minimum: Role) -> Callable[..., Coroutine[Any, Any, User]]:
    async def _dep(user: User = Depends(current_user)) -> User:
        if ROLE_RANK[Role(user.role)] < ROLE_RANK[minimum]:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Permisos insuficientes")
        return user

    return _dep
