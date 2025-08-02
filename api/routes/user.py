from fastapi import APIRouter, HTTPException, Depends
from api.database import db
from api.utils.logger import get_logger
from api.schemas.users import CreateUser, UserDB, User
from api.auth import verify_token
import traceback

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/users",
    tags=["Usuários"],
    responses={
        401: {"description": "Token de autenticação inválido"},
        500: {"description": "Erro interno do servidor"}
    }
)

@router.post(
    "/create", 
    response_model=UserDB, 
    status_code=201,
    summary="Criar novo usuário",
    description="""
    Cria um novo usuário no sistema.
    
    - Requer autenticação via Firebase Auth ou token local
    - O user_id é extraído automaticamente do token
    - Apenas o nome é necessário no corpo da requisição
    - Retorna os dados básicos do usuário criado
    """,
    responses={
        201: {"description": "Usuário criado com sucesso"},
        400: {"description": "Dados inválidos"},
    }
)
async def create_user(
    user_data: CreateUser,
    user_id: str = Depends(verify_token)
):
    try:
        user = db.create_user(user_data, user_id)
        return user

    except Exception as e:
        logger.error(f"Erro ao criar usuário: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get(
    "/me", 
    response_model=User, 
    status_code=200,
    summary="Obter usuário atual",
    description="""
    Retorna os dados completos do usuário autenticado.
    
    - Identifica o usuário automaticamente pelo token
    - Inclui lista de chats do usuário
    - Não requer parâmetros adicionais
    """,
    responses={
        200: {"description": "Dados do usuário retornados com sucesso"},
        404: {"description": "Usuário não encontrado"},
    }
)
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
    