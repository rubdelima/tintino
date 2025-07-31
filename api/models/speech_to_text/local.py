import whisper #type:ignore
import magic
import tempfile
from fastapi import UploadFile

model = whisper.load_model("turbo") #type:ignore

def transcribe_audio_whisper_local(file: UploadFile) -> str:
    content = file.file.read()
    file.file.seek(0)

    mime = magic.from_buffer(content, mime=True)
    if not mime.startswith("audio/"):
        raise ValueError("Arquivo enviado não é um áudio válido.")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp_file:
        tmp_file.write(content)
        tmp_file.flush()

        result = model.transcribe(tmp_file.name, language="pt")
        return result["text"] #type:ignore