"""Atomic persistence and revalidation for approved executive briefings."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile

from pydantic import ValidationError

from src.ai.schemas import ExecutiveBriefing, GroundingContext, ReportingPeriod
from src.ai.service import validate_complete_briefing
from src.ai.validation import BriefingValidationError


DEFAULT_BRIEFING_DIRECTORY = (
    Path(__file__).resolve().parents[2] / "data" / "generated" / "briefings"
)


class BriefingStorageError(RuntimeError):
    """Raised when a saved briefing is absent, invalid, stale, or unsupported."""


def briefing_path(
    reporting_period: ReportingPeriod,
    directory: Path = DEFAULT_BRIEFING_DIRECTORY,
) -> Path:
    """Return the canonical path for any fiscal quarter."""
    return directory / f"{reporting_period.identifier}.json"


def save_briefing(
    briefing: ExecutiveBriefing,
    context: GroundingContext,
    directory: Path = DEFAULT_BRIEFING_DIRECTORY,
) -> Path:
    """Validate first, then atomically replace the period briefing."""
    try:
        validate_complete_briefing(briefing, context)
    except BriefingValidationError as error:
        raise BriefingStorageError("Refusing to save an invalid briefing.") from error
    destination = briefing_path(briefing.reporting_period, directory)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(briefing.model_dump_json(indent=2))
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        temporary_path.replace(destination)
    except OSError as error:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise BriefingStorageError("Could not persist the approved briefing.") from error
    return destination


def load_saved_briefing(
    reporting_period: ReportingPeriod,
    context: GroundingContext,
    directory: Path = DEFAULT_BRIEFING_DIRECTORY,
) -> ExecutiveBriefing:
    """Load and reapprove saved JSON against the current grounding context."""
    path = briefing_path(reporting_period, directory)
    if not path.is_file():
        raise BriefingStorageError("No saved briefing exists for this period.")
    try:
        briefing = ExecutiveBriefing.model_validate_json(
            path.read_text(encoding="utf-8")
        )
        if briefing.reporting_period != reporting_period:
            raise BriefingValidationError("Saved briefing period is stale.")
        validate_complete_briefing(briefing, context)
    except (OSError, ValidationError, ValueError, BriefingValidationError) as error:
        raise BriefingStorageError(
            "Saved briefing is malformed, stale, or unsupported."
        ) from error
    return briefing
