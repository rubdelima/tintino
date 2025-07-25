from api.utils.logger import get_logger
from api.constraints import config
import os
from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)

if config.get("Whisper", {}).get("local", False):
    logger.info("Carregando modelo Whisper Turbo para transcrição de áudio.")
    
    import whisper #type:ignore
    model = whisper.load_model("turbo") #type:ignore

    def transcribe_audio(file_path: str) -> str:
        result = model.transcribe(file_path, language="pt")
        return result["text"]
    
    logger.info("Modelo Whisper Turbo carregado com sucesso.")

else: 
    
    logger.info("Carregando cliente OpenAI para transcrição de áudio.")
    
    from openai import OpenAI
    client = OpenAI()
    client.api_key = os.getenv("OPENAI_API_KEY")

    def transcribe_audio(file_path: str) -> str:
        with open(file_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model=config.get("Whisper", {}).get("model", "whisper-1"),
                file=audio_file
            )
        
        return result.text
    
    logger.info("Cliente OpenAI carregado com sucesso.")