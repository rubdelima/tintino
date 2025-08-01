import streamlit as st
from typing import List, Optional
from api.schemas.messages import MiniChat, Chat
from app.api_handler import get_chats

def get_user_chats(user_id: Optional[str] = None) -> List[MiniChat]:
    if "chats" not in st.session_state:
        st.session_state.chats = get_chats(user_id)

    return st.session_state.chats