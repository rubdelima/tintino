from abc import ABC, abstractmethod
from api.schemas.llm import NewChat, ContinueChat, SubmitImageResponse, AssertContinueChat
from api.schemas.messages import ChatItems
from typing import Literal, Optional
from fastapi import UploadFile

models_list = ["global", "new_chat", "continue_chat", "submit", "assert_continue"]

class CoreModelInterface(ABC):
    
    @abstractmethod
    def get_model_name(self, source: Literal["global", "new_chat", "continue_chat", "submit", "assert_continue"]) -> str:
        pass

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
    def generate_text_to_voice(self, prompt: str, user_id:str, voice_name:Optional[str]=None, chat_id: Optional[str] = None, message_id: Optional[int] = None, feedback:bool=False) -> str:
        pass
