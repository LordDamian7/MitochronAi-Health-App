"""
utils.py - Shared Helper Utilities

Stateless, pure helper functions used across the app.
No Streamlit imports here — keep this reusable and testable.
"""

from __future__ import annotations
import re
from datetime import datetime


# ─── Urgency Colour Mapping ───────────────────────────────────────────────────

URGENCY_CONFIG: dict[str, dict] = {
    "Low": {
        "color": "#2d6a4f",       # Deep green
        "bg": "#d8f3dc",
        "emoji": "🟢",
        "label": "LOW",
        "description": "Symptoms are mild. Self-care or a routine clinic visit is appropriate.",
    },
    "Medium": {
        "color": "#b5451b",       # Deep orange
        "bg": "#ffe8d6",
        "emoji": "🟠",
        "label": "MEDIUM",
        "description": "Consider visiting a clinic or GP within the next 24–48 hours.",
    },
    "High": {
        "color": "#c1121f",       # Red
        "bg": "#fde8e8",
        "emoji": "🔴",
        "label": "HIGH",
        "description": "Seek same-day medical attention at a hospital or urgent care centre.",
    },
    "Emergency": {
        "color": "#ffffff",
        "bg": "#c1121f",
        "emoji": "🚨",
        "label": "EMERGENCY",
        "description": "Call emergency services immediately. This may be life-threatening.",
    },
    "Unknown": {
        "color": "#495057",
        "bg": "#e9ecef",
        "emoji": "❓",
        "label": "UNKNOWN",
        "description": "Unable to determine urgency. Please consult a healthcare professional.",
    },
}


def get_urgency_config(urgency: str) -> dict:
    """Returns the display config for a given urgency level."""
    return URGENCY_CONFIG.get(urgency, URGENCY_CONFIG["Unknown"])


# ─── Input Validation ─────────────────────────────────────────────────────────

def validate_inputs(age: int, symptoms: str) -> tuple[bool, str]:
    """
    Validates user inputs before sending to the AI engine.

    Returns:
        (is_valid, error_message)
    """
    if age < 0 or age > 120:
        return False, "Please enter a valid age between 0 and 120."

    cleaned = symptoms.strip()
    if len(cleaned) < 10:
        return False, "Please describe your symptoms in more detail (at least 10 characters)."

    if len(cleaned) > 2000:
        return False, "Symptom description is too long. Please limit to 2000 characters."

    # Basic check: reject if only numbers/special chars
    if not re.search(r"[a-zA-Z]", cleaned):
        return False, "Symptom description must contain readable text."

    return True, ""


# ─── Text Utilities ───────────────────────────────────────────────────────────

def sanitize_text(text: str) -> str:
    """Remove potentially problematic characters while preserving medical text."""
    # Strip HTML/script tags just in case
    text = re.sub(r"<[^>]+>", "", text)
    # Normalise excessive whitespace
    text = re.sub(r"\s{3,}", "  ", text)
    return text.strip()


def format_conditions_list(conditions: list[str]) -> str:
    """
    Formats a list of possible conditions into a numbered string.
    Returns a fallback message if the list is empty.
    """
    if not conditions:
        return "No specific conditions identified. Please consult a healthcare professional."
    return "\n".join(f"{i+1}. {c}" for i, c in enumerate(conditions))


# ─── Timestamp ────────────────────────────────────────────────────────────────

def get_timestamp() -> str:
    """Returns a human-readable timestamp for report headers."""
    return datetime.now().strftime("%d %B %Y, %H:%M")


# ─── Symptom Checkbox Presets ─────────────────────────────────────────────────

COMMON_SYMPTOMS: list[str] = [
    "Fever",
    "Headache",
    "Fatigue / Weakness",
    "Nausea",
    "Vomiting",
    "Diarrhoea",
    "Cough",
    "Sore throat",
    "Body aches / Joint pain",
    "Rash or skin changes",
    "Abdominal pain",
    "Dizziness",
    "Loss of appetite",
    "Chills / Sweating",
    "Yellow eyes or skin (jaundice)",
]