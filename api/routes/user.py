from fastapi import APIRouter, HTTPException, Depends
from api.database import db
from api.utils.logger import get_logger
from api.schemas.users import CreateUser, UserDB, User
from api.auth import verify_token
import traceback

logger = get_logger(__name__)

router = APIRouter()

@router.post("/create", response_model=UserDB, status_code=201)
async def create_user(user_data: CreateUser, user_id: str = Depends(verify_token)):
    try:
        user = db.create_user(user_data, user_id)
        return user

    except Exception as e:
        logger.error(f"Erro ao criar usuário: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/me", response_model=User, status_code=200)
async def get_current_user(user_id: str = Depends(verify_token)):
    try:
        user = db.get_user(user_id)
        return user

    except ValueError as e:
        logger.warning(f"Erro ao buscar usuário: {e}")
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    except Exception as e:
        logger.error(f"Erro ao buscar usuário: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error")
    