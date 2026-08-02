"""Provider-independent schemas, grounding, and validation for AI briefings."""

from src.ai.business_drivers import (
    BusinessDriverError,
    derive_driver_ranking,
    load_business_driver_context,
    validate_business_driver_packet,
)
from src.ai.grounding import GroundingError, build_grounding_context
from src.ai.schemas import (
    AnnualFacts,
    ApprovedBusinessDriverPacket,
    BusinessDriverContext,
    BriefingFigureClaim,
    BriefingInsight,
    ExecutiveBriefing,
    FigureUnit,
    FactClassification,
    GroundedFigure,
    GroundingContext,
    MetricName,
    PeriodFacts,
    ReportingPeriod,
    SegmentResult,
    SourceReference,
)
from src.ai.validation import BriefingValidationError, validate_briefing

__all__ = [
    "AnnualFacts",
    "ApprovedBusinessDriverPacket",
    "BusinessDriverContext",
    "BusinessDriverError",
    "BriefingFigureClaim",
    "BriefingInsight",
    "BriefingValidationError",
    "ExecutiveBriefing",
    "FigureUnit",
    "FactClassification",
    "GroundedFigure",
    "GroundingContext",
    "GroundingError",
    "MetricName",
    "PeriodFacts",
    "ReportingPeriod",
    "SegmentResult",
    "SourceReference",
    "build_grounding_context",
    "derive_driver_ranking",
    "load_business_driver_context",
    "validate_briefing",
    "validate_business_driver_packet",
]
