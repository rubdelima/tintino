import firebase_admin
from firebase_admin import credentials, firestore, storage  # type:ignore
from fastapi import HTTPException, UploadFile
import uuid
import os
from datetime import datetime, timezone
import json
from typing import Optional, Any, Dict, cast
from api.database.interface import DatabaseInterface
from api.schemas.users import User, CreateUser, UserDB
from api.schemas.messages import Chat, ChatItems, MiniChatBase, MiniChat, SubmitImageMessage, Message
from api.utils import get_mime_extension, generate_filename
from api.utils.logger import get_logger
from api.constraints import config

logger = get_logger(__name__)

def get_credentials() -> dict:
    firebase_config_str = os.getenv('FIREBASE_CREDENTIALS_JSON')
    if not firebase_config_str:
        possible_paths = [
            "./firebase.json",
            "/etc/secrets/firebase.json"
        ]

        for path in possible_paths:
            if os.path.exists(path):
                with open(path) as f:
                    firebase_config_str = f.read()
                    break

        if not firebase_config_str:
            raise FileNotFoundError("Arquivo firebase.json não encontrado em nenhum dos locais esperados")

    return json.loads(firebase_config_str)

# Obter usuário de teste do config
TEST_USER = config.get("APISettings", {}).get("test_user", "")



