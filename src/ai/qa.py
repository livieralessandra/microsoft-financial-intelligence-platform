"""Provider-independent prompting and validation for grounded financial Q&A."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Protocol, runtime_checkable

from pydantic import ValidationError

from src.ai import validation as briefing_validation
from src.ai.schemas import (
    FactClassification,
    GroundedAnswer,
    GroundedAnswerClaim,
    GroundingContext,
    QAClassification,
)


MAX_QUESTION_LENGTH = 500
MAX_HISTORY_TURNS = 3
PROHIBITED_ADVICE = re.compile(
    r"\b(buy|sell|hold|price targets?|investment advice|invest|"
    r"forecasts?|recommendations?)\b",
    re.IGNORECASE,
)


class GroundedQAError(RuntimeError):
    """Raised when a provider answer is unsafe, malformed, or ungrounded."""


@dataclass(frozen=True)
class QATurn:
    """One session-only question and approved answer supplied as history."""

    question: str
    answer: str


@dataclass(frozen=True)
class QAPrompt:
    """Stable prompt components for any future structured-output provider."""

    system_instructions: str
    question: str
    approved_context_json: str
    history_json: str
    output_schema_json: str


@runtime_checkable
class QAProvider(Protocol):
    """A provider returning one structured grounded-answer JSON document."""

    def generate_answer(self, prompt: QAPrompt) -> str:
        """Generate a structured answer without tools or external retrieval."""
        ...


QA_SYSTEM_INSTRUCTIONS = """Answer only from the supplied approved Microsoft financial context.
Do not browse, retrieve external information, use tools, recalculate figures, or guess.
Return insufficient_context when the approved context cannot answer the question.
Every factual claim must include its exact approved metric, value, unit, classification,
and source IDs. Attribute management explanations to Microsoft management. Separate
reported facts, derived metrics, management explanations, and AI interpretations.
Do not provide forecasts, price targets, investment advice, or buy/sell language.
Return JSON only and match the GroundedAnswer JSON Schema exactly."""


def build_qa_prompt(
    question: str,
    context: GroundingContext,
    history: tuple[QATurn, ...] = (),
) -> QAPrompt:
    """Build a bounded deterministic prompt containing approved context only."""
    normalized = question.strip()
    if not normalized or len(normalized) > MAX_QUESTION_LENGTH:
        raise GroundedQAError("Question must contain 1 to 500 characters.")
    bounded_history = history[-MAX_HISTORY_TURNS:]
    return QAPrompt(
        system_instructions=QA_SYSTEM_INSTRUCTIONS,
        question=normalized,
        approved_context_json=json.dumps(
            context.model_dump(mode="json"), sort_keys=True, ensure_ascii=False
        ),
        history_json=json.dumps(
            [turn.__dict__ for turn in bounded_history],
            sort_keys=True,
            ensure_ascii=False,
        ),
        output_schema_json=json.dumps(
            GroundedAnswer.model_json_schema(), sort_keys=True, ensure_ascii=False
        ),
    )


def _allowed_sources(context: GroundingContext) -> set[str]:
    sources = {source.source_id for source in context.sources}
    drivers = context.business_drivers
    if drivers is not None and drivers.availability == "available" and drivers.packet:
        sources.update(source.source_id for source in drivers.packet.sources)
    return sources


def _validate_numeric_claim(
    claim: GroundedAnswerClaim,
    context: GroundingContext,
) -> bool:
    assert claim.value is not None and claim.unit is not None
    grounded = briefing_validation._grounded_figures(context)
    financial_matches = [
        figure
        for (source_id, metric), figure in grounded.items()
        if metric == claim.metric and source_id in claim.source_ids
    ]
    if financial_matches:
        figure = financial_matches[0]
        expected_classification = (
            QAClassification.REPORTED_FACT
            if claim.metric in {"revenue", "gross_profit", "operating_income", "net_income"}
            else QAClassification.DERIVED_METRIC
        )
        return (
            claim.classification in {expected_classification, QAClassification.AI_INTERPRETATION}
            and claim.unit == figure.unit
            and briefing_validation._values_match(claim.value, figure.value, claim.unit)
        )

    approved = briefing_validation._approved_business_claims(context).get(claim.metric)
    if approved is None:
        return False
    value, unit, classification, source_ids = approved
    expected = (
        QAClassification.REPORTED_FACT
        if classification == FactClassification.REPORTED
        else QAClassification.DERIVED_METRIC
    )
    return (
        claim.classification in {expected, QAClassification.AI_INTERPRETATION}
        and claim.unit == unit
        and set(claim.source_ids) == source_ids
        and briefing_validation._values_match(claim.value, value, unit)
    )


def validate_grounded_answer(
    answer: GroundedAnswer,
    context: GroundingContext,
) -> None:
    """Reject unsupported periods, claims, sources, and investment language."""
    errors: list[str] = []
    if answer.reporting_period != context.requested_period:
        errors.append("Answer reporting period does not match approved context.")
    if set(answer.source_ids) - _allowed_sources(context):
        errors.append("Answer contains an unsupported source ID.")
    narrative = " ".join(
        filter(
            None,
            (
                answer.answer,
                answer.plain_language_explanation,
                *answer.suggested_investigation_areas,
            ),
        )
    )
    if PROHIBITED_ADVICE.search(narrative):
        errors.append("Answer contains prohibited investment or forecast language.")

    drivers = context.business_drivers
    explanations = {}
    if drivers is not None and drivers.availability == "available" and drivers.packet:
        explanations = {
            item.explanation_id: item
            for item in drivers.packet.management_explanations
        }
    for claim in answer.claims:
        if set(claim.source_ids) - _allowed_sources(context):
            errors.append(f"Unsupported claim source for {claim.metric}.")
            continue
        if claim.classification == QAClassification.MANAGEMENT_EXPLANATION:
            explanation = explanations.get(claim.management_explanation_id)
            if (
                explanation is None
                or claim.metric != explanation.explanation_id
                or set(claim.source_ids) != set(explanation.source_ids)
                or "management" not in answer.answer.lower()
            ):
                errors.append("Unsupported or unattributed management explanation.")
        elif not _validate_numeric_claim(claim, context):
            errors.append(f"Unsupported or mismatched claim: {claim.metric}.")
    if errors:
        raise GroundedQAError(" ".join(errors))


def generate_grounded_answer(
    question: str,
    context: GroundingContext,
    provider: QAProvider,
    history: tuple[QATurn, ...] = (),
) -> GroundedAnswer:
    """Return only provider output that passes schema and local grounding checks."""
    prompt = build_qa_prompt(question, context, history)
    try:
        raw = provider.generate_answer(prompt)
        if not isinstance(raw, str):
            raise TypeError("Provider response must be JSON text.")
        answer = GroundedAnswer.model_validate_json(raw)
        validate_grounded_answer(answer, context)
        return answer
    except (GroundedQAError, TypeError, ValueError, ValidationError) as error:
        raise GroundedQAError("Grounded answer could not be approved.") from error
    except Exception as error:
        raise GroundedQAError("Grounded answer provider failed safely.") from error
