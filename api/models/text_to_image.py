from api.schemas.llm import ChatResponse
from google.genai import types
from api.models.google import google_client
from PIL import Image
from io import BytesIO

def generate_scene_image(description: str, chat_id:str, message_id: int) ->str:
    image_path = f'./temp/{chat_id}/{message_id}/scene_image.png'
    contents = ("Crie uma imagem cartunesca a partir dessa descrição: ",  description)

    response = google_client.models.generate_content(
        model="gemini-2.0-flash-preview-image-generation",
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
        )
    )

    for part in response.candidates[0].content.parts:
      if part.inline_data is not None:
        image = Image.open(BytesIO((part.inline_data.data)))
        image.save(image_path)
    
    return image_path