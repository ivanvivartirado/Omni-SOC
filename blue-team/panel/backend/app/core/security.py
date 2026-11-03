import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import get_settings

_ph = PasswordHasher()  # Argon2id con los parámetros recomendados por RFC 9106
_DUMMY_HASH = _ph.hash(secrets.token_urlsafe(16))

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"
CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "x-csrf-token"

TokenKind = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """Verifica en tiempo constante; si el usuario no existe se compara contra un hash ficticio."""
    try:
        return _ph.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    return _ph.check_needs_rehash(password_hash)


def validate_password_strength(password: str) -> str | None:
    if len(password) < 12:
        return "La contraseña debe tener al menos 12 caracteres"
    classes = sum(
        [
            any(c.islower() for c in password),
            any(c.isupper() for c in password),
            any(c.isdigit() for c in password),
            any(not c.isalnum() for c in password),
        ]
    )
    if classes < 3:
        return "La contraseña debe combinar al menos 3 de: minúsculas, mayúsculas, números y símbolos"
    return None


def create_token(user_id: int, role: str, token_version: int, kind: TokenKind) -> tuple[str, datetime]:
    settings = get_settings()
    now = datetime.now(UTC)
    ttl = timedelta(minutes=settings.access_token_minutes) if kind == "access" else timedelta(hours=settings.refresh_token_hours)
    exp = now + ttl
    payload = {"sub": str(user_id), "role": role, "ver": token_version, "typ": kind, "iat": now, "exp": exp}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256"), exp


def decode_token(token: str, kind: TokenKind) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    if payload.get("typ") != kind:
        return None
    return payload


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)
