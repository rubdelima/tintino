import streamlit as st
from api.schemas.messages import Chat
from app.utils.draw_canvas import draw_canvas
from app.utils import submit_drawing
import app.api_handler.chat as handler
from typing import Optional

def history_page(mini_chat: Chat, user_id: Optional[str] = None):
    chat = handler.get_chat(mini_chat.chat_id, user_id)
    
    st.title(chat.title)

    history_tabs = st.tabs([str(i) for i in range(len(chat.messages))])

    for index,  (tab, message) in enumerate(zip(history_tabs, chat.messages)):
        with tab:
            st.audio(message.audio, format="audio/wav", start_time=0, autoplay=True)
            st.image(message.image, use_container_width=True)
            if index == len(chat.messages) - 1:
                draw_result = draw_canvas()
                if st.button("Enviar Desenho", disabled= not draw_result):
                    response = submit_drawing(draw_result.image_data, chat.chat_id, message.message_index)
                    st.audio(response.audio, format="audio/wav", start_time=0, autoplay=True)
            else:
                if len(chat.subimits) > index and (image := chat.subimits[index].image):
                    st.image(image, use_container_width=True)