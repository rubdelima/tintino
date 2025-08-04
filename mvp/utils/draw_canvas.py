import streamlit as st
from streamlit_drawable_canvas import st_canvas


def draw_canvas():
    col1, col2 = st.columns([1,4])
    with col1:
        stroke_color = st.color_picker("Cor")
    with col2:
        stroke_width = st.slider("Largura da linha", 1, 20, 2)

    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        background_color="#FFFFFF",
        update_streamlit=True,
        height=800,
        width=800,
        key="canvas",
        display_toolbar=False
    )

    return canvas_result