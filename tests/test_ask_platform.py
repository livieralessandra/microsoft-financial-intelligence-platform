"""Tests for deterministic and provider-independent grounded Q&A."""

from decimal import Decimal

import pytest

from src.ai.grounding import build_grounding_context
from src.ai.qa import (
    GroundedQAError,
    QATurn,
    build_qa_prompt,
    generate_grounded_answer,
    validate_grounded_answer,
)
from src.ai.schemas import (
    FigureUnit,
    GroundedAnswer,
    GroundedAnswerClaim,
    QAClassification,
    ReportingPeriod,
)
from src.ask_platform import (
    MAX_AZURE_QUESTIONS_PER_SESSION,
    UNSUPPORTED_MESSAGE,
    answer_platform_question,
    azure_qa_enabled,
)


class FakeQAProvider:
    def __init__(self, response: str | Exception) -> None:
        self.response = response
        self.calls = []

    def generate_answer(self, prompt) -> str:
        self.calls.append(prompt)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def _valid_answer(context) -> GroundedAnswer:
    source_id = context.current_period.source_id
    return GroundedAnswer(
        reporting_period=context.requested_period,
        status="supported",
        answer="Revenue was $90.0 billion for the quarter.",
        plain_language_explanation="Revenue is the money generated before expenses.",
        claims=(
            GroundedAnswerClaim(
                metric="revenue",
                classification=QAClassification.REPORTED_FACT,
                value=Decimal("90000000000"),
                unit=FigureUnit.USD,
                source_ids=(source_id,),
            ),
        ),
        metric_names=("revenue",),
        source_ids=(source_id,),
        suggested_investigation_areas=("Compare revenue growth over time.",),
    )


@pytest.mark.parametrize(
    "question",
    (
        "What does revenue mean?",
        "What is the difference between QoQ and YoY?",
        "Did Microsoft perform well?",
        "What drove Microsoft's growth?",
        "What was the main headwind?",
        "Are Microsoft's margins strong?",
        "What should I investigate next?",
        "Explain this quarter like I do not know finance.",
    ),
)
def test_supported_questions_are_deterministic_without_provider(
    question,
    financial_datasets,
) -> None:
    context = build_grounding_context(financial_datasets, "FY2026-Q4")
    provider_factory_called = False

    def forbidden_factory():
        nonlocal provider_factory_called
        provider_factory_called = True
        raise AssertionError("Deterministic questions must not construct Azure")

    result = answer_platform_question(
        question,
        context,
        enable_azure=True,
        provider_factory=forbidden_factory,
    )
    assert result.mode == "deterministic"
    assert result.answer
    assert not result.azure_request_made
    assert not provider_factory_called


def test_unsupported_question_when_azure_disabled(financial_datasets) -> None:
    context = build_grounding_context(financial_datasets, "FY2026-Q4")
    result = answer_platform_question("Who is Microsoft's CEO?", context)
    assert result.mode == "insufficient_context"
    assert result.answer == UNSUPPORTED_MESSAGE


def test_azure_enablement_is_explicit() -> None:
    assert not azure_qa_enabled({})
    assert not azure_qa_enabled({"ENABLE_AZURE_QA": "false"})
    assert azure_qa_enabled({"ENABLE_AZURE_QA": "true"})


def test_provider_runs_only_for_explicit_enabled_unsupported_question(
    financial_datasets,
) -> None:
    context = build_grounding_context(financial_datasets, "FY2026-Q4")
    provider = FakeQAProvider(_valid_answer(context).model_dump_json())
    result = answer_platform_question(
        "Summarize the approved revenue figure.",
        context,
        enable_azure=True,
        provider_factory=lambda: provider,
    )
    assert result.mode == "grounded_ai"
    assert result.azure_request_made
    assert len(provider.calls) == 1


def test_question_length_and_five_request_limit(financial_datasets) -> None:
    context = build_grounding_context(financial_datasets, "FY2026-Q4")
    provider = FakeQAProvider(_valid_answer(context).model_dump_json())
    too_long = answer_platform_question("x" * 501, context, enable_azure=True)
    limited = answer_platform_question(
        "Answer a custom approved question.",
        context,
        enable_azure=True,
        provider_factory=lambda: provider,
        azure_questions_used=MAX_AZURE_QUESTIONS_PER_SESSION,
    )
    assert "500" in too_long.answer
    assert "five-question" in limited.answer
    assert not provider.calls


