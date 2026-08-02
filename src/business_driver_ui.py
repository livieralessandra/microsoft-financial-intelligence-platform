"""Deterministic presentation model for approved business-driver context."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.ai.schemas import (
    BusinessDriverContext,
    FigureUnit,
    ReportedBusinessFact,
)


PRIORITY_SIGNAL_METRICS = (
    "azure_cloud_services_growth_pct",
    "microsoft_cloud_revenue_growth_pct",
    "commercial_rpo_growth_pct",
    "m365_commercial_cloud_reported_growth_pct",
    "m365_consumer_cloud_growth_pct",
    "linkedin_revenue_growth_pct",
    "search_advertising_ex_tac_growth_pct",
    "windows_oem_devices_growth_pct",
    "xbox_content_services_growth_pct",
    "m365_copilot_paid_seats",
)

PRIORITY_EXPLANATION_IDS = (
    "azure_capacity_constraint",
    "azure_efficiency_capacity",
    "cloud_margin_pressure",
    "windows_oem_weakness",
    "xbox_comparison",
    "linkedin_marketing_solutions",
)


@dataclass(frozen=True)
class ContributorPresentation:
    segment: str
    revenue_change: str
    contribution: str
    direction: str
    classification: str = "DERIVED"


@dataclass(frozen=True)
class SignalPresentation:
    label: str
    value: str
    tone: str
    classification: str = "REPORTED"


@dataclass(frozen=True)
class ExplanationPresentation:
    statement: str
    attribution: str
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class SourcePresentation:
    title: str
    source_id: str
    url: str


@dataclass(frozen=True)
class BusinessDriverPresentation:
    positive_contributors: tuple[ContributorPresentation, ...]
    headwinds: tuple[ContributorPresentation, ...]
    signals: tuple[SignalPresentation, ...]
    explanations: tuple[ExplanationPresentation, ...]
    sources: tuple[SourcePresentation, ...]


def _trim_decimal(value: Decimal) -> str:
    display = format(value, "f")
    return display.rstrip("0").rstrip(".") if "." in display else display


def _signed_percent(value: Decimal) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{_trim_decimal(value)}%"


def _signed_billions(value: Decimal) -> str:
    billions = value / Decimal("1000000000")
    sign = "+" if billions > 0 else "-" if billions < 0 else ""
    return f"{sign}${abs(billions):.3f}B"


def _count_value(value: Decimal, qualifier: str) -> str:
    if value >= Decimal("1000000") and value % Decimal("1000000") == 0:
        display = f"{_trim_decimal(value / Decimal('1000000'))} million"
    else:
        display = f"{value:,.0f}"
    return f"More than {display}" if qualifier == "more_than" else display


def _signal_value(fact: ReportedBusinessFact) -> tuple[str, str]:
    if fact.unit == FigureUnit.PERCENT:
        value = _signed_percent(fact.value)
        tone = (
            "positive"
            if fact.value > 0
            else "negative"
            if fact.value < 0
            else "neutral"
        )
        return value, tone
    if fact.unit == FigureUnit.COUNT:
        return _count_value(fact.value, fact.qualifier), "neutral"
    if fact.unit == FigureUnit.USD:
        return _signed_billions(fact.value), "neutral"
    return _trim_decimal(fact.value), "neutral"


def build_business_driver_presentation(
    context: BusinessDriverContext | None,
) -> BusinessDriverPresentation | None:
    """Build display-ready content only from an available approved packet."""
    if (
        context is None
        or context.availability != "available"
        or context.packet is None
        or context.derived_ranking is None
    ):
        return None

    contributions = {
        item.segment: item for item in context.derived_ranking.contributions
    }

    def contributor(segment: str, direction: str) -> ContributorPresentation:
        item = contributions[segment]
        return ContributorPresentation(
            segment=item.segment,
            revenue_change=_signed_billions(item.absolute_revenue_change),
            contribution=f"{item.contribution_pct:.2f}%",
            direction=direction,
        )

    positive = tuple(
        contributor(segment, "positive")
        for segment in context.derived_ranking.positive_contributors
    )
    headwinds = tuple(
        contributor(segment, "negative")
        for segment in context.derived_ranking.negative_contributors
    )

    indicators = {fact.metric: fact for fact in context.packet.product_indicators}
    signals = []
    for metric in PRIORITY_SIGNAL_METRICS:
        fact = indicators.get(metric)
        if fact is None:
            continue
        value, tone = _signal_value(fact)
        signals.append(
            SignalPresentation(
                label=fact.label,
                value=value,
                tone=tone,
            )
        )

    explanations = {
        item.explanation_id: item
        for item in context.packet.management_explanations
    }
    selected_explanations = tuple(
        ExplanationPresentation(
            statement=explanations[explanation_id].statement,
            attribution=explanations[explanation_id].attribution,
            source_ids=explanations[explanation_id].source_ids,
        )
        for explanation_id in PRIORITY_EXPLANATION_IDS
        if explanation_id in explanations
    )
    sources = tuple(
        SourcePresentation(
            title=source.title,
            source_id=source.source_id,
            url=source.url,
        )
        for source in context.packet.sources
    )
    return BusinessDriverPresentation(
        positive_contributors=positive,
        headwinds=headwinds,
        signals=tuple(signals),
        explanations=selected_explanations,
        sources=sources,
    )
