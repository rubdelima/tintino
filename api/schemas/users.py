from pydantic import BaseModel
from api.schemas.messages import MiniChat

class CreateUser(BaseModel):
    name: str

class UserDB(BaseModel):
    user_id: str
    name: str

class User(UserDB):
    chats: list[MiniChat] = []