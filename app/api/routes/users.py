from fastapi import APIRouter, Depends
from app.api.deps import get_current_user, require_roles
from app.schemas.user import UserRead
from app.db.models import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)):
    return user

@router.get("/admin/secret", dependencies=[Depends(require_roles("admin"))])
async def admin_secret():
    return {"secret": "ok"}
