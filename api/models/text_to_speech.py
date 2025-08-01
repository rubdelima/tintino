import wave
from google.genai import types
import os
from api.models.google import google_client
from api.constraints import config
from api.database import db
from typing import Optional

voice_name = config.get("Gemini", {}).get("voice_name", "Kore")  # type:ignore

def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
   with wave.open(filename, "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)

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
   
   audio_part = response.candidates[0].content.parts[0] # type:ignore
   destination_path = f"{user_id}/{chat_id}/{message_id}/audio" if chat_id and (message_id is not None) else f"{user_id}/audio"
   
   return db.upload_generated_archive(
       audio_part.inline_data.data, # type:ignore
       destination_path=destination_path,
       mime_type=audio_part.inline_data.mime_type, # type:ignore
       base_filename="feedback" if  feedback else None
   )