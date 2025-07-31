from abc import ABC, abstractmethod
from api.schemas.users import User, CreateUser, UserDB, LoginHandler
from api.schemas.messages import Chat, MiniChat, SubmitImageMessage, Message
from fastapi import UploadFile
import magic
import mimetypes
from typing import Literal

async def get_mime_extension(file: UploadFile):
    try:
        content = await file.read()
        await file.seek(0)
        
        mime = magic.from_buffer(content, mime=True)
        extension = mimetypes.guess_extension(mime) or '.bin'
        
        return content, mime, extension
        
    except Exception as e:
        await file.seek(0)
        content = await file.read()
        await file.seek(0)
        return content, 'application/octet-stream', '.bin'

class DatabaseInterface(ABC):
    
    # User Functions
    @abstractmethod
    def create_user(self, temp_user: CreateUser) -> UserDB:
        """Create a new user."""
        pass

    @abstractmethod
    def login_user(self, login_handler: LoginHandler) -> User:
        """Log in a user by their email and password."""
        pass

    @abstractmethod
    def get_user(self, user_id: str) -> User:
        """Retrieve a user by their ID."""
        pass
    
    @abstractmethod
    def verify_user(self, user_id: str) -> bool:
        """Verify if a user exists by their ID."""
        pass
    
    # Chat Functions
    @abstractmethod
    def get_user_chats(self, user_id: str) -> list[MiniChat]:
        """Retrieve all chats for a given user."""
        pass
    
    @abstractmethod
    async def store_archive(self, user_id: str, file: UploadFile) -> str:
        """Store an archive file for a user."""
        pass
    
    @abstractmethod
    def get_chat(self, chat_id: str, user_id:str) -> Chat:
        """Retrieve a chat by its ID."""
        pass
    
    @abstractmethod
    def save_chat(self, chat: MiniChat) -> None:
        """Save a chat."""
        pass
    
    @abstractmethod
    def update_chat(self, user_id: str, chat_id: str, target: Literal["messages", "submits"], item: SubmitImageMessage | Message) -> None:
        """Update a chat by adding a message or submission."""
        pass