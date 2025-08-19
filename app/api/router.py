from fastapi import APIRouter, Depends
from app.api.routes import auth, users, public
from app.core.config import get_settings
from app.core.rate_limit import rate_limit

settings = get_settings()
api_router = APIRouter(prefix=settings.API_V1_STR, dependencies=[Depends(rate_limit("api", settings.RATE_LIMIT_DEFAULT_LIMIT, settings.RATE_LIMIT_DEFAULT_WINDOW))])
api_router.include_router(public.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
