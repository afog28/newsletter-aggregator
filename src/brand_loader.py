from functools import lru_cache
from pathlib import Path

DOCS_DIR = Path(__file__).parent.parent / "docs"


def _read(filename: str) -> str:
    path = DOCS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Missing required brand doc: {path}\n"
            "Please fill in the docs/ files before running the pipeline."
        )
    return path.read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def load_brand_brain() -> str:
    return _read("brand_brain.md")


@lru_cache(maxsize=None)
def load_linkedin_rules() -> str:
    return _read("linkedin_rules.md")


@lru_cache(maxsize=None)
def load_video_script_rules() -> str:
    return _read("video_script_rules.md")
