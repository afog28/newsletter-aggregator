"""
One-time local script to get a Gmail OAuth2 refresh token.

Run this on your local machine (not in CI):
    python scripts/gmail_auth_setup.py

Reads GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET from .env (or environment).
After running, copy the printed GMAIL_REFRESH_TOKEN into your .env file.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Error: google-auth-oauthlib not installed. Run: pip install google-auth-oauthlib")
    sys.exit(1)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]


def main():
    client_id = os.environ.get("GMAIL_CLIENT_ID")
    client_secret = os.environ.get("GMAIL_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("Error: GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET must be set in .env")
        sys.exit(1)

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8080/"],
        }
    }

    print("Copy the URL below and open it in the correct browser profile:")
    print("(The URL will appear after this line — look for 'Please visit this URL')\n")

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=8080, open_browser=False)
    # ↑ open_browser=False so you can copy the URL and open it in the right browser profile

    print("\n" + "=" * 60)
    print("SUCCESS — copy these into your .env file:\n")
    print(f"GMAIL_REFRESH_TOKEN={creds.refresh_token}")
    print(f"GOOGLE_SHEETS_REFRESH_TOKEN={creds.refresh_token}")
    print("=" * 60)
    print("\nBoth tokens are the same value — one OAuth grant covers Gmail + Sheets.")
    print("Also add both to Railway Variables when deploying.")


if __name__ == "__main__":
    main()
