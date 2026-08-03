"""Deterministic, plain-language explanations from approved grounding data."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.ai.schemas import GroundingContext, MetricName


METRIC_DEFINITIONS = {
    "Revenue": "The total money generated from sales before expenses.",
    "Gross profit": "Revenue left after the direct costs of delivering products and services.",
    "Operating income": "Profit from the core business after operating expenses.",
    "Net income": "Profit remaining after all expenses, interest, and taxes.",
    "QoQ growth": "How a result changed compared with the immediately preceding quarter.",
    "YoY growth": "How a result changed compared with the same quarter one year earlier.",
    "Gross margin": "The share of revenue left after direct delivery costs.",
    "Operating margin": "The share of revenue left after core operating expenses.",
    "Net margin": "How much profit the company kept from every dollar of revenue.",
    "Segment contribution": "How much one business segment added to or reduced the company’s total change.",
    "Headwind": "A business area or condition that reduced growth or profitability.",
}


@dataclass(frozen=True)
class PlainEnglishTakeaway:
    """One supported conclusion with a presentation-only semantic category."""

    category: str
    text: str


@dataclass(frozen=True)
class PlainEnglishSummary:
    """Display-ready deterministic conclusions for one approved period."""

    headline: str
    takeaways: tuple[PlainEnglishTakeaway, ...]
    source_ids: tuple[str, ...]

    @property
    def points(self) -> tuple[str, ...]:
        """Preserve the complete ordered summary as plain strings."""
        return tuple(takeaway.text for takeaway in self.takeaways)


VISIBLE_TAKEAWAY_PRIORITY = (
    "revenue_momentum",
    "largest_contributor",
    "principal_headwind",
    "profitability",
    "management_context",
)


def select_visible_takeaways(
    summary: PlainEnglishSummary,
    limit: int = 4,
) -> tuple[PlainEnglishTakeaway, ...]:
    """Select a compact set without discarding the complete summary."""
    selected: list[PlainEnglishTakeaway] = []
    for category in VISIBLE_TAKEAWAY_PRIORITY:
        item = next(
            (
                takeaway
                for takeaway in summary.takeaways
                if takeaway.category == category
            ),
            None,
        )
        if item is not None:
            selected.append(item)
        if len(selected) == limit:
            break
    return tuple(selected)


def _figure(context: GroundingContext, metric: MetricName) -> Decimal | None:
    return next(
        (
            figure.value
            for figure in context.current_period.figures
            if figure.metric == metric
        ),
        None,
    )


def build_plain_english_summary(context: GroundingContext) -> PlainEnglishSummary:
    """Translate only supported financial and driver facts into plain language."""
    qoq = _figure(context, MetricName.REVENUE_QOQ_GROWTH_PCT)
    yoy = _figure(context, MetricName.REVENUE_YOY_GROWTH_PCT)
    net_margin = _figure(context, MetricName.NET_MARGIN_PCT)
    takeaways: list[PlainEnglishTakeaway] = []

    def add(category: str, text: str) -> None:
        takeaways.append(PlainEnglishTakeaway(category=category, text=text))

    if qoq is not None and yoy is not None and qoq > 0 and yoy > 0:
        headline = "Microsoft had a strong quarter."
        add(
            "revenue_momentum",
            "Revenue increased compared with both the prior quarter and the same quarter last year."
        )
    elif (qoq is not None and qoq > 0) or (yoy is not None and yoy > 0):
        headline = "Microsoft reported positive revenue momentum."
        comparison = "prior quarter" if qoq is not None and qoq > 0 else "same quarter last year"
        add(
            "revenue_momentum",
            f"Revenue increased compared with the {comparison}.",
        )
    else:
        headline = "Microsoft’s latest quarter requires a closer look."
        add(
            "revenue_momentum",
            "Approved growth measures do not show broad positive revenue momentum.",
        )

    drivers = context.business_drivers
    driver_sources: set[str] = set()
    if (
        drivers is not None
        and drivers.availability == "available"
        and drivers.packet is not None
        and drivers.derived_ranking is not None
    ):
        ranking = drivers.derived_ranking
        positives = ranking.positive_contributors
        if positives:
            add(
                "largest_contributor",
                f"{positives[0]} was the largest positive segment contributor.",
            )
        if len(positives) > 1:
            add(
                "secondary_contributor",
                f"{positives[1]} was the second positive contributor.",
            )
        if ranking.negative_contributors:
            add(
                "principal_headwind",
                f"{ranking.negative_contributors[0]} was the segment headwind.",
            )

        indicators = {item.metric: item for item in drivers.packet.product_indicators}
        azure = indicators.get("azure_cloud_services_growth_pct")
        if azure is not None and azure.value > 0:
            add("positive_signal", "Azure was a major positive product signal.")
        negative_labels = [
            indicators[metric].label
            for metric in (
                "windows_oem_devices_growth_pct",
                "xbox_content_services_growth_pct",
            )
            if metric in indicators and indicators[metric].value < 0
        ]
        if negative_labels:
            names = [label.split(" growth")[0] for label in negative_labels]
            add(
                "negative_signal",
                f"{' and '.join(names)} were negative product signals.",
            )

        explanations = {
            item.explanation_id: item
            for item in drivers.packet.management_explanations
        }
        pressure = explanations.get("cloud_margin_pressure")
        if pressure is not None:
            add(
                "management_context",
                "Microsoft management attributed some gross-margin pressure to Azure mix, AI infrastructure investment, and product usage."
            )
        driver_sources.update(source.source_id for source in drivers.packet.sources)

    if net_margin is not None and net_margin >= Decimal("20"):
        add(
            "profitability",
            "Profitability remained strong, with a healthy share of revenue retained as profit.",
        )

    sources = {source.source_id for source in context.sources}
    sources.update(driver_sources)
    return PlainEnglishSummary(
        headline=headline,
        takeaways=tuple(takeaways),
        source_ids=tuple(sorted(sources)),
    )
