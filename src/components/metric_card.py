import streamlit as st
import base64


def image_to_base64(icon_path):
    with open(icon_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


def metric_card(title, value, icon_path, change="", change_color="#666666"):
    icon_base64 = image_to_base64(icon_path)

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">
                <img src="data:image/png;base64,{icon_base64}" />
            </div>
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-change" style="color:{change_color};">{change}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def insight_card(title, main_text, sub_text, icon_path):
    icon_base64 = image_to_base64(icon_path)

    st.markdown(
        f"""
        <div class="metric-card insight-card">
            <div class="metric-icon">
                <img src="data:image/png;base64,{icon_base64}" />
            </div>
            <div class="metric-title">{title}</div>
            <div class="insight-main">{main_text}</div>
            <div class="insight-sub">{sub_text}</div>
        </div>
        """,
        unsafe_allow_html=True
    )