def test_prompt_supplies_at_most_three_prior_turns(financial_datasets) -> None:
    context = build_grounding_context(financial_datasets, "FY2026-Q4")
    history = tuple(QATurn(question=f"q{index}", answer=f"a{index}") for index in range(5))
    prompt = build_qa_prompt("Explain approved revenue.", context, history)
    assert "q0" not in prompt.history_json
    assert "q1" not in prompt.history_json
    assert all(f"q{index}" in prompt.history_json for index in (2, 3, 4))


def test_valid_structured_answer_generation(financial_datasets) -> None:
    context = build_grounding_context(financial_datasets, "FY2026-Q4")
    expected = _valid_answer(context)
    provider = FakeQAProvider(expected.model_dump_json())
    assert generate_grounded_answer("What was revenue?", context, provider) == expected


def test_invented_figure_unknown_source_and_period_are_rejected(
    financial_datasets,
) -> None:
    context = build_grounding_context(financial_datasets, "FY2026-Q4")
    valid = _valid_answer(context)
    invented_claim = valid.claims[0].model_copy(update={"value": Decimal("1")})
    invented = valid.model_copy(update={"claims": (invented_claim,)})
    unknown_claim = valid.claims[0].model_copy(update={"source_ids": ("unknown",)})
    unknown = valid.model_copy(
        update={"claims": (unknown_claim,), "source_ids": ("unknown",)}
    )
    wrong_period = valid.model_copy(
        update={"reporting_period": ReportingPeriod.parse("FY2025-Q4")}
    )
    unsupported_claim = valid.claims[0].model_copy(
        update={"metric": "product.unsupported_growth"}
    )
    unsupported = valid.model_copy(
        update={
            "claims": (unsupported_claim,),
            "metric_names": ("product.unsupported_growth",),
        }
    )
    for answer in (invented, unknown, wrong_period, unsupported):
        with pytest.raises(GroundedQAError):
            validate_grounded_answer(answer, context)


def test_investment_advice_is_rejected(financial_datasets) -> None:
    context = build_grounding_context(financial_datasets, "FY2026-Q4")
    answer = _valid_answer(context).model_copy(
        update={"answer": "You should buy Microsoft shares."}
    )
    with pytest.raises(GroundedQAError):
        validate_grounded_answer(answer, context)


def test_management_explanation_requires_explicit_attribution(
    financial_datasets,
) -> None:
    context = build_grounding_context(financial_datasets, "FY2026-Q4")
    source_id = "msft_ir_fy2026_q4_earnings_call"
    answer = GroundedAnswer(
        reporting_period=context.requested_period,
        status="supported",
        answer="Azure mix caused gross-margin pressure.",
        claims=(
            GroundedAnswerClaim(
                metric="cloud_margin_pressure",
                classification=QAClassification.MANAGEMENT_EXPLANATION,
                source_ids=(source_id,),
                management_explanation_id="cloud_margin_pressure",
            ),
        ),
        metric_names=("cloud_margin_pressure",),
        source_ids=(source_id,),
        suggested_investigation_areas=(),
    )
    with pytest.raises(GroundedQAError):
        validate_grounded_answer(answer, context)


def test_insufficient_context_answer_is_valid(financial_datasets) -> None:
    context = build_grounding_context(financial_datasets, "FY2026-Q4")
    answer = GroundedAnswer(
        reporting_period=context.requested_period,
        status="insufficient_context",
        answer="The approved context does not contain that information.",
        claims=(),
        metric_names=(),
        source_ids=(),
        suggested_investigation_areas=(),
    )
    validate_grounded_answer(answer, context)


def test_provider_failure_is_safe_and_does_not_expose_error(financial_datasets) -> None:
    context = build_grounding_context(financial_datasets, "FY2026-Q4")
    provider = FakeQAProvider(RuntimeError("secret raw SDK body"))
    result = answer_platform_question(
        "Answer a custom question.",
        context,
        enable_azure=True,
        provider_factory=lambda: provider,
    )
    assert result.mode == "insufficient_context"
    assert "secret" not in result.answer
    assert "SDK" not in result.answer
    assert result.azure_request_made