class FirebaseDB(DatabaseInterface):
    def __init__(self) -> None:
        try:
            cred = credentials.Certificate(get_credentials())

            project_id = cred.project_id
            storage_bucket_url = f"{project_id}.firebasestorage.app"

            firebase_admin.initialize_app(cred, {
                'storageBucket': storage_bucket_url
            })

            logger.info("Firebase inicializado com sucesso.")

            self.db = firestore.client()
            self.bucket = storage.bucket()
            self.temp_chat_ids: Dict[str, str] = {}
            # Armazena mensagens pré-geradas (pending) em memória, similar ao LocalDatabase
            # Estrutura: { chat_id: Message.dict() }
            self.pending_messages: Dict[str, dict] = {}

        except Exception as e:
            logger.error(f"Erro ao inicializar o Firebase: {e}")
            raise HTTPException(
                status_code=500, detail="Não foi possível conectar ao Firebase.")

    # --- Pending Message Helpers (para pre-generation) ---
    def set_pending_message(self, chat_id: str, message: Any) -> None:
        """Salva/atualiza mensagem pré-gerada em memória."""
        self.pending_messages[chat_id] = message

    def pop_pending_message(self, chat_id: str) -> Optional[Any]:
        """Retorna e remove a mensagem pré-gerada do chat, se existir."""
        return self.pending_messages.pop(chat_id, None)

    # --- User Functions ---

    def create_user(self, user_data: CreateUser, user_id: str) -> UserDB:
        user_doc = self.db.collection('users').document(user_id).get()
        if user_doc.exists:
            # Usuário já existe, retorna o existente
            user_data_db = user_doc.to_dict() or {}
            return UserDB(user_id=user_id, name=user_data_db.get('name', user_data.name))
        user = UserDB(
            user_id=user_id,
            name=user_data.name
        )
        self.db.collection('users').document(user_id).set(user.model_dump())
        logger.info(f"Usuário criado no Firestore com ID: {user_id}")
        return user

    def get_user(self, user_id: str) -> User:
        user_doc = self.db.collection('users').document(user_id).get()
        if not user_doc.exists:
            raise ValueError("User not found")

        user_data = cast(dict[str, Any], user_doc.to_dict())
        return User(**user_data, chats=self.get_user_chats(user_id))
    
    def verify_user(self, user_id: str) -> bool:
        # Sempre permitir usuário de teste do config
        if user_id == TEST_USER:
            return True
            
        user_doc = self.db.collection('users').document(user_id).get()
        return user_doc.exists

    # --- Chat Functions ---

    def get_user_chats(self, user_id: str) -> list[MiniChat]:
        chats_ref = self.db.collection('chats')
        stream = chats_ref.where('user_id', '==', user_id).stream()
        user_chats = [MiniChat(**(doc.to_dict() or {})) for doc in stream]
        user_chats.sort(key=lambda x: x.last_update, reverse=True)
        
        return user_chats
    
    def get_chat_items(self, chat_id: str) -> ChatItems:
        messages_ref = self.db.collection("messages")
        stream = messages_ref.where('chat_id', '==', chat_id).stream()
        chat_items = [doc.to_dict() for doc in stream]
        chat_items.sort(key=lambda x: x['message_index'])
        
        return ChatItems(
            history="\n".join(item["text_voice"] for item in chat_items),
            painted_items=", ".join(item["paint_image"] for item in chat_items),
            last_image=chat_items[-1]["image"]
        )
    
    def upload_archive(self, file_bytes:bytes, blob_path:str, mime_type) ->str:
        blob = self.bucket.blob(blob_path)
        
        blob.upload_from_string(
            file_bytes,
            content_type=mime_type
        )
        
        blob.make_public()
        
        logger.info(f"Arquivo salvo/sobrescrito para o Cloud Storage (Firebase) em: {blob.public_url}")
        
        return blob.public_url
    
    async def store_user_archive(self, user_id: str, file: UploadFile) -> str:
        try:
            content, mime, extension = await get_mime_extension(file)
            
            file_id = str(uuid.uuid4())
            blob_name = f"archives/{user_id}/{file_id}{extension}"
        
            return self.upload_archive(content, blob_name, mime)

        except Exception as e:
            logger.error(f"Erro ao salvar arquivo no Cloud Storage: {e}")
            raise e
        
    def upload_generated_archive(
        self, 
        file_bytes: bytes, 
        destination_path: str, 
        mime_type: str,
        base_filename: Optional[str] = None
    ) -> str:
    
        filename = generate_filename(mime_type, base_filename)
        blob_name = f"{destination_path}/{filename}"
        
        try:
            return self.upload_archive(file_bytes, blob_name, mime_type)
        except Exception as e:
            logger.error(f"Erro ao fazer upload do arquivo gerado: {e}")
            raise e

    def assert_chat_exists(self, chat_id: str, user_id: str) -> tuple[firestore.DocumentReference, MiniChat]:
        chat_ref = self.db.collection('chats').document(chat_id)
        chat_doc = chat_ref.get()
        
        if not chat_doc.exists:
            raise HTTPException(status_code=404, detail="Chat not found")
        chat_data = chat_doc.to_dict() or {}
        if chat_data.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized access")
        return chat_ref, MiniChat(**chat_data)
    
    def get_chat(self, chat_id: str, user_id: str) -> Chat:
        _, chat_data = self.assert_chat_exists(chat_id, user_id)
        messages_ref = self.db.collection('messages')
        messages_docs = list(messages_ref.where('chat_id', '==', chat_id).stream())
        messages = [Message(**(doc.to_dict() or {})) for doc in messages_docs]
        messages.sort(key=lambda x: x.message_index)
        submits_ref = self.db.collection('submits')
        sub_docs = list(submits_ref.where('chat_id', '==', chat_id).stream())
        subimits = [SubmitImageMessage(**(doc.to_dict() or {})) for doc in sub_docs]
        subimits = [s for s in subimits if s.data.is_correct]
        subimits.sort(key=lambda x: x.message_index)
        return Chat(
            messages=messages,
            subimits=subimits,
            **chat_data.model_dump()
        )
    
    def generate_new_chat_id(self) ->str:
        while self.db.collection('chats').document(chat_id := str(uuid.uuid4())).get().exists:
            pass
        return chat_id

    def get_new_chat_id(self, user_id: str) -> str:
        chat_id = self.generate_new_chat_id()
        self.temp_chat_ids[user_id] = chat_id
        return chat_id

    def save_chat(self, user_id :str, chat: MiniChatBase) -> MiniChat:
        chat_json = chat.model_dump()
        
        chat_json['user_id'] = user_id
        
        chat_id = self.temp_chat_ids.get(user_id)
        if chat_id is None:
            chat_id = self.generate_new_chat_id()
        else:
            del self.temp_chat_ids[user_id]
        chat_json['chat_id'] = chat_id
        
        chat_json['last_update'] = datetime.now(tz=timezone.utc).isoformat()
        
        self.db.collection('chats').document(chat_json['chat_id']).set(chat_json)
        
        return MiniChat(**chat_json)

    def update_chat(self, user_id: str, chat_id: str, target: str, item: SubmitImageMessage | Message) -> None:
        doc_ref, doc_data = self.assert_chat_exists(chat_id, user_id)

        doc_ref.update({'last_update': datetime.now(tz=timezone.utc).isoformat()})
        
        message_id = str(uuid.uuid4())
        
        item_json = item.model_dump()
        item_json["chat_id"] = chat_id
        
        self.db.collection(target).document(message_id).set(item_json)
