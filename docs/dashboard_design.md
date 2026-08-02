# MVP Power BI Dashboard Design

## Document Role

This document defines the MVP Power BI experience for the Microsoft Financial
Intelligence Platform. It translates the existing product vision, principles,
decision framework, metric inventory, and SQL analytics layer into a concrete
dashboard experience. It is not a new product requirements document or a
replacement for the product vision.

---

## 1. Dashboard Purpose

The dashboard helps a business professional quickly understand Microsoft's
current financial performance, what changed, whether the change is part of a
broader trend, and what deserves attention.

The experience should turn validated SEC filing data into a concise executive
view first, then allow progressively deeper quarterly and annual analysis. The
Executive Overview must communicate the current situation in under one minute.

The dashboard is one delivery surface of the broader platform. The underlying
ingestion, transformation, validation, storage, and analytics layers remain
essential to its accuracy and future use by Power BI and AI summaries.

## 2. Primary User

The primary user is a business professional who needs to understand and explain
Microsoft's financial performance without spending hours reading SEC filings
or interpreting accounting-oriented tables.

The MVP assumes that the user:

- Understands common business terms such as revenue and profit, but may not be
  a finance specialist.
- Wants a reliable executive answer before exploring details.
- Needs comparisons and context, not isolated numbers.
- May use the findings in a meeting, briefing, or follow-up analysis.

## 3. Core User Need

> Help me understand how Microsoft is performing now, what changed, whether it
> is a broader trend, and what I should investigate next.

The dashboard should reduce time-to-understanding while preserving the accuracy
and traceability of Microsoft's official SEC data.

## 4. Business Questions the Dashboard Must Answer

The MVP must answer these questions in order:

1. What is the latest available Microsoft fiscal period?
2. How much revenue did Microsoft generate in that period?
3. Did revenue increase or decrease from the previous quarter?
4. Did revenue increase or decrease from the same quarter last year?
5. How profitable was the latest quarter?
6. How have revenue and profit changed across recent quarters?
7. Are margins improving, stable, or deteriorating?
8. Is the latest performance consistent with the longer-term annual trend?
9. Which material movements deserve further attention?
10. Can the user confidently summarize Microsoft's performance to someone else?

The Power BI MVP can identify material movements from the available SQL
metrics. Operational causes such as product, segment, pricing, acquisition, or
geographic drivers are not in that analytics layer. Separately, the Streamlit
AI workflow can use an approved period-specific business-driver packet; FY2026
Q4 is the only currently approved packet, and management explanations remain
explicitly attributed.

## 5. Information Hierarchy

The experience follows an executive-first, progressive-disclosure hierarchy:

1. **Orientation:** Show the latest fiscal period and establish that all
   headline values refer to the same period.
2. **Current performance:** Show revenue, growth, and profitability in a compact
   KPI band.
3. **Change:** Show the quarterly revenue trajectory and the direction and
   magnitude of key movements.
4. **Interpretation:** Reserve a clearly labeled area for deterministic key
   insights now and an AI-generated executive summary later.
5. **Quarterly diagnosis:** Let users compare revenue and profit measures and
   inspect margin trends.
6. **Long-term context:** Show annual growth and profitability trends.

### Executive Overview Reading Order

The first page should use this top-to-bottom reading order:

1. Page title, latest fiscal-period badge, and data-source context.
2. Revenue and revenue growth cards.
3. Margin cards.
4. Quarterly revenue trend.
5. Key insights / executive summary area.

This hierarchy is intentionally narrow. The main page should not require
scrolling at the target desktop canvas size.

## 6. Recommended Pages

The MVP contains three pages:

1. **Executive Overview** — the current situation and the fastest path to
   understanding.
2. **Quarterly Performance** — quarterly revenue, profit, comparisons, and
   profitability trends.
3. **Historical Trends** — annual growth and margin context.

Page navigation should remain visible and use these exact names. Page 1 opens by
default.

---

## 7. Page 1 — Executive Overview

### Purpose

