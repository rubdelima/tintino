import base64
from concurrent.futures import ThreadPoolExecutor
from fastapi import UploadFile
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import time
from typing import Optional

from api.database import db
from api.models.google import continue_chat_llm, submit_llm
from api.models.prompts import submit_image_prompt, continue_chat_prompt
from api.models.text_to_image import generate_scene_image
from api.models.text_to_speech import generate_text_to_voice
from api.schemas.llm import ContinueChat, SubmitImageResponse
from api.schemas.messages import SubmitImageMessage, Message
from api.utils import get_mime_extension
from api.utils.logger import get_logger


logger = get_logger(__name__)

def generate_image_audio(result: ContinueChat, user_id:str, chat_id:Optional[str]=None, message_id: Optional[int]=None) -> tuple[str, str]:

    audio_prompt = "Narre essa história para uma criança de 5 anos, com uma voz amigável e entusiástica: " + \
        result.text_voice + ".\n" + result.intro_voice

    with ThreadPoolExecutor() as executor:
        start_time = time.time()
        future_audio = executor.submit(generate_text_to_voice, 
                                       audio_prompt, user_id, chat_id, message_id)
        
        future_image = executor.submit(generate_scene_image, 
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
        
    messages = [
        AIMessage(content=[{
            "type": "image_url",
            "image_url": items.last_image,
        }]),
        SystemMessage(content=continue_chat_prompt.format(
            history=items.history,
            painted_items=items.painted_items
        )),
        HumanMessage(content="Continue a história")
    ]
        
    
    logger.debug(f"Enviando prompt para o Gemini do chat {chat_id} e mensagem {message_id}")

    result = continue_chat_llm.invoke(messages)

    assert isinstance(result, ContinueChat)
    
    logger.debug(f"Resposta do Gemini recebida para o chat {chat_id} e mensagem {message_id}")
    image, audio = generate_image_audio(result, user_id, chat_id, message_id)
    
    message = Message(
        message_index=message_id,
        image=image,
        audio=audio,
        **result.model_dump()
    )
    
    db.update_chat(user_id, chat_id, 'messages', message)
    
    return message

async def submit_image(chat_id: str, target: str, image_file: UploadFile) -> SubmitImageResponse:
    
    image_bytes, mime_type, _ = await get_mime_extension(image_file)
    
    image_message = {
        "type": "image",
        "source_type": "base64",
        "mime_type": mime_type,
        "data": base64.b64encode(image_bytes).decode('utf-8'),
    }
    
    del image_bytes
    
    messages = [
        SystemMessage(submit_image_prompt.format(doodle_name=target)),
        HumanMessage(content=[image_message, f"O meu desenho é de um/uma {target}. O que você achou?"]),
    ]
    
    logger.debug(f"Submetendo nova imagem para o chat: {chat_id}")
    start_time = time.time()
    result = submit_llm.invoke(messages)
    assert isinstance(result, SubmitImageResponse)
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
    
    feedback_audio = generate_text_to_voice(feedback_audio + result.feedback, user_id, chat_id, message_id, True)

    logger.debug(f"Áudio de feedback gerado em {time.time() - start_time:.2f} segundos.")
    
    logger.debug(f"Salvando feedback de imagem para o chat {chat_id} e mensagem {message_id}")
    
    submit_message =  SubmitImageMessage(
        message_index=message_id,
        audio=feedback_audio,
        data = result,
        image=image
    )
    
    db.update_chat(user_id, chat_id, 'submits', submit_message)
    
    return submit_message