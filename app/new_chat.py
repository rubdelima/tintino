import streamlit as st
import app.api_handler.chat as handler
import tempfile
from app.utils.text import home_intro, home_description

st.markdown(home_intro)

with st.columns([1,2,1])[1]:
    st.image("./assets/images/logo.png", use_container_width=True)

st.markdown(home_description)

audio_value = st.audio_input("Fale sua ideia para a história")

submit_button = st.button("Criar História", disabled=not audio_value)

if submit_button and audio_value:
    with st.spinner("Criando a História..."):
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_file:
            assert audio_value is not None
            temp_file.write(audio_value.read())
            temp_file.flush()
            result = handler.create_chat(audio_path=temp_file.name)

        st.session_state["redirect_chat"] = result.chat_id
        st.rerun()