Answer, in under one minute: How is Microsoft performing now, what changed, and
what deserves attention?

### Filters and Context

The page is fixed to the latest available fiscal period. It should not include
a fiscal-period slicer because changing the period would make the meaning of
"current" ambiguous. Detailed period exploration belongs on Page 2.

Display the source context as: **Microsoft SEC Company Facts · Latest available
fiscal period**. A compact header badge supplies the precise period without
using KPI-card space.

### KPI Cards and Visuals

| # | Element | Exact content and format | SQL view and fields | Why it is included |
|---|---|---|---|---|
| 1 | Latest fiscal-period badge | `FY{fiscal_year} {fiscal_period}`; text in the page header | `vw_latest_quarter`: `fiscal_year`, `fiscal_period` | Orients the user and prevents KPI values from being read without adding another analytical card. |
| 2 | Revenue card | `Revenue`; currency in USD billions, one decimal place | `vw_latest_quarter`: `revenue` | Revenue is the clearest headline measure of current business scale and growth. |
| 3 | QoQ revenue growth card | `Revenue growth vs prior quarter`; percentage, one decimal place; include up/down/flat indicator | `vw_latest_quarter`: `revenue_qoq_growth_pct` | Answers what changed most recently and provides short-term momentum. |
| 4 | YoY revenue growth card | `Revenue growth vs prior year`; percentage, one decimal place; include up/down/flat indicator | `vw_latest_quarter`: `revenue_yoy_growth_pct` | Controls for seasonality by comparing the same fiscal quarter across years. |
| 5 | Gross margin card | `Gross margin`; percentage, one decimal place | `vw_latest_quarter`: `gross_margin_pct` | Shows how much revenue remains after cost of revenue and provides a high-level view of business economics. |
| 6 | Operating margin card | `Operating margin`; percentage, one decimal place | `vw_latest_quarter`: `operating_margin_pct` | Shows profitability from core operations and operating leverage. |
| 7 | Net margin card | `Net margin`; percentage, one decimal place | `vw_latest_quarter`: `net_margin_pct` | Shows bottom-line profitability after all expenses and other effects. |
| 8 | Quarterly revenue trend | Line chart; x-axis `fiscal_year` + ordered `fiscal_period`; y-axis revenue in USD billions; show the most recent 12 quarters by default | `vw_quarterly_analytics`: `fiscal_year`, `fiscal_period`, `quarter_number`, `revenue` | Establishes whether the latest revenue result continues or breaks the recent trend. Twelve quarters balance trend context with readability. |
| 9 | Key insights / executive summary area | A text panel containing three concise observations: latest revenue growth, profitability snapshot, and one notable trend; labeled as described below | `vw_latest_quarter` for current metrics plus `vw_quarterly_analytics` for recent trend context | Converts metrics into a scannable executive narrative and supports the product principle of understanding over information. |

### Layout

- Top row: page title and latest fiscal period.
- Second row: Revenue, QoQ revenue growth, and YoY revenue growth.
- Third row: Gross margin, Operating margin, and Net margin.
- Lower section: quarterly revenue trend on approximately two-thirds of the
  width; executive summary area on the remaining one-third.

Revenue and its comparisons appear before margins because they explain the
current direction before the page evaluates profitability.

---

## 8. Page 2 — Quarterly Performance

### Purpose

Help the user inspect quarterly performance, compare the four available
financial measures, and determine whether profitability is improving or
deteriorating.

### Filters and Interactions

Provide a fiscal-year slicer with multi-select and a default range covering the
most recent three fiscal years, plus a single-select metric control containing
Revenue, Gross profit, Operating income, and Net income. A period selected in a
chart may cross-filter the cards and detail table. Include a visible **Reset
filters** action.

The four KPI cards show the selected quarter when one quarter is selected. When
no single quarter is selected, they show the latest quarter within the active
fiscal-year filter. The page subtitle must display the active fiscal period so
the card context is never implicit.

### KPI Cards and Visuals

