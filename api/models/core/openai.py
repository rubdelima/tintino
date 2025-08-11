from api.database import db
from api.constraints import config
from api.models.core.interface import CoreModelInterface, models_list
import api.models.prompts as prompts
from api.schemas.llm import NewChat, ContinueChat, SubmitImageResponse, AssertContinueChat
from api.schemas.messages import ChatItems
from api.utils.logger import get_logger
from api.utils import image_part_from_any, get_mime_extension

import base64
from dotenv import load_dotenv
from fastapi import UploadFile
from openai import OpenAI
import os
import time
from typing import Optional
import json

logger = get_logger(__name__)
load_dotenv()
openai_configs = config.get("OpenAI", {})

class OpenAIModel(CoreModelInterface):
    def __init__(self):
        logger.info("Configurando cliente OpenAI com a chave da API")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        
        if OPENAI_API_KEY is None:
            logger.error("Chave da API da OpenAI não encontrada. Certifique-se de definir a variável de ambiente OPENAI_API_KEY.")
            exit(1)
        
        self.client = OpenAI()
        logger.info
        
        self.global_model = "OpenAI"
        self.new_chat_model = openai_configs.get("new_chat", "gpt-5-mini")
        self.continue_chat_model = openai_configs.get("continue_chat", "gpt-5-mini")
        self.submit_model= openai_configs.get("submit", "gpt-5-mini")
        self.assert_continue_model = openai_configs.get("assert_continue", "gpt-5-nano")
        self.generate_image_model = openai_configs.get("generate_image", "gpt-5")
        self.generate_voice_model = openai_configs.get("generate_voice","gpt-4o-mini-tts")
        self.voice_names = [
            "alloy", "ash", "ballad",
            "coral", "echo", "fable",
            "nova", "onyx", "sage", "shimmer"
        ]
        
    def new_chat(self, child_name:str, instruction:str) ->NewChat:
        response = self.client.responses.create(
            model = self.new_chat_model,
            text=prompts.initial_json_text, #type:ignore
            input=[
                {"role" : "system", "content" : prompts.initial_json_input.format(child_name=child_name)},
                {"role" : "user", "content" : instruction}
            ]
        )

        return NewChat(**json.loads(response.output_text))

    def assert_continue_chat(self, items: ChatItems, chat_id:str, result:ContinueChat) -> ContinueChat:
        
        logger.debug(f"Enviando prompt de validação para {self.get_model_name('assert_continue')}")
        start_time = time.time()
        assert_result_request = self.client.responses.create(
            model=self.assert_continue_model,
            text=prompts.assert_continue_chat_json_text, #type:ignore
            input=prompts.assert_continue_chat_input.format(
                history=items.history,
                painted_items=items.painted_items,
                requested_item=result.paint_image,
            )
        )
        assert_result = AssertContinueChat(**json.loads(assert_result_request.output_text))
        logger.debug(f"Resposta de validação recebida: {assert_result.is_correct} em {time.time() - start_time:.2f} segundos.")
        
        if not assert_result.is_correct:
            logger.warning(f"Validação do chat para o usuário falhou: {assert_result.feedback}")
            logger.debug(f"Enviando prompt de correção para {self.get_model_name('continue_chat')}")
            start_time = time.time()
            new_continue = self.client.responses.create(
                previous_response_id=chat_id,
                model=self.continue_chat_model,
                text=prompts.continue_chat_json_text, #type:ignore
                input=assert_result.feedback
            )
            logger.debug(f"Resposta de correção recebida: {result} em {time.time() - start_time:.2f} segundos.")
            
            result = ContinueChat(**json.loads(new_continue.output_text))
               
        return result
    
    def continue_chat(self, items:ChatItems, user_name:str) -> ContinueChat:
        messages  = [
            {
                "role" : "system", 
                "content":  prompts.continue_chat_input.format(
                    history=items.history,
                    painted_items=items.painted_items,
                    child_name=user_name,
                )
            },
            {
                "role" : "user",
                "content" : [
                    {"type" : "input_text", "text" : "Continue a história"},
                    image_part_from_any(items.last_image)
                ]
                
            }
        ]
        
        response = self.client.responses.create(
            model=self.continue_chat_model,
            text=prompts.continue_chat_json_text, #type:ignore
            input=messages #type:ignore
        )
        
        continue_chat = ContinueChat(**json.loads(response.output_text))
        
        if config.get("Models", {}).get("assert_continue", True):
            continue_chat = self.assert_continue_chat(items, response.id, continue_chat)
        
        return continue_chat

    async def submit(self, image_file: UploadFile, target:str, user_name:str) -> SubmitImageResponse:
        
        image_bytes, mime_type, _ = await get_mime_extension(image_file)
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mime_type or 'image/png'};base64,{b64}"
        del image_bytes
        
        messages = [
            {"role": "system","content" : prompts.submit_image_prompt_input.format(doodle_name=target, child_name=user_name)},
            {"role" : "user", "content" : [
                {"type" : "input_text", "text" : f"O meu desenho é de um/uma {target}. O que você achou?"},
                {"type" : "input_image", "image_url" : data_url}
            ]}
        ]

        response = self.client.responses.create(
            model=self.submit_model,
            text=prompts.submit_image_json_text, #type:ignore
            input=messages
        )

        return SubmitImageResponse(**json.loads(response.output_text))


    def generate_text_to_voice(self, content: str, instructions:str, user_id:str, voice_name:Optional[str]=None,
                               chat_id: Optional[str] = None, message_id: Optional[int] = None, feedback:bool=False) -> str:
        
        if voice_name is None:
            voice_name = openai_configs.get("voce_name", "shimmer")
                
        with self.client.audio.speech.with_streaming_response.create(
            model=self.generate_voice_model,
            voice=voice_name, #type:ignore
            input=content,
            instructions=instructions,
            response_format='wav'
        ) as response:
            audio_data = response.read()

        destination_path = f"{user_id}/{chat_id}/{message_id}/audio" if chat_id and (message_id is not None) else f"{user_id}/audio"
        
        return db.upload_generated_archive(
            audio_data,
            destination_path=destination_path,
            mime_type='audio/wav',
            base_filename="feedback" if  feedback else None
        )

    def generate_scene_image(self, description: str, user_id:str, 
                             chat_id:Optional[str] = None, message_id: Optional[int] = None) ->str:
        
        response = self.client.responses.create(
            model=self.generate_image_model,
            input=description,
            tools=[{"type": "image_generation"}],
        )
                
        image_data = [
            output.result
            for output in response.output
            if output.type == "image_generation_call"
        ]
        
        del response

        assert image_data
        image_base64 = image_data[0]
        
        del image_data
        
        image_bytes = base64.b64decode(image_base64) #type:ignore
        
        destination_path = f"{user_id}/{chat_id}/{message_id}/images/scene_image.png" if chat_id and (message_id is not None) else f"{user_id}/images/scene_image.png"

        url_or_path = db.upload_generated_archive(
            file_bytes=image_bytes,
            destination_path=destination_path,
            mime_type="image/png"
        )
        
        return url_or_path