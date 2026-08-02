"""End-to-end tests for provider-neutral briefing generation and display."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from src.ai.grounding import build_grounding_context
from src.ai.prompting import BriefingPrompt, build_briefing_prompt
from src.ai.providers import BriefingProvider
from src.ai.schemas import (
    BriefingBusinessClaim,
    BriefingFigureClaim,
    BriefingInsight,
    ExecutiveBriefing,
    FactClassification,
    FigureUnit,
    GroundingContext,
    MetricName,
    ReportingPeriod,
)
from src.ai.selection import select_briefing_for_display
from src.ai.service import BriefingGenerationError, generate_executive_briefing
from src.ai.storage import (
    BriefingStorageError,
    briefing_path,
    load_saved_briefing,
    save_briefing,
)
from src.data_loader import FinancialDatasets


FINANCIAL_SOURCE = "quarterly_analytics:FY2026-Q4"
PRESS_SOURCE = "msft_ir_fy2026_q4_press_release"
CALL_SOURCE = "msft_ir_fy2026_q4_earnings_call"


class FakeProvider:
    """Injected deterministic provider; performs no I/O."""

    def __init__(self, response: str) -> None:
        self.response = response
        self.prompt: BriefingPrompt | None = None

    def generate(self, prompt: BriefingPrompt) -> str:
        self.prompt = prompt
        return self.response


@pytest.fixture
def context(financial_datasets: FinancialDatasets) -> GroundingContext:
    return build_grounding_context(financial_datasets, "FY2026-Q4")


@pytest.fixture
def complete_briefing(context: GroundingContext) -> ExecutiveBriefing:
    categories = (
        "overall_performance",
        "primary_drivers",
        "headwinds",
        "profitability_context",
        "attention",
        "investigate_next",
    )
    insights = []
    for category in categories:
        figure_claims = ()
        business_claims = ()
        source_ids = (PRESS_SOURCE,)
        management_ids = ()
        if category == "overall_performance":
            source_ids = (FINANCIAL_SOURCE,)
            figure_claims = (
                BriefingFigureClaim(
                    metric=MetricName.REVENUE,
                    value=Decimal("90000000000"),
                    unit=FigureUnit.USD,
                    source_id=FINANCIAL_SOURCE,
                ),
            )
        elif category == "primary_drivers":
            business_claims = (
                BriefingBusinessClaim(
                    metric="segment.intelligent_cloud.contribution_pct",
                    value=Decimal("69.50"),
                    unit=FigureUnit.PERCENT,
                    classification=FactClassification.DERIVED,
                    source_ids=(PRESS_SOURCE,),
                ),
            )
        elif category == "headwinds":
            source_ids = (CALL_SOURCE,)
            management_ids = ("windows_oem_weakness",)
        insights.append(
            BriefingInsight(
                category=category,
                title=category.replace("_", " ").title(),
                narrative="Approved context supports this concise executive observation.",
                classification=FactClassification.AI_INTERPRETATION,
                source_ids=source_ids,
                figure_claims=figure_claims,
                business_claims=business_claims,
                management_explanation_ids=management_ids,
            )
        )
    return ExecutiveBriefing(
        reporting_period=context.requested_period,
        headline="Validated executive briefing",
        executive_summary="A concise synthesis of approved financial and driver context.",
        insights=tuple(insights),
        source_ids=(FINANCIAL_SOURCE, PRESS_SOURCE, CALL_SOURCE),
    )


def test_prompt_construction_is_deterministic(context: GroundingContext) -> None:
    first = build_briefing_prompt(context)
    second = build_briefing_prompt(context)
    assert first == second
    assert "Do not browse" in first.system_instructions
    assert "Do not invent, estimate, or recalculate" in first.system_instructions
    assert "investment advice" in first.system_instructions
    assert "FY2026-Q4" not in first.system_instructions
    assert '"fiscal_year": 2026' in first.approved_context_json


def test_provider_protocol_and_valid_generation(
    context: GroundingContext,
    complete_briefing: ExecutiveBriefing,
) -> None:
    provider = FakeProvider(complete_briefing.model_dump_json())
    assert isinstance(provider, BriefingProvider)
    result = generate_executive_briefing(context.requested_period, context, provider)
    assert result == complete_briefing
    assert provider.prompt == build_briefing_prompt(context)


def test_generation_rejects_malformed_json(context: GroundingContext) -> None:
    with pytest.raises(BriefingGenerationError):
        generate_executive_briefing(
            context.requested_period,
            context,
            FakeProvider("{not-json"),
        )


def test_generation_rejects_period_mismatch(
    context: GroundingContext,
    complete_briefing: ExecutiveBriefing,
) -> None:
    stale = complete_briefing.model_copy(
        update={"reporting_period": ReportingPeriod.parse("FY2025-Q4")}
    )
    with pytest.raises(BriefingGenerationError):
        generate_executive_briefing(
            context.requested_period, context, FakeProvider(stale.model_dump_json())
        )


def test_generation_rejects_unsupported_source(
    context: GroundingContext,
    complete_briefing: ExecutiveBriefing,
) -> None:
    unsupported = complete_briefing.model_copy(
        update={"source_ids": (*complete_briefing.source_ids, "unknown_source")}
    )
    with pytest.raises(BriefingGenerationError):
        generate_executive_briefing(
            context.requested_period,
            context,
            FakeProvider(unsupported.model_dump_json()),
        )


def test_generation_rejects_invented_figure(
    context: GroundingContext,
    complete_briefing: ExecutiveBriefing,
) -> None:
    insight = complete_briefing.insights[0]
    invented_claim = insight.figure_claims[0].model_copy(
        update={"value": Decimal("90000000001")}
    )
    invented_insight = insight.model_copy(update={"figure_claims": (invented_claim,)})
    invented = complete_briefing.model_copy(
        update={"insights": (invented_insight, *complete_briefing.insights[1:])}
    )
    with pytest.raises(BriefingGenerationError):
        generate_executive_briefing(
            context.requested_period, context, FakeProvider(invented.model_dump_json())
        )


def test_generation_rejects_unsupported_driver(
    context: GroundingContext,
    complete_briefing: ExecutiveBriefing,
) -> None:
    insight = complete_briefing.insights[1]
    unsupported_claim = insight.business_claims[0].model_copy(
        update={"metric": "invented_business_driver"}
    )
    unsupported_insight = insight.model_copy(
        update={"business_claims": (unsupported_claim,)}
    )
    unsupported = complete_briefing.model_copy(
        update={
            "insights": (
                complete_briefing.insights[0],
                unsupported_insight,
                *complete_briefing.insights[2:],
            )
        }
    )
    with pytest.raises(BriefingGenerationError):
        generate_executive_briefing(
            context.requested_period,
            context,
            FakeProvider(unsupported.model_dump_json()),
        )


def test_atomic_persistence_and_valid_loading(
    tmp_path: Path,
    context: GroundingContext,
    complete_briefing: ExecutiveBriefing,
) -> None:
    path = save_briefing(complete_briefing, context, tmp_path)
    assert path == tmp_path / "FY2026-Q4.json"
    assert not list(tmp_path.glob("*.tmp"))
    assert load_saved_briefing(context.requested_period, context, tmp_path) == (
        complete_briefing
    )


def test_invalid_replacement_never_overwrites_valid_file(
    tmp_path: Path,
    context: GroundingContext,
    complete_briefing: ExecutiveBriefing,
) -> None:
    path = save_briefing(complete_briefing, context, tmp_path)
    original = path.read_text()
    invalid = complete_briefing.model_copy(
        update={"reporting_period": ReportingPeriod.parse("FY2025-Q4")}
    )
    with pytest.raises(BriefingStorageError):
        save_briefing(invalid, context, tmp_path)
    assert path.read_text() == original


@pytest.mark.parametrize("contents", ["{bad-json", "{}"])
def test_saved_loader_rejects_invalid_json(
    tmp_path: Path,
    context: GroundingContext,
    contents: str,
) -> None:
    briefing_path(context.requested_period, tmp_path).write_text(contents)
    with pytest.raises(BriefingStorageError):
        load_saved_briefing(context.requested_period, context, tmp_path)


def test_saved_loader_rejects_stale_period(
    tmp_path: Path,
    context: GroundingContext,
    complete_briefing: ExecutiveBriefing,
) -> None:
    stale = complete_briefing.model_copy(
        update={"reporting_period": ReportingPeriod.parse("FY2025-Q4")}
    )
    briefing_path(context.requested_period, tmp_path).write_text(
        stale.model_dump_json()
    )
    with pytest.raises(BriefingStorageError):
        load_saved_briefing(context.requested_period, context, tmp_path)


def test_display_selection_uses_ai_only_when_valid(
    tmp_path: Path,
    context: GroundingContext,
    complete_briefing: ExecutiveBriefing,
) -> None:
    assert select_briefing_for_display(context, tmp_path).mode == "deterministic"
    save_briefing(complete_briefing, context, tmp_path)
    selection = select_briefing_for_display(context, tmp_path)
    assert selection.mode == "ai"
    assert selection.briefing == complete_briefing


def test_display_selection_falls_back_for_invalid_saved_json(
    tmp_path: Path,
    context: GroundingContext,
) -> None:
    briefing_path(context.requested_period, tmp_path).write_text("not-json")
    selection = select_briefing_for_display(context, tmp_path)
    assert selection.mode == "deterministic"
    assert selection.briefing is None
    assert "invalid" not in selection.status.lower()


def test_generic_non_q4_prompt_and_path(
    financial_datasets: FinancialDatasets,
    tmp_path: Path,
) -> None:
    context = build_grounding_context(financial_datasets, "FY2026-Q3")
    prompt = build_briefing_prompt(context)
    assert '"fiscal_period": "Q3"' in prompt.approved_context_json
    assert briefing_path(context.requested_period, tmp_path).name == "FY2026-Q3.json"
    assert select_briefing_for_display(context, tmp_path).mode == "deterministic"
