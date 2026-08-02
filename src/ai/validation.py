"""Validate structured executive briefings against approved grounding facts."""

from decimal import Decimal

from src.ai.schemas import (
    BriefingBusinessClaim,
    ExecutiveBriefing,
    FactClassification,
    FigureUnit,
    GroundedFigure,
    GroundingContext,
)


PERCENTAGE_TOLERANCE = Decimal("0.01")


class BriefingValidationError(RuntimeError):
    """Raised when a briefing contains an unsupported structured claim."""


def _grounded_figures(
    context: GroundingContext,
) -> dict[tuple[str, str], GroundedFigure]:
    result: dict[tuple[str, str], GroundedFigure] = {}
    facts = (
        context.current_period,
        context.previous_quarter,
        context.prior_year_quarter,
        context.annual_context,
    )
    for fact_group in facts:
        if fact_group is None:
            continue
        for figure in fact_group.figures:
            result[(figure.source_id, figure.metric.value)] = figure
    return result


def _values_match(
    claimed: Decimal,
    grounded: Decimal,
    unit: FigureUnit,
) -> bool:
    """Match USD exactly and percentages within 0.01 percentage points."""
    if unit in {FigureUnit.USD, FigureUnit.COUNT}:
        return claimed == grounded
    return abs(claimed - grounded) <= PERCENTAGE_TOLERANCE


def validate_briefing(
    briefing: ExecutiveBriefing,
    context: GroundingContext,
) -> None:
    """Validate all structured claims and source IDs in a briefing."""
    errors: list[str] = []
    if briefing.reporting_period != context.requested_period:
        errors.append(
            "Briefing reporting period does not match grounding context."
        )

    allowed_sources = {source.source_id for source in context.sources}
    driver_context = context.business_drivers
    if driver_context is not None and driver_context.availability == "available":
        if driver_context.packet is not None:
            allowed_sources.update(
                source.source_id for source in driver_context.packet.sources
            )
    declared_sources = set(briefing.source_ids)
    unsupported_sources = sorted(declared_sources - allowed_sources)
    if unsupported_sources:
        errors.append(
            "Unsupported briefing source IDs: "
            f"{', '.join(unsupported_sources)}."
        )

    grounded = _grounded_figures(context)
    claim_sources: set[str] = set()
    seen_claims: set[tuple[str, str]] = set()
    for insight in briefing.insights:
        unsupported_insight_sources = sorted(
            set(insight.source_ids) - allowed_sources
        )
        if unsupported_insight_sources:
            errors.append(
                "Unsupported insight source IDs: "
                f"{', '.join(unsupported_insight_sources)}."
            )
        claim_sources.update(insight.source_ids)
        for claim in insight.figure_claims:
            key = (claim.source_id, claim.metric.value)
            claim_sources.add(claim.source_id)
            if key in seen_claims:
                errors.append(
                    "Duplicate figure claim: "
                    f"{claim.source_id}/{claim.metric.value}."
                )
                continue
            seen_claims.add(key)
            grounded_figure = grounded.get(key)
            if grounded_figure is None:
                errors.append(
                    "Unsupported figure claim: "
                    f"{claim.source_id}/{claim.metric.value}."
                )
                continue
            if claim.unit != grounded_figure.unit:
                errors.append(
                    f"Incorrect unit for {claim.metric.value} from "
                    f"{claim.source_id}."
                )
                continue
            if not _values_match(
                claim.value,
                grounded_figure.value,
                claim.unit,
            ):
                errors.append(
                    f"Figure mismatch for {claim.metric.value} from "
                    f"{claim.source_id}: claimed {claim.value}, "
                    f"grounded {grounded_figure.value}."
                )
        for claim in insight.business_claims:
            claim_sources.update(claim.source_ids)
            error = _validate_business_claim(claim, context)
            if error is not None:
                errors.append(error)
        if insight.management_explanation_ids:
            if (
                driver_context is None
                or driver_context.availability != "available"
                or driver_context.packet is None
            ):
                errors.append(
                    "Management explanations require approved business-driver context."
                )
            else:
                approved_explanations = {
                    item.explanation_id
                    for item in driver_context.packet.management_explanations
                }
                unknown = sorted(
                    set(insight.management_explanation_ids)
                    - approved_explanations
                )
                if unknown:
                    errors.append(
                        "Unsupported management explanations: "
                        f"{', '.join(unknown)}."
                    )

    undeclared_claim_sources = sorted(claim_sources - declared_sources)
    if undeclared_claim_sources:
        errors.append(
            "Figure claims use undeclared source IDs: "
            f"{', '.join(undeclared_claim_sources)}."
        )

    if errors:
        raise BriefingValidationError(" ".join(errors))


def _segment_metric_name(segment: str, metric: str) -> str:
    slug = "_".join(segment.lower().replace("&", "and").split())
    return f"segment.{slug}.{metric}"


def _approved_business_claims(
    context: GroundingContext,
) -> dict[str, tuple[Decimal, FigureUnit, FactClassification, set[str]]]:
    drivers = context.business_drivers
    if (
        drivers is None
        or drivers.availability != "available"
        or drivers.packet is None
        or drivers.derived_ranking is None
    ):
        return {}
    approved = {
        fact.metric: (
            fact.value,
            fact.unit,
            FactClassification.REPORTED,
            set(fact.source_ids),
        )
        for fact in (*drivers.packet.reported_facts, *drivers.packet.product_indicators)
    }
    for segment in drivers.packet.segment_results:
        for metric, value, unit in (
            ("current_revenue", segment.current_revenue, FigureUnit.USD),
            ("prior_year_revenue", segment.prior_year_revenue, FigureUnit.USD),
            ("reported_growth_pct", segment.reported_growth_pct, FigureUnit.PERCENT),
        ):
            approved[_segment_metric_name(segment.segment, metric)] = (
                value,
                unit,
                FactClassification.REPORTED,
                set(segment.source_ids),
            )
    for contribution in drivers.derived_ranking.contributions:
        for metric, value, unit in (
            ("absolute_revenue_change", contribution.absolute_revenue_change, FigureUnit.USD),
            ("contribution_pct", contribution.contribution_pct, FigureUnit.PERCENT),
        ):
            approved[_segment_metric_name(contribution.segment, metric)] = (
                value,
                unit,
                FactClassification.DERIVED,
                set(contribution.source_ids),
            )
    return approved


def _validate_business_claim(
    claim: BriefingBusinessClaim,
    context: GroundingContext,
) -> str | None:
    approved = _approved_business_claims(context).get(claim.metric)
    if approved is None:
        return f"Unsupported business-driver claim: {claim.metric}."
    value, unit, classification, source_ids = approved
    if claim.classification != classification:
        return f"Incorrect classification for business-driver claim {claim.metric}."
    if claim.unit != unit:
        return f"Incorrect unit for business-driver claim {claim.metric}."
    if set(claim.source_ids) != source_ids:
        return f"Incorrect source IDs for business-driver claim {claim.metric}."
    if not _values_match(claim.value, value, unit):
        return f"Figure mismatch for business-driver claim {claim.metric}."
    return None