| # | Element | Exact content and format | SQL view and fields | Why it is included |
|---|---|---|---|---|
| 1 | Revenue card | `Revenue`; USD billions, one decimal place | `vw_quarterly_analytics`: `revenue` | Establishes the scale of sales for the active quarter. |
| 2 | Gross profit card | `Gross profit`; USD billions, one decimal place | `vw_quarterly_analytics`: `gross_profit` | Connects revenue to the profit remaining after cost of revenue. |
| 3 | Operating income card | `Operating income`; USD billions, one decimal place | `vw_quarterly_analytics`: `operating_income` | Shows earnings from operations and highlights operating leverage or pressure. |
| 4 | Net income card | `Net income`; USD billions, one decimal place | `vw_quarterly_analytics`: `net_income` | Shows the bottom-line result for the active quarter. |
| 5 | Selected quarterly metric trend | One line chart controlled by the metric selector; default Revenue; x-axis fiscal period; y-axis selected metric in USD billions | `vw_quarterly_financials`: `fiscal_year`, `fiscal_period`, and the selected field from `revenue`, `gross_profit`, `operating_income`, `net_income` | Gives every supported financial measure a clear quarterly trend while showing only one at a time, reducing visual density and avoiding misleading scale comparisons. |
| 6 | Quarterly profitability trends | Three-line chart; Gross margin, Operating margin, and Net margin; percentage y-axis; common fiscal-period x-axis | `vw_quarterly_analytics`: `fiscal_year`, `fiscal_period`, `quarter_number`, `gross_margin_pct`, `operating_margin_pct`, `net_margin_pct` | Reveals whether growth is translating into stronger profitability and whether margin changes are broad or isolated. |
| 7 | Quarterly comparison table | Rows by fiscal period; columns: Revenue, QoQ revenue growth, YoY revenue growth, Gross profit, Operating income, Net income, Gross margin, Operating margin, Net margin | `vw_quarterly_analytics`: corresponding fields plus `fiscal_year`, `fiscal_period`, `quarter_number` | Supports exact-value lookup, quarter-to-quarter comparison, and export without making a dense table the primary experience. |

### Display Rules

- Sort all quarterly visuals by `fiscal_year`, then `quarter_number`; never sort
  fiscal periods alphabetically.
- Place the four cards in one compact row, the selected-metric and profitability
  charts side by side, and the comparison table below them.
- Keep the table to approximately six visible rows with vertical scrolling.
  It is a lookup and accessibility aid, not the page's dominant element.
- Use one decimal place for USD billions and percentages.
- Permit negative operating income, net income, and their margins; display a
  minus sign and accessible negative-state indicator.
- Do not imply that a quarter caused another metric to change. The page shows
  relationships and trends, not causal attribution.

---

## 9. Page 3 — Historical Trends

### Purpose

Show whether current performance is part of a broader annual pattern and help
the user distinguish short-term movement from long-term direction.

### Filters and Interactions

Provide a fiscal-year range slicer. Default to all complete fiscal years
from FY2019 onward. FY2019 is the first year in the current dataset with four
non-null quarters for all four MVP metrics. Selecting a year in one chart
cross-filters the other annual visuals.

Only years with Q1–Q4 and non-null revenue, gross profit, operating income, and
net income may appear on this page. Determine eligibility during refresh from
`vw_quarterly_financials`, then filter `vw_annual_financials` to those fiscal
years. This can be implemented in the Power BI semantic model with the current
views and avoids presenting a partial-year sum as a completed annual result.

### KPI Cards and Visuals

