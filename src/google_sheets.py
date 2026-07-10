import hashlib
import os
from datetime import datetime

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials


# -------------------------------------------------
# GOOGLE API CONFIGURATION
# -------------------------------------------------

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

LOCAL_CREDENTIALS_PATH = "config/credentials.json"


# Local development uses the local spreadsheet ID.
# Streamlit Cloud uses the spreadsheet ID stored in Secrets.
if os.path.exists(LOCAL_CREDENTIALS_PATH):
    SPREADSHEET_ID = "1EHMbBlDCXeUPjWA1CW9-rMunxyDTxvpWtOamitdL00c"
else:
    try:
        SPREADSHEET_ID = st.secrets["spreadsheet_id"]
    except Exception as error:
        raise RuntimeError(
            "The Google Spreadsheet ID was not found. "
            "For Streamlit Cloud, add spreadsheet_id to the app's Secrets."
        ) from error


ACCOUNT_SHEET_NAME = "Account Created"

ACCOUNT_HEADERS = [
    "Name",
    "Email",
    "Password_Hash",
    "Role",
    "Approved",
    "Active",
    "Created_At",
    "Approved_By",
    "Approved_At",
    "Last_Login",
]


# -------------------------------------------------
# GOOGLE SHEETS CONNECTION
# -------------------------------------------------

@st.cache_resource
def get_client():
    """
    Local environment:
        Uses config/credentials.json

    Streamlit Cloud:
        Uses st.secrets["gcp_service_account"]
    """

    if os.path.exists(LOCAL_CREDENTIALS_PATH):
        credentials = Credentials.from_service_account_file(
            LOCAL_CREDENTIALS_PATH,
            scopes=SCOPES,
        )

    else:
        try:
            service_account_info = dict(
                st.secrets["gcp_service_account"]
            )

        except Exception as error:
            raise RuntimeError(
                "Google service-account credentials were not found. "
                "For local development, add config/credentials.json. "
                "For Streamlit Cloud, add a [gcp_service_account] "
                "section in the app's Secrets settings."
            ) from error

        credentials = Credentials.from_service_account_info(
            service_account_info,
            scopes=SCOPES,
        )

    return gspread.authorize(credentials)


@st.cache_resource
def get_spreadsheet():
    client = get_client()
    return client.open_by_key(SPREADSHEET_ID)


# -------------------------------------------------
# DATA LOADING
# -------------------------------------------------

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


# -------------------------------------------------
# PASSWORD AND BOOLEAN HELPERS
# -------------------------------------------------

def hash_password(password):
    """
    Preserves compatibility with accounts created using the current
    SHA-256 password-hashing method.
    """

    return hashlib.sha256(
        str(password).encode("utf-8")
    ).hexdigest()


def parse_boolean(value, default=False):
    """
    Strictly converts Google Sheets values into Python booleans.

    Accepted true values:
        TRUE, YES, Y, 1

    Accepted false values:
        FALSE, NO, N, 0

    Missing or unexpected values return the supplied default.
    """

    if isinstance(value, bool):
        return value

    if value is None:
        return default

    normalized_value = str(value).strip().upper()

    if normalized_value in {
        "TRUE",
        "YES",
        "Y",
        "1",
    }:
        return True

    if normalized_value in {
        "FALSE",
        "NO",
        "N",
        "0",
    }:
        return False

    return default


# -------------------------------------------------
# ACCOUNT WORKSHEET SETUP
# -------------------------------------------------

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

        worksheet.append_row(
            headers,
            value_input_option="USER_ENTERED",
        )

    return worksheet


def prepare_account_worksheet():
    """
    Ensures the Account Created worksheet contains every required
    account-management column.

    Existing accounts are marked Approved and Active only if those
    columns did not previously exist.
    """

    worksheet = get_or_create_worksheet(
        ACCOUNT_SHEET_NAME,
        ACCOUNT_HEADERS,
    )

    existing_headers = worksheet.row_values(1)

    if not existing_headers:
        worksheet.append_row(
            ACCOUNT_HEADERS,
            value_input_option="USER_ENTERED",
        )

        return worksheet, ACCOUNT_HEADERS

    approved_column_missing = "Approved" not in existing_headers
    active_column_missing = "Active" not in existing_headers

    missing_headers = [
        header
        for header in ACCOUNT_HEADERS
        if header not in existing_headers
    ]

    if missing_headers:
        updated_headers = existing_headers + missing_headers

        end_cell = gspread.utils.rowcol_to_a1(
            1,
            len(updated_headers),
        )

        worksheet.update(
            range_name=f"A1:{end_cell}",
            values=[updated_headers],
        )

        existing_headers = updated_headers

    header_positions = {
        header: index + 1
        for index, header in enumerate(existing_headers)
    }

    # Preserve access for accounts that existed before authorization
    # columns were originally introduced.
    if approved_column_missing or active_column_missing:
        existing_records = worksheet.get_all_records()

        for row_number, record in enumerate(
            existing_records,
            start=2,
        ):
            email = str(
                record.get("Email", "")
            ).strip()

            if not email:
                continue

            if approved_column_missing:
                worksheet.update_cell(
                    row_number,
                    header_positions["Approved"],
                    "TRUE",
                )

            if active_column_missing:
                worksheet.update_cell(
                    row_number,
                    header_positions["Active"],
                    "TRUE",
                )

    return worksheet, existing_headers


