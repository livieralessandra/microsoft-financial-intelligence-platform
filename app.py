"""Streamlit MVP for the Microsoft Financial Intelligence Platform."""

from html import escape

import pandas as pd
import streamlit as st

from src.ai.business_drivers import BusinessDriverError
from src.ai.grounding import GroundingError, build_grounding_context
from src.ai.schemas import ExecutiveBriefing, ReportingPeriod
from src.ai.selection import BriefingSelection, select_briefing_for_display
from src.charts import (
    annual_margin_trend,
    annual_revenue_and_growth,
    margin_trend,
    quarterly_metric_trend,
    revenue_trend,
)
from src.data_loader import (
    DataValidationError,
    FinancialDatasets,
    load_financial_datasets,
)
from src.formatters import fiscal_label, format_billions, format_percent
from src.insights import build_executive_insights


st.set_page_config(
    page_title="Microsoft Financial Intelligence Platform",
    page_icon="▦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

APP_CSS = """
<style>
:root {
    --blue: #0078D4;
    --blue-dark: #004E8C;
    --blue-soft: #EAF4FC;
    --green: #107C10;
    --green-soft: #EFF8EF;
    --red: #D83B01;
    --red-soft: #FFF3EF;
    --yellow: #FFB900;
    --ink: #1B1A19;
    --muted: #605E5C;
    --subtle: #8A8886;
    --line: #EDEBE9;
    --surface: #FFFFFF;
    --canvas: #F7F8FA;
}
.stApp {
    background: var(--canvas);
    color: var(--ink);
    font-family: "Segoe UI", Arial, sans-serif;
}
.block-container {
    max-width: 1480px;
    padding-top: 1rem;
    padding-bottom: 2.5rem;
}
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stAppDeployButton"],
.stDeployButton,
#MainMenu,
footer {
    display: none !important;
}
.hero {
    position: relative;
    overflow: hidden;
    background: linear-gradient(118deg, #003A6D 0%, #0067B8 58%, #0078D4 100%);
    border-radius: 20px;
    color: #FFFFFF;
    padding: 2.35rem 2.55rem 2.15rem;
    margin: .7rem 0 1.35rem;
    box-shadow: 0 14px 38px rgba(0, 78, 140, .18);
}
.hero::after {
    content: "";
    position: absolute;
    width: 280px;
    height: 280px;
    right: -90px;
    top: -130px;
    border: 1px solid rgba(255, 255, 255, .18);
    border-radius: 50%;
}
.hero-kicker {
    font-size: .72rem;
    font-weight: 700;
    letter-spacing: .12em;
    text-transform: uppercase;
    opacity: .8;
    margin-bottom: .65rem;
}
.hero h1 {
    color: #FFFFFF;
    font-size: clamp(2.1rem, 3.4vw, 3.25rem);
    font-weight: 650;
    letter-spacing: -.035em;
    line-height: 1.05;
    margin: 0;
}
.hero-subtitle {
    color: rgba(255, 255, 255, .94);
    font-size: 1.13rem;
    line-height: 1.5;
    margin: .8rem 0 0;
    max-width: 920px;
}
.hero-capability {
    color: rgba(255, 255, 255, .72);
    font-size: .86rem;
    line-height: 1.5;
    margin-top: .5rem;
    max-width: 900px;
}
.hero-meta {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: .55rem;
    margin-top: 1.25rem;
}
.period-badge, .tech-badge {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    font-size: .75rem;
    font-weight: 650;
    line-height: 1;
}
.period-badge {
    background: #FFFFFF;
    color: var(--blue-dark);
    padding: .58rem .8rem;
}
.tech-badge {
    border: 1px solid rgba(255, 255, 255, .25);
    color: rgba(255, 255, 255, .88);
    padding: .5rem .68rem;
}
.page-hero {
    background: #FFFFFF;
    border-radius: 18px;
    padding: 1.25rem 1.65rem;
    margin: .55rem 0 1rem;
    box-shadow: 0 8px 28px rgba(27, 26, 25, .07);
    border-left: 4px solid var(--blue);
}
.page-hero .hero-kicker { color: var(--blue); opacity: 1; }
.page-hero h1 {
    color: var(--ink);
    font-size: clamp(1.8rem, 3vw, 2.5rem);
    font-weight: 650;
    letter-spacing: -.025em;
    margin: 0;
}
.page-hero p {
    color: var(--muted);
    font-size: .92rem;
    line-height: 1.55;
    margin: .4rem 0 0;
}
div[role="radiogroup"] {
    gap: .25rem;
    background: #FFFFFF;
    border-radius: 14px;
    padding: .36rem;
    box-shadow: 0 4px 16px rgba(27, 26, 25, .06);
}
div[role="radiogroup"] label {
    position: relative;
    padding: .42rem .75rem;
    border-radius: 9px;
    transition: background-color .15s ease, color .15s ease;
}
div[role="radiogroup"] label[data-baseweb="radio"] > div > div:first-child {
    position: absolute;
    width: 1px;
    height: 1px;
    opacity: 0;
    overflow: hidden;
}
div[role="radiogroup"] label:focus-within {
    outline: 2px solid var(--blue-dark);
    outline-offset: 2px;
}
div[role="radiogroup"] label:hover { background: var(--blue-soft); }
div[role="radiogroup"] label:has(input:checked) {
    background: var(--blue);
    color: #FFFFFF;
}
div[role="radiogroup"] label:has(input:checked) p { color: #FFFFFF; }
.section-heading { margin: 2rem 0 .85rem; }
.section-eyebrow {
    color: var(--blue);
    font-size: .7rem;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
    margin-bottom: .28rem;
}
.section-heading h2 {
    color: var(--ink);
    font-size: 1.42rem;
    font-weight: 650;
    letter-spacing: -.015em;
    margin: 0;
}
.section-heading p {
    color: var(--muted);
    font-size: .9rem;
    line-height: 1.5;
    margin: .28rem 0 0;
}
.kpi-card {
    position: relative;
    min-height: 132px;
    background: var(--surface);
    border-radius: 16px;
    padding: 1.15rem 1.25rem;
    box-shadow: 0 6px 22px rgba(27, 26, 25, .065);
    transition: transform .16s ease, box-shadow .16s ease;
}
.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 28px rgba(27, 26, 25, .1);
}
.kpi-card::before {
    content: "";
    position: absolute;
    left: 0;
    top: 1.15rem;
    bottom: 1.15rem;
    width: 3px;
    border-radius: 0 3px 3px 0;
    background: var(--blue);
}
.kpi-card.featured {
    min-height: 148px;
    background: linear-gradient(145deg, #FFFFFF 0%, #F2F8FD 100%);
}
.kpi-card.featured::before { width: 5px; }
.kpi-card.positive::before { background: var(--green); }
.kpi-card.negative::before { background: var(--red); }
.kpi-label {
    color: var(--muted);
    font-size: .72rem;
    font-weight: 700;
    letter-spacing: .07em;
    text-transform: uppercase;
}
.kpi-value {
    color: var(--ink);
    font-size: clamp(1.7rem, 2.6vw, 2.25rem);
    font-weight: 650;
    letter-spacing: -.025em;
    line-height: 1.15;
    margin-top: .62rem;
}
.kpi-card.featured .kpi-value {
    color: var(--blue-dark);
    font-size: clamp(2.15rem, 3.2vw, 2.85rem);
}
.kpi-card.positive .kpi-value { color: var(--green); }
.kpi-card.negative .kpi-value { color: var(--red); }
.kpi-context {
    color: var(--subtle);
    font-size: .75rem;
    line-height: 1.4;
    margin-top: .35rem;
}
.semantic-label {
    font-size: .7rem;
    font-weight: 650;
    margin-left: .25rem;
}
.briefing-shell {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 1.1rem;
    min-height: 396px;
    box-shadow: 0 6px 22px rgba(27, 26, 25, .065);
}
.briefing-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: .05rem .1rem .75rem;
}
.briefing-header h3 {
    color: var(--ink);
    font-size: 1rem;
    font-weight: 650;
    margin: 0;
}
.briefing-tag {
    color: var(--blue-dark);
    background: var(--blue-soft);
    border-radius: 999px;
    font-size: .66rem;
    font-weight: 700;
    letter-spacing: .04em;
    padding: .34rem .52rem;
    text-transform: uppercase;
}
.insight-item {
    background: #F9FAFB;
    border-radius: 11px;
    padding: .72rem .82rem;
    margin-top: .55rem;
}
.insight-title {
    color: var(--ink);
    font-weight: 650;
    font-size: .8rem;
    margin-bottom: .2rem;
}
.insight-body {
    color: var(--muted);
    font-size: .8rem;
    line-height: 1.45;
}
.source-note { color: var(--muted); font-size: .74rem; margin-top: .75rem; }
[data-testid="stPlotlyChart"] {
    background: var(--surface);
    border-radius: 16px;
    padding: .2rem .4rem;
    box-shadow: 0 6px 22px rgba(27, 26, 25, .06);
}
[data-testid="stDataFrame"] {
    border: 0;
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 6px 22px rgba(27, 26, 25, .055);
}
.stSelectbox label, .stMultiSelect label {
    color: var(--ink);
    font-weight: 600;
}
.stSelectbox, .stMultiSelect { margin-bottom: .1rem; }
.app-footer {
    border-top: 1px solid var(--line);
    margin-top: 2.5rem;
    padding: 1.4rem .1rem .5rem;
}
.footer-title {
    color: var(--ink);
    font-size: .82rem;
    font-weight: 650;
}
.footer-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-top: .75rem;
}
.footer-label {
    color: var(--subtle);
    font-size: .64rem;
    font-weight: 700;
    letter-spacing: .07em;
    text-transform: uppercase;
}
.footer-value {
    color: var(--muted);
    font-size: .73rem;
    line-height: 1.4;
    margin-top: .18rem;
}
@media (max-width: 900px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    .hero { padding: 1.8rem 1.5rem; }
    .footer-grid { grid-template-columns: repeat(2, 1fr); }
    .kpi-card { min-height: 118px; }
}
@media (max-width: 600px) {
    .hero h1 { font-size: 2rem; }
    .hero-subtitle { font-size: 1rem; }
    .footer-grid { grid-template-columns: 1fr; }
    div[role="radiogroup"] { flex-direction: column; align-items: stretch; }
}
</style>
"""


def section_heading(
    title: str,
    subtitle: str,
    eyebrow: str = "Analysis",
) -> None:
    """Render a consistent section heading."""
    st.markdown(
        '<div class="section-heading">'
        f'<div class="section-eyebrow">{escape(eyebrow)}</div>'
        f"<h2>{escape(title)}</h2><p>{escape(subtitle)}</p></div>",
        unsafe_allow_html=True,
    )


def hero(
    title: str,
    subtitle: str,
    period: str | None = None,
    primary: bool = False,
) -> None:
    """Render the product or page header."""
    if not primary:
        st.markdown(
            '<div class="page-hero">'
            '<div class="hero-kicker">Financial intelligence</div>'
            f"<h1>{escape(title)}</h1><p>{escape(subtitle)}</p></div>",
            unsafe_allow_html=True,
        )
        return

    badges = "".join(
        f'<span class="tech-badge">{technology}</span>'
        for technology in (
            "Python",
            "SQLite",
            "SQL Analytics",
            "Streamlit",
            "Plotly",
        )
    )
    st.markdown(
        '<div class="hero">'
        '<div class="hero-kicker">Validated financial intelligence platform</div>'
        f"<h1>{escape(title)}</h1>"
        f'<div class="hero-subtitle">{escape(subtitle)}</div>'
        '<div class="hero-capability">Built from Microsoft&#39;s public SEC '
        "filings using Python, SQLite, SQL analytics, and interactive "
        "business intelligence.</div>"
        '<div class="hero-meta">'
        '<span class="period-badge">Last available fiscal period · '
        f"{escape(period or 'Not available')}</span>{badges}</div></div>",
        unsafe_allow_html=True,
    )


def kpi_card(
    label: str,
    value: str,
    context: str,
    tone: str = "neutral",
    featured: bool = False,
) -> None:
    """Render an accessible KPI card."""
    classes = ["kpi-card", tone]
    if featured:
        classes.append("featured")
    semantic = {
        "positive": '<span class="semantic-label">▲ Positive</span>',
        "negative": '<span class="semantic-label">▼ Negative</span>',
    }.get(tone, "")
    st.markdown(
        f'<div class="{" ".join(classes)}">'
        f'<div class="kpi-label">{escape(label)}{semantic}</div>'
        f'<div class="kpi-value">{escape(value)}</div>'
        f'<div class="kpi-context">{escape(context)}</div></div>',
        unsafe_allow_html=True,
    )


def performance_tone(value: float) -> str:
    """Map signed performance to a semantic style without hiding the sign."""
    if pd.isna(value) or float(value) == 0:
        return "neutral"
    return "positive" if float(value) > 0 else "negative"


def render_deterministic_briefing(data: FinancialDatasets) -> None:
    """Render the existing deterministic fallback without an AI label."""
    insights = build_executive_insights(data.latest, data.quarterly_analytics)
    items = "".join(
        '<div class="insight-item">'
        f'<div class="insight-title">{escape(item.title)}</div>'
        f'<div class="insight-body">{escape(item.body)}</div></div>'
        for item in insights
    )
    st.markdown(
        '<div class="briefing-shell">'
        '<div class="briefing-header"><h3>Executive briefing</h3>'
        '<span class="briefing-tag">Data supported</span></div>'
        f"{items}</div>",
        unsafe_allow_html=True,
    )


def render_ai_briefing(briefing: ExecutiveBriefing) -> None:
    """Render a briefing that has already passed persistence revalidation."""
    category_labels = {
        "overall_performance": "Overall performance",
        "primary_drivers": "Primary drivers",
        "headwinds": "Headwinds",
        "profitability_context": "Profitability context",
        "attention": "What deserves attention",
        "investigate_next": "Investigate next",
    }
    classification_labels = {
        "reported": "Reported fact",
        "derived": "Derived metric",
        "management_explanation": "Management-attributed",
        "ai_interpretation": "AI interpretation",
    }
    items = "".join(
        '<div class="insight-item">'
        f'<div class="insight-title">{escape(category_labels[insight.category])}'
        f' · {escape(insight.title)}</div>'
        f'<div class="insight-body">{escape(insight.narrative)}</div>'
        '<div class="source-note">'
        f'{escape(classification_labels[insight.classification.value])} · '
        f'Sources: {escape(", ".join(insight.source_ids))}</div></div>'
        for insight in briefing.insights
    )
    sources = "".join(
        f"<li>{escape(source_id)}</li>" for source_id in briefing.source_ids
    )
    st.markdown(
        '<div class="briefing-shell">'
        '<div class="briefing-header">'
        '<h3>AI-Generated Executive Briefing</h3>'
        '<span class="briefing-tag">Validated</span></div>'
        f'<div class="insight-title">{escape(briefing.headline)}</div>'
        f'<div class="insight-body">{escape(briefing.executive_summary)}</div>'
        f"{items}"
        '<div class="source-note"><strong>Source transparency</strong>'
        f"<ul>{sources}</ul></div></div>",
        unsafe_allow_html=True,
    )


def app_footer() -> None:
    """Render lightweight source, engine, visualization, and purpose metadata."""
    items = (
        ("Data source", "Microsoft SEC Company Facts API"),
        ("Analytics engine", "SQLite + SQL Analytics Views"),
        ("Visualization", "Streamlit + Plotly"),
        (
            "Purpose",
            "Executive-ready intelligence from validated public financial data",
        ),
    )
    content = "".join(
        "<div>"
        f'<div class="footer-label">{escape(label)}</div>'
        f'<div class="footer-value">{escape(value)}</div></div>'
        for label, value in items
    )
    st.markdown(
        '<div class="app-footer">'
        '<div class="footer-title">Microsoft Financial Intelligence Platform</div>'
        f'<div class="footer-grid">{content}</div></div>',
        unsafe_allow_html=True,
    )


def financial_table(
    frame: pd.DataFrame,
    annual: bool = False,
) -> pd.DataFrame:
    """Create a presentation-only table without changing source values."""
    result = frame.copy()
    if annual:
        result = result[[
            "fiscal_year", "revenue", "revenue_yoy_growth_pct",
            "gross_profit", "operating_income", "net_income",
            "gross_margin_pct", "operating_margin_pct", "net_margin_pct",
        ]]
        result.columns = [
            "Fiscal year", "Revenue", "Revenue growth", "Gross profit",
            "Operating income", "Net income", "Gross margin",
            "Operating margin", "Net margin",
        ]
        percent_columns = [
            "Revenue growth", "Gross margin", "Operating margin", "Net margin"
        ]
    else:
        result = result[[
            "fiscal_year", "fiscal_period", "revenue", "gross_profit",
            "operating_income", "net_income",
        ]]
        result.columns = [
            "Fiscal year", "Quarter", "Revenue", "Gross profit",
            "Operating income", "Net income",
        ]
        percent_columns = []
    result["Fiscal year"] = (
        "FY" + result["Fiscal year"].astype(int).astype(str)
    )
    for column in (
        "Revenue", "Gross profit", "Operating income", "Net income"
    ):
        if column in result:
            result[column] = result[column].map(format_billions)
    for column in percent_columns:
        result[column] = result[column].map(format_percent)
    return result


def executive_overview(data: FinancialDatasets) -> None:
    """Render current performance and decision-ready context."""
    latest = data.latest.iloc[0]
    period = fiscal_label(
        latest["fiscal_year"], str(latest["fiscal_period"])
    )
    hero(
        "Microsoft Financial Intelligence Platform",
        "Transforming Microsoft's public SEC filings into executive-ready "
        "financial intelligence.",
        period,
        primary=True,
    )
    section_heading(
        "Executive snapshot",
        "The latest financial period, growth momentum, and profitability "
        "at a glance.",
        "Current performance",
    )
    primary_column, qoq_column, yoy_column = st.columns([1.42, 1, 1])
    with primary_column:
        kpi_card(
            "Revenue",
            format_billions(latest["revenue"]),
            f"{period} · Microsoft fiscal reporting",
            featured=True,
        )
    with qoq_column:
        qoq = latest["revenue_qoq_growth_pct"]
        kpi_card(
            "QoQ Revenue Growth",
            format_percent(qoq, True),
            "Compared with the prior quarter",
            tone=performance_tone(qoq),
        )
    with yoy_column:
        yoy = latest["revenue_yoy_growth_pct"]
        kpi_card(
            "YoY Revenue Growth",
            format_percent(yoy, True),
            "Compared with the same quarter last year",
            tone=performance_tone(yoy),
        )

    margin_columns = st.columns(3)
    for column, item in zip(
        margin_columns,
        (
            (
                "Gross Margin",
                format_percent(latest["gross_margin_pct"]),
                "Gross profit as a share of revenue",
            ),
            (
                "Operating Margin",
                format_percent(latest["operating_margin_pct"]),
                "Operating income as a share of revenue",
            ),
            (
                "Net Margin",
                format_percent(latest["net_margin_pct"]),
                "Net income as a share of revenue",
            ),
        ),
        strict=True,
    ):
        with column:
            kpi_card(*item)

    section_heading(
        "Revenue trajectory and executive briefing",
        "Recent revenue momentum paired with concise, data-supported context.",
        "Executive insights",
    )
    chart_column, insight_column = st.columns([1.9, 1])
    with chart_column:
        st.plotly_chart(
            revenue_trend(data.quarterly_analytics),
            width="stretch",
            config={"displayModeBar": False},
        )
    with insight_column:
        reporting_period = ReportingPeriod(
            fiscal_year=int(latest["fiscal_year"]),
            fiscal_period=str(latest["fiscal_period"]),
        )
        selection: BriefingSelection | None = None
        try:
            context = build_grounding_context(data, reporting_period)
            selection = select_briefing_for_display(context)
        except (BusinessDriverError, GroundingError, ValueError):
            selection = None
        if (
            selection is not None
            and selection.mode == "ai"
            and selection.briefing is not None
        ):
            render_ai_briefing(selection.briefing)
        else:
            render_deterministic_briefing(data)
    st.markdown(
        '<div class="source-note">Source: Microsoft SEC Company Facts '
        "filings. Q4 values may be derived by the validated data pipeline "
        "from full-year and nine-month observations.</div>",
        unsafe_allow_html=True,
    )


def quarterly_performance(data: FinancialDatasets) -> None:
    """Render focused quarterly metric and profitability exploration."""
    hero(
        "Quarterly Performance",
        "Compare Microsoft's core financial measures and profitability "
        "across fiscal quarters.",
    )
    years = sorted(
        data.quarterly_financials["fiscal_year"].astype(int).unique()
    )
    filter_column, metric_column = st.columns([1.2, 1])
    with filter_column:
        selected_years = st.multiselect(
            "Fiscal years", options=years, default=years[-3:],
            format_func=lambda year: f"FY{year}",
        )
    metric_options = {
        "Revenue": "revenue",
        "Gross Profit": "gross_profit",
        "Operating Income": "operating_income",
        "Net Income": "net_income",
    }
    with metric_column:
        metric_label = st.selectbox(
            "Financial metric", options=list(metric_options)
        )
    if not selected_years:
        st.info("Select at least one fiscal year to view quarterly performance.")
        return
    financials = data.quarterly_financials[
        data.quarterly_financials["fiscal_year"].isin(selected_years)
    ]
    analytics = data.quarterly_analytics[
        data.quarterly_analytics["fiscal_year"].isin(selected_years)
    ]
    section_heading(
        f"{metric_label} by quarter",
        "Use the metric selector to compare direction without mixing "
        "measures on different ranges.",
        "Quarterly performance",
    )
    st.plotly_chart(
        quarterly_metric_trend(
            financials, metric_options[metric_label], metric_label
        ),
        width="stretch",
        config={"displayModeBar": False},
    )
    section_heading(
        "Profitability trends",
        "Gross, operating, and net margins show how efficiently revenue "
        "translated into profit.",
        "Margin analysis",
    )
    st.plotly_chart(
        margin_trend(analytics),
        width="stretch",
        config={"displayModeBar": False},
    )
    section_heading(
        "Quarterly financial detail",
        "Exact values from the approved quarterly financial dataset.",
        "Supporting data",
    )
    st.dataframe(
        financial_table(financials),
        use_container_width=True,
        hide_index=True,
        height=280,
    )
    st.markdown(
        '<div class="source-note">Source: Microsoft SEC Company Facts '
        "filings.</div>",
        unsafe_allow_html=True,
    )


def historical_trends(data: FinancialDatasets) -> None:
    """Render finalized annual results and long-term trend context."""
    hero(
        "Historical Trends",
        "Separate short-term movement from Microsoft's broader annual "
        "growth and profitability trajectory.",
    )
    annual = data.annual
    latest = annual.iloc[-1]
    card_columns = st.columns(2)
    with card_columns[0]:
        kpi_card(
            "Annual Revenue", format_billions(latest["revenue"]),
            f"FY{int(latest['fiscal_year'])} · complete fiscal year",
            featured=True,
        )
    with card_columns[1]:
        annual_growth = latest["revenue_yoy_growth_pct"]
        kpi_card(
            "Annual Revenue Growth",
            format_percent(annual_growth, True),
            f"FY{int(latest['fiscal_year'])} vs prior fiscal year",
            tone=performance_tone(annual_growth),
        )
    section_heading(
        "Annual revenue and growth",
        "Revenue scale and the SQL-calculated year-over-year growth rate.",
        "Historical performance",
    )
    st.plotly_chart(
        annual_revenue_and_growth(annual), width="stretch",
        config={"displayModeBar": False},
    )
    section_heading(
        "Annual profitability",
        "Long-term gross, operating, and net margin direction.",
        "Margin analysis",
    )
    st.plotly_chart(
        annual_margin_trend(annual), width="stretch",
        config={"displayModeBar": False},
    )
    section_heading(
        "Annual financial summary",
        "Only complete fiscal years from FY2019 onward are included.",
        "Supporting data",
    )
    st.dataframe(
        financial_table(annual, annual=True),
        use_container_width=True,
        hide_index=True,
        height=320,
    )
    st.markdown(
        '<div class="source-note">Source: Microsoft SEC Company Facts '
        "filings. Finalized annual results require Q1-Q4 and non-null "
        "values for all four MVP metrics.</div>",
        unsafe_allow_html=True,
    )


def main() -> None:
    """Load approved data and route to the selected application page."""
    st.markdown(APP_CSS, unsafe_allow_html=True)
    try:
        data = load_financial_datasets()
    except DataValidationError as error:
        st.error(
            "The financial intelligence datasets are unavailable or invalid."
        )
        st.code(str(error), language=None)
        st.stop()
    page = st.radio(
        "Navigation",
        ("Executive Overview", "Quarterly Performance", "Historical Trends"),
        horizontal=True,
        label_visibility="collapsed",
    )
    if page == "Executive Overview":
        executive_overview(data)
    elif page == "Quarterly Performance":
        quarterly_performance(data)
    else:
        historical_trends(data)
    app_footer()


if __name__ == "__main__":
    main()
