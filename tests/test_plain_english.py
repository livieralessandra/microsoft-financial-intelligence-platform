"""Tests for deterministic plain-language financial comprehension."""

from src.ai.grounding import build_grounding_context
from src.plain_english import (
    METRIC_DEFINITIONS,
    build_plain_english_summary,
    select_visible_takeaways,
)


def test_all_required_metric_definitions_are_available() -> None:
    assert tuple(METRIC_DEFINITIONS) == (
        "Revenue",
        "Gross profit",
        "Operating income",
        "Net income",
        "QoQ growth",
        "YoY growth",
        "Gross margin",
        "Operating margin",
        "Net margin",
        "Segment contribution",
        "Headwind",
    )
    assert all(len(definition) <= 100 for definition in METRIC_DEFINITIONS.values())


def test_fy2026_q4_plain_english_summary_uses_approved_context(
    financial_datasets,
) -> None:
    context = build_grounding_context(financial_datasets, "FY2026-Q4")
    summary = build_plain_english_summary(context)
    text = " ".join((summary.headline, *summary.points))

    assert summary.headline == "Microsoft had a strong quarter."
    assert "prior quarter and the same quarter last year" in text
    assert "Intelligent Cloud was the largest" in text
    assert "Productivity and Business Processes was the second" in text
    assert "More Personal Computing was the segment headwind" in text
    assert "Azure was a major positive" in text
    assert "Windows OEM and Devices and Xbox content and services" in text
    assert "Profitability remained strong" in text
    assert "Microsoft management attributed" in text
    visible = select_visible_takeaways(summary)
    assert len(visible) == 4
    assert tuple(item.category for item in visible) == (
        "revenue_momentum",
        "largest_contributor",
        "principal_headwind",
        "profitability",
    )


def test_plain_english_omits_unavailable_business_drivers(
    financial_datasets,
) -> None:
    context = build_grounding_context(financial_datasets, "FY2026-Q3")
    summary = build_plain_english_summary(context)
    text = " ".join((summary.headline, *summary.points))

    assert "Revenue increased" in text
    assert "Profitability remained strong" in text
    assert "Intelligent Cloud" not in text
    assert "Azure" not in text
    assert "management attributed" not in text
    visible = select_visible_takeaways(summary)
    assert tuple(item.category for item in visible) == (
        "revenue_momentum",
        "profitability",
    )
