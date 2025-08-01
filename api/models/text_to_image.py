from google.genai import types
from api.models.google import google_client
from api.database import db
from typing import Optional

def generate_scene_image(description: str, user_id:str, chat_id:Optional[str] = None, message_id: Optional[int] = None) ->str:
    image_path = f'./temp/{chat_id}/{message_id}/scene_image.png'
    contents = ("Crie uma imagem cartunesca a partir dessa descrição: ",  description)

    response = google_client.models.generate_content(
        model="gemini-2.0-flash-preview-image-generation",
        contents=contents, #type:ignore
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
        )
    )

    image_bytes = None
    image_mime_type = None

    for part in response.candidates[0].content.parts: # type:ignore
        if part.inline_data:
            image_bytes = part.inline_data.data
            image_mime_type = part.inline_data.mime_type
            break

    if image_bytes and image_mime_type:
        destination_path = f"{user_id}/{chat_id}/{message_id}/images/scene_image.png" if chat_id and (message_id is not None) else f"{user_id}/images/scene_image.png"
        url_or_path = db.upload_generated_archive(
            file_bytes=image_bytes,
            destination_path=destination_path,
            mime_type=image_mime_type,
        )
        return url_or_path

    raise ValueError("Nenhuma imagem foi gerada ou encontrada na resposta da API.")