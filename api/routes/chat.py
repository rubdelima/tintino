from fastapi import APIRouter, HTTPException
from api.schemas.messages import NewChatInput, Chat, SubmitImageMessage, SubmitImageHandler
from api.services.chat import new_chat, chats, continue_chat
from api.utils.logger import get_logger
from api.services.messages import submit_image, generate_feedback_audio

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
async def submit_image_api(handler: SubmitImageHandler):
    """Submit an image for a specific chat."""
    if handler.chat_id not in chats:
        logger.error(f"Chat não encontrado: {handler.chat_id}")
        raise HTTPException(status_code=404, detail="Chat not found")
    
    try:
        chat = chats[handler.chat_id]
        if handler.message_id >= len(chat.messages):
            logger.error(f"Mensagem com ID {handler.message_id} não encontrada no chat: {handler.chat_id}")
            raise HTTPException(status_code=404, detail="Message not found")

        if handler.message_id in [img_msg.message_index for img_msg in chat.subimits]:
            logger.warning(f"Imagem já submetida para a mensagem {handler.message_id} no chat: {handler.chat_id}")
            return {"error": "Image already submitted for this message"}
        
        logger.info(f"Submetendo imagem {len(chat.messages)} em {handler.image_path} de um {chat.messages[-1].data.paint_image} para o chat: {handler.chat_id}")
        
        result = submit_image(handler.chat_id, chat.messages[handler.message_id].data.paint_image, len(chat.messages), handler.image_path)

        if result.is_correct:
            logger.info(f"Imagem submetida corretamente para o chat: {handler.chat_id}, gerando nova mensagem.")
            feedback_audio = "Fale de uma maneira energética, elogiando o desenho da criança com essas palavras: "
            continue_chat(handler.chat_id)
        else:
            logger.warning(f"Imagem submetida incorretamente para o chat: {handler.chat_id}, gerando feedback.")
            feedback_audio = "Fale de uma maneira apasiguadora, incentivando a criança a melhorar seu desenho com essas palavras: "
            
        feedback = generate_feedback_audio(result, feedback_audio, handler.chat_id, handler.message_id)
        
        if result.is_correct:
            chats[handler.chat_id].subimits.append(feedback)

        return feedback
    
    except Exception as e:
        logger.error(f"Erro ao submeter imagem: {e}")
        return {"error": str(e)}