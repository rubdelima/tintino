from typing import Optional
from fastapi import UploadFile
from api.constraints import config
from api.models.core.google import GoogleModel
from api.models.core.interface import CoreModelInterface
from api.models.core.openai import OpenAIModel
from api.schemas.llm import NewChat, ContinueChat, SubmitImageResponse, AssertContinueChat
from api.schemas.messages import ChatItems

models_settings = config.get("Models", {})

class MultiModels(CoreModelInterface):
    def __init__(self) -> None:
        self.openai_model = OpenAIModel()
        self.google_model = GoogleModel()
        
        self.global_model = "MultiModels"
        
        if models_settings.get("core_model", "google") == "google":
            self.new_chat_model = self.google_model.new_chat_model
            self.continue_chat_model = self.google_model.continue_chat_model
            self.assert_continue_model = self.google_model.assert_continue_model
            self.submit_model = self.google_model.submit_model
        
        else:
            self.new_chat_model = self.openai_model.new_chat_model
            self.continue_chat_model = self.openai_model.continue_chat_model
            self.assert_continue_model = self.openai_model.assert_continue_model
            self.submit_model = self.openai_model.submit_model
        
        if models_settings.get('generate_image', 'google') == 'google':
            self.generate_image_model = self.google_model.generate_image_model
        else:
            self.generate_image_model = self.openai_model.generate_image_model
        if models_settings.get('generate_voice', 'google') == 'google':
            self.generate_voice_model = self.google_model.generate_voice_model
            self.voice_names = self.google_model.voice_names
        else:
            self.generate_voice_model = self.openai_model.generate_voice_model
            self.voice_names = self.openai_model.voice_names

    def new_chat(self, child_name: str, instruction: str) -> NewChat:
        if models_settings.get("core_model", "google") == "google":
            return self.google_model.new_chat(child_name, instruction)
        return self.openai_model.new_chat(child_name, instruction)
    
    def continue_chat(self, items:ChatItems, user_name:str) -> ContinueChat:
        if models_settings.get("core_model", "google") == "google":
            return self.google_model.continue_chat(items, user_name)
        return self.openai_model.continue_chat(items, user_name)
    
    async def submit(self, image_file: UploadFile, target:str, user_name:str) -> SubmitImageResponse:
        if models_settings.get("core_model", "google") == "google":
            return await self.google_model.submit(image_file, target, user_name)
        return await self.openai_model.submit(image_file, target, user_name)
    
    def generate_text_to_voice(self, content: str, instructions:str, user_id:str, voice_name:Optional[str]=None,
                               chat_id: Optional[str] = None, message_id: Optional[int] = None, feedback:bool=False) -> str:
        if models_settings.get("generate_voice", "google") == "google":
            return self.google_model.generate_text_to_voice(content, instructions, user_id, voice_name, chat_id, message_id, feedback)
        return self.openai_model.generate_text_to_voice(content, instructions, user_id, voice_name, chat_id, message_id, feedback)
    
    def generate_scene_image(self, description: str, user_id:str, 
                             chat_id:Optional[str] = None, message_id: Optional[int] = None) ->str:
        if models_settings.get("generate_image", "google") == "google":
            return self.google_model.generate_scene_image(description, user_id, chat_id, message_id)
        return self.openai_model.generate_scene_image(description, user_id, chat_id, message_id)