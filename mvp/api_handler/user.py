import requests

from api.schemas.users import User, UserDB, CreateUser
from mvp.api_handler.utils import API_URL, DEFAULT_USER

def create_user(name: str, token: str) -> UserDB:
    user_data = CreateUser(name=name)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{API_URL}/api/users/create", 
        json=user_data.model_dump(),
        headers=headers
    )
    response.raise_for_status()
    return UserDB(**response.json())

def get_current_user(token: str) -> User:
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{API_URL}/api/users/me",
        headers=headers
    )
    response.raise_for_status()
    return User(**response.json())

def get_user(user_id: str = DEFAULT_USER) -> User:
    response = requests.post(f"{API_URL}/api/users/get_user", json={"user_id": user_id})
    response.raise_for_status()
    return User(**response.json())