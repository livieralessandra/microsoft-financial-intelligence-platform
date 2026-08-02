"""Provider-independent schemas, grounding, and validation for AI briefings."""

from src.ai.grounding import GroundingError, build_grounding_context
from src.ai.schemas import (
    AnnualFacts,
    BriefingFigureClaim,
    BriefingInsight,
    ExecutiveBriefing,
    FigureUnit,
    GroundedFigure,
    GroundingContext,
    MetricName,
    PeriodFacts,
    ReportingPeriod,
    SourceReference,
)
from src.ai.validation import BriefingValidationError, validate_briefing

__all__ = [
    "AnnualFacts",
    "BriefingFigureClaim",
    "BriefingInsight",
    "BriefingValidationError",
    "ExecutiveBriefing",
    "FigureUnit",
    "GroundedFigure",
    "GroundingContext",
    "GroundingError",
    "MetricName",
    "PeriodFacts",
    "ReportingPeriod",
    "SourceReference",
    "build_grounding_context",
    "validate_briefing",
]
