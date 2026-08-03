"""Deterministic Q&A routing and safe optional grounded-provider orchestration."""

from __future__ import annotations

from dataclasses import dataclass
import os
import re
from typing import Callable, Mapping

from src.ai.qa import (
    GroundedQAError,
    MAX_QUESTION_LENGTH,
    QAProvider,
    QATurn,
    generate_grounded_answer,
)
from src.ai.schemas import GroundedAnswer, GroundingContext
from src.plain_english import METRIC_DEFINITIONS, build_plain_english_summary


MAX_AZURE_QUESTIONS_PER_SESSION = 5
UNSUPPORTED_MESSAGE = (
    "Live grounded Q&A is not enabled yet. I can currently explain the displayed "
    "metrics, performance, approved drivers, headwinds, and areas to investigate."
)
SAFE_FAILURE_MESSAGE = (
    "A grounded answer could not be approved. Please try a displayed example question."
)


@dataclass(frozen=True)
class PlatformAnswer:
    """Safe display result from deterministic or validated grounded Q&A."""

    mode: str
    answer: str
    source_ids: tuple[str, ...] = ()
    grounded_answer: GroundedAnswer | None = None
    azure_request_made: bool = False


def azure_qa_enabled(environment: Mapping[str, str] | None = None) -> bool:
    """Enable Azure Q&A only for an explicit truthy environment setting."""
    values = os.environ if environment is None else environment
    return values.get("ENABLE_AZURE_QA", "").strip().lower() in {
        "1", "true", "yes", "on"
    }


def _normalize(question: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", question.lower()).strip()


def _glossary_answer(normalized: str) -> str | None:
    aliases = {
        "revenue": "Revenue",
        "gross profit": "Gross profit",
        "operating income": "Operating income",
        "net income": "Net income",
        "qoq": "QoQ growth",
        "quarter over quarter": "QoQ growth",
        "yoy": "YoY growth",
        "year over year": "YoY growth",
        "gross margin": "Gross margin",
        "operating margin": "Operating margin",
        "net margin": "Net margin",
        "segment contribution": "Segment contribution",
        "headwind": "Headwind",
    }
    if "difference" in normalized and "qoq" in normalized and "yoy" in normalized:
        return f"QoQ: {METRIC_DEFINITIONS['QoQ growth']} YoY: {METRIC_DEFINITIONS['YoY growth']}"
    if not any(word in normalized for word in ("mean", "what is", "explain", "definition")):
        return None
    for alias, label in sorted(aliases.items(), key=lambda item: -len(item[0])):
        if alias in normalized:
            return f"{label}: {METRIC_DEFINITIONS[label]}"
    return None


def deterministic_answer(
    question: str,
    context: GroundingContext,
) -> PlatformAnswer | None:
    """Answer supported common questions without a provider or AI label."""
    normalized = _normalize(question)
    glossary = _glossary_answer(normalized)
    if glossary is not None:
        return PlatformAnswer(mode="deterministic", answer=glossary)

    summary = build_plain_english_summary(context)
    drivers = context.business_drivers
    ranking = (
        drivers.derived_ranking
        if drivers is not None and drivers.availability == "available"
        else None
    )
    if any(phrase in normalized for phrase in ("perform well", "strong quarter")):
        return PlatformAnswer(
            mode="deterministic",
            answer=f"{summary.headline} {summary.points[0]}",
            source_ids=summary.source_ids,
        )
    if any(phrase in normalized for phrase in ("explain this quarter", "plain english", "do not know finance")):
        return PlatformAnswer(
            mode="deterministic",
            answer=" ".join((summary.headline, *summary.points)),
            source_ids=summary.source_ids,
        )
    if any(phrase in normalized for phrase in ("drove", "drivers", "growth")) and "mean" not in normalized:
        if ranking is None or not ranking.positive_contributors:
            return PlatformAnswer(
                mode="deterministic",
                answer="Approved financial data shows the change in revenue, but approved driver context is unavailable for this period.",
                source_ids=summary.source_ids,
            )
        names = ranking.positive_contributors[:2]
        return PlatformAnswer(
            mode="deterministic",
            answer=f"The largest approved positive segment contributors were {' and '.join(names)}.",
            source_ids=summary.source_ids,
        )
    if "headwind" in normalized:
        if ranking is None or not ranking.negative_contributors:
            answer = "No approved segment headwind is available for this period."
        else:
            answer = f"The main approved segment headwind was {ranking.negative_contributors[0]}."
        return PlatformAnswer(mode="deterministic", answer=answer, source_ids=summary.source_ids)
    if "margin" in normalized and any(word in normalized for word in ("strong", "profit", "healthy")):
        profitability = next(
            (point for point in summary.points if point.startswith("Profitability")),
            "The displayed margins show how much revenue remained at each stage of profitability.",
        )
        return PlatformAnswer(mode="deterministic", answer=profitability, source_ids=summary.source_ids)
    if "investigate" in normalized or "attention" in normalized:
        areas = ["revenue growth durability", "margin direction"]
        if ranking is not None and ranking.negative_contributors:
            areas.append(f"the {ranking.negative_contributors[0]} headwind")
        return PlatformAnswer(
            mode="deterministic",
            answer="Useful next areas to investigate are " + ", ".join(areas) + ".",
            source_ids=summary.source_ids,
        )
    return None


def answer_platform_question(
    question: str,
    context: GroundingContext,
    *,
    enable_azure: bool = False,
    provider_factory: Callable[[], QAProvider] | None = None,
    azure_questions_used: int = 0,
    history: tuple[QATurn, ...] = (),
) -> PlatformAnswer:
    """Answer deterministically first, then optionally invoke one grounded provider."""
    normalized = question.strip()
    if not normalized or len(normalized) > MAX_QUESTION_LENGTH:
        return PlatformAnswer(
            mode="insufficient_context",
            answer="Questions must contain between 1 and 500 characters.",
        )
    deterministic = deterministic_answer(normalized, context)
    if deterministic is not None:
        return deterministic
    if not enable_azure:
        return PlatformAnswer(mode="insufficient_context", answer=UNSUPPORTED_MESSAGE)
    if azure_questions_used >= MAX_AZURE_QUESTIONS_PER_SESSION:
        return PlatformAnswer(
            mode="insufficient_context",
            answer="This session has reached the five-question grounded Q&A limit.",
        )
    if provider_factory is None:
        return PlatformAnswer(mode="insufficient_context", answer=SAFE_FAILURE_MESSAGE)
    try:
        approved = generate_grounded_answer(
            normalized,
            context,
            provider_factory(),
            history[-3:],
        )
    except GroundedQAError:
        return PlatformAnswer(
            mode="insufficient_context",
            answer=SAFE_FAILURE_MESSAGE,
            azure_request_made=True,
        )
    return PlatformAnswer(
        mode=("grounded_ai" if approved.status == "supported" else "insufficient_context"),
        answer=approved.answer,
        source_ids=approved.source_ids,
        grounded_answer=approved,
        azure_request_made=True,
    )
