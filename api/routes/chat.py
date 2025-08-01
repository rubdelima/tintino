from fastapi import APIRouter, HTTPException, Depends, UploadFile
from fastapi.security import HTTPAuthorizationCredentials

from api.schemas.messages import Chat, SubmitImageMessage, SubmitImageHandler
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
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/{chat_id}/submit_image", response_model=SubmitImageMessage, status_code=201)
async def submit_image_api(chat_id:str, image: UploadFile, credentials: HTTPAuthorizationCredentials = Depends(security_bearer)):
    """Submit an image for a specific chat."""
    try:
        user_id = credentials.credentials
        chat = db.get_chat(chat_id, user_id)
        message_index = len(chat.subimits)
        
        logger.info(f"Submetendo desenho {message_index} do chat : {chat}")
        
        result = await submit_image(chat_id, chat.messages[-1].paint_image, image)
        
        if result.is_correct:
            logger.info(f"Imagem submetida corretamente para o chat: {chat_id}, gerando nova mensagem.")
            feedback_audio = "Fale de uma maneira energética, elogiando o desenho da criança com essas palavras: "
            continue_chat(user_id, chat_id, message_index + 1)
        else:
            logger.info(f"Imagem submetida incorretamente para o chat: {chat_id}, gerando feedback.")
            feedback_audio = "Fale de uma maneira apasiguadora, incentivando a criança a melhorar seu desenho com essas palavras: "
            
        feedback = generate_feedback_audio(result, feedback_audio, user_id, chat_id, message_index)
        
        return feedback
    
    except HTTPException as http_exc:
        logger.error(f"Erro ao submeter imagem: {http_exc.detail}")
        raise http_exc
    
    except Exception as e:
        logger.error(f"Erro ao submeter imagem: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")