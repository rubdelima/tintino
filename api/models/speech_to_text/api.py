from openai import OpenAI
from fastapi import UploadFile
import magic
import os

from api.constraints import config

client = OpenAI()

openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("A chave de API do OpenAI não está definida. Verifique a variável de ambiente OPENAI_API_KEY.")

client.api_key = openai_api_key

def transcribe_audio_filelike(file: UploadFile) -> str:
    mime = magic.from_buffer(file.file.read(1024), mime=True)
    file.file.seek(0)

    if not mime.startswith("audio/"):
        raise ValueError("Arquivo enviado não é um áudio válido.")

    result = client.audio.transcriptions.create(
        model=config.get("Whisper", {}).get("model", "whisper-1"),
        file=file.file
    )
    
    return result.text
