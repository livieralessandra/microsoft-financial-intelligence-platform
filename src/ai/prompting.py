"""Deterministic prompts for provider-independent executive briefings."""

from __future__ import annotations

from dataclasses import dataclass
import json

from src.ai.schemas import ExecutiveBriefing, GroundingContext


SYSTEM_INSTRUCTIONS = """You create source-grounded Microsoft executive briefings.
Use only the supplied approved context. Do not browse or use outside knowledge.
Do not invent, estimate, or recalculate figures. Copy approved values exactly.
Explicitly distinguish reported facts, derived metrics, management explanations,
and AI interpretations. Attribute management explanations to Microsoft management.
Every insight must list all supporting source IDs, and every structured numeric
claim must use the approved metric name, value, unit, classification, and source.
Do not provide investment advice, forecasts, price targets, or buy/sell language.
Return JSON only, matching the supplied ExecutiveBriefing JSON Schema exactly.
Include exactly one insight in each category: overall_performance, primary_drivers,
headwinds, profitability_context, attention, and investigate_next."""


@dataclass(frozen=True)
class BriefingPrompt:
    """Stable provider-neutral prompt components."""

    system_instructions: str
    approved_context_json: str
    output_schema_json: str


def build_briefing_prompt(context: GroundingContext) -> BriefingPrompt:
    """Serialize approved context and output contract deterministically."""
    context_json = json.dumps(
        context.model_dump(mode="json"),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    schema_json = json.dumps(
        ExecutiveBriefing.model_json_schema(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    return BriefingPrompt(
        system_instructions=SYSTEM_INSTRUCTIONS,
        approved_context_json=context_json,
        output_schema_json=schema_json,
    )
