import json
import logging
import uuid
from datetime import datetime, timezone

from src.claude_client import ClaudeClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an expert news analyst. Your job is to process a batch of newsletter emails and:
1. Identify all distinct topics/stories covered across the emails.
2. Merge duplicate coverage (different newsletters reporting on the same story = ONE topic).
3. Return a structured JSON array of unique topics.

Rules:
- Only include genuinely distinct topics (not slight variations of the same story).
- Prefer the most informative title and summary across all sources.
- Extract any relevant URLs from the source emails for each topic.
- Return ONLY valid JSON — no markdown fences, no prose.

Output format (JSON array):
[
  {
    "title": "Short, clear topic title",
    "summary": "2–4 sentence neutral summary of the story",
    "source_newsletters": ["Newsletter Name 1", "Newsletter Name 2"],
    "source_urls": ["https://...", "https://..."]
  }
]
"""


def _build_user_prompt(emails: list[dict]) -> str:
    parts = ["Here are today's newsletter emails:\n"]
    for i, e in enumerate(emails, 1):
        parts.append(f"--- Email {i} ---")
        parts.append(f"From: {e['sender']}")
        parts.append(f"Subject: {e['subject']}")
        parts.append(f"Body:\n{e['body']}")
        if e["urls"]:
            parts.append(f"URLs found: {', '.join(e['urls'][:10])}")
        parts.append("")
    return "\n".join(parts)


def _strip_fences(text: str) -> str:
    """Strip markdown code fences that Claude sometimes wraps JSON in."""
    text = text.strip()
    if text.startswith("```"):
        # Remove opening fence (```json or ```)
        text = text[text.index("\n") + 1:] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[: text.rfind("```")]
    return text.strip()


def _parse_topics(raw: str, claude: ClaudeClient) -> list[dict]:
    cleaned = _strip_fences(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Claude returned invalid JSON after stripping fences — attempting one-shot correction.")
        correction_prompt = (
            "The following is malformed JSON. Return only the corrected, valid JSON array:\n\n"
            + cleaned
        )
        corrected = _strip_fences(claude.call(
            system_prompt="Return only valid JSON. No prose, no markdown fences.",
            user_prompt=correction_prompt,
        ))
        return json.loads(corrected)  # Let this raise if still invalid


def extract_unique_topics(emails: list[dict], claude: ClaudeClient) -> list[dict]:
    """
    Sends all emails to Claude for deduplication and topic extraction.
    Returns a list of topic dicts enriched with topic_id and run_timestamp.
    """
    logger.info("Sending %d emails to Claude for topic extraction...", len(emails))
    user_prompt = _build_user_prompt(emails)
    raw = claude.call(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt, max_tokens=8192)

    topics = _parse_topics(raw, claude)
    now = datetime.now(timezone.utc).isoformat()

    for topic in topics:
        topic["topic_id"] = str(uuid.uuid4())
        topic["run_timestamp"] = now

    logger.info("Extracted %d unique topics from %d emails.", len(topics), len(emails))
    return topics