| # | Element | Exact content and format | SQL view and fields | Why it is included |
|---|---|---|---|---|
| 1 | Latest annual revenue card | `Annual revenue`; latest complete fiscal year; USD billions, one decimal place | `vw_annual_financials`: `fiscal_year`, `revenue` | Gives an immediate annual scale reference before the user reads the trends. |
| 2 | Latest annual revenue growth card | `Annual revenue growth`; latest complete fiscal year; percentage, one decimal place | `vw_annual_financials`: `revenue_yoy_growth_pct` | Summarizes long-term growth momentum in one number. |
| 3 | Annual revenue and growth | Combo chart; columns for annual revenue in USD billions; line for annual revenue growth percentage; x-axis fiscal year | `vw_annual_financials`: `fiscal_year`, `revenue`, `revenue_yoy_growth_pct` | Shows both absolute scale and growth rate, making acceleration or deceleration visible. |
| 4 | Annual margin trends | Three-line chart; Annual gross margin, operating margin, and net margin; percentage y-axis; x-axis fiscal year | `vw_annual_financials`: `fiscal_year`, `gross_margin_pct`, `operating_margin_pct`, `net_margin_pct` | Shows whether Microsoft's longer-term profitability is strengthening, stable, or weakening. |
| 5 | Annual financial detail table | Rows by fiscal year; columns: Revenue, Revenue growth, Gross margin, Operating margin, Net margin | `vw_annual_financials`: `fiscal_year`, `revenue`, `revenue_yoy_growth_pct`, `gross_margin_pct`, `operating_margin_pct`, `net_margin_pct` | Provides precise values and an accessible alternative to reading chart positions. |

Place the two cards in one compact row, the two charts side by side, and the
detail table beneath them. The charts are the primary experience; the table is
for exact-value lookup and accessibility.

---

## 10. SQL View Usage

The Power BI semantic model should use the analytics views as follows:

| SQL view | MVP role |
|---|---|
| `vw_latest_quarter` | Single-row source for Page 1 KPI cards and the current-period portion of the executive summary. |
| `vw_quarterly_analytics` | Primary quarterly analytical source for growth, margins, Page 1 revenue trend, and Page 2 cards/table. |
| `vw_quarterly_financials` | Simple wide financial source for the Page 2 selected-metric trend and the complete-year eligibility check used by Page 3. |
| `vw_annual_financials` | Source for all Page 3 cards, annual revenue growth, and margin trends after applying the complete-year eligibility filter. |
| `executive_dashboard` | Existing simplified quarterly export. It is not required as a separate Power BI source because `vw_quarterly_analytics` contains the same financial values and margins plus growth fields. Keeping it outside the report model avoids duplicate facts and ambiguous relationships. |

Power BI should not recompute SQL-provided growth percentages or margins unless
required solely for display behavior. Centralizing financial calculations in
the analytics layer keeps results consistent across Power BI, exports, and
future AI consumers.

### Current Data Scope

- All five SQL views named above exist in the current SQLite database.
- The latest-quarter, quarterly growth, quarterly margin, and annual fields
  specified for the visuals exist in those views.
- Revenue is complete across all four quarters beginning in FY2019. Earlier
  years contain operating income, net income, and in some years gross profit,
  but no revenue under the currently selected SEC revenue concept.
- The Power BI MVP therefore uses FY2019 onward for visuals that compare all
  four metrics or calculate revenue-based growth and margins. This is a
  data-availability boundary, not a user-selectable default that can expose
  unsupported earlier comparisons.
- No new SQL view or metric is required to build the defined MVP. Power BI needs
  only display measures, a four-option metric selector, chronological sort
  behavior, and a refresh-time complete-year eligibility rule.

## 11. What Is Excluded from the MVP

Exclude the following from the Power BI MVP until the required semantic-model
data, product behavior, or trust controls exist. Some business-driver and AI
capabilities now exist in the Streamlit workflow through separate approved
packets; they are not silently treated as Power BI/SQL features.

- Segment, product, geography, customer, and business-driver visuals sourced
  from the current SQL views. FY2026 Q4 segment and product context exists only
  in the approved business-driver packet used by AI grounding.
- Unattributed causal explanations of why a metric changed.
- Operating cash flow, total assets, total liabilities, cash and equivalents,
  and EPS. Operating cash flow appears in the existing metric inventory as a
  core dashboard metric, but none of these measures are currently produced by
  the transformation pipeline or analytics views.
