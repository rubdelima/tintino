import traceback
import os

os.makedirs("temp", exist_ok=True)

try:
    import streamlit as st
    
    st.set_page_config(
        page_title="Tintino",
        page_icon="./assets/images/icon.png",
        layout="centered",
        initial_sidebar_state="expanded"
    )
    
    st.logo("./assets/images/icon.png", size="large")
    
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
    
    if "redirect_chat" in st.session_state:
        chat_id = st.session_state["redirect_chat"]
        st.session_state["redirect_chat"] = None
        st.switch_page(chat_id)
    
except Exception as e:
    traceback.print_exc()