import wave
from google.genai import types
import os
import io
from api.models.google import google_client
from api.constraints import config
from api.database import db
from typing import Optional

voice_name = config.get("Gemini", {}).get("voice_name", "Kore")  # type:ignore

def convert_raw_audio_to_wav(raw_audio_data: bytes,channels: int = 1,sampwidth: int = 2,framerate: int = 24000) -> bytes:    
    wav_in_memory = io.BytesIO()
    with wave.open(wav_in_memory, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(raw_audio_data)
        
    return wav_in_memory.getvalue()
 
def generate_text_to_voice(prompt: str, user_id:str, chat_id: Optional[str] = None, message_id: Optional[int] = None, feedback:bool=False) -> str:
   response = google_client.models.generate_content(
      model="gemini-2.5-flash-preview-tts",
      contents=prompt,
      config=types.GenerateContentConfig(
         response_modalities=["AUDIO"],
         speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
               prebuilt_voice_config=types.PrebuiltVoiceConfig(
                  voice_name=voice_name,
               )
            )
         ),
      )
   )
   
   audio_bytes = convert_raw_audio_to_wav(response.candidates[0].content.parts[0].inline_data.data ) #type:ignore
   del response
   
   destination_path = f"{user_id}/{chat_id}/{message_id}/audio" if chat_id and (message_id is not None) else f"{user_id}/audio"
   
   return db.upload_generated_archive(
       audio_bytes,
       destination_path=destination_path,
       mime_type='audio/wav',
       base_filename="feedback" if  feedback else None
   )