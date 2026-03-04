import json
import logging

from src.brand_loader import load_brand_brain, load_linkedin_rules, load_video_script_rules
from src.claude_client import ClaudeClient

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LinkedIn Agent
# ---------------------------------------------------------------------------

def _linkedin_system_prompt() -> str:
    return f"""\
You are a LinkedIn content strategist writing on behalf of this brand.

## Brand Identity
{load_brand_brain()}

## LinkedIn Content Rules
{load_linkedin_rules()}

## Output Format
Return ONLY valid JSON (no markdown fences, no prose) with this exact structure:
{{
  "post_copy": "The full LinkedIn post text, ready to publish",
  "visual_suggestion": "Description of the ideal image, video, or carousel to pair with this post"
}}
"""


def _linkedin_user_prompt(topic: dict) -> str:
    return (
        f"Write a LinkedIn post for this topic:\n\n"
        f"Title: {topic['title']}\n"
        f"Summary: {topic['summary']}\n"
        f"Source URLs: {', '.join(topic.get('source_urls', []))}"
    )


# ---------------------------------------------------------------------------
# Video Script Agent
# ---------------------------------------------------------------------------

def _video_system_prompt() -> str:
    return f"""\
You are a short-form video script writer creating content on behalf of this brand.

## Brand Identity
{load_brand_brain()}

## Video Script Rules
{load_video_script_rules()}

## Output Format
Return ONLY valid JSON (no markdown fences, no prose) with this exact structure:
{{
  "hook": "The opening 3–5 seconds of spoken script",
  "narration_script": "The full spoken narration from start to finish",
  "storyboard_notes": "Shot-by-shot visual direction notes for each section of the script"
}}
"""


def _video_user_prompt(topic: dict) -> str:
    return (
        f"Write a short-form video script for this topic:\n\n"
        f"Title: {topic['title']}\n"
        f"Summary: {topic['summary']}\n"
        f"Source URLs: {', '.join(topic.get('source_urls', []))}"
    )


# ---------------------------------------------------------------------------
# Shared JSON parser
# ---------------------------------------------------------------------------

def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text[text.index("\n") + 1:] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[: text.rfind("```")]
    return text.strip()


def _parse_json(raw: str, claude: ClaudeClient) -> dict:
    cleaned = _strip_fences(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Content agent returned invalid JSON — attempting one-shot correction.")
        corrected = _strip_fences(claude.call(
            system_prompt="Return only valid JSON. No prose, no markdown fences.",
            user_prompt=f"Fix this malformed JSON and return only the corrected JSON:\n{cleaned}",
        ))
        return json.loads(corrected)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def generate_content(topic: dict, claude: ClaudeClient) -> dict:
    """
    Runs both content agents for a single topic.
    Returns a dict with 'linkedin' and 'video' keys.
    """
    logger.info("Generating content for topic: %s", topic["title"])

    linkedin_raw = claude.call(
        system_prompt=_linkedin_system_prompt(),
        user_prompt=_linkedin_user_prompt(topic),
    )
    linkedin = _parse_json(linkedin_raw, claude)

    video_raw = claude.call(
        system_prompt=_video_system_prompt(),
        user_prompt=_video_user_prompt(topic),
    )
    video = _parse_json(video_raw, claude)

    return {"linkedin": linkedin, "video": video}
