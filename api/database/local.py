from fastapi import UploadFile, HTTPException
import json
import os
from functools import wraps
import uuid
from pathlib import Path
from datetime import datetime, timezone

from api.database.interface import *
from api.utils.logger import get_logger
from api.constraints import config
from api.schemas.messages import MiniChat, ChatItems
from api.schemas.users import CreateUser
from api.constraints import config
from api.utils import get_mime_extension, generate_filename

database_configs = config.get("Database", {})
# Obter usuário de teste do config
TEST_USER = config.get("APISettings", {}).get("test_user", "")

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
        self.temp_chat_ids = {}
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
    def create_user(self, user_data: CreateUser, user_id: str) -> UserDB:
        user = UserDB(
            user_id=user_id,
            name=user_data.name
        )
        self.users[user_id] = user.model_dump()
        return user
    
    def get_user(self, user_id: str) -> User:
        temp_user = self.users.get(user_id)
        if not temp_user:
            raise ValueError("User not found")
        
        return User(**temp_user, chats=self.get_user_chats(user_id))
    
    def verify_user(self, user_id: str) -> bool:
        # Sempre permitir usuário de teste do config
        if user_id == TEST_USER:
            return True
        return user_id in self.users
    
    def get_user_chats(self, user_id: str) -> list[MiniChat]:
        user_chats = [
            MiniChat(**chat) for chat in self.chats.values()
            if chat['user_id'] == user_id
        ]
        user_chats.sort(key=lambda x: x.last_update, reverse=True)
        return user_chats
    
    def get_chat_items(self, chat_id: str) -> ChatItems:
        chat = self.chats.get(chat_id)
        
        if not chat:
            raise ValueError("Chat not found")
        
        chat_messages = chat.get('messages')

        chat_messages.sort(key=lambda x: x['message_index'])

        return ChatItems(
            history="\n".join(item["text_voice"] for item in chat_messages),
            painted_items=", ".join(item["paint_image"] for item in chat_messages),
            last_image=chat_messages[-1]["image"]
        ) 
    
    async def store_user_archive(self, user_id: str, file: UploadFile) -> str:
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
    
    def upload_generated_archive(
            self, 
            file_bytes: bytes, 
            destination_path: str, 
            mime_type: str,
            base_filename: Optional[str] = None) -> str:
        
        filename = generate_filename(mime_type, base_filename)
        
        file_path = Path(f'./temp/archives/{destination_path}') / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(file_bytes)
        
        file_path_str = str(file_path)
        logger.info(f"Arquivo {mime_type} salvo em: {file_path_str}")

        return file_path_str
    
    def assert_chat_exists(self, chat_id: str, user_id: str) -> dict:
        if chat_id not in self.chats:
            raise HTTPException(status_code=404, detail="Chat not found")
        if self.chats[chat_id]['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized access")
        return self.chats[chat_id]
    
    def get_chat(self, chat_id: str, user_id:str) -> Chat:
        temp_chat = self.assert_chat_exists(chat_id, user_id)
        return Chat(**temp_chat)
    
    def generate_new_chat_id(self) -> str:
        while (chat_id := str(uuid.uuid4())) in self.chats:
            continue
        return chat_id
    
    def get_new_chat_id(self, user_id:str) -> str:
        chat_id = self.generate_new_chat_id()
        self.temp_chat_ids[user_id] = chat_id
        return chat_id
    
    @auto_save
    def save_chat(self, user_id: str, chat: MiniChatBase) -> MiniChat:
        
        chat_id = self.temp_chat_ids.get(user_id)
        if chat_id is None:
            chat_id = self.generate_new_chat_id()
        else:
            del self.temp_chat_ids[user_id]
        
        self.chats[chat_id] = Chat(chat_id=chat_id, **chat.model_dump())
        return self.chats[chat_id]
    
    @auto_save
    def update_chat(self, user_id: str, chat_id: str, target: Literal["messages", "submits"], item: SubmitImageMessage | Message) -> None:
        assert target in ["messages", "submits"], "Target must be 'messages' or 'submits'"
        
        if chat_id not in self.chats:
            raise ValueError("Chat not found")
        
        if self.chats[chat_id]["user_id"] != user_id:
            raise ValueError("Unauthorized access")

        self.chats[chat_id][target].append(item.model_dump())
        self.chats[chat_id]["last_update"] = datetime.now(tz=timezone.utc).isoformat()