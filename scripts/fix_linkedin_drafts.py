"""
One-time fix: remove the spurious empty 'Notes' column (col 7) from existing
LinkedIn Drafts rows so that Run Timestamp lands in col 7 (matching the header).

Before: Date | Topic ID | Title | Post Copy | Visual Suggestion | PENDING | (empty Notes) | Run Timestamp
After:  Date | Topic ID | Title | Post Copy | Visual Suggestion | PENDING | Run Timestamp
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
SHEET_LINKEDIN = "LinkedIn Drafts"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def build_service():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_SHEETS_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build("sheets", "v4", credentials=creds)


def main():
    service = build_service()
    sheets = service.spreadsheets()

    # Read all values including header
    result = sheets.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_LINKEDIN}!A1:Z",
    ).execute()
    all_rows = result.get("values", [])

    if not all_rows:
        print("Sheet is empty, nothing to fix.")
        return

    header = all_rows[0]
    data_rows = all_rows[1:]
    print(f"Header: {header}")
    print(f"Data rows found: {len(data_rows)}")

    if not data_rows:
        print("No data rows to fix.")
        return

    # Inspect first data row
    print(f"\nFirst data row ({len(data_rows[0])} cols): {data_rows[0]}")

    # If rows have 8 cols, col index 6 (0-based) is the empty Notes and col 7 is Run Timestamp
    # Fix: drop col 6 (empty string) so Run Timestamp moves to col 6
    fixed_rows = []
    for row in data_rows:
        # Pad short rows to 8 cols
        padded = row + [""] * (8 - len(row))
        # Remove col index 6 (empty Notes)
        fixed = padded[:6] + [padded[7]]  # cols 0-5 + col 7 (Run Timestamp)
        fixed_rows.append(fixed)

    print(f"\nFirst fixed row ({len(fixed_rows[0])} cols): {fixed_rows[0]}")

    # Clear the data rows (keep header in row 1)
    # Data starts at row 2
    last_data_row = 1 + len(data_rows)
    clear_range = f"{SHEET_LINKEDIN}!A2:H{last_data_row}"
    sheets.values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=clear_range,
    ).execute()
    print(f"\nCleared range {clear_range}")

    # Write fixed rows back starting at A2
    sheets.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_LINKEDIN}!A2",
        valueInputOption="RAW",
        body={"values": fixed_rows},
    ).execute()
    print(f"Wrote {len(fixed_rows)} fixed rows back to {SHEET_LINKEDIN}.")
    print("Done!")


if __name__ == "__main__":
    main()
