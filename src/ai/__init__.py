"""Provider-independent schemas, grounding, and validation for AI briefings."""

from src.ai.business_drivers import (
    BusinessDriverError,
    derive_driver_ranking,
    load_business_driver_context,
    validate_business_driver_packet,
)
from src.ai.grounding import GroundingError, build_grounding_context
from src.ai.prompting import BriefingPrompt, build_briefing_prompt
from src.ai.providers import BriefingProvider
from src.ai.schemas import (
    AnnualFacts,
    ApprovedBusinessDriverPacket,
    BusinessDriverContext,
    BriefingFigureClaim,
    BriefingBusinessClaim,
    BriefingInsight,
    ExecutiveBriefing,
    FigureUnit,
    FactClassification,
    GroundedFigure,
    GroundedAnswer,
    GroundedAnswerClaim,
    GroundingContext,
    MetricName,
    PeriodFacts,
    ReportingPeriod,
    QAClassification,
    SegmentResult,
    SourceReference,
)
from src.ai.validation import BriefingValidationError, validate_briefing
from src.ai.qa import (
    GroundedQAError,
    QAProvider,
    QAPrompt,
    QATurn,
    build_qa_prompt,
    generate_grounded_answer,
    validate_grounded_answer,
)
from src.ai.selection import BriefingSelection, select_briefing_for_display
from src.ai.service import (
    BriefingGenerationError,
    generate_executive_briefing,
    validate_complete_briefing,
)
from src.ai.storage import (
    BriefingStorageError,
    briefing_path,
    load_saved_briefing,
    save_briefing,
)

__all__ = [
    "AnnualFacts",
    "ApprovedBusinessDriverPacket",
    "BusinessDriverContext",
    "BusinessDriverError",
    "BriefingFigureClaim",
    "BriefingBusinessClaim",
    "BriefingGenerationError",
    "BriefingPrompt",
    "BriefingProvider",
    "BriefingSelection",
    "BriefingStorageError",
    "BriefingInsight",
    "BriefingValidationError",
    "ExecutiveBriefing",
    "FigureUnit",
    "FactClassification",
    "GroundedFigure",
    "GroundedAnswer",
    "GroundedAnswerClaim",
    "GroundedQAError",
    "GroundingContext",
    "GroundingError",
    "MetricName",
    "PeriodFacts",
    "QAClassification",
    "QAProvider",
    "QAPrompt",
    "QATurn",
    "ReportingPeriod",
    "SegmentResult",
    "SourceReference",
    "build_grounding_context",
    "build_briefing_prompt",
    "build_qa_prompt",
    "briefing_path",
    "derive_driver_ranking",
    "load_business_driver_context",
    "load_saved_briefing",
    "generate_executive_briefing",
    "generate_grounded_answer",
    "save_briefing",
    "select_briefing_for_display",
    "validate_briefing",
    "validate_business_driver_packet",
    "validate_complete_briefing",
    "validate_grounded_answer",
]
