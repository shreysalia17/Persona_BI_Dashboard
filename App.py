import base64
import streamlit as st

from src.google_sheets import create_account, validate_login


st.set_page_config(
    page_title="Persona Intelligence",
    page_icon="💎",
    layout="wide"
)


def image_to_base64(path):
    with open(path, "rb") as img:
        return base64.b64encode(img.read()).decode()


def hide_sidebar():
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] {
            display: none;
        }

        div[data-testid="stSidebarCollapsedControl"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_login_page():
    hide_sidebar()

    hero_image = image_to_base64("assets/images/Persona_hero.png")

    st.markdown(
        f"""
        <style>
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"],
        .block-container {{
            background: #F2E8D8 !important;
        }}

        .login-hero {{
            max-width: 920px;
            height: 360px;
            margin: 28px auto 24px auto;
            border-radius: 28px;
            background-image: url('data:image/png;base64,{hero_image}');
            background-size: cover;
            background-position: center;
            box-shadow: 0px 18px 42px rgba(88, 67, 43, 0.18);
        }}

        .login-title {{
            text-align: center;
            font-size: 46px;
            font-weight: 850;
            color: #2F2A24;
            margin-top: 8px;
            margin-bottom: 6px;
        }}

        .login-subtitle {{
            text-align: center;
            font-size: 18px;
            color: #6F655B;
            margin-bottom: 34px;
        }}

        div[data-testid="stForm"] {{
            max-width: 640px;
            margin: 0 auto;
            background: #FFF7EC;
            border: 1px solid #D8C29D;
            border-radius: 22px;
            padding: 28px;
            box-shadow: 0px 14px 34px rgba(88, 67, 43, 0.12);
        }}

        div[data-testid="stTabs"] {{
            max-width: 700px;
            margin: 0 auto;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.html(
        """
        <div class="login-hero"></div>
        <div class="login-title">Persona Intelligence</div>
        <div class="login-subtitle">Secure access to the executive BI platform</div>
        """
    )

    tab1, tab2 = st.tabs(["Login", "Create Account"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")

            if login_btn:
                valid, user_record = validate_login(email, password)

                if valid:
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"] = email
                    st.session_state["user_name"] = user_record.get("Name", "User")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

    with tab2:
        with st.form("create_account_form"):
            name = st.text_input("Full Name")
            new_email = st.text_input("Email Address")
            new_password = st.text_input("Create Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            create_btn = st.form_submit_button("Create Account")

            if create_btn:
                if not name or not new_email or not new_password:
                    st.error("Please fill all fields.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    success, message = create_account(
                        name=name,
                        email=new_email,
                        password=new_password,
                        role="User",
                    )

                    if success:
                        st.success(message)
                        st.info("You can now login using your new account.")
                    else:
                        st.error(message)


if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False


if not st.session_state["authenticated"]:
    show_login_page()
    st.stop()


with st.sidebar:
    st.markdown(f"**Signed in as:**  \n{st.session_state.get('user_name', 'User')}")

    if st.button("Logout"):
        st.session_state["authenticated"] = False
        st.session_state["user_email"] = None
        st.session_state["user_name"] = None
        st.rerun()


pages = {
    "Persona Intelligence": [
        st.Page("pages/Home.py", title="Home"),
    ],

    "Executive Analytics": [
        st.Page("pages/Executive_Dashboard.py", title="Executive Dashboard"),
        st.Page("pages/Store_Performance.py", title="Store Performance"),
        st.Page("pages/Customer_Performance.py", title="Customer Performance"),
        st.Page("pages/Jewelery_Analysis.py", title="Jewelry Analysis"),
        st.Page("pages/Sales_Analysis.py", title="Sales Analysis"),
    ],

    "Intelligence": [
        st.Page("pages/Inventory_Intelligence.py", title="Inventory Intelligence"),
        st.Page("pages/Sales_Forecasting.py", title="Sales Forecasting"),
        st.Page("pages/AI_Insights.py", title="AI Insights"),
        st.Page("pages/Smart_Search.py", title="Smart Search"),
        st.Page("pages/Executive_Briefing.py", title="Executive Briefing"),
    ],

    "Reports": [
        st.Page("pages/Report_Center.py", title="Report Center"),
    ],
}


pg = st.navigation(pages)
pg.run()