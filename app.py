"""
app.py - HealthTriage AI — Main Streamlit Application

Entry point. Handles all UI rendering, user input collection,
safety pre-screening, and result display.

Run with:
    streamlit run app.py
"""

import streamlit as st

from config import APP_TITLE, APP_SUBTITLE, APP_VERSION, DISCLAIMER, validate_config
from safety import check_for_emergency, get_emergency_keywords_display
from triage_engine import analyze_symptoms
from utils import (
    validate_inputs,
    sanitize_text,
    get_urgency_config,
    format_conditions_list,
    get_timestamp,
    COMMON_SYMPTOMS,
)

# ─── Page Config (must be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Global ── */
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }

    /* ── Header ── */
    .app-header {
        background: linear-gradient(135deg, #0a3d62 0%, #1a6b9c 100%);
        padding: 2rem 2.5rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .app-header h1 {
        font-size: 2rem;
        font-weight: 600;
        margin: 0 0 0.3rem;
        letter-spacing: -0.5px;
    }
    .app-header p {
        font-size: 0.95rem;
        opacity: 0.8;
        margin: 0;
    }

    /* ── Disclaimer Banner ── */
    .disclaimer {
        background: #fff8e1;
        border-left: 4px solid #f59e0b;
        padding: 0.75rem 1rem;
        border-radius: 0 8px 8px 0;
        font-size: 0.85rem;
        color: #78350f;
        margin-bottom: 1.5rem;
    }

    /* ── Section Cards ── */
    .section-card {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .section-title {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: #6c757d;
        margin-bottom: 1rem;
    }

    /* ── Urgency Badge ── */
    .urgency-badge {
        display: inline-block;
        padding: 0.5rem 1.5rem;
        border-radius: 50px;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 500;
        font-size: 1.1rem;
        letter-spacing: 2px;
        margin: 0.5rem 0;
    }

    /* ── Emergency Flash ── */
    @keyframes emergency-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    .emergency-banner {
        animation: emergency-pulse 1s ease-in-out infinite;
        background: #c1121f !important;
        color: white !important;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }

    /* ── Conditions List ── */
    .condition-item {
        background: #f8f9fa;
        border-radius: 6px;
        padding: 0.6rem 1rem;
        margin-bottom: 0.5rem;
        font-size: 0.95rem;
        border-left: 3px solid #1a6b9c;
    }

    /* ── Recommendation Box ── */
    .recommendation-box {
        background: #f0f7ff;
        border: 1px solid #bfdbfe;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        font-size: 0.95rem;
        line-height: 1.7;
        color: #1e3a5f;
    }

    /* ── Footer ── */
    .footer {
        text-align: center;
        font-size: 0.78rem;
        color: #adb5bd;
        padding: 1.5rem 0 0.5rem;
    }

    /* ── Streamlit overrides ── */
    .stButton > button {
        background: linear-gradient(135deg, #0a3d62, #1a6b9c);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.65rem 2rem;
        font-size: 1rem;
        font-weight: 500;
        width: 100%;
        transition: opacity 0.2s;
    }
    .stButton > button:hover {
        opacity: 0.88;
    }

    div[data-testid="stTextArea"] textarea {
        font-size: 0.95rem;
    }

    .stCheckbox label {
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


# ─── Config Validation ────────────────────────────────────────────────────────
is_valid, config_error = validate_config()


# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="app-header">
    <h1>🏥 {APP_TITLE}</h1>
    <p>{APP_SUBTITLE} &nbsp;·&nbsp; v{APP_VERSION}</p>
</div>
""", unsafe_allow_html=True)

# ─── Disclaimer ───────────────────────────────────────────────────────────────
st.markdown(f'<div class="disclaimer">{DISCLAIMER}</div>', unsafe_allow_html=True)

# ─── API Key Warning ──────────────────────────────────────────────────────────
if not is_valid:
    st.error(f"⚙️ Configuration Error: {config_error}")
    st.info("Add your OpenAI API key to a `.env` file: `OPENAI_API_KEY=sk-...`")
    st.stop()


# ─── Input Form ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Patient Information</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    age = st.number_input(
        "Age",
        min_value=0, max_value=120, value=25, step=1,
        help="Enter patient age in years."
    )
with col2:
    gender = st.selectbox(
        "Gender",
        options=["Prefer not to say", "Male", "Female", "Other"],
        index=1,
    )

symptoms = st.text_area(
    "Describe your symptoms",
    placeholder=(
        "e.g. I've had a high fever (39°C) for 3 days, along with severe headache, "
        "body aches, and chills. I also feel very weak and have no appetite..."
    ),
    height=130,
    help="Be as specific as possible: location, severity, what makes it worse or better.",
)

duration = st.text_input(
    "How long have you had these symptoms?",
    placeholder="e.g. 3 days, 2 weeks, since yesterday morning",
)

st.markdown("</div>", unsafe_allow_html=True)

# ─── Common Symptoms Checklist ────────────────────────────────────────────────
with st.expander("➕ Quick-select common symptoms (optional)"):
    st.caption("Tick any additional symptoms that apply. These will be combined with your description above.")
    cols = st.columns(3)
    selected_symptoms: list[str] = []
    for i, symptom in enumerate(COMMON_SYMPTOMS):
        with cols[i % 3]:
            if st.checkbox(symptom, key=f"sym_{i}"):
                selected_symptoms.append(symptom)

# ─── Emergency Hint ───────────────────────────────────────────────────────────
with st.expander("🚨 When to call emergency services immediately"):
    kw_list = get_emergency_keywords_display()
    st.warning(
        "If you or someone has **" + "**, **".join(kw_list) + "** — "
        "**call 112 or 199 NOW** and do not use this tool."
    )

st.divider()

# ─── Analyze Button ───────────────────────────────────────────────────────────
analyze_clicked = st.button("🔍 Analyze Symptoms", use_container_width=True)

# ─── Analysis Logic ───────────────────────────────────────────────────────────
if analyze_clicked:
    # 1. Input validation
    is_input_valid, input_error = validate_inputs(age, symptoms)
    if not is_input_valid:
        st.error(f"⚠️ {input_error}")
        st.stop()

    # 2. Sanitize
    clean_symptoms = sanitize_text(symptoms)

    # 3. Safety pre-screen
    is_emergency, emergency_response = check_for_emergency(clean_symptoms)

    if is_emergency:
        result = emergency_response
    else:
        # 4. LLM analysis
        with st.spinner("Analyzing symptoms — please wait..."):
            user_input = {
                "age": age,
                "gender": gender,
                "symptoms": clean_symptoms,
                "duration": duration,
                "selected_symptoms": selected_symptoms,
            }
            result = analyze_symptoms(user_input)

    # ─── Results Display ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## 📋 Triage Assessment")
    st.caption(f"Generated: {get_timestamp()}")

    urgency = result.get("urgency", "Unknown")
    cfg = get_urgency_config(urgency)

    # Emergency banner (animated)
    if urgency == "EMERGENCY" or urgency == "Emergency":
        st.markdown(
            f'<div class="emergency-banner">🚨 EMERGENCY — SEEK IMMEDIATE MEDICAL HELP 🚨</div>',
            unsafe_allow_html=True,
        )

    # ── Urgency Card ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Urgency Level</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div>
            <span class="urgency-badge" style="background:{cfg['bg']};color:{cfg['color']};">
                {cfg['emoji']} &nbsp; {cfg['label']}
            </span>
            <p style="margin-top:0.6rem;font-size:0.9rem;color:#495057;">{cfg['description']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Possible Conditions ───────────────────────────────────────────────────
    conditions = result.get("conditions", [])
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Possible Conditions (Non-Diagnostic)</div>', unsafe_allow_html=True)
    st.caption("These are potential possibilities only — NOT a diagnosis.")
    if conditions:
        for condition in conditions:
            st.markdown(f'<div class="condition-item">• {condition}</div>', unsafe_allow_html=True)
    else:
        st.info("No specific conditions identified.")
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Recommendation ────────────────────────────────────────────────────────
    recommendation = result.get("recommendation", "")
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Recommended Next Steps</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="recommendation-box">{recommendation}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Emergency keyword matches (debug info for emergency cases) ────────────
    if is_emergency and result.get("matched_keywords"):
        with st.expander("ℹ️ Emergency trigger details"):
            st.write("Detected keywords:", result["matched_keywords"])

    # ── Re-disclaimer ─────────────────────────────────────────────────────────
    st.markdown(f'<div class="disclaimer">{DISCLAIMER}</div>', unsafe_allow_html=True)

    # ── New Assessment button ─────────────────────────────────────────────────
    if st.button("🔄 Start New Assessment"):
        st.rerun()


# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="footer">{APP_TITLE} v{APP_VERSION} &nbsp;·&nbsp; '
    'For informational purposes only &nbsp;·&nbsp; '
    'Not a substitute for professional medical advice</div>',
    unsafe_allow_html=True,
)