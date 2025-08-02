import streamlit as st
from typing import List, Optional, Union
from api.schemas.messages import MiniChat, Chat
import app.api_handler as api_handler

def get_user_chats(user_id: Optional[str] = None) -> List[Union[MiniChat, Chat]]:
    if "chats" not in st.session_state:
        st.session_state.chats = api_handler.get_chats(user_id)

    return st.session_state.chats

def get_chat(chat_id: str, user_id: Optional[str] = None) -> Chat:
    if "chat_dict" not in st.session_state:
        st.session_state.chat_dict = {}
    
    if chat_id not in st.session_state.chat_dict:
        st.session_state.chat_dict[chat_id] = api_handler.get_chat(chat_id, user_id)

    return st.session_state.chat_dict[chat_id]

def add_chat(chat: Chat) -> None:
    if "chat_dict" not in st.session_state:
        st.session_state.chat_dict = {}

    st.session_state.chat_dict[chat.chat_id] = chat
    
    if "chats" not in st.session_state:
        st.session_state.chats = []
    
    st.session_state.chats.append(chat)