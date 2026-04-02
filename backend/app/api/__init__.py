from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.board import router as board_router

router = APIRouter(prefix="/api")
router.include_router(auth_router)
router.include_router(board_router)


@router.get("/health")
def health():
    return {"status": "ok"}
