from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import user_out
from app.core.db import get_session
from app.core.deps import require_role
from app.core.security import hash_password, validate_password_strength
from app.models import Role, User
from app.services.audit import audit

router = APIRouter(prefix="/api/users", tags=["users"])


class UserIn(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-z0-9_.-]+$")
    full_name: str = Field("", max_length=128)
    password: str = Field(min_length=12, max_length=256)
    role: Role = Role.VIEWER


class UserPatch(BaseModel):
    full_name: str | None = Field(None, max_length=128)
    role: Role | None = None
    is_active: bool | None = None
    password: str | None = Field(None, min_length=12, max_length=256)


@router.get("")
async def list_users(
    _: User = Depends(require_role(Role.ADMIN)), session: AsyncSession = Depends(get_session)
) -> list[dict[str, object]]:
    users = await session.scalars(select(User).order_by(User.id))
    return [{**user_out(u), "is_active": u.is_active} for u in users]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserIn, request: Request, admin: User = Depends(require_role(Role.ADMIN)), session: AsyncSession = Depends(get_session)
) -> dict[str, object]:
    if err := validate_password_strength(body.password):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, err)
    if await session.scalar(select(User).where(User.username == body.username)):
        raise HTTPException(status.HTTP_409_CONFLICT, "El usuario ya existe")
    user = User(username=body.username, full_name=body.full_name, role=body.role, password_hash=hash_password(body.password))
    session.add(user)
    await session.flush()
    await audit(session, request, "user_created", user=admin, target=body.username, details={"role": body.role})
    return user_out(user)


@router.patch("/{user_id}")
async def update_user(
    user_id: int,
    body: UserPatch,
    request: Request,
    admin: User = Depends(require_role(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    if user.id == admin.id and (body.role not in (None, Role.ADMIN) or body.is_active is False):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puedes quitarte el rol admin ni desactivarte")
    changes = body.model_dump(exclude_none=True, exclude={"password"})
    for k, v in changes.items():
        setattr(user, k, v)
    if body.password:
        if err := validate_password_strength(body.password):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, err)
        user.password_hash = hash_password(body.password)
        changes["password"] = "***"  # noqa: S105
    if changes:
        user.token_version += 1
    await audit(session, request, "user_updated", user=admin, target=user.username, details=changes)
    return {**user_out(user), "is_active": user.is_active}
