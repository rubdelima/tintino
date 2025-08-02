from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.security import HTTPAuthorizationCredentials
from typing import List
import traceback

from api.schemas.messages import Chat, MiniChat, SubmitImageMessage, SubmitImageHandler
from api.services.chat import new_chat, continue_chat
from api.utils.logger import get_logger
from api.services.messages import submit_image, generate_feedback_audio
from api.database import db
from api.auth import security_bearer

logger = get_logger(__name__)

router = APIRouter()

@router.post("/", response_model=Chat, status_code=201)
async def create_chat(voice_audio : UploadFile, credentials: HTTPAuthorizationCredentials = Depends(security_bearer)):
    user_id = credentials.credentials
    try:
        chat = await new_chat(user_id, voice_audio) #type:ignore
        logger.info(f"Chat de Título: {chat.title} - ID: {chat.chat_id}")
        return chat
    except HTTPException as http_exc:
        logger.error(f"Erro ao criar chat: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Erro ao criar chat: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/", response_model=List[MiniChat], status_code=200)
async def get_chats(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)):
    user_id = credentials.credentials
    try:
        user = db.get_user(user_id)
        return user.chats
    except HTTPException as http_exc:
        logger.error(f"Erro ao buscar chats: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Erro ao buscar chats: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/{chat_id}", response_model=Chat, status_code=200)
async def get_chat(chat_id: str, credentials: HTTPAuthorizationCredentials = Depends(security_bearer)):
    """Retrieve a specific chat by its ID."""
    user_id = credentials.credentials
    try:
        chat = db.get_chat(chat_id, user_id) #type:ignore
        return chat
    except HTTPException as http_exc:
        logger.error(f"Erro ao buscar chat: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Erro ao buscar chat: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/{chat_id}/submit_image", response_model=SubmitImageMessage, status_code=201)
async def submit_image_api(chat_id:str, image: UploadFile = File(..., media_type="image/*"), credentials: HTTPAuthorizationCredentials = Depends(security_bearer)):
    """Submit an image for a specific chat."""
    try:
        user_id = credentials.credentials
        chat = db.get_chat(chat_id, user_id)
        message_index = len(chat.subimits)
        
        logger.debug(f"Submetendo desenho {message_index} do chat : {chat.chat_id}")
        
        result = await submit_image(chat_id, chat.messages[-1].paint_image, image)
        
        image_path = None
        if result.is_correct:
            logger.info(f"Imagem submetida corretamente para o chat: {chat_id}, gerando nova mensagem.")
            image_path = await db.store_user_archive(user_id, image)
            feedback_audio = "Fale de uma maneira energética, elogiando o desenho da criança com essas palavras: "
            continue_chat(user_id, chat_id, message_index + 1)
        else:
            logger.info(f"Imagem submetida incorretamente para o chat: {chat_id}, gerando feedback.")
            feedback_audio = "Fale de uma maneira apasiguadora, incentivando a criança a melhorar seu desenho com essas palavras: "
            
        feedback = generate_feedback_audio(result, feedback_audio, user_id, chat_id, message_index, image_path)
        
        return feedback
    
    except HTTPException as http_exc:
        logger.error(f"Erro ao submeter imagem: {http_exc.detail}")
        raise http_exc
    
    except Exception as e:
        logger.error(f"Erro ao submeter imagem: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")