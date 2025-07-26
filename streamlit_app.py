import traceback
import os

os.makedirs("temp", exist_ok=True)

try:
    import streamlit as st
    
    st.set_page_config(
        page_title="Louie",
        page_icon="🎨",
        layout="centered",
        initial_sidebar_state="expanded"
    )
    
    from app.history import history_page
    from app.utils import get_chats
    
    chats = get_chats()
    
    pages = {
        "Nova História": [
            st.Page(
                "app/new_chat.py",
                icon="🖌️",
                title="Nova História",
                default=True,
            )
        ],
        "Ultimas Histórias" : [
            st.Page(
                lambda chat=chat: history_page(chat),
                icon= "🎨",
                title= chat.title,
                url_path= chat.chat_id,
            ) for chat in chats
        ]
    }
    
    pg = st.navigation(pages)
    pg.run()
    
except Exception as e:
    traceback.print_exc()