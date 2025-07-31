from fastapi import HTTPException, UploadFile
import os
from api.schemas.messages import NewChatInput, Chat
from api.utils.logger import get_logger
from api.models.speech_to_text import transcribe_audio
import uuid
from api.utils import store_temp_file
import time
from api.services.messages import new_message, generate_next_message
import threading
import os
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

logger = get_logger(__name__)

os.makedirs('./temp', exist_ok=True)

async def new_chat(audio_file: UploadFile) -> Chat:
    
    chat_id = str(uuid.uuid4())    
    logger.debug(f"Criando novo chat com ID: {chat_id}")
    
    logger.debug("Transcrevendo áudio para texto...")
    start_time = time.time()
    instruction = transcribe_audio(audio_file)
    logger.debug(f"Transcrição concluída em {time.time() - start_time:.2f} segundos.")
    
    message = new_message(instruction, chat_id, 0)
    
    chat = Chat(
        chat_id=chat_id,
        title=message.data.title if message.data.title else "Nova História",
        messages=[message],
        subimits=[]
    )
    
    
    
    logger.debug(f"Novo chat criado com ID: {chat_id} e título: {chat.title}")
    
    return chat

def continue_chat(chat_id: str):
    """
    Continua o chat gerando a próxima mensagem de forma assíncrona
    """
    def _continue_chat_async():
        try:
            chat = chats.get(chat_id)
            if not chat:
                logger.error(f"Chat {chat_id} não encontrado")
                return
            
            logger.info(f"Gerando próxima mensagem para o chat: {chat_id}")
            
            message = generate_next_message(
                chat_id=chat_id,
                message_id=len(chat.messages),
                history=[msg.data.text_voice for msg in chat.messages],
                paintned_items=", ".join([msg.data.paint_image for msg in chat.messages]),
                last_image=chat.messages[-1].image
            )
            
            chats[chat_id].messages.append(message)
            
            save_json(f'./temp/{chat_id}/chat.json', chats[chat_id].model_dump())
            
            logger.info(f"Próxima mensagem gerada com sucesso para o chat: {chat_id}")
            
        except Exception as e:
            logger.error(f"Erro ao continuar chat {chat_id}: {str(e)}")
    
    thread = threading.Thread(target=_continue_chat_async, daemon=True)
    thread.start()
    
    logger.info(f"Iniciando geração assíncrona da próxima mensagem para o chat: {chat_id}")