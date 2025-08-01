from openai import OpenAI
from fastapi import UploadFile
import magic
import os
from pathlib import Path

from api.constraints import config
from api.models.speech_to_text.utils import convert_to_wav

client = OpenAI()

openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("A chave de API do OpenAI não está definida. Verifique a variável de ambiente OPENAI_API_KEY.")

client.api_key = openai_api_key
valid_mime_types = ['audio/flac', 'audio/m4a', 'audio/mp3', 'audio/mp4', 'audio/mpeg', 'audio/mpga', 'audio/oga', 'audio/ogg', 'audio/wav', 'audio/webm']

def transcribe_audio_filelike(file_path: Path) -> str:
    result = client.audio.transcriptions.create(
        model=config.get("Whisper", {}).get("model", "whisper-1"),
        file=file_path,
    )
    
    return result.text
