from pydantic import BaseModel
from api.schemas.llm import ContinueChat, SubmitImageResponse
from typing import List, Optional
from datetime import datetime

class ChatItems(BaseModel):
    history: str
    painted_items: str
    last_image: str

class NewChatInput(BaseModel):
    audio_path: Optional[str] = None
    instruction : Optional[str] = None

class Message(ContinueChat):
    message_index : int
    image : str
    audio : str
    
class SubmitImageMessage(BaseModel):
    message_index : int
    audio : str
    image : Optional[str] = None
    data : SubmitImageResponse

class MiniChatBase(BaseModel):
    title: str 
    chat_image : str
    last_update : datetime

class MiniChat(MiniChatBase):
    chat_id: str

class Chat(MiniChat):
    messages : List[Message] = []
    subimits : List[SubmitImageMessage] = []

class SubmitImageHandler(BaseModel):
    chat_id: str
    message_id: int
    image_path: str

