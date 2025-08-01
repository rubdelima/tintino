from pydantic import BaseModel, EmailStr, field_validator
from api.schemas.messages import MiniChat

class LoginHandler(BaseModel):
    email: EmailStr
    password: str
    
    @field_validator("password")
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return value

class CreateUser(LoginHandler):
    name: str

class UserDB(CreateUser):
    user_id: str

class User(UserDB):
    chats: list[MiniChat] = []