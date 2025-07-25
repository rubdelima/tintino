from api.schemas.llm import ChatResponse, SubmitImageResponse, SubmitImageAPIResponse
from api.schemas.messages import NewChatInput, Message, SubmitImageMessage, Chat, SubmitImageHandler
from api.constraints import config
from typing import List, Optional

import requests

API_SETTINGS = config.get("APISettings", {})
HOST = API_SETTINGS.get("host", "0.0.0.0")
PORT = API_SETTINGS.get("port", 8000)

API_URL = API_SETTINGS.get("url", False)
if not API_URL:
    API_URL = f"http://{HOST}:{PORT}"

def test_api_connection() -> bool:
    """Test the connection to the API."""
    try:
        response = requests.get(f"{API_URL}/")
        print(response.json())
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"Error connecting to API: {e}")
        return False

def get_chats() -> List[Chat]:
    """Retrieve all chats from the API."""
    response = requests.get(f"{API_URL}/api/chat/")
    
    if response.status_code == 200:
        return [Chat(**chat) for chat in response.json()]
    
    raise Exception(f"Failed to retrieve chats: {response.status_code} - {response.text}")

def create_chat(audio_path: Optional[str] = None, instruction: Optional[str] = None) -> Chat:
    """Create a new chat session."""
    assert audio_path or instruction, "Either audio_path or instruction must be provided."
    input_data = NewChatInput(audio_path=audio_path, instruction=instruction)

    response = requests.post(f"{API_URL}/api/chat/", json=input_data.model_dump())
    if response.status_code == 201:
        return Chat(**response.json())

    raise Exception(f"Failed to create chat: {response.status_code} - {response.text}")

def get_chat(chat_id: str) -> Chat:
    """Retrieve a specific chat by its ID."""
    response = requests.get(f"{API_URL}/api/chat/{chat_id}")
    if response.status_code == 200:
        return Chat(**response.json())

    raise Exception(f"Failed to retrieve chat: {response.status_code} - {response.text}")

def submit_image(chat_id: str, message_id: int, image_path: str) -> SubmitImageAPIResponse:
    """Submit an image for a specific chat."""
    if not chat_id or not message_id or not image_path:
        raise ValueError("chat_id, message_id, and image_path must be provided.")

    input_data = SubmitImageHandler(chat_id=chat_id, message_id=message_id, image_path=image_path)
    response = requests.post(f"{API_URL}/api/chat/{chat_id}", json=input_data.model_dump())
    if response.status_code == 200:
        return SubmitImageAPIResponse(**response.json())

    raise Exception(f"Failed to submit image: {response.status_code} - {response.text}")
