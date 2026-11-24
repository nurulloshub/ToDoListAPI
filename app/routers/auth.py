from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..rate_limit import limiter
from ..schemas import RefreshRequest, Token, UserLogin, UserRegister
from ..security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(tags=["auth"])


def _issue_tokens(user_id: int) -> Token:
    access = create_access_token(str(user_id))
    return Token(
        token=access,
        access_token=access,
        refresh_token=create_refresh_token(str(user_id)),
    )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(
    request: Request,
    payload: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> Token:
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _issue_tokens(user.id)


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Token:
    user = await db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return _issue_tokens(user.id)


@router.post("/refresh", response_model=Token)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> Token:
    try:
        data = decode_token(payload.refresh_token, expected_type="refresh")
        user_id = int(data["sub"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    return _issue_tokens(user.id)