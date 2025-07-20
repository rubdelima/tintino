from pydantic import BaseModel
from api.schemas.llm import ChatResponse, SubmitImageResponse
from typing import List, Optional

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

class Chat(BaseModel):
    chat_id : str
    title : str
    messages : List[Message]
    submit_image_messages : List[SubmitImageMessage]

