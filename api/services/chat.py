from fastapi import HTTPException, UploadFile
import os
from api.schemas.messages import Chat, MiniChatBase, Message
from api.utils.logger import get_logger
from api.models.speech_to_text import transcribe_audio
import time
from api.services.messages import new_message, generate_image_audio
import threading
import asyncio
import os
from api.models.core import core_model
from typing import Union, List, Callable, Optional, Awaitable
from api.schemas.llm import NewChat
from api.database import db
from datetime import datetime, timezone
from api.models.speech_to_text.utils import prepare_audio_file
import traceback

logger = get_logger(__name__)

os.makedirs('./temp', exist_ok=True)

async def new_chat(user_id:str, audio_file: UploadFile, voice_name: str = "Kore") -> Chat:
    # Trasncrição de Áudio
    #TODO: Sempre está achando que é outro formato mesmo sendo WAV, futuramente resolver !
    audio_path = await prepare_audio_file(audio_file)
    logger.debug("Transcrevendo áudio para texto...")
    start_time = time.time()
    instruction = transcribe_audio(audio_path)
    audio_path.unlink(missing_ok=True)
    logger.debug(f"Transcrição concluída em {time.time() - start_time:.2f} segundos.")
    
    user = db.get_user(user_id)
    
    # Geração de História
    logger.debug(f"Enviando prompt para o {core_model.get_model_name('global')} do chat")
    start_time = time.time()
    result = core_model.new_chat(user.name, instruction)
    logger.debug(f"Resposta do Gemini recebida em {time.time() - start_time:.2f} segundos. Nome da história: {result.title}")
    
    # Salvando o Chat
    chat = db.save_chat(user_id, MiniChatBase(
        title=result.title,
        chat_image=result.shortcode,
        last_update= datetime.now(timezone.utc),
        voice_name=voice_name or "Kore"
    ))
    
    # Geração de Audio e Imagem
    image, audio = generate_image_audio(result, user_id, chat.chat_id, 0, voice_name)
    
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
    

    # Iniciar geração da próxima mensagem em background e salvar em pending_messages
    def _generate_next():
        try:
            logger.info(f"Pré-processando próxima mensagem para o chat: {chat.chat_id}")
            next_msg = new_message(user_id, chat.chat_id, 1)
            db.set_pending_message(chat.chat_id, next_msg.model_dump())
            logger.info(f"Mensagem pré-processada salva para o chat: {chat.chat_id}")
        except Exception as e:
            logger.error(f"Erro ao pré-processar próxima mensagem: {e}")
    threading.Thread(target=_generate_next, daemon=True).start()

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
            logger.error(traceback.format_exc())
    
    thread = threading.Thread(target=_continue_chat_async, daemon=True)
    logger.info(f"Iniciando geração assíncrona da próxima mensagem para o chat: {chat_id}")
    thread.start()

async def continue_chat_async(user_id: str, chat_id: str, message_id: int, 
                            callback: Optional[Callable[[Message], Awaitable[None]]] = None) -> Message:
    """
    Versão assíncrona do continue_chat que permite callback quando a mensagem é gerada.
    
    Args:
        user_id: ID do usuário
        chat_id: ID do chat
        message_id: Índice da nova mensagem
        callback: Função assíncrona opcional para ser chamada quando a mensagem estiver pronta
        
    Returns:
        Message: A nova mensagem gerada
    """
    
    def _generate_message():
        try:
            logger.info(f"Gerando próxima mensagem para o chat: {chat_id}")
            message = new_message(user_id, chat_id, message_id)
            logger.info(f"Próxima mensagem gerada com sucesso para o chat: {chat_id}")
            return message
            
        except Exception as e:
            logger.error(f"Erro ao continuar chat {chat_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise e
    
    # Executa a geração em uma thread separada para não bloquear o loop de eventos
    loop = asyncio.get_event_loop()
    message = await loop.run_in_executor(None, _generate_message)
    
    # Chama o callback se fornecido
    if callback:
        await callback(message)
    
    return message
    