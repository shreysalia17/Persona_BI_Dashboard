import base64
import streamlit as st


def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def image_to_base64(path):
    with open(path, "rb") as img:
        return base64.b64encode(img.read()).decode()


load_css("assets/styles.css")

hero_image = image_to_base64("assets/images/persona_hero.png")

executive_icon = image_to_base64("assets/icons/executive_analysis.png")
diamond_icon = image_to_base64("assets/icons/diamond.png")
ai_icon = image_to_base64("assets/icons/ai.png")


st.html(
    f"""
    <div class="hero-section" style="background-image:url('data:image/png;base64,{hero_image}');">
        <div class="hero-overlay"></div>
    </div>
    """
)

st.html(
    """
    <div class="home-intro">
        <h2>Persona Business Intelligence</h2>
        <p>Luxury Retail Executive Decision Platform</p>
    </div>
    """
)

st.html(
    f"""
    <div class="feature-grid">

        <div class="feature-card">
            <img src="data:image/png;base64,{executive_icon}" class="feature-img">
            <h3>Executive Analytics</h3>
            <p>Monitor executive KPIs including revenue, profitability, store performance and overall business health.</p>
        </div>

        <div class="feature-card">
            <img src="data:image/png;base64,{diamond_icon}" class="feature-img">
            <h3>Product Intelligence</h3>
            <p>Analyze jewelry performance, inventory, profit margins, customer demand and best-selling collections.</p>
        </div>

        <div class="feature-card">
            <img src="data:image/png;base64,{ai_icon}" class="feature-img">
            <h3>AI Decision Support</h3>
            <p>Receive AI-powered insights, sales forecasting, inventory alerts and strategic recommendations.</p>
        </div>

    </div>
    """
)

st.html(
    """
    <div class="footer">
        <hr>
        <h4>Persona Intelligence Suite</h4>
        <p>Luxury Retail Business Intelligence Platform</p>
        <p>Built with Google Sheets • Python • Streamlit • Plotly</p>
        <p>Version 1.0 | © 2026 Persona Intelligence</p>
    </div>
    """
)