- Forecasts, valuation, price targets, recommendations, and investment advice.
- Peer or competitor benchmarking.
- Scenario planning and what-if parameters.
- Natural-language search or conversational analytics.
- Live AI requests from Power BI or Streamlit. The implemented AI workflow uses
  explicit offline generation and saved, revalidated JSON; live Azure
  generation remains pending deployment and quota.
- Filing-document navigation or accession-level drill-through. Accession
  numbers exist in the base `quarterly_financials` table but are not exposed in
  the current analytics views.
- User accounts, alerts, subscriptions, collaboration, and personalization.
- Mobile-specific layouts unless separately prioritized after the desktop MVP.
- Decorative charts, gauges, speedometers, 3D charts, and visuals that do not
  answer one of the defined business questions.

These exclusions keep the first release focused on fast, trustworthy
understanding of the financial metrics currently supported by the platform.

## 12. Executive Briefing Behavior

Page 1 reserves an executive briefing panel.

The Power BI MVP should use either:

1. Clearly labeled, deterministic text assembled from the latest-quarter and
   trend fields; or
2. A neutral unavailable-state message that does not imply generation occurred.

The Streamlit implementation now makes a stricter runtime selection: it loads a
saved AI-generated briefing only after revalidating it against current approved
financial and business-driver context. Otherwise it displays the existing
deterministic briefing without an AI-generated label. Streamlit never calls
Azure while rendering.

Any validated AI-generated summary should:

- State the fiscal period being summarized.
- Describe performance and profitability using supported structured claims.
- Separate primary drivers, headwinds, attention items, and investigation
  questions.
- Distinguish reported facts, derived metrics, management-attributed
  explanations, and AI interpretation.
- Distinguish facts from interpretation.
- Use only validated analytics-layer data.
- Identify its source and generation status.
- Remain concise and executive-readable.
- Never present investment advice or replace user judgment.

The SQL views do not contain narrative drivers or source-level citations.
Qualitative driver claims therefore require an approved business-driver packet,
and accession-level filing citations remain unavailable.

## 13. UX and Accessibility Principles

### Clarity and Cognitive Load

- Lead with the answer, then provide detail.
- Use plain business language; avoid SEC/XBRL field names in visible labels.
- Keep each visual tied to a defined business question.
- Use whitespace and consistent alignment instead of decorative containers.
- Avoid scrolling on Page 1 at the target desktop canvas size.
- Keep tooltips concise and define QoQ, YoY, and margin terms in plain language.

### Consistent Financial Formatting

- Label currency as USD and display headline values in billions.
- Use one decimal place for currency and percentages in the report.
- Show full precision in tooltips only when useful.
- Use `FY2026 Q4` formatting consistently.
- Order quarters Q1, Q2, Q3, Q4 using `quarter_number`.
- Clearly label derived Q4 values in metadata or tooltips when provenance fields
  become available to the semantic model.

### Accessible Visual Design

- Meet WCAG 2.1 AA contrast targets for text and meaningful visual elements.
- Do not communicate positive, negative, or selected states by color alone; pair
  color with arrows, signs, labels, or patterns.
- Use a color-blind-safe palette with stable metric colors across pages.
- Provide descriptive visual titles that state the question or takeaway.
- Add alt text to every non-text visual.
- Preserve logical keyboard tab order from page title to filters, KPIs, charts,
  and tables.
- Keep text at readable sizes and avoid rotated axis labels.
- Provide the detail tables as accessible alternatives to charts.
- Ensure focus indicators and selected-filter states are visible.

### Trust and Interpretation

- Identify Microsoft SEC Company Facts as the data source.
- Display the fiscal period prominently and never mix periods within a KPI band.
- Distinguish generated or deterministic narrative from raw financial facts.
- Treat missing values as unavailable; never silently replace them with zero.
- Use neutral colors by default. A decline is not automatically "bad," and an
  increase is not automatically "good" without business context.
- Avoid causal language unless future source data directly supports it.

## 14. MVP Acceptance Criteria

