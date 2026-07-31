# Microsoft Financial Intelligence Platform

An end-to-end financial intelligence platform that transforms Microsoft's SEC filings into structured business insights.

The platform automatically downloads Microsoft's public financial data from the SEC, validates and transforms it through a Python ETL pipeline, stores normalized financial statements in SQLite, and exposes reusable SQL analytics views that power executive dashboards, business intelligence, and future AI-generated financial summaries.

---

## Architecture

SEC Company Facts API
        ↓
Python ETL
        ↓
Data Validation
        ↓
SQLite Database
        ↓
SQL Analytics Views
        ↓
Power BI Dashboard
        ↓
AI Executive Summary

---

## Features

- Automated SEC data ingestion
- Financial data transformation
- Fiscal period normalization
- Quarterly Q4 derivation
- Data validation pipeline
- SQLite data warehouse
- SQL analytics layer
- Quarterly financial analytics
- Revenue growth calculations
- Margin analysis
- Executive financial snapshot
- Power BI ready
- AI-ready architecture

---

## Streamlit MVP

The local web application provides three executive-first experiences:

- Executive Overview
- Quarterly Performance
- Historical Trends

From the repository root:

```bash
python3 -m pip install -r requirements.txt
python3 python/build_powerbi_dataset.py
python3 -m streamlit run app.py
```

Streamlit opens the application at `http://localhost:8501`. The app reads only
the approved exports in `data/powerbi`; it does not use
`data/processed/executive_dashboard.csv`.

---

## Tech Stack

- Python
- SQLite
- SQL
- Power BI
- Streamlit
- Plotly
- Git
- GitHub
- Microsoft SEC Company Facts API

---

## Current Project Structure

```
microsoft-financial-intelligence-platform/

├── data/
│   ├── raw/
│   ├── processed/
│   └── powerbi/
│
├── python/
│   ├── download_sec_data.py
│   ├── transform_financial_data.py
│   ├── validate_data.py
│   ├── load_financial_data.py
│   ├── create_analytics_views.py
│   └── build_powerbi_dataset.py
│
├── src/
│   ├── data_loader.py
│   ├── formatters.py
│   ├── insights.py
│   └── charts.py
│
├── sql/
│   └── create_views.sql
│
├── docs/
│
├── .streamlit/
├── app.py
├── requirements.txt
└── README.md
```

---

## Current Status

✅ SEC Data Ingestion

✅ Python ETL Pipeline

✅ Financial Data Validation

✅ SQLite Data Warehouse

✅ SQL Analytics Layer

✅ Streamlit MVP

🟡 Power BI Dashboard (Planned)

🟡 AI Executive Summary (Planned)

---

## Future Roadmap

- Interactive Power BI dashboard
- AI-generated earnings summaries
- Product Requirements Document (PRD)
- User research
- Feature roadmap
- Azure deployment
