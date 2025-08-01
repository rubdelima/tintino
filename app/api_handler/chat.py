import os
import requests
from typing import List, Optional

from app.api_handler.utils import get_mime_from_path, API_URL, DEFAULT_USER
from api.schemas.messages import SubmitImageMessage, Chat, MiniChat

def get_chats(user_id : Optional[str] = None) -> List[MiniChat]:
    """Retrieve all chats from the API."""
    response = requests.get(
        f"{API_URL}/api/chat/", 
        headers={
            "Authorization": f"Bearer {user_id if user_id else DEFAULT_USER}"
        }
    )

    if response.status_code == 200:
        return [MiniChat(**chat) for chat in response.json()]
    
    raise Exception(f"Failed to retrieve chats: {response.status_code} - {response.text}")

def create_chat(audio_path: str, user_id : Optional[str] = None ) -> Chat:
    """Create a new chat session."""
    content, mime, _ = get_mime_from_path(audio_path)
    
    response = requests.post(
        f"{API_URL}/api/chat/",
        headers={
            "Authorization": f"Bearer {user_id if user_id else DEFAULT_USER}"
        },
        files={
            "voice_audio": (os.path.basename(audio_path), content, mime)
        }
    )
    
    if response.status_code == 201:
        return Chat(**response.json())

    raise Exception(f"Failed to create chat: {response.status_code} - {response.text}")

def get_chat(chat_id: str, user_id: Optional[str] = None) -> Chat:
    """Retrieve a specific chat by its ID."""
    response = requests.get(
        f"{API_URL}/api/chat/{chat_id}",
        headers={
            "Authorization": f"Bearer {user_id if user_id else DEFAULT_USER}"
        }
    )

    if response.status_code == 200:
        return Chat(**response.json())

    raise Exception(f"Failed to retrieve chat: {response.status_code} - {response.text}")

def submit_image(chat_id: str, image_path: str, user_id: Optional[str] = None) -> SubmitImageMessage:
    """Submit an image for a specific chat."""
    content, mime, extension = get_mime_from_path(image_path)
    response = requests.post(
        f"{API_URL}/api/chat/{chat_id}/submit_image",
        headers={
            "Authorization": f"Bearer {user_id if user_id else DEFAULT_USER}"
        },
        files={
            "image": (os.path.basename(image_path), content, mime)
        }
    )

    if response.status_code == 201:
        return SubmitImageMessage(**response.json())

    raise Exception(f"Failed to submit image: {response.status_code} - {response.text}")
