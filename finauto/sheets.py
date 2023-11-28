import os.path
from functools import lru_cache
from fastapi import HTTPException
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import date

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = "1IySauVdf2QOP3NYW-fGWrav52Voyk3b4mzY_Cctxc_Y"
SAMPLE_RANGE_NAME = "Transactions!A:H"


@lru_cache(maxsize=None)
def get_service():
    creds = None
    if os.path.exists("config/token.json"):
        creds = Credentials.from_authorized_user_file("config/token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "config/credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("config/token.json", "w") as token:
            token.write(creds.to_json())

    return build("sheets", "v4", credentials=creds)


@lru_cache(maxsize=None)
def fetch_categories() -> list[str]:
    service = get_service()

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Planned Budget!B:C")
        .execute()
    )
    values = result.get("values", [])

    if not values:
        raise HTTPException(status_code=500, detail="No data found.")
    categories = []

    for row in values[1:]:
        # Print columns A and E, which correspond to indices 0 and 4.
        categories.append(row[0])

    return categories


def append_transaction(
    name: str,
    category: str,
    expense_type: str,
    date: date,
    description: str,
    price: str,
) -> None:
    service = get_service()
    # Date	ISO Date	Type	Currency	Price	Category	Description	Month

    values = [
        [
            date.strftime("%w %B, %Y"),  # Date
            date.isoformat(),  # ISO Date
            expense_type,  # Type
            "BRL",  # Currency
            f"R${price}",  # Price
            category,  # Category
            f"{name} - {description}",  # Description
            date.strftime("%B %Y"),  # Month
        ]
    ]
    body = {"values": values}

    service.spreadsheets().values().append(
        spreadsheetId=SAMPLE_SPREADSHEET_ID,
        range="Transactions!A1",
        valueInputOption="RAW",
        body=body,
    ).execute()
