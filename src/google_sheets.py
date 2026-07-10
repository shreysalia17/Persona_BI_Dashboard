import hashlib
from datetime import datetime

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SPREADSHEET_ID = "1EHMbBlDCXeUPjWA1CW9-rMunxyDTxvpWtOamitdL00c"

ACCOUNT_SHEET_NAME = "Account Created"

ACCOUNT_HEADERS = [
    "Name",
    "Email",
    "Password_Hash",
    "Role",
    "Approved",
    "Active",
    "Created_At",
    "Approved_At",
    "Last_Login",
]


@st.cache_resource
def get_client():
    """
    Use Streamlit Secrets when deployed and the local credentials file
    when running on the developer's computer.
    """
    if "gcp_service_account" in st.secrets:
        credentials = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]),
            scopes=SCOPES,
        )
    else:
        credentials = Credentials.from_service_account_file(
            "config/credentials.json",
            scopes=SCOPES,
        )

    return gspread.authorize(credentials)


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
    """
    Hash the password before writing it to Google Sheets.

    This preserves compatibility with accounts already created using
    the previous version of the application.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def parse_boolean(value, default=False):
    """
    Convert Google Sheets values such as TRUE, FALSE, Yes, No, 1 and 0
    into Python boolean values.
    """
    if isinstance(value, bool):
        return value

    if value is None or str(value).strip() == "":
        return default

    normalized_value = str(value).strip().lower()

    return normalized_value in {
        "true",
        "yes",
        "y",
        "1",
        "approved",
        "active",
    }


def get_or_create_worksheet(sheet_name, headers):
    spreadsheet = get_spreadsheet()

    try:
        worksheet = spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=sheet_name,
            rows=1000,
            cols=max(len(headers), 10),
        )
        worksheet.append_row(headers)

    return worksheet


def prepare_account_worksheet():
    """
    Create the account worksheet if needed and ensure all required
    authorization columns exist.

    Existing accounts are automatically marked Approved and Active
    when the new columns are introduced so current users are not locked out.
    """
    worksheet = get_or_create_worksheet(
        ACCOUNT_SHEET_NAME,
        ACCOUNT_HEADERS,
    )

    existing_headers = worksheet.row_values(1)

    approved_column_was_missing = "Approved" not in existing_headers
    active_column_was_missing = "Active" not in existing_headers

    missing_headers = [
        header
        for header in ACCOUNT_HEADERS
        if header not in existing_headers
    ]

    if missing_headers:
        updated_headers = existing_headers + missing_headers

        worksheet.update(
            range_name=f"A1:{gspread.utils.rowcol_to_a1(1, len(updated_headers))}",
            values=[updated_headers],
        )

        existing_headers = updated_headers

    header_positions = {
        header: index + 1
        for index, header in enumerate(existing_headers)
    }

    # Preserve access for accounts that existed before the approval system.
    existing_records = worksheet.get_all_records()

    for row_number, record in enumerate(existing_records, start=2):
        email = str(record.get("Email", "")).strip()

        if not email:
            continue

        if approved_column_was_missing:
            worksheet.update_cell(
                row_number,
                header_positions["Approved"],
                "TRUE",
            )

        if active_column_was_missing:
            worksheet.update_cell(
                row_number,
                header_positions["Active"],
                "TRUE",
            )

    return worksheet, existing_headers


def create_account(name, email, password, role="User"):
    """
    Submit a new access request.

    New users are saved as:
        Approved = FALSE
        Active = TRUE

    An administrator must change Approved to TRUE in Google Sheets
    before the user can log in.
    """
    worksheet, headers = prepare_account_worksheet()

    clean_name = str(name).strip()
    clean_email = str(email).strip().lower()
    clean_password = str(password)

    if not clean_name or not clean_email or not clean_password:
        return False, "Please complete all required fields."

    existing_records = worksheet.get_all_records()

    for record in existing_records:
        existing_email = str(record.get("Email", "")).strip().lower()

        if existing_email == clean_email:
            approved = parse_boolean(
                record.get("Approved"),
                default=False,
            )

            active = parse_boolean(
                record.get("Active"),
                default=True,
            )

            if approved and active:
                return False, "An approved account already exists for this email."

            if not approved:
                return False, "An access request for this email is already pending."

            if not active:
                return False, "This account has been deactivated. Contact the administrator."

            return False, "An account already exists for this email."

    new_record = {
        "Name": clean_name,
        "Email": clean_email,
        "Password_Hash": hash_password(clean_password),
        "Role": role,
        "Approved": "FALSE",
        "Active": "TRUE",
        "Created_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Approved_At": "",
        "Last_Login": "",
    }

    row_values = [
        new_record.get(header, "")
        for header in headers
    ]

    worksheet.append_row(
        row_values,
        value_input_option="USER_ENTERED",
    )

    st.cache_data.clear()

    return (
        True,
        "Access request submitted successfully. "
        "You can log in after an administrator approves your request.",
    )


def validate_login(email, password):
    """
    Validate the password and account authorization status.

    Login is permitted only when:
        Approved = TRUE
        Active = TRUE
    """
    worksheet, headers = prepare_account_worksheet()

    clean_email = str(email).strip().lower()
    password_hash = hash_password(str(password))

    records = worksheet.get_all_records()

    header_positions = {
        header: index + 1
        for index, header in enumerate(headers)
    }

    for row_number, record in enumerate(records, start=2):
        record_email = str(record.get("Email", "")).strip().lower()
        stored_password_hash = str(
            record.get("Password_Hash", "")
        ).strip()

        if (
            record_email == clean_email
            and stored_password_hash == password_hash
        ):
            approved = parse_boolean(
                record.get("Approved"),
                default=False,
            )

            active = parse_boolean(
                record.get("Active"),
                default=True,
            )

            if not approved:
                pending_record = dict(record)
                pending_record["Login_Status"] = "Pending Approval"

                return False, pending_record

            if not active:
                inactive_record = dict(record)
                inactive_record["Login_Status"] = "Inactive"

                return False, inactive_record

            login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if "Last_Login" in header_positions:
                worksheet.update_cell(
                    row_number,
                    header_positions["Last_Login"],
                    login_time,
                )

            approved_record = dict(record)
            approved_record["Last_Login"] = login_time
            approved_record["Login_Status"] = "Approved"

            return True, approved_record

    return False, {
        "Login_Status": "Invalid Credentials",
    }