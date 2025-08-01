from fastapi import APIRouter, HTTPException
from api.database import db
from api.utils.logger import get_logger
from api.schemas.users import LoginHandler,  CreateUser, UserDB, User
import traceback

logger = get_logger(__name__)

router = APIRouter()

@router.post("/create", response_model=UserDB, status_code=201)
async def create_user(user_data: CreateUser):
    """Create a new user."""
    try:
        user = db.create_user(user_data)
        return user

    except Exception as e:
        logger.error(f"Erro ao criar usuário: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/login", response_model=User, status_code=200)
async def login_user(handler: LoginHandler):
    """Login a user with email and password."""
    try:
        user = db.login_user(handler)
        return user
    
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    
    except Exception as e:
        logger.error(f"Erro ao fazer login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/get_user", response_model=User, status_code=200)
async def get_user(user_id: str):
    """Retrieve a user by their ID."""
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
    