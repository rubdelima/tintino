from pydantic import BaseModel
from api.schemas.llm import ChatResponse, SubmitImageResponse
from typing import List, Optional
from datetime import datetime

class NewChatInput(BaseModel):
    audio_path: Optional[str] = None
    instruction : Optional[str] = None

class Message(BaseModel):
    message_index : int
    image : str
    audio : str
    data : ChatResponse

class SubmitImageMessage(BaseModel):
    message_index : int
    audio : str
    data : SubmitImageResponse

class MiniChat(BaseModel):
    chat_id: str
    title: str 
    chat_image : str
    last_update : datetime

class Chat(MiniChat):
    messages : List[Message] = []
    subimits : List[SubmitImageMessage] = []

class SubmitImageHandler(BaseModel):
    chat_id: str
    message_id: int
    image_path: str

