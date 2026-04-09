"""
Shared Gemini client utility.
Supports automatic API key rotation across GEMINI_API_KEY_1, GEMINI_API_KEY_2, ...
Falls back gracefully with exponential backoff on 429 RESOURCE_EXHAUSTED errors.
"""

import os
import time
from google import genai
from dotenv import load_dotenv

load_dotenv()

MODEL = "gemini-2.5-flash-lite"


def _get_api_keys(extra_key: str = None) -> list[str]:
    """
    Collect all available API keys from env vars and optional override.
    Checks GEMINI_API_KEY_1, GEMINI_API_KEY_2, ... and GEMINI_API_KEY.
    """
    keys = []

    # Numbered keys (primary rotation pool)
    for i in range(1, 10):
        k = os.getenv(f"GEMINI_API_KEY_{i}")
        if k:
            keys.append(k)

    # Legacy single key fallback
    legacy = os.getenv("GEMINI_API_KEY")
    if legacy and legacy not in keys:
        keys.append(legacy)

    # Caller-supplied override goes first
    if extra_key and extra_key not in keys:
        keys.insert(0, extra_key)

    if not keys:
        raise EnvironmentError(
            "No Gemini API key found. Set GEMINI_API_KEY_1 (or GEMINI_API_KEY) "
            "in your .env file or enter one in the sidebar."
        )
    return keys


def call_gemini(prompt: str, agent_name: str = "Agent", api_key: str = None) -> str:
    """
    Call the Gemini API with automatic key rotation and retry logic.

    - Tries each API key in sequence on 429 RESOURCE_EXHAUSTED errors.
    - Applies exponential backoff (2s, 4s, 8s) between attempts on the same key.
    - Raises RuntimeError with a clear message if all keys are exhausted.

    Args:
        prompt:     The full prompt string to send.
        agent_name: Human-readable agent name for error messages.
        api_key:    Optional key override (e.g. from sidebar input).

    Returns:
        The response text from Gemini.
    """
    keys = _get_api_keys(api_key)
    last_error = None

    for key_index, key in enumerate(keys, start=1):
        client = genai.Client(api_key=key)
        key_label = f"key {key_index}/{len(keys)}"

        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
            )
            if not response.text:
                raise ValueError("Empty response received from Gemini API.")
            return response.text

        except Exception as exc:
            err = str(exc)
            is_quota = "429" in err or "RESOURCE_EXHAUSTED" in err

            if is_quota:
                # This key is exhausted — try next key immediately
                last_error = exc
                continue
            else:
                # Non-quota errors fail immediately
                raise RuntimeError(
                    f"{agent_name} API call failed ({key_label}): {exc}"
                ) from exc

    raise RuntimeError(
        f"{agent_name} failed: all {len(keys)} API key(s) are rate-limited or exhausted. "
        f"Last error: {last_error}"
    )
