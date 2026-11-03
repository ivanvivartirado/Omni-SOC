"""Protección contra fuerza bruta en el login: bloqueo progresivo por usuario y límite por IP."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import LoginAttempt


def lockout_seconds(failures: int, last_failure: datetime, now: datetime, settings: Settings) -> int:
    """Segundos de bloqueo restantes. A partir de N fallos: 1, 2, 4, 8... minutos (tope configurable)."""
    if failures < settings.login_max_failures:
        return 0
    minutes = min(2 ** (failures - settings.login_max_failures), settings.login_lockout_max_minutes)
    remaining = (last_failure + timedelta(minutes=minutes) - now).total_seconds()
    return max(0, int(remaining))


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


async def retry_after(session: AsyncSession, username: str, ip: str, settings: Settings) -> int:
    now = datetime.now(UTC)
    window_start = now - timedelta(minutes=settings.login_window_minutes)

    last_success = await session.scalar(
        select(func.max(LoginAttempt.ts)).where(LoginAttempt.username == username, LoginAttempt.success)
    )
    since = max(window_start, _aware(last_success)) if last_success else window_start
    failures, last_failure = (
        await session.execute(
            select(func.count(), func.max(LoginAttempt.ts)).where(
                LoginAttempt.username == username, ~LoginAttempt.success, LoginAttempt.ts > since
            )
        )
    ).one()
    user_wait = lockout_seconds(failures, _aware(last_failure), now, settings) if last_failure else 0

    ip_failures, ip_oldest = (
        await session.execute(
            select(func.count(), func.min(LoginAttempt.ts)).where(
                LoginAttempt.ip == ip, ~LoginAttempt.success, LoginAttempt.ts > window_start
            )
        )
    ).one()
    ip_wait = 0
    if ip_failures >= settings.login_ip_max_failures and ip_oldest:
        ip_wait = max(0, int((_aware(ip_oldest) + timedelta(minutes=settings.login_window_minutes) - now).total_seconds()))
    return max(user_wait, ip_wait)


async def record_attempt(session: AsyncSession, username: str, ip: str, success: bool) -> None:
    session.add(LoginAttempt(username=username, ip=ip, success=success))
    await session.flush()
