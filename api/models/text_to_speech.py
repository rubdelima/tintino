import wave
from google.genai import types
from api.models.google import google_client
import os

def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
   with wave.open(filename, "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)

def generate_text_to_voice(prompt: str, chat_id: str, message_id: int, feedback:bool=False) -> str:
   response = google_client.models.generate_content(
      model="gemini-2.5-flash-preview-tts",
      contents=prompt,
      config=types.GenerateContentConfig(
         response_modalities=["AUDIO"],
         speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
               prebuilt_voice_config=types.PrebuiltVoiceConfig(
                  voice_name='Kore',
               )
            )
         ),
      )
   )
   
   data = response.candidates[0].content.parts[0].inline_data.data #type:ignore
   
   if feedback:
        filename = f'./temp/{chat_id}/{message_id}/feedback.wav'
        if os.path.exists(filename):
           os.remove(filename)
        
   else:
     filename= f'./temp/{chat_id}/{message_id}/history.wav'
   
   wave_file(filename, data)
   
   return filename
