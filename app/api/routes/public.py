from fastapi import APIRouter

router = APIRouter(prefix="/public", tags=["public"])

@router.get("/ping")
async def ping():
    return {"pong": True}

@router.get("/health")
async def health():
    return {"status": "ok"}
