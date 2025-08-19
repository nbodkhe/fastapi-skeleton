from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update
from datetime import datetime, timezone
from app.db.session import get_db
from app.db.models import User, RefreshToken
from app.schemas.user import UserCreate, UserRead
from app.schemas.auth import LoginRequest, TokenPair, RefreshRequest, AccessToken, LogoutRequest
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.config import get_settings
from app.core.rate_limit import rate_limit

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRead, dependencies=[Depends(rate_limit("register", settings.RATE_LIMIT_LOGIN_LIMIT, settings.RATE_LIMIT_LOGIN_WINDOW))])
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(User).where(User.email == payload.email))
    if q.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = User(email=payload.email, full_name=payload.full_name, hashed_password=get_password_hash(payload.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.post("/login", response_model=TokenPair, dependencies=[Depends(rate_limit("login", settings.RATE_LIMIT_LOGIN_LIMIT, settings.RATE_LIMIT_LOGIN_WINDOW))])
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(User).where(User.email == payload.email))
    user = q.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(str(user.id), user.role)
    refresh_token, jti, exp = create_refresh_token(user.id)
    db.add(RefreshToken(user_id=user.id, jti=jti, expires_at=exp.replace(tzinfo=None), revoked=False))
    await db.commit()
    return TokenPair(access_token=access_token, refresh_token=refresh_token)

@router.post("/refresh", response_model=AccessToken, dependencies=[Depends(rate_limit("refresh", settings.RATE_LIMIT_LOGIN_LIMIT, settings.RATE_LIMIT_LOGIN_WINDOW))])
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        data = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if data.get("typ") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    jti = data.get("jti")
    sub = data.get("sub")
    if not jti or not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    q = await db.execute(select(RefreshToken).where(RefreshToken.jti == jti))
    rt = q.scalar_one_or_none()
    if rt is None or rt.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
    if datetime.utcnow() >= rt.expires_at:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    u = await db.execute(select(User).where(User.id == int(sub)))
    user = u.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")
    token = create_access_token(str(user.id), user.role)
    return AccessToken(access_token=token)

@router.post("/logout", dependencies=[Depends(rate_limit("logout", settings.RATE_LIMIT_LOGIN_LIMIT, settings.RATE_LIMIT_LOGIN_WINDOW))])
async def logout(payload: LogoutRequest, db: AsyncSession = Depends(get_db)):
    try:
        data = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if data.get("typ") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    jti = data.get("jti")
    if not jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    q = await db.execute(select(RefreshToken).where(RefreshToken.jti == jti))
    rt = q.scalar_one_or_none()
    if rt is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown token")
    rt.revoked = True
    await db.commit()
    return {"detail": "Logged out"}
