from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import client_ip
from app.models import AuditLog, User


async def audit(
    session: AsyncSession,
    request: Request | None,
    action: str,
    user: User | None = None,
    username: str = "",
    target: str = "",
    details: dict[str, Any] | None = None,
    commit: bool = True,
) -> None:
    session.add(
        AuditLog(
            user_id=user.id if user else None,
            username=user.username if user else username,
            action=action,
            target=target,
            ip=client_ip(request) if request else "",
            details=details or {},
        )
    )
    if commit:
        await session.commit()
