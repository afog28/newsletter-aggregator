import os
import logging
from anthropic import Anthropic, RateLimitError, APIStatusError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config.settings import CLAUDE_MODEL

logger = logging.getLogger(__name__)


class ClaudeClient:
    def __init__(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY environment variable is not set.")
        self._client = Anthropic(api_key=api_key)

    @retry(
        retry=retry_if_exception_type((RateLimitError, APIStatusError)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=5, max=60),
        reraise=True,
    )
    def call(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
        logger.debug("Calling Claude API (model=%s, max_tokens=%d)", CLAUDE_MODEL, max_tokens)
        response = self._client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text
