from pydub import AudioSegment
from io import BytesIO
import tempfile
from pathlib import Path
from fastapi import UploadFile
from api.utils.logger import get_logger
import magic
import time

from api.utils import get_mime_extension

logger = get_logger(__name__)

def convert_to_wav(audio_bytes: bytes) -> Path:
    time_start = time.time()
    audio = AudioSegment.from_file(BytesIO(audio_bytes))
    logger.debug(f"Tempo de conversão para WAV: {time.time() - time_start:.2f} segundos")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav_file:
        temp_wav_file_path = temp_wav_file.name
        audio.export(temp_wav_file, format="wav")
        temp_wav_file.flush()

    return Path(temp_wav_file_path)

async def prepare_audio_file(file: UploadFile) -> Path:    
    audio_bytes, mime, extension = await get_mime_extension(file)
    
    valid_mime_types = ['audio/flac', 'audio/m4a', 'audio/mp3', 'audio/mp4', 'audio/mpeg', 'audio/mpga', 'audio/oga', 'audio/ogg', 'audio/wav', 'audio/webm']

    if mime not in valid_mime_types:
        logger.warning(f"Formato de áudio {mime} não suportado. Realizando conversão para WAV.")
        return convert_to_wav(audio_bytes)
    else:
        logger.debug(f"Formato de áudio {mime} é válido. Salvando como arquivo temporário.")
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temp_wav_file:
            temp_wav_file_path = temp_wav_file.name
            audio = AudioSegment.from_file(BytesIO(audio_bytes))
            audio.export(temp_wav_file, format="wav")
            temp_wav_file.flush()
        
        return Path(temp_wav_file_path)
