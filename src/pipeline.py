"""
Newsletter Aggregator Pipeline — main entry point.

Run locally:
    python -m src.pipeline

Deployed on Railway as a daily cron (see railway.toml).
"""

import logging
import sys
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()  # No-op in Railway (vars are set natively); loads .env locally

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger("pipeline")


def main() -> None:
    start = time.time()
    logger.info("=== Newsletter pipeline started (%s) ===", datetime.now(timezone.utc).date())

    # --- Step 1: Fetch emails ---
    from src.gmail_client import fetch_recent_emails
    emails = fetch_recent_emails()

    if not emails:
        logger.info("No newsletter emails found in the last 24 hours. Nothing to do.")
        logger.info("=== Pipeline complete in %.1fs ===", time.time() - start)
        sys.exit(0)

    logger.info("Fetched %d emails.", len(emails))

    # --- Step 2: Deduplicate & extract topics ---
    from src.claude_client import ClaudeClient
    from src.topic_extractor import extract_unique_topics

    claude = ClaudeClient()
    topics = extract_unique_topics(emails, claude)

    if not topics:
        logger.info("Claude found no distinct topics in today's emails. Nothing to write.")
        logger.info("=== Pipeline complete in %.1fs ===", time.time() - start)
        sys.exit(0)

    # --- Step 3: Write topics to Sheets ---
    from src.sheets_client import SheetsClient
    sheets = SheetsClient()
    sheets.write_topics(topics)

    # --- Step 4: Generate content for each topic ---
    from src.content_agents import generate_content

    all_drafts = []
    for i, topic in enumerate(topics, 1):
        logger.info("Generating content for topic %d/%d: %s", i, len(topics), topic["title"])
        draft = generate_content(topic, claude)
        all_drafts.append(draft)

    # --- Step 5: Write drafts to Sheets ---
    sheets.write_linkedin_drafts(topics, all_drafts)
    sheets.write_video_scripts(topics, all_drafts)

    elapsed = time.time() - start
    logger.info(
        "=== Pipeline complete in %.1fs — %d topics, %d drafts written to Sheets ===",
        elapsed,
        len(topics),
        len(all_drafts),
    )


if __name__ == "__main__":
    main()
