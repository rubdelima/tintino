from pydantic import BaseModel
from api.schemas.messages import MiniChat

class LoginHandler(BaseModel):
    email: str
    password: str

class CreateUser(LoginHandler):
    name: str

class UserDB(CreateUser):
    user_id: str

class User(UserDB):
    chats: list[MiniChat] = []