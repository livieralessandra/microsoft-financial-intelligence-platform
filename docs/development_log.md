# Development log

This log preserves the project’s progression while distinguishing completed implementation from pending external validation.

## Sprint 1 — Data acquisition

### Goal

Download Microsoft’s official financial data from the SEC.

### Outcome

Connected to the SEC Company Facts API using Python and retained the raw JSON dataset.

### Key concepts

- APIs and HTTP requests
- JSON and User-Agent headers
- Error handling and timeouts
- ETL extraction

### Reflection

The project began with source reliability and data acquisition rather than dashboard construction.

## Validated SEC-to-product pipeline

The transformation layer selected Microsoft observations by their actual fiscal-period dates instead of always retaining the latest comparative filing. This prevented later filings from contaminating earlier fiscal years. Q4 values are derived only from compatible full-year and nine-month facts. Validation, SQLite loading, and SQL analytics views established one calculation authority for quarterly growth, annual growth, and margins.

`build_powerbi_dataset.py` exports four approved SQL views directly to `data/powerbi` and verifies required views, columns, row counts, and ordering.

## Product surfaces

Streamlit became the primary product interface with Executive Overview, Quarterly Performance, and Historical Trends. Power BI remains a complementary reporting layer using the same approved analytics foundation. Deterministic insights in `src/insights.py` provide useful narrative without claiming AI generation.

## Phase 1 — Provider-independent grounding

Implemented:

- generic reporting-period identifiers;
- strict `GroundingContext` and `ExecutiveBriefing` schemas;
- injected approved financial datasets;
- core-metric eligibility checks;
- annual as-of logic preventing Q1–Q3 look-ahead;
- exact USD and tolerant percentage validation;
- deterministic fixtures and tests.

No provider, credentials, network calls, or Streamlit changes were introduced in this phase.

## Phase 2 — Approved Microsoft business drivers

Added an FY2026 Q4 approved Microsoft Investor Relations packet with deterministic source IDs. The packet separates reported facts, segment results, product indicators, management-attributed explanations, and source metadata. Code derives segment absolute change, contribution percentage, and positive/headwind ranking, with exact reconciliation to the company revenue increase. Missing period packets remain explicitly unavailable rather than inferred.

## Phase 3 — Validated briefing workflow and fallback

Added deterministic prompt construction, the provider-independent `BriefingProvider` protocol, generation approval, atomic persistence, saved-briefing revalidation, and Streamlit-facing selection logic. Streamlit displays “AI-Generated Executive Briefing” only for a real saved artifact that passes current validation. Missing, stale, malformed, or unsupported output uses the unchanged deterministic fallback.

## Phase 4 — Azure adapter and offline CLI

Added the official OpenAI Python SDK, an Azure OpenAI v1 adapter, Pydantic structured-output parsing with strict JSON Schema fallback, explicit timeout, disabled retries, and secret-safe errors. Added `python/generate_ai_briefing.py` for explicit dry-run or generation. Streamlit never constructs the provider or calls Azure.

The adapter and CLI are fully mocked in tests. No live Azure generation is claimed.

## Phase 5 — Portfolio and launch readiness

Aligned the README and product documents with actual implementation, documented architecture and AI methodology, added a planned user-research protocol, created an interview/demo script and launch criteria, and added secret-free GitHub Actions compilation and tests.

## Current external dependency

Live AI generation remains pending a compatible Azure deployment and available quota. User research is also pending. These are deliberately documented as incomplete; no fake briefing, deployment status, user finding, or Microsoft endorsement is asserted.
