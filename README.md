# MitochronAi-Health-App
MitochronAI Health App is an AI-powered health triage system that analyzes user-reported symptoms and provides possible conditions, urgency levels, and recommended next steps in real time.

Built with Python, Streamlit, and LLM integration, the app is designed to support early health decision-making, improve awareness, and guide users on when to seek medical attention—especially in underserved and resource-limited environments.

Key features include:
 • Intelligent symptom analysis using AI
 • Urgency classification (Low, Medium, High, Emergency)
 • Emergency detection with safety overrides
 • Clean and accessible user interface
 • Context-aware health suggestions (e.g., malaria, typhoid relevance)

⚠️ Disclaimer: MitochronAI does not provide medical diagnoses and is not a substitute for professional healthcare.

## Run it
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # then add your OpenAI API key (macOS/Linux: cp)
streamlit run app.py
```

## How it works
- `safety.py` screens for emergency keywords **before** any AI call; an emergency is flagged by fixed rules, never left to the model.
- `triage_engine.py` asks the model for possible conditions and an urgency level, and parses the JSON it returns.
- `config.py` reads settings from the environment.

## Licence
MIT, see [LICENSE](LICENSE).
