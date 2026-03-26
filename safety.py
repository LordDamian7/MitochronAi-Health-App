"""
safety.py - Emergency Detection & Safety Override System

This module performs FAST, keyword-based pre-screening of symptoms
BEFORE any LLM call. If emergency keywords are detected, it returns
an override response immediately — no API latency, no ambiguity.

This is a hard safety guardrail.
"""

from __future__ import annotations
import re

# ─── Emergency Keyword Registry ───────────────────────────────────────────────
# Each entry is a regex pattern (case-insensitive) that signals a potential
# life-threatening emergency. Group by clinical category for readability.

EMERGENCY_PATTERNS: list[str] = [
    # Cardiac
    r"chest\s*pain",
    r"chest\s*tightness",
    r"heart\s*attack",
    r"palpitations.*severe",
    r"irregular\s*heartbeat.*severe",

    # Respiratory
    r"difficulty\s*breath",
    r"trouble\s*breath",
    r"can'?t?\s*breath",
    r"shortness\s*of\s*breath.*severe",
    r"stopped\s*breath",
    r"not\s*breath",
    r"choking",

    # Neurological
    r"unconscious",
    r"unresponsive",
    r"passed?\s*out",
    r"fainting.*repeatedly",
    r"seizure",
    r"convuls",
    r"stroke",
    r"sudden\s*(weakness|numbness|paralysis)",
    r"facial\s*droop",
    r"slurred\s*speech",

    # Haemorrhagic / Trauma
    r"severe\s*bleed",
    r"heavy\s*bleed",
    r"uncontrolled\s*bleed",
    r"bleed.*won'?t?\s*stop",
    r"coughing\s*(up\s*)?blood",
    r"vomiting\s*(up\s*)?blood",
    r"blood\s*in\s*stool.*severe",

    # Anaphylaxis / Allergy
    r"anaphyla",
    r"throat\s*(closing|swelling)",
    r"allergic\s*reaction.*severe",

    # Altered consciousness
    r"loss\s*of\s*consciousness",
    r"not\s*waking",
    r"won'?t?\s*wake",

    # Poisoning / Overdose
    r"overdose",
    r"poison",
    r"swallowed.*chemical",

    # Obstetric
    r"heavy\s*(vaginal\s*)?bleeding.*pregnan",
    r"eclampsia",
]

# Pre-compile all patterns once at import time for performance
_COMPILED_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE) for p in EMERGENCY_PATTERNS
]

# ─── Override Response ────────────────────────────────────────────────────────
EMERGENCY_RESPONSE: dict = {
    "conditions": ["Potentially life-threatening condition detected"],
    "urgency": "EMERGENCY",
    "recommendation": (
        "🚨 CALL EMERGENCY SERVICES IMMEDIATELY (Nigeria: 112 or 199). "
        "Do NOT wait. Go to the nearest Emergency Room right now. "
        "If the person is unconscious, place them in the recovery position "
        "and do not leave them alone."
    ),
    "matched_keywords": [],  # Populated at runtime
}

# ─── Public API ───────────────────────────────────────────────────────────────

def check_for_emergency(symptoms_text: str) -> tuple[bool, dict | None]:
    """
    Scan free-text symptoms for emergency keywords.

    Args:
        symptoms_text: Raw symptom string entered by the user.

    Returns:
        (is_emergency, response_dict)
        - If emergency: (True, populated EMERGENCY_RESPONSE copy)
        - Otherwise:    (False, None)
    """
    if not symptoms_text or not symptoms_text.strip():
        return False, None

    matched: list[str] = []

    for pattern in _COMPILED_PATTERNS:
        m = pattern.search(symptoms_text)
        if m:
            matched.append(m.group(0))  # Record the exact match

    if matched:
        response = dict(EMERGENCY_RESPONSE)  # Shallow copy
        response["matched_keywords"] = list(set(matched))  # Deduplicate
        return True, response

    return False, None


def get_emergency_keywords_display() -> list[str]:
    """Returns a human-readable list of example emergency keywords (for UI hints)."""
    return [
        "chest pain", "difficulty breathing", "unconscious",
        "severe bleeding", "stroke", "seizure", "overdose",
        "throat closing", "not waking up",
    ]