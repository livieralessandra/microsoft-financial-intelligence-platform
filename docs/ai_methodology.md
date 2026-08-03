# AI methodology

## Objective

The AI workflow may summarize and organize approved evidence, but it cannot become a new source of financial facts or business drivers. A fluent response is acceptable only when its structured claims are traceable and validated.

## Approved data boundary

Financial grounding uses only the approved exports in `data/powerbi`. Qualitative business context uses only period-specific packets in `data/approved/business_drivers`. The model receives no browser, tools, retrieval service, file search, code execution, or external data source.

The currently approved business-driver coverage is FY2026 Q4. For another quarter, financial grounding can still work, but driver context is explicitly unavailable and the Streamlit application uses deterministic fallback content.

## Reporting-period grounding

Every request uses a canonical identifier such as `FY2026-Q4`. Grounding selects the exact quarterly row and requires revenue, gross profit, operating income, and net income. It may include the previous quarter and prior-year quarter when available.

Annual context follows an as-of rule:

- Q1–Q3 may use only the most recently completed prior fiscal year.
- Q4 may use the completed annual result for that same fiscal year.

This prevents later data from leaking into an earlier-period briefing.

## Source IDs

Financial sources identify the dataset and period, for example:

- `quarterly_analytics:FY2026-Q4`
- `annual_financials:FY2026`

Approved Investor Relations sources use deterministic IDs such as:

- `msft_ir_fy2026_q4_press_release`
- `msft_ir_fy2026_q4_metrics`
- `msft_ir_fy2026_q4_earnings_call`

Every production briefing insight must declare supporting source IDs. Structured claims also carry metric-specific source references.

## Classification model

| Classification | Meaning |
|---|---|
| Reported fact | A value explicitly present in an approved financial or Investor Relations source. |
| Derived metric | A deterministic calculation performed by platform code from approved facts. |
| Management explanation | A qualitative statement attributed to Microsoft management, not independently proven causation. |
| AI interpretation | A model-generated synthesis constrained by the supplied evidence. |

The workflow rejects derived values presented as reported and management explanations without attribution.

## Structured output

The provider must return JSON matching the strict `ExecutiveBriefing` Pydantic schema. Production approval also requires exactly one insight in each category:

- overall performance;
- primary drivers;
- headwinds;
- profitability context;
- what deserves attention;
- investigate next.

Unexpected fields, malformed values, duplicate sources, unsupported classifications, and missing insight provenance are rejected.

## Validation layers

### Figure validation

- Integer USD and count claims must match exactly.
- Percentages must be within 0.01 percentage points of the approved value.
- A claim is keyed by source ID and metric, preventing a correct number from being attached to the wrong measure.

### Source validation

Briefing and insight source IDs must exist in the current financial context or approved driver packet. Claim sources must be declared by the insight, and insight sources must be declared by the briefing.

### Business-driver validation

Reported company, product, and segment values are matched to approved packet fields. Segment absolute changes and contribution shares are calculated in code and labeled derived. Segment changes must reconcile exactly to the company revenue increase. Unsupported driver names and explanation IDs are rejected.

### Persistence validation

Provider output passes complete validation before `save_briefing` creates a temporary file. The temporary file is flushed, synchronized, and atomically replaced. An invalid replacement cannot touch an existing valid briefing.

Saved output is not trusted indefinitely. Streamlit revalidates it against the current `GroundingContext` on every load because approved exports, packet content, or validation rules may have changed since generation.

## Deterministic fallback

`src/insights.py` produces concise observations directly from approved financial datasets. It is used when:

- no saved briefing exists;
- saved JSON is malformed or stale;
- a figure or source fails validation;
- approved business-driver context is unavailable.

Fallback content is labeled “Executive briefing” and “Data supported,” never “AI-generated.” This keeps the product useful without misrepresenting generation status.

## Plain-language explanations and grounded Q&A

Executive Overview includes deterministic “In Plain English” conclusions, a concise metric guide, and supported common questions built directly from the current `GroundingContext`. These features work without Azure and are not labeled AI-generated. When a period has no approved business-driver packet, explanations remain limited to supported financial conclusions.

Interactive Azure Q&A is disabled by default and requires `ENABLE_AZURE_QA=true` plus the existing Azure environment configuration. Even when enabled, Azure is called only after explicit submission of a question that deterministic routing cannot answer. Provider output must match the strict `GroundedAnswer` schema and pass local period, figure, classification, source, driver, attribution, and investment-language validation before display. Insufficient approved evidence produces `insufficient_context`, not a guess.

Public-use controls include a 500-character question limit, at most five Azure requests per Streamlit session, no automatic retries, a bounded response, an explicit request timeout, no tools or external retrieval, and at most three prior session turns in a prompt. Questions are retained only in Streamlit session state and are never permanently stored. The interface warns users not to submit confidential information and states that answers are not investment advice.

## Unsupported claims and safety

The prompt and validators prohibit invented figures, unsupported drivers, unapproved sources, forecasts, price targets, investment recommendations, and buy/sell language. Narrative text is not treated as a substitute for structured claims. The platform supports business understanding, not investment advice.

## Current limitations

- SEC accession numbers are stored in the base financial table but are not exposed through the approved analytics views. Briefings therefore provide dataset/period source IDs rather than accession-level filing citations.
- Only FY2026 Q4 has an approved business-driver packet.
- Live Azure generation has not succeeded in this project environment because a compatible deployment and available quota are still pending.
- Live Azure Q&A has not been enabled or tested against a deployed model; quota and a compatible deployment remain pending.
- No user research has yet validated whether the AI briefing improves comprehension or trust relative to deterministic insights.

See [Architecture](architecture.md), [Azure generation](azure_ai_generation.md), and [User research plan](user_research.md).
