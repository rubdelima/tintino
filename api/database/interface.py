from abc import ABC, abstractmethod
from api.schemas.users import User, CreateUser, UserDB, LoginHandler
from api.schemas.messages import Chat, MiniChatBase, MiniChat, SubmitImageMessage, Message, ChatItems
from fastapi import UploadFile
from typing import Literal, Optional, Any

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
    def get_chat_items(self, chat_id: str) -> ChatItems:
        """Retrieve all messages for a given chat."""
        pass

    @abstractmethod
    async def store_user_archive(self, user_id: str, file: UploadFile) -> str:
        """Store an archive file for a user."""
        pass
    
    @abstractmethod
    def upload_generated_archive(
            self, 
            file_bytes: bytes, 
            destination_path: str, 
            mime_type: str,
            base_filename: Optional[str] = None) -> str:
        
        """Upload an generated file."""
        pass
    
    @abstractmethod
    def assert_chat_exists(self, chat_id: str, user_id: str) -> Any:
        """Check if a chat exists and belongs to the user."""
        pass
    
    @abstractmethod
    def get_chat(self, chat_id: str, user_id:str) -> Chat:
        """Retrieve a chat by its ID."""
        pass
    
    @abstractmethod
    def get_new_chat_id(self, user_id:str) -> str:
        """Generate a new unique chat ID."""
        pass
    
    @abstractmethod
    def save_chat(self, user_id: str, chat: MiniChatBase) -> MiniChat:
        """Save a chat."""
        pass
    
    @abstractmethod
    def update_chat(self, user_id: str, chat_id: str, target: Literal["messages", "submits"], item: SubmitImageMessage | Message) -> None:
        """Update a chat by adding a message or submission."""
        pass
    