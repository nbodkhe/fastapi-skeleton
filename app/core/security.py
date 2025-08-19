from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import get_settings
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(subject: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_MINUTES)
    to_encode = {"sub": subject, "exp": expire, "role": role, "typ": "access"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(user_id: int, jti: str | None = None, expires_days: int | None = None) -> tuple[str, str, datetime]:
    jti = jti or str(uuid.uuid4())
    days = settings.REFRESH_TOKEN_EXPIRES_DAYS if expires_days is None else expires_days
    expire = datetime.now(timezone.utc) + timedelta(days=days)
    to_encode = {"sub": str(user_id), "exp": expire, "jti": jti, "typ": "refresh"}
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expire

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
