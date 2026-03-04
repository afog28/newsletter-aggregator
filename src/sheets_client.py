import json
import logging
import os
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config.settings import (
    SHEET_LINKEDIN,
    SHEET_TOPICS,
    SHEET_VIDEO,
    SPREADSHEET_ID,
)

logger = logging.getLogger(__name__)

SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _build_service():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_SHEETS_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        scopes=SHEETS_SCOPES,
    )
    creds.refresh(Request())
    return build("sheets", "v4", credentials=creds)


class SheetsClient:
    def __init__(self):
        self._service = _build_service()
        self._spreadsheet_id = SPREADSHEET_ID
        if not self._spreadsheet_id:
            raise EnvironmentError("SPREADSHEET_ID environment variable is not set.")

    def _append(self, tab: str, rows: list[list]) -> None:
        range_name = f"{tab}!A1"
        for attempt in range(3):
            try:
                self._service.spreadsheets().values().append(
                    spreadsheetId=self._spreadsheet_id,
                    range=range_name,
                    valueInputOption="RAW",
                    insertDataOption="INSERT_ROWS",
                    body={"values": rows},
                ).execute()
                return
            except HttpError as exc:
                if attempt == 2:
                    logger.error(
                        "Failed to write %d rows to '%s' after 3 attempts. "
                        "UNWRITTEN ROWS DUMP: %s",
                        len(rows),
                        tab,
                        json.dumps(rows),
                    )
                    raise
                wait = 2 ** attempt
                logger.warning("Sheets write error (attempt %d/3), retrying in %ds: %s", attempt + 1, wait, exc)
                time.sleep(wait)

    def write_topics(self, topics: list[dict]) -> None:
        from datetime import date
        today = date.today().isoformat()
        rows = []
        for t in topics:
            rows.append([
                today,
                t.get("title", ""),
                t.get("summary", ""),
                ", ".join(t.get("source_newsletters", [])),
                ", ".join(t.get("source_urls", [])),
                t.get("topic_id", ""),
                t.get("run_timestamp", ""),
            ])
        logger.info("Writing %d topic rows to '%s'.", len(rows), SHEET_TOPICS)
        self._append(SHEET_TOPICS, rows)

    def write_linkedin_drafts(self, topics: list[dict], drafts: list[dict]) -> None:
        from datetime import date
        today = date.today().isoformat()
        rows = []
        for topic, draft in zip(topics, drafts):
            linkedin = draft.get("linkedin", {})
            rows.append([
                today,
                topic.get("topic_id", ""),
                topic.get("title", ""),
                linkedin.get("post_copy", ""),
                linkedin.get("visual_suggestion", ""),
                "PENDING",
                topic.get("run_timestamp", ""),
            ])
        logger.info("Writing %d LinkedIn draft rows to '%s'.", len(rows), SHEET_LINKEDIN)
        self._append(SHEET_LINKEDIN, rows)

    def write_video_scripts(self, topics: list[dict], drafts: list[dict]) -> None:
        from datetime import date
        today = date.today().isoformat()
        rows = []
        for topic, draft in zip(topics, drafts):
            video = draft.get("video", {})
            rows.append([
                today,
                topic.get("topic_id", ""),
                topic.get("title", ""),
                video.get("hook", ""),
                video.get("narration_script", ""),
                video.get("storyboard_notes", ""),
                "PENDING",
                "",  # Notes — left empty for user
                topic.get("run_timestamp", ""),
            ])
        logger.info("Writing %d video script rows to '%s'.", len(rows), SHEET_VIDEO)
        self._append(SHEET_VIDEO, rows)
