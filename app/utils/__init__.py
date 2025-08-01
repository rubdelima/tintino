from api.schemas.messages import SubmitImageMessage
import streamlit as st
import numpy as np
import app.api_handler.chat as handler
from PIL import Image

def submit_drawing(image : 'np.ndarray', chat_id: str, message_id: int) -> SubmitImageMessage:
    with st.spinner("Submitting image..."):
        
        image_path = f"./temp/{chat_id}/{message_id}/submission.png"
        
        pil_image = Image.fromarray(image)
        pil_image.save(image_path)
        
        print(f"Submitting image for chat {chat_id}, message {message_id} at {image_path}")
        
        response = handler.submit_image(
            chat_id=chat_id,
            message_id=message_id,
            image_path=image_path
        )
    
    return response