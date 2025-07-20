import whisper #type:ignore
from api.utils.logger import get_logger

logger = get_logger(__name__)

logger.info("Carregando modelo Whisper Turbo para transcrição de áudio.")
model = whisper.load_model("turbo") #type:ignore
logger.info("Modelo Whisper Turbo carregado com sucesso.")

def transcribe_audio(file_path: str) -> str:
    result = model.transcribe(file_path, language="pt")
    return result["text"]
