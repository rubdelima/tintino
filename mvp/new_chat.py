import streamlit as st
import app.api_handler.chat as handler
from mvp.utils.text import home_intro, home_description
from mvp.utils.cache import add_chat

st.markdown(home_intro)

with st.columns([1,2,1])[1]:
    st.image("./assets/images/logo.png", use_container_width=True)

st.markdown(home_description)

audio_value = st.audio_input("Fale sua ideia para a história")

submit_button = st.button("Criar História")

if submit_button:
    with st.spinner("Criando a História..."):
        if audio_value is None:
            st.warning("Por favor, grave um áudio antes de enviar.")
        else: 
            try:
                assert audio_value is not None, "O áudio não pode ser None"
                result = handler.create_chat(audio_value.read())
                add_chat(result)
                st.session_state["redirect_chat"] = result.chat_id
                st.rerun()
            
            except Exception as e:
                st.error(f"Erro ao criar a história: {str(e)}")
                st.session_state["redirect_chat"] = None
            finally:
                if audio_value is not None:
                    audio_value.close()