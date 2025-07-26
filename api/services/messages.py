from api.utils.logger import get_logger
from api.schemas.messages import Message, Chat
from api.utils import image_to_b64, path_to_b64
from api.schemas.messages import SubmitImageMessage
from api.models.google import new_chat_llm, submit_llm
from api.models.text_to_image import generate_scene_image
from api.models.text_to_speech import generate_text_to_voice
from api.schemas.llm import ChatResponse, SubmitImageResponse
from api.models.prompts import submit_image_prompt, initial_prompt, new_message_prompt

import os
import time
import threading
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from langchain_core.messages import HumanMessage, SystemMessage

logger = get_logger(__name__)

def generate_image_audio(result: ChatResponse, chat_id: str, message_id: int) -> Message:
    
    audio_prompt = "Narre essa história para uma criança de 5 anos, com uma voz amigável e entusiástica: " + \
        result.text_voice + ".\n" + result.intro_voice

    with ThreadPoolExecutor() as executor:
        start_time = time.time()
        future_audio = executor.submit(generate_text_to_voice, 
                                       audio_prompt, chat_id, message_id)
        future_image = executor.submit(generate_scene_image, result.scene_image_description, chat_id, message_id)
        
        future_audio.add_done_callback(lambda f: logger.debug(f"Áudio gerado em {time.time() - start_time:.2f} segundos."))
        future_image.add_done_callback(lambda f: logger.debug(f"Imagem gerada em {time.time() - start_time:.2f} segundos."))

    image = future_image.result()
    audio = future_audio.result()

    return Message(
        message_index=message_id,
        image=image,
        audio=audio,
        data=result
    )

def new_message(instruction:str, chat_id: str, message_id: int) -> Message:
    os.makedirs(f'./temp/{chat_id}/{message_id}', exist_ok=True)
    
    logger.debug(f"Criando nova mensagem com ID: {message_id} no chat: {chat_id}")

    messages = [SystemMessage(content=initial_prompt), HumanMessage(content=instruction)]

    logger.debug(f"Enviando prompt para o Gemini do chat {chat_id} e mensagem {message_id}")

    result = new_chat_llm.invoke(messages)
    
    assert isinstance(result, ChatResponse)

    return generate_image_audio(result, chat_id, message_id)

def generate_next_message(chat_id, message_id, history:list[str], paintned_items : str, last_image:Optional[str] = None):
    os.makedirs(f'./temp/{chat_id}/{message_id}', exist_ok=True)
    
    logger.debug(f"Criando nova mensagem com ID: {message_id} no chat: {chat_id}")
    
    messages = [
        {
            "role" : "assistant",
            "text" : hist_part
        }
        for hist_part in history
    ]
    
    if last_image:
        messages.append(image_to_b64(last_image, "Última imagem gerada"))
    
    messages.append({
        "role" : "system",
        "text" : new_message_prompt.format(painted_items=paintned_items)
    })
    
    logger.debug(f"Enviando prompt para o Gemini do chat {chat_id} e mensagem {message_id}")

    result = new_chat_llm.invoke(messages)
    
    assert isinstance(result, ChatResponse)
    
    return generate_image_audio(result, chat_id, message_id)

def submit_image(chat_id: str, target: str, message_id:int, image_path: str) -> SubmitImageResponse:
    
    image_message = {
        "type": "image",
        "source_type": "base64",
        "mime_type": "image/png",
        "data": path_to_b64(image_path),
    }
    
    messages = [
        HumanMessage(content=[image_message]),
        SystemMessage(submit_image_prompt.format(doodle_name=target))
    ]
    
    logger.debug(f"Submetendo nova imagem para o chat: {chat_id}")
    
    start_time = time.time()
    
    result = submit_llm.invoke(messages)

    assert isinstance(result, SubmitImageResponse)

    logger.debug(f"Imagem submetida em {time.time() - start_time:.2f} segundos.")
    
    return result
    
def generate_feedback_audio(result: SubmitImageResponse, feedback_audio:str, chat_id: str, message_id: int) -> SubmitImageMessage:
    start_time = time.time()
    
    feedback_audio = generate_text_to_voice(feedback_audio + result.feedback, chat_id, message_id, True)

    logger.debug(f"Áudio de feedback gerado em {time.time() - start_time:.2f} segundos.")
    
    return SubmitImageMessage(
        message_index=message_id,
        audio=feedback_audio,
        data = result
    )