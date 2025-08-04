from api.schemas.messages import SubmitImageMessage
import streamlit as st
import numpy as np
import app.api_handler.chat as handler
from PIL import Image
from typing import Optional
import tempfile
from pathlib import Path
import emoji

def get_emoji(shortcode: str) -> str:
    if  (emoji_str := emoji.emojize(shortcode)) == shortcode:
        emoji_str = "🎨"
    
    return emoji_str

def submit_drawing(image: 'np.ndarray', chat_id: str, message_id: int, user_id: Optional[str] = None) -> SubmitImageMessage:
    with st.spinner("Submitting image..."):
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            
            pil_image = Image.fromarray(image)
            del image
            
            pil_image.save(temp_path)
            del pil_image
        
        try:
            print(f"Submitting image for chat {chat_id}, message {message_id} at {temp_path}")
            
            response = handler.submit_image(
                chat_id=chat_id,
                image_path=str(temp_path),
                user_id=user_id
            )
        
            return response
        
        finally:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except (OSError, PermissionError):
                    st.error("Failed to delete temporary image file. It may be in use by another process.")
                    print(f"Failed to delete temporary file: {temp_path}")