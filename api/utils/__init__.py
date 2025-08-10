import json
import base64
from typing import Optional
import magic
import mimetypes
from fastapi import UploadFile
import uuid
from pathlib import Path
import os
import io
import wave

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

async def get_mime_extension(file: UploadFile):
    try:
        content = await file.read()
        await file.seek(0)
        
        mime = magic.from_buffer(content, mime=True)
        extension = mimetypes.guess_extension(mime) or '.bin'
        
        return content, mime, extension
        
    except Exception as e:
        await file.seek(0)
        content = await file.read()
        await file.seek(0)
        return content, 'application/octet-stream', '.bin'

async def store_temp_file(file: UploadFile) -> tuple[str, str]:
    temp_id = str(uuid.uuid4())
    
    content, mime, extension = await get_mime_extension(file)
    
    temp_dir = Path('./temp') / temp_id
    os.makedirs(temp_dir, exist_ok=True)
    file_path = temp_dir / f"file{extension}"
    
    file_path.write_bytes(content)
    
    return str(file_path), mime

def generate_filename(mime_type: str, base_filename: Optional[str]) -> str:

    if base_filename is None:
        base_filename = str(uuid.uuid4())
    
    extension = mimetypes.guess_extension(mime_type)
    
    if not extension:
        extension = '.bin'
        
    return f"{base_filename}{extension}"

def convert_raw_audio_to_wav(raw_audio_data: bytes,channels: int = 1,sampwidth: int = 2,framerate: int = 24000) -> bytes:    
    wav_in_memory = io.BytesIO()
    with wave.open(wav_in_memory, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(raw_audio_data)
        
    return wav_in_memory.getvalue()