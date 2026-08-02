"""Generate and approve executive briefings through an injected provider."""

from __future__ import annotations

from pydantic import ValidationError

from src.ai.prompting import build_briefing_prompt
from src.ai.providers import BriefingProvider
from src.ai.schemas import ExecutiveBriefing, GroundingContext, ReportingPeriod
from src.ai.validation import BriefingValidationError, validate_briefing


REQUIRED_BRIEFING_CATEGORIES = frozenset(
    {
        "overall_performance",
        "primary_drivers",
        "headwinds",
        "profitability_context",
        "attention",
        "investigate_next",
    }
)


class BriefingGenerationError(RuntimeError):
    """Raised when provider output cannot become an approved briefing."""


def validate_complete_briefing(
    briefing: ExecutiveBriefing,
    context: GroundingContext,
) -> None:
    """Enforce the complete production contract in addition to schema validity."""
    drivers = context.business_drivers
    if drivers is None or drivers.availability != "available":
        raise BriefingValidationError(
            "Approved business-driver context is unavailable."
        )
    categories = [insight.category for insight in briefing.insights]
    if set(categories) != REQUIRED_BRIEFING_CATEGORIES or len(categories) != len(
        REQUIRED_BRIEFING_CATEGORIES
    ):
        raise BriefingValidationError(
            "Briefing must contain each required executive category exactly once."
        )
    if any(not insight.source_ids for insight in briefing.insights):
        raise BriefingValidationError("Every briefing insight requires source IDs.")
    validate_briefing(briefing, context)


def generate_executive_briefing(
    reporting_period: ReportingPeriod,
    context: GroundingContext,
    provider: BriefingProvider,
) -> ExecutiveBriefing:
    """Return provider output only after schema and grounding approval."""
    if reporting_period != context.requested_period:
        raise BriefingGenerationError(
            "Requested period does not match the grounding context."
        )
    try:
        try:
            response = provider.generate(build_briefing_prompt(context))
        except Exception as error:
            raise BriefingGenerationError("The briefing provider failed.") from error
        if not isinstance(response, str):
            raise TypeError("Provider response must be JSON text.")
        briefing = ExecutiveBriefing.model_validate_json(response)
        if briefing.reporting_period != reporting_period:
            raise BriefingValidationError(
                "Provider response period does not match the requested period."
            )
        validate_complete_briefing(briefing, context)
    except (BriefingValidationError, TypeError, ValidationError, ValueError) as error:
        raise BriefingGenerationError(
            "Provider output failed briefing approval."
        ) from error
    return briefing
