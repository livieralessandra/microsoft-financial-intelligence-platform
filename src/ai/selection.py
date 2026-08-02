"""Streamlit-neutral selection between approved AI and deterministic fallback."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.ai.schemas import ExecutiveBriefing, GroundingContext
from src.ai.storage import (
    DEFAULT_BRIEFING_DIRECTORY,
    BriefingStorageError,
    load_saved_briefing,
)


@dataclass(frozen=True)
class BriefingSelection:
    """Safe presentation decision with no technical error disclosure."""

    mode: Literal["ai", "deterministic"]
    briefing: ExecutiveBriefing | None
    status: str


def select_briefing_for_display(
    context: GroundingContext,
    directory: Path = DEFAULT_BRIEFING_DIRECTORY,
) -> BriefingSelection:
    """Select AI only when drivers and saved output both revalidate."""
    drivers = context.business_drivers
    if drivers is None or drivers.availability != "available":
        return BriefingSelection(
            mode="deterministic",
            briefing=None,
            status="Approved business-driver context is not available.",
        )
    try:
        briefing = load_saved_briefing(
            context.requested_period,
            context,
            directory,
        )
    except BriefingStorageError:
        return BriefingSelection(
            mode="deterministic",
            briefing=None,
            status="A validated AI briefing is not available.",
        )
    return BriefingSelection(
        mode="ai",
        briefing=briefing,
        status="Validated against approved financial and business-driver sources.",
    )
