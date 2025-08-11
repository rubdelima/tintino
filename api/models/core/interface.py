from abc import ABC, abstractmethod
from api.schemas.llm import NewChat, ContinueChat, SubmitImageResponse, AssertContinueChat
from api.schemas.messages import ChatItems
from typing import Literal, Optional
from fastapi import UploadFile

models_list = ["global", "new_chat", "continue_chat", "submit", "assert_continue"]

class CoreModelInterface(ABC):
    global_model : str
    new_chat_model : str
    continue_chat_model : str
    submit_model :str
    assert_continue_model : str
    generate_image_model : str
    generate_voice_model : str
    
    def get_model_name(self, source: Literal["global", "new_chat", "continue_chat", "submit", "assert_continue"]) -> str:
        if source not in models_list:
            raise ValueError(f"Modelo desconhecido: {source}")
        if source == "global":
            return self.global_model
        
        return f"{self.global_model} : {getattr(self, f'{source}_model')}"

    @abstractmethod
    def new_chat(self, child_name:str, instruction:str) ->NewChat:
        pass
    
    @abstractmethod
    def continue_chat(self, items:ChatItems, user_name:str) -> ContinueChat:
        pass

    @abstractmethod
    async def submit(self, image_file: UploadFile, target:str, user_name:str) -> SubmitImageResponse:
        pass
    
    @abstractmethod
    def generate_scene_image(self, description: str, user_id:str, chat_id:Optional[str] = None, message_id: Optional[int] = None) ->str:
        pass
    
    @abstractmethod
    def generate_text_to_voice(self, content: str, instructions:str, user_id:str, voice_name:Optional[str]=None, chat_id: Optional[str] = None, message_id: Optional[int] = None, feedback:bool=False) -> str:
        pass
