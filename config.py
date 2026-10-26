"""App settings, read from environment variables (or a local .env file)."""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

APP_TITLE = "MitochronAI Health"
APP_SUBTITLE = "AI-assisted symptom triage"
APP_VERSION = "1.0.0"
DISCLAIMER = (
    "⚠️ MitochronAI does not provide medical diagnoses and is not a substitute for professional healthcare. "
    "If you think you are having an emergency, contact your local emergency number or go to the nearest hospital now."
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1200"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))


def validate_config() -> tuple[bool, str]:
    """Return (ok, error message). The app stops with the message when the key is missing."""
    if not OPENAI_API_KEY:
        return False, "OPENAI_API_KEY is not set."
    return True, ""
