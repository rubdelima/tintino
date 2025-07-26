import streamlit as st
import app.api_handler as handler
import os

st.markdown("""
## 🐠 Tintino – Histórias Interativas com Inteligência Artificial

> **Objetivo**: Tornar a tecnologia uma aliada para contar histórias, estimulando a criatividade, a imaginação e a autonomia das crianças através de um ambiente lúdico, educativo e interativo.
""")

with st.columns([1,2,1])[1]:
    st.image("./assets/images/logo.png", use_container_width=True)

st.markdown("""
**Tintino** é um projeto desenvolvido para a disciplina de **Criatividade Computacional**, com o propósito de explorar o uso de **Inteligência Artificial** na criação de histórias **interativas e personalizadas para crianças**.

A proposta do projeto é transformar a experiência de contar histórias em algo mais **imaginativo, dinâmico e multimodal**, por meio de:

🎨 **Imagens Geradas por IA**: as cenas e personagens são criados a partir de prompts, trazendo ilustrações únicas e encantadoras.

🎙️ **Narração por Voz**: com uso de síntese de voz, as histórias ganham vida por meio de áudios expressivos e imersivos.

🗣️ **Interações por Fala e Escuta**: a criança pode participar das histórias, fazendo escolhas, respondendo perguntas e interagindo com os personagens por voz.

🖍️ **Avaliação de Desenhos**: o sistema também incentiva a criatividade ao permitir que a criança desenhe e receba um retorno gentil da IA, incentivando a expressão artística.

Você pode experimentar o Tintino gravando um áudio no botão abaixo e criando uma nova história.
""")

audio_value = st.audio_input("Fale sua ideia para a história")

submit_button = st.button("Criar História", disabled=not audio_value)

if submit_button:
    with st.spinner("Criando a História..."):
        
        os.makedirs("temp", exist_ok=True)
        temp_file = "./temp/temp_audio.wav"
        with open(temp_file, "wb") as f:
            f.write(audio_value.read())

        result = handler.create_chat(audio_path=temp_file)

        st.session_state["redirect_chat"] = result.chat_id
        
        st.rerun()