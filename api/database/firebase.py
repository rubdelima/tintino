import firebase_admin
from firebase_admin import credentials, firestore, storage #type:ignore
from google.cloud.firestore_v1 import ArrayUnion, FieldFilter #type:ignore
from fastapi import UploadFile, HTTPException
import uuid
from datetime import datetime, timezone

from api.database.interface import DatabaseInterface, get_mime_extension
from api.schemas.users import User, CreateUser, UserDB, LoginHandler
from api.schemas.messages import Chat, MiniChat, SubmitImageMessage, Message

from api.utils.logger import get_logger

logger = get_logger(__name__)

class FirebaseDB(DatabaseInterface):
    def __init__(self) -> None:
        try:
            cred = credentials.Certificate("firebase.json")

            project_id = cred.project_id
            storage_bucket_url = f"{project_id}.appspot.com"

            firebase_admin.initialize_app(cred, {
                'storageBucket': storage_bucket_url
            })

            logger.info("Firebase inicializado com sucesso.")

            self.db = firestore.client()
            self.bucket = storage.bucket()

        except Exception as e:
            logger.error(f"Erro ao inicializar o Firebase: {e}")
            raise HTTPException(
                status_code=500, detail="Não foi possível conectar ao Firebase.")

    # --- User Functions ---

    def create_user(self, temp_user: CreateUser) -> UserDB:
        user_id = str(uuid.uuid4())
        user = UserDB(
            user_id=user_id,
            **temp_user.model_dump(),
        )
        
        self.db.collection('users').document(user_id).set(user.model_dump())
        logger.info(f"Usuário criado no Firestore com ID: {user_id}")
        return user

    def login_user(self, login_handler: LoginHandler) -> User:
        users_ref = self.db.collection('users')
        
        query = users_ref.\
            where(FieldFilter('email', '==', login_handler.email)).\
                where(FieldFilter('password', '==', login_handler.password)).\
            limit(1)

        results = list(query.stream())

        if not results:
            raise ValueError("Invalid email or password")

        user_data = results[0].to_dict()

        return User(**user_data, chats=self.get_user_chats(user_data['user_id']))

    def get_user(self, user_id: str) -> User:
        doc_ref = self.db.collection('users').document(user_id)
        user_doc = doc_ref.get()

        if not user_doc.exists:
            raise ValueError("User not found")

        user_data = user_doc.to_dict()
        return User(**user_data, chats=self.get_user_chats(user_id))

    # --- Chat Functions ---

    def get_user_chats(self, user_id: str) -> list[MiniChat]:
        chats_ref = self.db.collection('chats')
        
        query = chats_ref.\
            where(FieldFilter('user_id', '==', user_id)).\
            order_by('last_update', direction=firestore.Query.DESCENDING)

        user_chats = [MiniChat(**doc.to_dict()) for doc in query.stream()]
        return user_chats

    async def store_archive(self, user_id: str, file: UploadFile) -> str:
        try:
            content, mime, extension = await get_mime_extension(file)
            
            file_id = str(uuid.uuid4())
            blob_name = f"archives/{user_id}/{file_id}{extension}"
        
            blob = self.bucket.blob(blob_name)

            blob.upload_from_string(
                content,
                content_type=mime
            )

            blob.make_public()

            logger.info(
                f"Arquivo salvo no Cloud Storage em: {blob.public_url}")
            
            return blob.public_url

        except Exception as e:
            logger.error(f"Erro ao salvar arquivo no Cloud Storage: {e}")
            raise e

    def get_chat(self, chat_id: str, user_id: str) -> Chat:
        doc_ref = self.db.collection('chats').document(chat_id)
        chat_doc = doc_ref.get()

        if not chat_doc.exists:
            raise ValueError("Chat not found")

        chat_data = chat_doc.to_dict()
        if chat_data.get('user_id') != user_id:
            raise ValueError("Unauthorized access")

        return Chat(**chat_data)

    def save_chat(self, chat: MiniChat) -> None:
        self.db.collection('chats').document(
            chat.chat_id).set(chat.model_dump())

    def update_chat(self, user_id: str, chat_id: str, target: str, item: SubmitImageMessage | Message) -> None:
        doc_ref = self.db.collection('chats').document(chat_id)

        chat_doc = doc_ref.get()
        
        if not chat_doc.exists:
            raise ValueError("Chat not found")
        
        if chat_doc.to_dict().get('user_id') != user_id:
            raise ValueError("Unauthorized access")

        doc_ref.update({
            target: ArrayUnion([item.model_dump()]),
            'last_update': datetime.now(tz=timezone.utc).isoformat()
        })