def get_account_records():
    """
    Returns current account records directly from Google Sheets.

    Account information is intentionally not cached so approval and
    deactivation changes are detected immediately.
    """

    worksheet, headers = prepare_account_worksheet()
    records = worksheet.get_all_records()

    return worksheet, headers, records


# -------------------------------------------------
# ACCESS REQUEST
# -------------------------------------------------

def create_account(name, email, password, role="User"):
    """
    Submits a new access request.

    New requests receive:
        Approved = FALSE
        Active = TRUE

    An administrator must change Approved to TRUE before the user
    can access the dashboard.
    """

    worksheet, headers, existing_records = get_account_records()

    clean_name = str(name).strip()
    clean_email = str(email).strip().lower()
    clean_password = str(password)

    if not clean_name or not clean_email or not clean_password:
        return False, "Please complete all required fields."

    for record in existing_records:
        existing_email = str(
            record.get("Email", "")
        ).strip().lower()

        if existing_email != clean_email:
            continue

        approved = parse_boolean(
            record.get("Approved"),
            default=False,
        )

        active = parse_boolean(
            record.get("Active"),
            default=False,
        )

        if approved and active:
            return (
                False,
                "An approved account already exists for this email.",
            )

        if not approved:
            return (
                False,
                "An access request for this email is already pending.",
            )

        if not active:
            return (
                False,
                "This account has been deactivated. "
                "Please contact the administrator.",
            )

        return False, "An account already exists for this email."

    new_record = {
        "Name": clean_name,
        "Email": clean_email,
        "Password_Hash": hash_password(clean_password),
        "Role": role,
        "Approved": "FALSE",
        "Active": "TRUE",
        "Created_At": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "Approved_By": "",
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
        "Your request is awaiting administrator approval.",
    )


# -------------------------------------------------
# CURRENT ACCOUNT ACCESS CHECK
# -------------------------------------------------

def validate_account_access(email):
    """
    Checks whether an existing account is currently approved and active.

    This can be used in App.py to force-log-out an already authenticated
    user when Approved or Active is changed to FALSE.
    """

    clean_email = str(email).strip().lower()

    if not clean_email:
        return False, {
            "Login_Status": "Invalid Account",
        }

    _, _, records = get_account_records()

    matching_records = [
        record
        for record in records
        if str(
            record.get("Email", "")
        ).strip().lower() == clean_email
    ]

    if not matching_records:
        return False, {
            "Login_Status": "Account Not Found",
        }

    if len(matching_records) > 1:
        return False, {
            "Login_Status": "Duplicate Account",
        }

    record = matching_records[0]

    approved = parse_boolean(
        record.get("Approved"),
        default=False,
    )

    active = parse_boolean(
        record.get("Active"),
        default=False,
    )

    if not approved:
        pending_record = dict(record)
        pending_record["Login_Status"] = "Pending Approval"

        return False, pending_record

    if not active:
        inactive_record = dict(record)
        inactive_record["Login_Status"] = "Inactive"

        return False, inactive_record

    approved_record = dict(record)
    approved_record["Login_Status"] = "Approved"

    return True, approved_record


# -------------------------------------------------
# LOGIN VALIDATION
# -------------------------------------------------

def validate_login(email, password):
    """
    Login succeeds only when:

        Email matches
        Password matches
        Approved = TRUE
        Active = TRUE

    Duplicate email records are blocked for security.
    """

    worksheet, headers, records = get_account_records()

    clean_email = str(email).strip().lower()
    supplied_password_hash = hash_password(password)

    matching_email_records = []

    for row_number, record in enumerate(
        records,
        start=2,
    ):
        record_email = str(
            record.get("Email", "")
        ).strip().lower()

        if record_email == clean_email:
            matching_email_records.append(
                (row_number, record)
            )

    if not matching_email_records:
        return False, {
            "Login_Status": "Invalid Credentials",
        }

    if len(matching_email_records) > 1:
        return False, {
            "Login_Status": "Duplicate Account",
        }

    row_number, record = matching_email_records[0]

    stored_password_hash = str(
        record.get("Password_Hash", "")
    ).strip()

    if stored_password_hash != supplied_password_hash:
        return False, {
            "Login_Status": "Invalid Credentials",
        }

    approved = parse_boolean(
        record.get("Approved"),
        default=False,
    )

    active = parse_boolean(
        record.get("Active"),
        default=False,
    )

    if not approved:
        pending_record = dict(record)
        pending_record["Login_Status"] = "Pending Approval"

        return False, pending_record

    if not active:
        inactive_record = dict(record)
        inactive_record["Login_Status"] = "Inactive"

        return False, inactive_record

    current_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    header_positions = {
        header: index + 1
        for index, header in enumerate(headers)
    }

    # If the account was manually approved but Approved_At is blank,
    # record the first successful login after approval.
    approved_at_value = str(
        record.get("Approved_At", "")
    ).strip()

    if (
        not approved_at_value
        and "Approved_At" in header_positions
    ):
        worksheet.update_cell(
            row_number,
            header_positions["Approved_At"],
            current_time,
        )

    if "Last_Login" in header_positions:
        worksheet.update_cell(
            row_number,
            header_positions["Last_Login"],
            current_time,
        )

    approved_record = dict(record)
    approved_record["Approved_At"] = (
        approved_at_value or current_time
    )
    approved_record["Last_Login"] = current_time
    approved_record["Login_Status"] = "Approved"

    return True, approved_record