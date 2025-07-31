from fastapi import UploadFile
from api.database.interface import *
import json
import os
from functools import wraps
import uuid
from pathlib import Path

from api.utils.logger import get_logger
from api.constraints import config
from api.schemas.messages import MiniChat
from api.schemas.users import CreateUser
from datetime import datetime, timezone

database_configs = config.get("Database", {})

logger = get_logger(__name__)

def load_json(file_path: str):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        return {}

def save_json(file_path: str, data: dict):
    try:
        with open(file_path, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        raise e

def auto_save(func):
    """Salva automaticamente os arquivos de usuários e chats"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if hasattr(self, 'save') and self.save:
            save_json("./temp/users.json", self.users)
            save_json("./temp/chats.json", self.chats)
        return result
    return wrapper

class LocalDatabase(DatabaseInterface):
    def __init__(self) -> None:
        self.save = database_configs.get('save_local', False)
        if self.save:
            self.load_db()
        else:
            self.users = {}
            self.chats = {}
            self.archives = set()
    
    def load_db(self):
        os.makedirs("./temp/", exist_ok=True)
        self.chats = load_json("./temp/chats.json")
        self.users = load_json("./temp/users.json")
        self.archives = {
                path.stem for path in Path("./temp/archives").glob("**/*") 
                if path.is_file()
            } if Path("./temp/archives").exists() else set()
        
    @auto_save
    def create_user(self, temp_user: CreateUser) -> UserDB:
        user_id = str(uuid.uuid4())
        user = UserDB(
            user_id=user_id,
            **temp_user.model_dump(),
        )
        self.users[user_id] = user.model_dump()
        return user
    
    def login_user(self, login_handler: LoginHandler) -> User:
        temp_user = next((
            UserDB(**data) for data in self.users.values()
            if data['email'] == login_handler.email and data['password'] == login_handler.password
        ), None)
        
        if not temp_user:
            raise ValueError("Invalid email or password")
        
        return User(**temp_user.model_dump(), chats=self.get_user_chats(temp_user.user_id))
    
    def get_user(self, user_id: str) -> User:
        temp_user = self.users.get(user_id)
        if not temp_user:
            raise ValueError("User not found")
        
        return User(**temp_user.model_dump(), chats=self.get_user_chats(user_id))
    
    def verify_user(self, user_id: str) -> bool:
        return user_id in self.users
    
    def get_user_chats(self, user_id: str) -> list[MiniChat]:
        user_chats = [
            MiniChat(**chat) for chat in self.chats.values()
            if chat['user_id'] == user_id
        ]
        user_chats.sort(key=lambda x: x.last_update, reverse=True)
        return user_chats
    
    async def store_archive(self, user_id: str, file: UploadFile) -> str:
        try:
            user_path = Path(f"./temp/archives/{user_id}")
            user_path.mkdir(parents=True, exist_ok=True)
            
            content, mime, extension = await get_mime_extension(file)
            
            while (file_id := f"{uuid.uuid4()}") in self.archives:
                continue

            file_name = f"{file_id}{extension}"
            file_path = user_path / file_name
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            del content
            
            logger.info(f"Arquivo {mime} salvo em: {file_path}")
            return str(file_path)
        
        except Exception as e:
            logger.error(f"Error storing archive: {e}")
            raise e
        
    def get_chat(self, chat_id: str, user_id:str) -> Chat:
        temp_chat = self.chats.get(chat_id)
        if not temp_chat:
            raise ValueError("Chat not found")

        if temp_chat['user_id'] != user_id:
            raise ValueError("Unauthorized access")

        return Chat(**temp_chat.model_dump())
    
    @auto_save
    def save_chat(self, chat: MiniChat) -> None:
        self.chats[chat.chat_id] = Chat(**chat.model_dump())
    
    @auto_save
    def update_chat(self, user_id: str, chat_id: str, target: Literal["messages", "submits"], item: SubmitImageMessage | Message) -> None:
        assert target in ["messages", "submits"], "Target must be 'messages' or 'submits'"
        
        if chat_id not in self.chats:
            raise ValueError("Chat not found")
        
        if self.chats[chat_id]["user_id"] != user_id:
            raise ValueError("Unauthorized access")

        self.chats[chat_id][target].append(item.model_dump())
        self.chats[chat_id]["last_update"] = datetime.now(tz=timezone.utc).isoformat()