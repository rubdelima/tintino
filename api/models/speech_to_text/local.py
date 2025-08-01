import whisper #type:ignore
import magic
import tempfile
from fastapi import UploadFile
import os
from pathlib import Path

model = whisper.load_model("turbo") #type:ignore

def transcribe_audio_whisper_local(file_path: Path) -> str:
    result = model.transcribe(str(file_path), language="pt")
    return result["text"] #type:ignore