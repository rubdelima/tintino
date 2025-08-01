from fastapi import HTTPException, UploadFile
import os
from api.schemas.messages import Chat, MiniChatBase, Message
from api.utils.logger import get_logger
from api.models.speech_to_text import transcribe_audio
import time
from api.services.messages import new_message, generate_image_audio
import threading
import os
from api.models.prompts import initial_prompt
from api.models.google import new_chat_llm
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Union, List
from api.schemas.llm import NewChat
from api.database import db
from datetime import datetime, timezone

logger = get_logger(__name__)

os.makedirs('./temp', exist_ok=True)

async def new_chat(user_id:str, audio_file: UploadFile) -> Chat:
    # Trasncrição de Áudio    
    logger.debug("Transcrevendo áudio para texto...")
    start_time = time.time()
    instruction = transcribe_audio(audio_file)
    logger.debug(f"Transcrição concluída em {time.time() - start_time:.2f} segundos.")
    
    # Geração de História
    messages : List[Union[SystemMessage, HumanMessage]] = [SystemMessage(content=initial_prompt),HumanMessage(content=instruction)]
    logger.debug(f"Enviando prompt para o Gemini do chat")
    start_time = time.time()
    result = new_chat_llm.invoke(messages)
    assert isinstance(result, NewChat)
    logger.debug(f"Resposta do Gemini recebida em {time.time() - start_time:.2f} segundos. Nome da história: {result.title}")
    
    # Obter o ID do Chat
    chat_id = db.get_new_chat_id(user_id)
    
    # Geração de Audio e Imagem
    image, audio = generate_image_audio(result, user_id, chat_id, 0)
    
    # Salvando o Chat
    chat = db.save_chat(user_id, MiniChatBase(
        title=result.title,
        chat_image=image,
        last_update= datetime.now(timezone.utc),
    ))
    
    # Salvando Mensagem
    logger.debug(f"Salvando nova mensagem no banco de dados para o chat {chat.chat_id}")
    message = Message(
        paint_image=result.paint_image,
        text_voice=result.text_voice,
        intro_voice=result.intro_voice,
        scene_image_description=result.scene_image_description,
        message_index=0,
        image=image,
        audio=audio
    )    
    db.update_chat(user_id, chat.chat_id, 'messages', message)
    
    return Chat(
        messages=[message],
        **chat.model_dump()
    )

def continue_chat(user_id:str, chat_id: str, message_id: int) -> None:
    """
    Continua o chat gerando a próxima mensagem de forma assíncrona
    """
    
    def _continue_chat_async():
        try:
            logger.info(f"Gerando próxima mensagem para o chat: {chat_id}")
            new_message(user_id, chat_id, message_id)
            logger.info(f"Próxima mensagem gerada com sucesso para o chat: {chat_id}")
            
        except Exception as e:
            logger.error(f"Erro ao continuar chat {chat_id}: {str(e)}")
    
    thread = threading.Thread(target=_continue_chat_async, daemon=True)
    logger.info(f"Iniciando geração assíncrona da próxima mensagem para o chat: {chat_id}")
    thread.start()
    