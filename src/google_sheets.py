import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
import hashlib


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SPREADSHEET_ID = "1EHMbBlDCXeUPjWA1CW9-rMunxyDTxvpWtOamitdL00c"


@st.cache_resource
def get_client():
    if "gcp_service_account" in st.secrets:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=SCOPES
        )
    else:
        creds = Credentials.from_service_account_file(
            "config/credentials.json",
            scopes=SCOPES
        )

    return gspread.authorize(creds)


@st.cache_resource
def get_spreadsheet():
    client = get_client()
    return client.open_by_key(SPREADSHEET_ID)


@st.cache_data(ttl=300)
def load_sheet(sheet_name):
    spreadsheet = get_spreadsheet()
    worksheet = spreadsheet.worksheet(sheet_name)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)


@st.cache_data(ttl=300)
def load_all_tables():
    return {
        "sales": load_sheet("Sales Table"),
        "products": load_sheet("Product Table"),
        "customers": load_sheet("Customer Table"),
        "inventory": load_sheet("Inventory Table"),
        "stores": load_sheet("Store Table"),
        "employees": load_sheet("Employees Table"),
        "returns": load_sheet("Returns Table"),
        "suppliers": load_sheet("Suppliers Table"),
    }


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def get_or_create_worksheet(sheet_name, headers):
    spreadsheet = get_spreadsheet()

    try:
        worksheet = spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=sheet_name,
            rows=1000,
            cols=len(headers)
        )
        worksheet.append_row(headers)

    return worksheet


def create_account(name, email, password, role="User"):
    worksheet = get_or_create_worksheet(
        "Account Created",
        ["Name", "Email", "Password_Hash", "Role", "Created_At"]
    )

    existing_records = worksheet.get_all_records()

    for record in existing_records:
        if record["Email"].lower() == email.lower():
            return False, "Account already exists."

    worksheet.append_row([
        name,
        email,
        hash_password(password),
        role,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ])

    st.cache_data.clear()

    return True, "Account created successfully."


def validate_login(email, password):
    worksheet = get_or_create_worksheet(
        "Account Created",
        ["Name", "Email", "Password_Hash", "Role", "Created_At"]
    )

    records = worksheet.get_all_records()
    password_hash = hash_password(password)

    for record in records:
        if (
            record["Email"].lower() == email.lower()
            and record["Password_Hash"] == password_hash
        ):
            return True, record

    return False, None