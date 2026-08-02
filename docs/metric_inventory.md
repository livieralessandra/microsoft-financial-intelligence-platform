# Metric inventory

## Financial metrics implemented end-to-end

| Metric | SEC concept | Current use |
|---|---|---|
| Revenue | `RevenueFromContractWithCustomerExcludingAssessedTax` | Quarterly and annual scale, QoQ/YoY revenue growth, margins |
| Gross profit | `GrossProfit` | Quarterly and annual profitability, gross margin |
| Operating income | `OperatingIncomeLoss` | Quarterly and annual operating performance, operating margin |
| Net income | `NetIncomeLoss` | Quarterly and annual bottom-line performance, net margin |

## SQL-derived analytics

| Metric | Calculation authority | Availability |
|---|---|---|
| Previous-quarter revenue | SQL analytics view | Quarterly analytics |
| Prior-year-quarter revenue | SQL analytics view | Quarterly analytics |
| QoQ revenue change and growth | SQL analytics view | Quarterly analytics |
| YoY revenue change and growth | SQL analytics view | Quarterly and annual analytics |
| Gross margin | SQL analytics view | Quarterly and annual analytics |
| Operating margin | SQL analytics view | Quarterly and annual analytics |
| Net margin | SQL analytics view | Quarterly and annual analytics |

Python, Streamlit, Power BI, and AI grounding consume these approved calculations rather than independently recreating them.

## Approved FY2026 Q4 business-driver metrics

The approved packet includes company results, segment revenue, Microsoft Cloud and product growth indicators, commercial remaining performance obligation, capital expenditures, and Microsoft 365 Copilot paid seats. It also includes management-attributed explanations from approved Investor Relations sources.

Segment absolute revenue change, contribution share, and ranking are derived in code. They are not labeled as Microsoft-reported metrics.

## Not implemented in the financial pipeline

- Operating cash flow
- Total assets
- Total liabilities
- Cash and cash equivalents
- Earnings per share
- Geographic revenue
- Customer-level or peer-company metrics
- Forecasts, valuation, or price targets

These items require explicit data-model, validation, and product decisions before inclusion. Their availability in a filing does not make them part of the current MVP.

## Traceability limitation

SEC accession numbers remain in the base `quarterly_financials` table but are not exposed through the approved analytics views. Current financial source IDs identify dataset and reporting period rather than a specific accession.
