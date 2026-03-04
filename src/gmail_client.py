import base64
import email
import logging
import os
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config.settings import GMAIL_LOOKBACK_HOURS, NEWSLETTER_SENDERS

logger = logging.getLogger(__name__)

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def _build_service():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        scopes=GMAIL_SCOPES,
    )
    creds.refresh(Request())
    return build("gmail", "v1", credentials=creds)


def _extract_body(payload: dict) -> str:
    """Recursively extract plain-text body from a Gmail message payload."""
    mime_type = payload.get("mimeType", "")
    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    if mime_type.startswith("multipart/"):
        for part in payload.get("parts", []):
            text = _extract_body(part)
            if text:
                return text
    return ""


def _extract_urls(body: str) -> list[str]:
    import re
    return re.findall(r"https?://[^\s\]\)>\"']+", body)


@retry(
    retry=retry_if_exception_type(HttpError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True,
)
def fetch_recent_emails() -> list[dict]:
    """
    Returns a list of email dicts for the last GMAIL_LOOKBACK_HOURS hours
    from NEWSLETTER_SENDERS. Empty list if none found.
    """
    if not NEWSLETTER_SENDERS:
        logger.warning("NEWSLETTER_SENDERS is empty in config/settings.py — no emails to fetch.")
        return []

    service = _build_service()

    # Build Gmail search query: from:(sender1 OR sender2) newer_than:1d
    from_query = " OR ".join(f"from:{s}" for s in NEWSLETTER_SENDERS)
    after_dt = datetime.now(timezone.utc) - timedelta(hours=GMAIL_LOOKBACK_HOURS)
    after_epoch = int(after_dt.timestamp())
    query = f"({from_query}) after:{after_epoch}"

    logger.info("Gmail query: %s", query)
    result = service.users().messages().list(userId="me", q=query, maxResults=100).execute()
    message_ids = [m["id"] for m in result.get("messages", [])]

    if not message_ids:
        logger.info("No emails found matching query.")
        return []

    logger.info("Found %d emails. Fetching full content...", len(message_ids))
    emails = []
    for msg_id in message_ids:
        msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
        headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
        body = _extract_body(msg["payload"])
        emails.append({
            "id": msg_id,
            "subject": headers.get("Subject", "(no subject)"),
            "sender": headers.get("From", ""),
            "date": headers.get("Date", ""),
            "body": body[:8000],  # cap per email to avoid huge prompts
            "urls": _extract_urls(body),
        })

    logger.info("Fetched %d emails successfully.", len(emails))
    return emails
