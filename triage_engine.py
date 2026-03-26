"""
triage_engine.py - AI Triage Engine

Handles all LLM interaction:
  - Builds structured, medically responsible prompts
  - Calls OpenAI API
  - Parses and validates JSON response
  - Falls back gracefully on errors

This module is intentionally decoupled from Streamlit so it can be
reused in other contexts (FastAPI, CLI, tests, etc.).
"""

from __future__ import annotations
import json
import logging
from typing import Any

import openai

from config import OPENAI_API_KEY, OPENAI_MODEL, MAX_TOKENS, TEMPERATURE

# Configure module-level logger
logger = logging.getLogger(__name__)

# ─── Response Schema ──────────────────────────────────────────────────────────
URGENCY_LEVELS = {"Low", "Medium", "High", "Emergency"}

EMPTY_RESPONSE: dict = {
    "conditions": [],
    "urgency": "Unknown",
    "recommendation": "Unable to process. Please consult a healthcare professional.",
}

# ─── System Prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are a cautious, responsible medical triage assistant AI.
Your role is DECISION SUPPORT — NOT medical diagnosis or prescription.

STRICT RULES:
1. NEVER state a definitive diagnosis.
2. NEVER recommend specific prescription drugs or dosages.
3. ALWAYS prioritize patient safety above all else.
4. Use cautious, non-alarmist language unless urgency is high.
5. Consider the West African / Nigerian epidemiological context:
   - Malaria, typhoid fever, and dengue fever are common differentials.
   - Sickle cell disease is prevalent.
   - Access to care may be limited; factor this into recommendations.
6. Be concise and clear — your output will be read by non-medical users.
7. Return ONLY valid JSON. No markdown, no preamble, no explanation outside the JSON.

OUTPUT FORMAT (strict JSON):
{
  "conditions": ["<condition 1>", "<condition 2>", ...],   // 2-5 possible conditions, phrased non-diagnostically
  "urgency": "<Low | Medium | High | Emergency>",
  "recommendation": "<1-3 actionable sentences on what the user should do next>"
}

URGENCY DEFINITIONS:
- Low: Symptoms are mild, non-urgent. Self-care or routine clinic visit is appropriate.
- Medium: Symptoms warrant a clinic or GP visit within 24–48 hours.
- High: Symptoms need same-day medical attention at a hospital or urgent care.
- Emergency: Life-threatening. Requires immediate emergency services.

IMPORTANT: You are not replacing a doctor. Frame language accordingly.
""".strip()


# ─── User Prompt Builder ──────────────────────────────────────────────────────

def _build_user_prompt(user_input: dict[str, Any]) -> str:
    """
    Constructs the user-facing portion of the prompt from structured input.

    Args:
        user_input: dict with keys: age, gender, symptoms, duration,
                    selected_symptoms (list).
    Returns:
        Formatted prompt string.
    """
    age = user_input.get("age", "Not provided")
    gender = user_input.get("gender", "Not provided")
    symptoms = user_input.get("symptoms", "").strip()
    duration = user_input.get("duration", "Not provided").strip()
    selected = user_input.get("selected_symptoms", [])

    # Merge typed and checkbox symptoms
    all_symptoms = symptoms
    if selected:
        checkbox_str = ", ".join(selected)
        all_symptoms = f"{symptoms}\nAdditional noted symptoms: {checkbox_str}".strip()

    return f"""
Patient Profile:
- Age: {age}
- Gender: {gender}
- Duration of symptoms: {duration if duration else "Not specified"}

Reported Symptoms:
{all_symptoms if all_symptoms else "No symptoms provided."}

Please analyze these symptoms and return your structured JSON response.
""".strip()


# ─── Core Analysis Function ───────────────────────────────────────────────────

def analyze_symptoms(user_input: dict[str, Any]) -> dict[str, Any]:
    """
    Main entry point. Sends patient data to the LLM and returns a
    structured triage response.

    Args:
        user_input: dict containing age, gender, symptoms, duration,
                    and optionally selected_symptoms.

    Returns:
        dict with keys: conditions (list), urgency (str), recommendation (str).
        On error, returns EMPTY_RESPONSE with an error note.
    """
    # Validate API key early
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key is missing.")
        return {**EMPTY_RESPONSE, "recommendation": "API key not configured. Please contact the administrator."}

    # Build prompts
    user_prompt = _build_user_prompt(user_input)

    logger.info("Sending triage request to %s", OPENAI_MODEL)

    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            response_format={"type": "json_object"},  # Enforces JSON mode
        )

        raw_content: str = response.choices[0].message.content or "{}"
        logger.debug("Raw LLM response: %s", raw_content)

        return _parse_and_validate(raw_content)

    except openai.AuthenticationError:
        logger.error("Invalid OpenAI API key.")
        return {**EMPTY_RESPONSE, "recommendation": "Invalid API key. Please check your configuration."}

    except openai.RateLimitError:
        logger.warning("OpenAI rate limit hit.")
        return {**EMPTY_RESPONSE, "recommendation": "Service temporarily busy. Please try again in a moment."}

    except openai.APIConnectionError:
        logger.error("Network error connecting to OpenAI.")
        return {**EMPTY_RESPONSE, "recommendation": "Network error. Please check your connection and retry."}

    except Exception as exc:
        logger.exception("Unexpected error in analyze_symptoms: %s", exc)
        return {**EMPTY_RESPONSE, "recommendation": f"An unexpected error occurred. Please try again."}


# ─── Response Parser ──────────────────────────────────────────────────────────

def _parse_and_validate(raw: str) -> dict[str, Any]:
    """
    Parses raw LLM JSON string and validates expected fields.

    Falls back to EMPTY_RESPONSE on any parse or validation failure.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("JSON parse error: %s | Raw: %s", e, raw)
        return {**EMPTY_RESPONSE}

    # Normalise field names (LLM may vary capitalisation)
    conditions = data.get("conditions") or data.get("Conditions") or []
    urgency = (data.get("urgency") or data.get("Urgency") or "Unknown").strip().capitalize()
    recommendation = (data.get("recommendation") or data.get("Recommendation") or "").strip()

    # Ensure urgency is one of the allowed levels
    if urgency not in URGENCY_LEVELS:
        logger.warning("Unexpected urgency value '%s', defaulting to 'Unknown'", urgency)
        urgency = "Unknown"

    # Ensure conditions is a list of strings
    if not isinstance(conditions, list):
        conditions = [str(conditions)]
    conditions = [str(c).strip() for c in conditions if c]

    return {
        "conditions": conditions or ["Unable to determine — please consult a doctor."],
        "urgency": urgency,
        "recommendation": recommendation or EMPTY_RESPONSE["recommendation"],
    }