from api.constraints import config
from api.database import db
from api.models.core.interface import CoreModelInterface, models_list
import api.models.prompts as prompts
from api.schemas.llm import NewChat, ContinueChat, SubmitImageResponse, AssertContinueChat
from api.schemas.messages import ChatItems
from api.utils import convert_raw_audio_to_wav, get_mime_extension
from api.utils.logger import get_logger
from dotenv import load_dotenv

import base64
from fastapi import UploadFile
from google import genai
from google.genai import types
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import time
from typing import Union, List, Literal, Optional

logger = get_logger(__name__)
load_dotenv()
default_voice_name = config.get("Gemini", {}).get("voice_name", "Kore") 

class GoogleModel(CoreModelInterface):
    def __init__(self):
        if os.getenv("GEMINI_API_KEY") is None:
            logger.error("Chave da API do Gemini não encontrada. Certifique-se de definir a variável de ambiente GEMINI_API_KEY.")
            exit(1)

        gemini_configs = config.get("Gemini", {})

        logger.info("Configurando cliente GenAI com a chave da API do Gemini")
        self.google_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        logger.info("Cliente GenAI configurado com sucesso.")
        
        logger.info(f"Carregando modelos da Google via Langchain")

        self.new_chat_model = gemini_configs.get("new_chat", "gemini-2.5-flash")
        self.continue_chat_model = gemini_configs.get("continue_chat", "gemini-2.5-flash")
        self.submit_model = gemini_configs.get("submit", "gemini-2.5-flash")
        self.assert_continue_model = gemini_configs.get("assert_continue", "gemini-2.5-flash-lite")

        self.new_chat_llm = ChatGoogleGenerativeAI(
            model=self.new_chat_model,
            google_api_key=os.getenv("GEMINI_API_KEY"),
        ).with_structured_output(NewChat)

        self.continue_chat_llm = ChatGoogleGenerativeAI(
            model=self.continue_chat_model,
            google_api_key=os.getenv("GEMINI_API_KEY"),
        ).with_structured_output(ContinueChat)

        self.submit_llm = ChatGoogleGenerativeAI(
            model=self.submit_model,
            google_api_key=os.getenv("GEMINI_API_KEY"),
        ).with_structured_output(SubmitImageResponse)

        self.assert_continue_llm = ChatGoogleGenerativeAI(
            model=self.assert_continue_model,
            google_api_key=os.getenv("GEMINI_API_KEY"),
        ).with_structured_output(AssertContinueChat)
        
    def get_model_name(self, source: Literal["global", "new_chat", "continue_chat", "submit", "assert_continue"]) -> str:
        if source not in models_list:
            raise ValueError(f"Modelo desconhecido: {source}")
        if source == "global":
            return "Google"
        return f"Google : {getattr(self, f'{source}_model')}"

    def new_chat(self, child_name:str, instruction:str) ->NewChat:
        messages : List[Union[SystemMessage, HumanMessage]] = [
            SystemMessage(content=prompts.initial_prompt_schema + prompts.initial_json_input.format(child_name=child_name)),
            HumanMessage(content=instruction)
            ]
        result = self.new_chat_llm.invoke(messages)
        assert isinstance(result, NewChat)
        return result

    def continue_chat(self, items:ChatItems, user_name:str) -> ContinueChat:
        messages = [
            AIMessage(content=[{
                "type": "image_url",
                "image_url": items.last_image,
            }]),

            SystemMessage(content=prompts.continue_chat_prompt_schema + prompts.continue_chat_input.format(
                history=items.history,
                painted_items=items.painted_items,
                child_name=user_name,
            )),
            
            HumanMessage(content="Continue a história")
        ]
        
        result = self.continue_chat_llm.invoke(messages)
        assert isinstance(result, ContinueChat)
        
        if config.get("Models", {}).get("assert_continue", True):
            result = self.assert_continue_chat(items, user_name, messages, result)

        return result # type:ignore

    async def submit(self, image_file: UploadFile, target:str, user_name:str) -> SubmitImageResponse:
        image_bytes, mime_type, _ = await get_mime_extension(image_file)

        image_message = {
            "type": "image",
            "source_type": "base64",
            "mime_type": mime_type,
            "data": base64.b64encode(image_bytes).decode('utf-8'),
        }

        del image_bytes
        
        messages = [
            SystemMessage(prompts.submit_image_prompt_schema + 
                          prompts.submit_image_prompt_input.format(doodle_name=target, child_name=user_name)),
            HumanMessage(content=[image_message, f"O meu desenho é de um/uma {target}. O que você achou?"]),
        ]

        result = self.submit_llm.invoke(messages)

        assert isinstance(result, SubmitImageResponse)
        
        return result

    def assert_continue_chat(self, items: ChatItems, user_name: str,
                             messages: List[Union[SystemMessage, HumanMessage, AIMessage]], 
                             result:ContinueChat) -> ContinueChat:
        
        messages += [
            AIMessage(content=result.model_dump_json()),
            SystemMessage(content=prompts.assert_continue_chat_prompt_schema + 
                          prompts.assert_continue_chat_input.format(
                history=items.history,
                painted_items=items.painted_items,
                requested_item=result.paint_image,
            ))
        ]
        
        logger.debug(f"Enviando prompt de validação para {self.get_model_name('assert_continue')}")
        start_time = time.time()
        assert_result = self.assert_continue_llm.invoke(messages)
        assert isinstance(assert_result, AssertContinueChat)
        logger.debug(f"Resposta de validação recebida: {assert_result.is_correct} em {time.time() - start_time:.2f} segundos.")

        if not assert_result.is_correct:
            logger.warning(f"Validação do chat para o usuário falhou: {assert_result.feedback}")
            
            messages.append(SystemMessage(content=prompts.fix_history_prompt_schema + 
                                          prompts.fix_history_prompt_input.format(
                    feedback = assert_result.feedback,
                    history=items.history,
                    painted_items=items.painted_items,
                    child_name=user_name
                )))
            
            logger.debug(f"Enviando prompt de correção para {self.get_model_name('continue_chat')}")
            start_time = time.time()
            result = self.continue_chat_llm.invoke(messages) #type:ignore
            assert isinstance(result, ContinueChat)
            logger.debug(f"Resposta de correção recebida: {result} em {time.time() - start_time:.2f} segundos.")

        return result
    
    def generate_text_to_voice(self, prompt: str, user_id:str, voice_name:Optional[str]=None,
                               chat_id: Optional[str] = None, message_id: Optional[int] = None, feedback:bool=False) -> str:
        
        if voice_name is None:
            voice_name = default_voice_name

        response = self.google_client.models.generate_content(
           model="gemini-2.5-flash-preview-tts",
           contents=prompt,
           config=types.GenerateContentConfig(
              response_modalities=["AUDIO"],
              speech_config=types.SpeechConfig(
                 voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                       voice_name=voice_name,
                    )
                 )
              ),
           )
        )

        audio_bytes = convert_raw_audio_to_wav(response.candidates[0].content.parts[0].inline_data.data ) #type:ignore

        del response

        destination_path = f"{user_id}/{chat_id}/{message_id}/audio" if chat_id and (message_id is not None) else f"{user_id}/audio"

        return db.upload_generated_archive(
            audio_bytes,
            destination_path=destination_path,
            mime_type='audio/wav',
            base_filename="feedback" if  feedback else None
        )
    
    def generate_scene_image(self, description: str, user_id:str, 
                             chat_id:Optional[str] = None, message_id: Optional[int] = None) ->str:
        
        contents = ("Crie uma imagem cartunesca a partir dessa descrição: ",  description)

        response = self.google_client.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=contents, #type:ignore
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            )
        )

        image_bytes = None
        image_mime_type = None

        for part in response.candidates[0].content.parts: # type:ignore
            if part.inline_data:
                image_bytes = part.inline_data.data
                image_mime_type = part.inline_data.mime_type
                break

        if image_bytes and image_mime_type:
            destination_path = f"{user_id}/{chat_id}/{message_id}/images/scene_image.png" if chat_id and (message_id is not None) else f"{user_id}/images/scene_image.png"
            url_or_path = db.upload_generated_archive(
                file_bytes=image_bytes,
                destination_path=destination_path,
                mime_type=image_mime_type,
            )
            return url_or_path

        raise ValueError("Nenhuma imagem foi gerada ou encontrada na resposta da API.")