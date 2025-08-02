from fastapi import APIRouter

from api.routes.chat import router as chat_router
from api.routes.user import router as user_router

router = APIRouter()
router.include_router(chat_router)
router.include_router(user_router)