"""Load and validate approved business-driver packets without network access."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from pydantic import ValidationError

from src.ai.schemas import (
    ApprovedBusinessDriverPacket,
    BusinessDriverContext,
    DerivedDriverRanking,
    DerivedSegmentContribution,
    FactClassification,
    FigureUnit,
    ReportingPeriod,
)


DEFAULT_PACKET_DIRECTORY = (
    Path(__file__).resolve().parents[2] / "data" / "approved" / "business_drivers"
)
CONTRIBUTION_QUANTUM = Decimal("0.01")


class BusinessDriverError(RuntimeError):
    """Raised when an approved packet is present but invalid."""


def validate_business_driver_packet(packet: ApprovedBusinessDriverPacket) -> None:
    source_ids = [source.source_id for source in packet.sources]
    if len(source_ids) != len(set(source_ids)):
        raise BusinessDriverError("Approved packet contains duplicate source IDs.")
    approved_sources = set(source_ids)
    if any(source.reporting_period != packet.reporting_period for source in packet.sources):
        raise BusinessDriverError("Official source reporting period does not match packet.")

    records = (
        *packet.reported_facts,
        *packet.segment_results,
        *packet.product_indicators,
        *packet.derived_metrics,
        *packet.management_explanations,
    )
    for record in records:
        unknown = set(record.source_ids) - approved_sources
        if unknown:
            raise BusinessDriverError(
                f"Unsupported source IDs for {getattr(record, 'metric', type(record).__name__)}: "
                f"{', '.join(sorted(unknown))}."
            )

    if packet.derived_metrics:
        raise BusinessDriverError(
            "Approved packet must not store computed segment metrics; derive them at load time."
        )

    metrics = {fact.metric: fact for fact in packet.reported_facts}
    required = {"revenue", "prior_year_quarter_revenue", "revenue_increase"}
    missing = required - metrics.keys()
    if missing:
        raise BusinessDriverError(
            f"Approved packet is missing required company facts: {', '.join(sorted(missing))}."
        )
    current_total = sum(segment.current_revenue for segment in packet.segment_results)
    prior_total = sum(segment.prior_year_revenue for segment in packet.segment_results)
    change_total = sum(
        segment.current_revenue - segment.prior_year_revenue
        for segment in packet.segment_results
    )
    if current_total != metrics["revenue"].value:
        raise BusinessDriverError("Segment current revenue does not reconcile to company revenue.")
    if prior_total != metrics["prior_year_quarter_revenue"].value:
        raise BusinessDriverError(
            "Segment prior-year revenue does not reconcile to company prior-year revenue."
        )
    if change_total != metrics["revenue_increase"].value:
        raise BusinessDriverError("Segment revenue changes do not reconcile exactly.")


def derive_driver_ranking(
    packet: ApprovedBusinessDriverPacket,
) -> DerivedDriverRanking:
    """Compute segment changes, contribution shares, and deterministic rankings."""
    validate_business_driver_packet(packet)
    total_change = next(
        fact.value for fact in packet.reported_facts if fact.metric == "revenue_increase"
    )
    if total_change == 0:
        raise BusinessDriverError("Cannot derive contribution shares from zero revenue change.")
    contributions = tuple(
        DerivedSegmentContribution(
            segment=segment.segment,
            absolute_revenue_change=(
                segment.current_revenue - segment.prior_year_revenue
            ),
            contribution_pct=(
                (segment.current_revenue - segment.prior_year_revenue)
                * Decimal("100")
                / total_change
            ).quantize(CONTRIBUTION_QUANTUM, rounding=ROUND_HALF_UP),
            classification=FactClassification.DERIVED,
            source_ids=segment.source_ids,
        )
        for segment in packet.segment_results
    )
    positive = tuple(
        item.segment
        for item in sorted(
            (item for item in contributions if item.absolute_revenue_change > 0),
            key=lambda item: (-item.absolute_revenue_change, item.segment),
        )
    )
    negative = tuple(
        item.segment
        for item in sorted(
            (item for item in contributions if item.absolute_revenue_change < 0),
            key=lambda item: (item.absolute_revenue_change, item.segment),
        )
    )
    return DerivedDriverRanking(
        reporting_period=packet.reporting_period,
        total_revenue_change=total_change,
        contributions=contributions,
        positive_contributors=positive,
        negative_contributors=negative,
        classification=FactClassification.DERIVED,
    )


def load_business_driver_context(
    reporting_period: ReportingPeriod | str,
    packet_directory: Path = DEFAULT_PACKET_DIRECTORY,
) -> BusinessDriverContext:
    """Load one period packet, returning an explicit unavailable state if absent."""
    period = (
        ReportingPeriod.parse(reporting_period)
        if isinstance(reporting_period, str)
        else reporting_period
    )
    if not isinstance(period, ReportingPeriod):
        raise TypeError("reporting_period must be a ReportingPeriod or canonical string.")
    path = packet_directory / f"{period.identifier}.json"
    if not path.is_file():
        return BusinessDriverContext(
            reporting_period=period,
            availability="unavailable",
            unavailable_reason=(
                f"No approved business-driver packet exists for {period.identifier}."
            ),
        )
    try:
        packet = ApprovedBusinessDriverPacket.model_validate_json(path.read_text())
    except (OSError, ValidationError, ValueError) as error:
        raise BusinessDriverError(f"Invalid approved packet {path}: {error}") from error
    if packet.reporting_period != period:
        raise BusinessDriverError(
            f"Packet period {packet.reporting_period.identifier} does not match {period.identifier}."
        )
    ranking = derive_driver_ranking(packet)
    return BusinessDriverContext(
        reporting_period=period,
        availability="available",
        packet=packet,
        derived_ranking=ranking,
    )