The MVP is accepted when all of the following are true.

### Executive Understanding

- [ ] The report opens on **Executive Overview**.
- [ ] A first-time business user can identify the latest fiscal period, revenue,
  QoQ revenue growth, YoY revenue growth, and all three margins without
  interaction.
- [ ] In a usability check, representative users can accurately summarize the
  current financial situation in under one minute.
- [ ] The executive summary area is present and does not imply unavailable AI
  functionality.

### Page and Visual Completeness

- [ ] The report contains exactly the three MVP pages defined in this document.
- [ ] Page 1 contains the fiscal-period badge, six specified KPI cards,
  quarterly revenue trend, and executive summary area.
- [ ] Page 2 contains the four financial cards, selected quarterly metric trend,
  profitability trend chart, and quarterly comparison table.
- [ ] Page 3 contains the two annual cards, annual revenue/growth combo chart,
  annual margin trend chart, and annual detail table.
- [ ] Every visual uses the SQL view and fields specified in this document.
- [ ] No excluded metric or unsupported causal explanation appears.

### Data Correctness

- [ ] Page 1 cards reconcile exactly to `vw_latest_quarter`.
- [ ] Quarterly financial visuals reconcile to `vw_quarterly_financials` or
  `vw_quarterly_analytics`, as specified.
- [ ] Annual visuals reconcile exactly to `vw_annual_financials`.
- [ ] Visuals requiring revenue or all four MVP metrics do not expose fiscal
  years before FY2019.
- [ ] QoQ and YoY growth and all margins use the analytics-layer calculations.
- [ ] Fiscal quarters sort chronologically using `quarter_number`.
- [ ] All cards in a KPI band refer to the same visible fiscal period.
- [ ] Missing data remains blank or is labeled unavailable rather than displayed
  as zero.
- [ ] A partial fiscal year is not presented as a completed annual result.

### Usability and Accessibility

- [ ] Page 1 requires no scrolling at the agreed desktop report size.
- [ ] Page navigation, active filters, and reset behavior are clear.
- [ ] Color is never the only indicator of direction, state, or selection.
- [ ] Text and meaningful visual elements meet WCAG 2.1 AA contrast targets.
- [ ] Every chart has alt text, a meaningful title, and an accessible table
  alternative where specified.
- [ ] Keyboard focus order follows the intended reading order.
- [ ] Currency, percentages, fiscal periods, labels, and tooltips are formatted
  consistently across all pages.

### Trust

- [ ] The report identifies Microsoft SEC Company Facts as its source.
- [ ] AI or deterministic narrative is clearly labeled.
- [ ] The report makes no forecasts, investment recommendations, or unsupported
  causal claims.
- [ ] Validation is run successfully on the transformed dataset before the
  Power BI dataset is refreshed.

---

## Current Assumptions and Data Gaps

1. The MVP uses the four measures supported end-to-end today: revenue, gross
   profit, operating income, and net income.
2. `vw_latest_quarter` represents the latest available fiscal quarter after a
   successful pipeline refresh.
3. Revenue is complete only from FY2019 onward under the current transformed SEC
   concept. Earlier years are outside the common four-metric MVP reporting
   window.
4. `vw_annual_financials` sums quarterly values but does not expose a
   completeness flag. The semantic model must admit only fiscal years with four
   non-null quarters for every MVP metric, determined from
   `vw_quarterly_financials`.
5. The current quarterly views expose revenue comparison fields but do not
   expose QoQ or YoY comparisons for gross profit, operating income, net income,
   or margins. The MVP therefore compares those measures visually over time
   rather than claiming unsupported period-over-period calculations.
6. The SQL layer contains two overlapping quarterly wide views:
   `executive_dashboard` and `vw_quarterly_analytics`. The latter is the primary
   Power BI source because it adds ordered periods, revenue growth, and margins.
7. Source accession numbers are retained in the base table but are not available
   through the analytics views. Full filing-level traceability requires a future
   analytics-view or drill-through enhancement.
