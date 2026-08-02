# Product brief

## Product overview

The Microsoft Financial Intelligence Platform transforms Microsoft’s public SEC financial data into validated analytics and executive-ready business context. Streamlit is the primary interface; Power BI is a complementary reporting layer. The platform also includes a source-grounded AI briefing workflow that is implemented and tested but awaits Azure deployment quota for live generation.

## Primary user

Business professionals who need to understand and explain Microsoft’s performance quickly but do not want to spend hours locating, reconciling, and interpreting financial disclosures.

## Problem statement

Microsoft publishes extensive quarterly and annual information through SEC filings and Investor Relations materials. The information is public, but it is distributed across accounting-oriented facts, comparative periods, earnings tables, and management commentary. Users must determine which period a fact belongs to, calculate comparisons consistently, and distinguish reported results from explanation or interpretation.

## Core user need

> Help me understand how Microsoft is performing now, what changed, what is driving the change, and what deserves further investigation.

## Implemented solution

- A validated SEC-to-SQL financial pipeline with correct fiscal-period selection and Q4 derivation.
- Approved quarterly and annual analytics views and exports.
- A three-page Streamlit experience for current, quarterly, and historical performance.
- A complementary Power BI report using the same approved analytics layer.
- Deterministic executive insights that remain available without AI.
- Period-specific approved Microsoft Investor Relations packets for business drivers, beginning with FY2026 Q4.
- Provider-independent briefing generation with strict claim and source validation.
- An Azure OpenAI adapter and explicit offline CLI that never runs during page rendering.

Natural-language search, open-ended retrieval, forecasting, valuation, and investment recommendations are not implemented.

## Desired outcomes

Planned user research will evaluate whether representative users can:

- summarize current performance in under one minute;
- identify the largest performance driver and main headwind accurately;
- explain the relevant comparison-period change;
- identify what deserves attention;
- use source and classification labels appropriately;
- distinguish deterministic insights from AI-generated content.

These outcomes are targets, not completed user-research findings.

## Current status

The data, analytics, Streamlit, Power BI, grounding, validation, persistence, and Azure CLI layers are implemented. Automated tests pass without Azure access. Live Azure generation is pending a compatible deployment and available quota, and user testing is pending execution of the documented research plan.
