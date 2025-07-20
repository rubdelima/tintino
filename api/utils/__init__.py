import json
import base64
from typing import Optional

def load_json(file_path: str) -> dict:
    with open(file_path, "r") as f:
        return json.load(f)


def save_json(file_path: str, data: dict) -> None:
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)


def path_to_b64(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def image_to_b64(image: str, text:Optional[str] = None) -> dict:
    data = {
        "type": "image",
        "source_type": "base64",
        "data": path_to_b64(image),
        "mime_type": "image/png"
    }
    if text:
        data["text"] = text
    return data
