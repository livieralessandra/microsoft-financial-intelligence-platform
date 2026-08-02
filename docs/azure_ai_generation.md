# Azure AI briefing generation

## Architecture

Executive briefings follow one explicit offline path:

`CLI generation → local validation → atomic saved JSON → Streamlit`

Streamlit never calls Azure. It reads a saved briefing, revalidates it against the current approved financial and business-driver context, and otherwise uses the deterministic fallback.

## Required configuration

Set these environment variables in the execution environment:

- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_DEPLOYMENT`

An Azure OpenAI deployment and available quota are required. The deployment name is passed as the SDK `model` parameter; the application does not assume an underlying model name.

## Commands

Validate configuration, grounding, prompt construction, and the destination without making a request or writing a file:

```bash
python3 python/generate_ai_briefing.py --period FY2026-Q4 --dry-run
```

Generate and save a validated briefing:

```bash
python3 python/generate_ai_briefing.py --period FY2026-Q4
```

Replace an existing briefing only after the replacement passes complete validation:

```bash
python3 python/generate_ai_briefing.py --period FY2026-Q4 --replace
```

Verify the saved briefing through the test suite:

```bash
python3 -m pytest -q
```

## Security and cost control

- Keep credentials only in environment variables; never place them in source files or saved briefings.
- `.env` and `.streamlit/secrets.toml` remain ignored by Git.
- Generated briefing JSON files are ignored by Git by default.
- Generation requires an explicit CLI invocation. Page rendering never spends Azure quota.
- SDK retries are disabled and each request has an explicit timeout.
- The command sends only the deterministic approved prompt and enables no tools, browsing, file search, retrieval, or code execution.
- A generated response is saved only after strict schema, period, figure, source, and business-driver validation.

This integration does not assert that live Azure generation has succeeded.
