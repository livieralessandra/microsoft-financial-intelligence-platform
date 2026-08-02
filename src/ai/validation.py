"""Validate structured executive briefings against approved grounding facts."""

from decimal import Decimal

from src.ai.schemas import (
    ExecutiveBriefing,
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
    if unit == FigureUnit.USD:
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

    undeclared_claim_sources = sorted(claim_sources - declared_sources)
    if undeclared_claim_sources:
        errors.append(
            "Figure claims use undeclared source IDs: "
            f"{', '.join(undeclared_claim_sources)}."
        )

    if errors:
        raise BriefingValidationError(" ".join(errors))
