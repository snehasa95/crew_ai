"""LLM provider configuration for the application service layer."""

from __future__ import annotations

import os

from crewai import LLM
from crewai.llms import cache as crewai_cache
from dotenv import load_dotenv
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

MODEL_NAME = "groq/openai/gpt-oss-120b"
load_dotenv()

# Groq rejects CrewAI's prompt cache metadata on user/system messages.
# Ensure the cache breakpoint marker is a no-op for this provider.
crewai_cache.mark_cache_breakpoint = lambda message: message


def _is_rate_limit_error(error: BaseException) -> bool:
    text = str(error).lower()
    return "429" in text or "rate limit" in text or "too many requests" in text


@retry(
    retry=retry_if_exception(_is_rate_limit_error),
    wait=wait_exponential(multiplier=1, min=2, max=16),
    stop=stop_after_attempt(3),
    reraise=True,
)
def build_llm() -> LLM:
    """Create the free-tier Groq chat model from the environment."""
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("groq_api_key")
    if not api_key:
        raise RuntimeError("Set GROQ_API_KEY before asking the assistant a question.")
    return LLM(model=MODEL_NAME, api_key=api_key, temperature=0.2)
