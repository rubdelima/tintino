import base64
from concurrent.futures import ThreadPoolExecutor
from fastapi import UploadFile
import time
from typing import Optional

from api.database import db
from api.schemas.llm import ContinueChat, SubmitImageResponse
from api.schemas.messages import SubmitImageMessage, Message
from api.utils.logger import get_logger
from api.models.core import core_model

logger = get_logger(__name__)

def generate_image_audio(result: ContinueChat, user_id:str, chat_id:Optional[str]=None, message_id: Optional[int]=None) -> tuple[str, str]:

    audio_prompt = "Narre essa história para uma criança de 5 anos, com uma voz amigável e entusiástica: " + \
        result.text_voice + ".\n" + result.intro_voice

    with ThreadPoolExecutor() as executor:
        start_time = time.time()
        future_audio = executor.submit(core_model.generate_text_to_voice, 
                                       audio_prompt, user_id, None, chat_id, message_id)
        
        future_image = executor.submit(core_model.generate_scene_image, 
                                       result.scene_image_description, user_id, chat_id, message_id)
        
        future_audio.add_done_callback(lambda f: logger.debug(f"Áudio gerado em {time.time() - start_time:.2f} segundos."))
        future_image.add_done_callback(lambda f: logger.debug(f"Imagem gerada em {time.time() - start_time:.2f} segundos."))

    image = future_image.result()
    audio = future_audio.result()

    return image, audio

def new_message(user_id:str, chat_id: str, message_id: int) -> Message:    
    logger.debug(f"Recuperando itens do chat {chat_id} para a nova mensagem {message_id}")
    items = db.get_chat_items(chat_id)
    logger.debug(f"Itens do chat {chat_id} obtidos")
    
    user = db.get_user(user_id)
    
    logger.debug(f"Enviando prompt para o {core_model.get_model_name('global')} do chat {chat_id} e mensagem {message_id}")
    start_time = time.time()
    result = core_model.continue_chat(items, user.name)
    logger.debug(f"Resposta do {core_model.get_model_name('global')} recebida em {time.time() - start_time:.2f} segundos para o chat {chat_id} e mensagem {message_id}")

    image, audio = generate_image_audio(result, user_id, chat_id, message_id)
    
    message = Message(
        message_index=message_id,
        image=image,
        audio=audio,
        **result.model_dump()
    )
    
    db.update_chat(user_id, chat_id, 'messages', message)
    
    return message

async def submit_image(chat_id: str, target: str, image_file: UploadFile, user_id:str) -> SubmitImageResponse:
    user = db.get_user(user_id)
    
    logger.debug(f"Submetendo nova imagem para o chat: {chat_id}")
    start_time = time.time()
    result = await core_model.submit(image_file, target, user.name)
    logger.debug(f"Imagem submetida em {time.time() - start_time:.2f} segundos.")
    
    return result
    
def generate_feedback_audio(
        result: SubmitImageResponse, 
        feedback_audio:str, 
        user_id:str, 
        chat_id: str, 
        message_id: int,
        image :Optional[str] = None) -> SubmitImageMessage:
    
    start_time = time.time()

    feedback_audio = core_model.generate_text_to_voice(feedback_audio + result.feedback, user_id, None, chat_id, message_id, True)

    logger.debug(f"Áudio de feedback gerado em {time.time() - start_time:.2f} segundos.")
    
    logger.debug(f"Salvando feedback de imagem para o chat {chat_id} e mensagem {message_id}")
    
    submit_message =  SubmitImageMessage(
        message_index=message_id,
        audio=feedback_audio,
        data = result,
        image=image
    )
    
    if result.is_correct:
        db.update_chat(user_id, chat_id, 'submits', submit_message)
    
    return submit_message