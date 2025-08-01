import requests

from api.schemas.users import LoginHandler, User, UserDB
from app.api_handler.utils import API_URL, DEFAULT_USER
from pydantic import ValidationError

def create_user(email:str, password:str)->UserDB:
    try:
        user = LoginHandler(email=email, password=password)
    except ValidationError as e:
        print(f"Validation error!")
        for err in e.errors():
            print(f"Campo: {err['loc'][0]}")
            print(f"Erro: {err['msg']}")
            print(f"Tipo: {err['type']}")
            print("="*30, end="\n\n")

        raise ValidationError(*[err['loc'][0] for err in e.errors()])

    response = requests.post(f"{API_URL}/api/users/create", json=user.model_dump())
    response.raise_for_status()
    return UserDB(**response.json())

def login_user(email: str, password: str) -> User:
    try:
        handler = LoginHandler(email=email, password=password)
    except ValidationError as e:
        print(f"Validation error!")
        for err in e.errors():
            print(f"Campo: {err['loc'][0]}")
            print(f"Erro: {err['msg']}")
            print(f"Tipo: {err['type']}")
            print("="*30, end="\n\n")
        raise ValidationError(*[err['loc'][0] for err in e.errors()])

    response = requests.post(f"{API_URL}/api/users/login", json=handler.model_dump())
    response.raise_for_status()
    return User(**response.json())

def get_user(user_id: str = DEFAULT_USER) -> User:
    response = requests.post(f"{API_URL}/api/users/get_user", json={"user_id": user_id})
    response.raise_for_status()
    return User(**response.json())