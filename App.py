import base64

import streamlit as st
from PIL import Image

from src.google_sheets import create_account, validate_login


logo = Image.open("assets/logo/persona_1.png")

st.set_page_config(
    page_title="Persona Intelligence",
    page_icon=logo,
    layout="wide",
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

        .access-note {{
            max-width: 640px;
            margin: 0 auto 18px auto;
            padding: 15px 18px;
            background: #F8EEDC;
            border: 1px solid #D8C29D;
            border-radius: 14px;
            color: #5E554C;
            font-size: 14px;
            line-height: 1.55;
            text-align: center;
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
        <div class="login-subtitle">
            Secure access to the executive BI platform
        </div>
        """
    )

    login_tab, request_access_tab = st.tabs(
        ["Login", "Request Access"]
    )

    # -------------------------------------------------
    # LOGIN
    # -------------------------------------------------

    with login_tab:
        with st.form("login_form"):
            email = st.text_input(
                "Email",
                key="login_email",
                placeholder="name@company.com",
            )

            password = st.text_input(
                "Password",
                type="password",
                key="login_password",
            )

            login_btn = st.form_submit_button(
                "Login",
                use_container_width=True,
            )

            if login_btn:
                clean_email = email.strip()

                if not clean_email or not password:
                    st.error("Please enter your email and password.")

                else:
                    valid, user_record = validate_login(
                        clean_email,
                        password,
                    )

                    if valid:
                        st.session_state["authenticated"] = True
                        st.session_state["user_email"] = clean_email
                        st.session_state["user_name"] = user_record.get(
                            "Name",
                            "User",
                        )
                        st.session_state["user_role"] = user_record.get(
                            "Role",
                            "User",
                        )

                        st.rerun()

                    else:
                        login_status = user_record.get(
                            "Login_Status",
                            "Invalid Credentials",
                        )

                        if login_status == "Pending Approval":
                            st.warning(
                                "Your access request is still awaiting "
                                "administrator approval."
                            )

                        elif login_status == "Inactive":
                            st.error(
                                "This account has been deactivated. "
                                "Please contact the system administrator."
                            )

                        else:
                            st.error("Invalid email or password.")

    # -------------------------------------------------
    # REQUEST ACCESS
    # -------------------------------------------------

    with request_access_tab:
        st.markdown(
            """
            <div class="access-note">
                Submit an access request using your company information.
                Your account will remain pending until it is reviewed and
                approved by an administrator.
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("request_access_form"):
            name = st.text_input(
                "Full Name",
                key="request_name",
            )

            new_email = st.text_input(
                "Company Email Address",
                key="request_email",
                placeholder="name@company.com",
            )

            new_password = st.text_input(
                "Create Password",
                type="password",
                key="request_password",
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                key="request_confirm_password",
            )

            request_btn = st.form_submit_button(
                "Submit Access Request",
                use_container_width=True,
            )

            if request_btn:
                clean_name = name.strip()
                clean_email = new_email.strip().lower()

                if (
                    not clean_name
                    or not clean_email
                    or not new_password
                    or not confirm_password
                ):
                    st.error("Please complete all required fields.")

                elif "@" not in clean_email:
                    st.error("Please enter a valid email address.")

                elif len(new_password) < 8:
                    st.error(
                        "Your password must contain at least 8 characters."
                    )

                elif new_password != confirm_password:
                    st.error("Passwords do not match.")

                else:
                    success, message = create_account(
                        name=clean_name,
                        email=clean_email,
                        password=new_password,
                        role="User",
                    )

                    if success:
                        st.success(message)

                        st.info(
                            "Your account cannot access the dashboard yet. "
                            "You will be able to log in after an "
                            "administrator changes Approved to TRUE in "
                            "the Account Created Google Sheet."
                        )

                    else:
                        st.error(message)


# -------------------------------------------------
# AUTHENTICATION SESSION
# -------------------------------------------------

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "user_email" not in st.session_state:
    st.session_state["user_email"] = None

if "user_name" not in st.session_state:
    st.session_state["user_name"] = None

if "user_role" not in st.session_state:
    st.session_state["user_role"] = None


if not st.session_state["authenticated"]:
    show_login_page()
    st.stop()


# -------------------------------------------------
# AUTHENTICATED SIDEBAR
# -------------------------------------------------

with st.sidebar:
    st.markdown(
        f"""
        **Signed in as**  
        {st.session_state.get("user_name", "User")}
        
        {st.session_state.get("user_email", "")}
        """
    )

    user_role = st.session_state.get("user_role")

    if user_role:
        st.caption(f"Role: {user_role}")

    if st.button(
        "Logout",
        use_container_width=True,
    ):
        st.session_state["authenticated"] = False
        st.session_state["user_email"] = None
        st.session_state["user_name"] = None
        st.session_state["user_role"] = None

        st.rerun()


# -------------------------------------------------
# APPLICATION NAVIGATION
# -------------------------------------------------

pages = {
    "Persona Intelligence": [
        st.Page(
            "pages/Home.py",
            title="Home",
        ),
    ],

    "Executive Analytics": [
        st.Page(
            "pages/Executive_Dashboard.py",
            title="Executive Dashboard",
        ),
        st.Page(
            "pages/Store_Performance.py",
            title="Store Performance",
        ),
        st.Page(
            "pages/Customer_Performance.py",
            title="Customer Performance",
        ),
        st.Page(
            "pages/Jewelery_Analysis.py",
            title="Jewelry Analysis",
        ),
        st.Page(
            "pages/Sales_Analysis.py",
            title="Sales Analysis",
        ),
    ],

    "Intelligence": [
        st.Page(
            "pages/Inventory_Intelligence.py",
            title="Inventory Intelligence",
        ),
        st.Page(
            "pages/Sales_Forecasting.py",
            title="Sales Forecasting",
        ),
        st.Page(
            "pages/AI_Insights.py",
            title="AI Insights",
        ),
        st.Page(
            "pages/Smart_Search.py",
            title="Smart Search",
        ),
        st.Page(
            "pages/Executive_Briefing.py",
            title="Executive Briefing",
        ),
    ],

    "Reports": [
        st.Page(
            "pages/Report_Center.py",
            title="Report Center",
        ),
    ],
}


pg = st.navigation(pages)
pg.run()