from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from .config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def _create_token(subject: str, delta: timedelta, token_type: str) -> str:
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(subject: str) -> str:
    return _create_token(
        subject,
        timedelta(minutes=settings.access_token_expire_minutes),
        "access",
    )


def create_refresh_token(subject: str) -> str:
    return _create_token(
        subject,
        timedelta(days=settings.refresh_token_expire_days),
        "refresh",
    )


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("Invalid token type")
    return payload