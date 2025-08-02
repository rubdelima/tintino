import requests
import mimetypes
import magic #type:ignore
import os
from api.constraints import config

API_SETTINGS = config.get("APISettings", {})
HOST = API_SETTINGS.get("host", "0.0.0.0")
PORT = API_SETTINGS.get("port", 8000)

DEFAULT_USER = API_SETTINGS.get("test_user", "f4b7b9e2-b26a-480a-ac43-0e085482390f")

API_URL = os.getenv("API_BASE_URL")
if not API_URL:
    API_URL = API_SETTINGS.get("url", False)
    if not API_URL:
        API_URL = f"http://{HOST}:{PORT}"

def get_mime_from_path(file_path: str) -> tuple[bytes, str, str]:
    with open(file_path, "rb") as f:
        content = f.read()
    try:
        mime = magic.from_buffer(content, mime=True)
        extension = mimetypes.guess_extension(mime) or ".bin"
        return content, mime, extension
    except Exception:
        return content, "application/octet-stream", ".bin"

def test_api_connection() -> bool:
    """Test the connection to the API."""
    try:
        response = requests.get(f"{API_URL}/")
        print(response.json())
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"Error connecting to API: {e}")
        return False