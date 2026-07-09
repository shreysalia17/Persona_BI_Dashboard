import base64
import streamlit as st


def image_to_base64(path):
    with open(path, "rb") as img:
        return base64.b64encode(img.read()).decode()


def page_header(title, subtitle):
    logo = image_to_base64("assets/logo/persona_1.png")

    html = f"""
    <div class="persona-header">
        <img src="data:image/png;base64,{logo}" class="persona-logo">

        <div class="persona-title">
            {title}
        </div>

        <div class="persona-subtitle">
            {subtitle}
        </div>
    </div>
    """

    st.html(html)