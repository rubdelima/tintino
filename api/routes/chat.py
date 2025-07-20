from fastapi import APIRouter, HTTPException
from api.schemas.messages import NewChatInput, Chat, SubmitImageMessage
from api.services.chat import new_chat, chats, continue_chat
from api.utils.logger import get_logger
from api.services.messages import submit_image

logger = get_logger(__name__)

router = APIRouter()

@router.get("/", response_model=list[Chat], status_code=200)
async def get_chats():
    """Retrieve all chats."""
    chats_list = list(chats.values())
    logger.info(f"Carregando todos os {len(chats_list)} chats.")
    return chats_list

@router.post("/", response_model=Chat, status_code=201)
async def create_chat(input_data: NewChatInput):
    """Create a new chat session.

    Args:
        input_data (NewChatInput): The input data for the new chat session.
    """
    try:
        chat = new_chat(input_data)
        logger.info(f"Chat de Título: {chat.title} - ID: {chat.chat_id}")
        return chat
    except Exception as e:
        logger.error(f"Erro ao criar chat: {e}")
        return {"error": str(e)}

@router.get("/{chat_id}", response_model=Chat, status_code=200)
async def get_chat(chat_id: str):
    """Retrieve a specific chat by its ID."""
    chat = chats.get(chat_id)
    if chat:
        return chat
    logger.warning(f"Chat não encontrado: {chat_id}")
    
    raise HTTPException(status_code=404, detail="Chat not found")

@router.post("/{chat_id}/submit_image", response_model=SubmitImageMessage, status_code=201)
async def submit_image_api(chat_id: str, message_id:int, image_path: str):
    """Submit an image for a specific chat."""
    if chat_id not in chats:
        logger.error(f"Chat não encontrado: {chat_id}")
        raise HTTPException(status_code=404, detail="Chat not found")
    
    try:
        chat = chats[chat_id]
        if message_id >= len(chat.messages):
            logger.error(f"Mensagem com ID {message_id} não encontrada no chat: {chat_id}")
            raise HTTPException(status_code=404, detail="Message not found")        
        
        if message_id in [img_msg.message_index for img_msg in chat.submit_image_messages]:
            logger.warning(f"Imagem já submetida para a mensagem {message_id} no chat: {chat_id}")
            return {"error": "Image already submitted for this message"}
        
        logger.info(f"Submetendo imagem {len(chat.messages)} em {image_path} de um {chat.messages[-1].data.paint_image} para o chat: {chat_id}")
        result = submit_image(chat_id, chat.messages[message_id].data.paint_image, len(chat.messages), image_path)
        
        if result.data.is_correct:
            logger.info(f"Imagem submetida corretamente para o chat: {chat_id}, gerando nova mensagem.")
            chats[chat_id].submit_image_messages.append(result)
            if len(chat.messages) - len(chat.submit_image_messages) >= 1:
                continue_chat(chat_id)
        
        return result
    
    except Exception as e:
        logger.error(f"Erro ao submeter imagem: {e}")
        return {"error": str(e)}