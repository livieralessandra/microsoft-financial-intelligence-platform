# Microsoft Financial Intelligence Platform — Codex Instructions

This is an existing project. Do not restart or redesign it.

## Safety rules

- Work only inside this repository.
- Stay on the current branch: `feature/ai-generated-insights`.
- Do not delete, rename, move, overwrite, or regenerate existing files without first inspecting them.
- Do not modify the existing SEC, Python, SQLite, SQL, Streamlit, or Power BI architecture unless there is a verified technical reason.
- Do not manually change approved financial data.
- Do not create duplicate files or duplicate documentation.
- Do not expose, print, read aloud, or commit secrets.
- Never modify `.env` or `.streamlit/secrets.toml`.
- Do not commit or push unless explicitly instructed.
- Before editing, run `git status` and inspect relevant files.
- After editing, run tests and show `git diff --stat`.

## Product decisions

- Streamlit is the primary product interface.
- Power BI is a complementary reporting layer.
- Preserve `src/insights.py` as the deterministic fallback.
- AI-generated insights must be real, structured, source-grounded, numerically validated, and traceable to source IDs.
- Do not claim Azure AI is live until a model deployment exists.
- Do not hard-code the system to FY2026 Q4.
- Build reusable logic for any eligible fiscal year and quarter.
- Use FY2026 Q4 only as the first validation case.
- Business drivers must come from approved official-source data, never model invention.

## Existing approved data

Prefer the validated datasets and existing loaders:

- `src/data_loader.py`
- `data/powerbi/quarterly_analytics.csv`
- `data/powerbi/annual_financials.csv`
- `data/powerbi/quarterly_financials.csv`
- `data/powerbi/latest_quarter.csv`

## First development phase

Build only the provider-independent AI foundation:

- generic fiscal-period identifier;
- strict grounding-context schema;
- strict executive-briefing schema;
- reusable context builder from approved datasets;
- validation for fiscal periods, numbers, and source IDs;
- deterministic test fixtures;
- unit tests.

Do not yet:

- call Azure;
- add credentials;
- change Streamlit UI;
- remove deterministic insights;
- generate all historical briefings;
- commit or push.
