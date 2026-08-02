# Demo and interview script

## 30-second explanation

“The Microsoft Financial Intelligence Platform turns Microsoft’s public SEC data into validated executive intelligence. A Python pipeline normalizes fiscal periods and derives Q4 safely, SQLite and SQL centralize analytics, and Streamlit presents current, quarterly, and annual performance. A complementary Power BI report uses the same approved views. I also built a source-grounded AI workflow that accepts only approved financial and Investor Relations context, validates every structured claim, and falls back deterministically. The Azure adapter is implemented, but live generation is pending deployment quota.”

## 90-second portfolio pitch

“I approached this as a platform and product problem, not a dashboard exercise. Business users need to answer four questions quickly: how Microsoft is performing, what changed, what is driving it, and what deserves attention.

The system begins with SEC Company Facts. Python selects observations belonging to the correct fiscal year, derives Q4 from full-year and nine-month values when necessary, validates the result, and loads SQLite. SQL views calculate growth and margins once, then approved exports power Streamlit and Power BI.

For business drivers, I created a period-specific approved packet from Microsoft Investor Relations. It separates reported facts, derived contribution metrics, and management-attributed explanations. The AI layer is provider-independent: it builds a strict grounding context, requests structured output, checks figures and source IDs, and atomically saves only an approved briefing. Streamlit never calls Azure; it revalidates saved JSON and otherwise displays deterministic insights. The workflow has 86 passing tests. The honest remaining dependency is a compatible Azure deployment and available quota, so I do not claim live AI generation yet.”

## Three-minute live demo

### 0:00–0:45 — Executive Overview

1. Open Streamlit on Executive Overview.
2. Point out the latest fiscal-period badge and FY2026 Q4 revenue.
3. Show QoQ and YoY growth plus gross, operating, and net margins.
4. Explain that the revenue chart gives orientation without changing the underlying SQL calculations.
5. Identify the current deterministic briefing label. If a real validated saved briefing is available later, show the distinct “AI-Generated Executive Briefing” label.

### 0:45–1:30 — Quarterly and historical context

1. Open Quarterly Performance.
2. Change the financial metric and explain chronological fiscal-quarter ordering.
3. Show the profitability trend and exact-value table.
4. Open Historical Trends and explain why only complete fiscal years from FY2019 onward appear.

### 1:30–2:20 — Trustworthy AI architecture

1. Show `data/approved/business_drivers/FY2026-Q4.json` without exposing unrelated local configuration.
2. Explain reported facts versus code-derived segment contribution and management attribution.
3. Show `src/ai/validation.py` and the atomic storage boundary.
4. Explain that missing or invalid JSON returns to `src/insights.py`.

### 2:20–3:00 — Offline Azure workflow and status

1. Show the documented dry-run command.
2. Explain that the CLI—not Streamlit—constructs the Azure provider.
3. Mention explicit timeout, disabled retries, strict structured output, and replacement protection.
4. Close with the actual status: implementation and mocked validation are complete; a deployment and quota are still required for a live generation claim.

## Technical architecture explanation

- **Data:** SEC JSON → fiscal transformation → validation → SQLite.
- **Analytics:** SQL views → approved CSV exports → Streamlit and Power BI.
- **Qualitative evidence:** approved Microsoft Investor Relations packet by reporting period.
- **AI:** `GroundingContext` → deterministic prompt → provider protocol → Azure CLI adapter.
- **Trust:** Pydantic schema → exact/tolerant figure checks → source and driver checks → atomic JSON.
- **Presentation:** revalidate saved output or use deterministic fallback; never call Azure during rendering.

## Product-management explanation

The product is designed around time-to-understanding rather than chart count. Executive Overview answers the current-state question first, Quarterly Performance supports diagnosis, and Historical Trends adds context. SQL owns calculations to prevent disagreement across surfaces. Approved driver packets trade breadth for traceability. Offline generation trades immediacy for cost control, repeatability, and safe fallback.

## Key tradeoffs

- Narrow Microsoft-only scope instead of shallow multi-company coverage.
- Four fully validated financial metrics instead of a larger incomplete inventory.
- Approved source packets instead of open-ended retrieval.
- Structured AI output instead of unconstrained prose.
- Offline generation instead of page-time latency and quota risk.
- Source IDs today instead of unsupported accession-level citation claims.

## Likely interview questions

**Why derive Q4?**  
SEC Company Facts may provide full-year and nine-month duration facts rather than a standalone fourth-quarter observation. The pipeline validates both periods and subtracts nine months from the annual value.

**How did you prevent comparative-filing leakage?**  
Observation selection ties facts to the fiscal year represented by their period dates instead of selecting whichever comparative observation was filed latest.

**Why is SQL the calculation authority?**  
It keeps growth and margins consistent across exports, Streamlit, Power BI, and AI grounding.

**How do you stop hallucinated numbers?**  
The provider must return structured claims. Every claim is matched to an approved metric and source; USD values match exactly and percentages use a 0.01-point tolerance.

**How do you validate business explanations?**  
Only approved packet content is available. Management explanations retain attribution, while segment contribution shares are calculated and labeled derived.

**Why not call Azure from Streamlit?**  
Offline generation controls cost, latency, retries, and auditability. The UI stays available through deterministic fallback.

**Is the AI live?**  
No. The adapter and CLI are implemented and mocked end-to-end, but live generation awaits a compatible Azure deployment and quota.

**Has the product been user tested?**  
Not yet. A structured four-participant research plan exists; no findings are claimed.

**Is Microsoft involved?**  
No. The project uses public disclosures and is not Microsoft-endorsed or validated.

## Offline fallback plan

If the hosted app or network is unavailable:

1. Run Streamlit locally against the committed approved exports.
2. If local rendering is unavailable, walk through the Power BI file or repository architecture.
3. Use the FY2026 Q4 approved CSV and business-driver packet to explain validated outputs.
4. Show test results and the dry-run path rather than attempting a live Azure call.
5. State clearly that any displayed deterministic insight is not AI-generated.
