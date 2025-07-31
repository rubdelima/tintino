import os
from dotenv import load_dotenv
from fastapi import UploadFile
import traceback

from api.utils.logger import get_logger
from api.constraints import config

load_dotenv()

logger = get_logger(__name__)

offline_mode = config.get("Whisper", {}).get("offline_mode", False)

if offline_mode:
    logger.info("Carregando modelo Whisper Turbo para transcrição de áudio.")
    
    try:
        from api.models.speech_to_text.local import transcribe_audio_whisper_local
        transcribe_audio = transcribe_audio_whisper_local
    
    except ImportError:
        logger.error("Erro ao importar o modelo Whisper Turbo. Verifique se o pacote 'whisper' está instalado.")
        offline_mode = False
    
    except Exception as e:
        logger.error(f"Erro ao carregar o modelo Whisper Turbo: {e}")
        offline_mode = False
    
    logger.info("Modelo Whisper Turbo carregado com sucesso.")

if not offline_mode:
    
    logger.info("Carregando cliente OpenAI para transcrição de áudio.")
    
    try:
        from api.models.speech_to_text.api import transcribe_audio_filelike
        transcribe_audio = transcribe_audio_filelike
    
    except Exception as e:
        logger.error(f"Erro ao carregar o cliente OpenAI: {e}")
        logger.error(traceback.format_exc())
        exit(1)

    logger.info("Cliente OpenAI carregado com sucesso.")