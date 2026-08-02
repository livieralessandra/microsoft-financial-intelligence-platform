"""Tests for approved business-driver loading, validation, and enrichment."""

from decimal import Decimal
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.ai.business_drivers import (
    BusinessDriverError,
    CONTRIBUTION_QUANTUM,
    DEFAULT_PACKET_DIRECTORY,
    load_business_driver_context,
)
from src.ai.grounding import build_grounding_context
from src.ai.schemas import (
    DerivedBusinessMetric,
    FactClassification,
    FigureUnit,
    ManagementExplanation,
    ReportingPeriod,
)
from src.data_loader import load_financial_datasets


FIXTURES = Path(__file__).parent / "fixtures"
PACKET_PATH = DEFAULT_PACKET_DIRECTORY / "FY2026-Q4.json"


def _packet_data() -> dict:
    return json.loads(PACKET_PATH.read_text())


def _write_packet(directory: Path, data: dict, name: str = "FY2026-Q4.json") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(json.dumps(data))


def test_loads_approved_fy2026_q4_packet() -> None:
    context = load_business_driver_context("FY2026-Q4")
    assert context.availability == "available"
    assert context.packet is not None
    assert len(context.packet.management_explanations) == 8
    assert {source.source_id for source in context.packet.sources} == {
        "msft_ir_fy2026_q4_press_release",
        "msft_ir_fy2026_q4_metrics",
        "msft_ir_fy2026_q4_earnings_call",
    }


def test_missing_packet_is_explicitly_unavailable(tmp_path: Path) -> None:
    context = load_business_driver_context("FY2025-Q3", tmp_path)
    assert context.availability == "unavailable"
    assert context.packet is None
    assert context.derived_ranking is None
    assert "FY2025-Q3" in context.unavailable_reason


def test_schema_rejects_extra_and_malformed_values() -> None:
    with pytest.raises(ValidationError, match="Extra inputs"):
        ReportingPeriod(fiscal_year=2026, fiscal_period="Q4", surprise=True)
    with pytest.raises(ValidationError):
        DerivedBusinessMetric(
            metric="segment_change",
            value="not-a-number",
            unit=FigureUnit.USD,
            classification=FactClassification.DERIVED,
            source_ids=("msft_ir_fy2026_q4_press_release",),
        )


def test_exact_reconciliation_and_expected_ranking_fixture() -> None:
    expected = json.loads(
        (FIXTURES / "fy2026_q4_driver_ranking.json").read_text()
    )
    context = load_business_driver_context("FY2026-Q4")
    ranking = context.derived_ranking
    assert ranking is not None
    assert ranking.total_revenue_change == Decimal("13566000000")
    assert list(ranking.positive_contributors) == expected["positive_contributors"]
    assert list(ranking.negative_contributors) == expected["negative_contributors"]
    actual = {item.segment: item for item in ranking.contributions}
    for segment, values in expected["contributions"].items():
        assert actual[segment].absolute_revenue_change == Decimal(
            values["absolute_revenue_change"]
        )
        assert (
            abs(actual[segment].contribution_pct - Decimal(values["contribution_pct"]))
            <= CONTRIBUTION_QUANTUM
        )
        assert actual[segment].classification == FactClassification.DERIVED
    assert sum(item.absolute_revenue_change for item in ranking.contributions) == Decimal(
        "13566000000"
    )


def test_rejects_segment_reconciliation_failure(tmp_path: Path) -> None:
    data = _packet_data()
    data["segment_results"][0]["current_revenue"] = "37847000001"
    _write_packet(tmp_path, data)
    with pytest.raises(BusinessDriverError, match="reconcile"):
        load_business_driver_context("FY2026-Q4", tmp_path)


def test_rejects_unknown_source_id(tmp_path: Path) -> None:
    data = _packet_data()
    data["product_indicators"][0]["source_ids"] = ["unknown_source"]
    _write_packet(tmp_path, data)
    with pytest.raises(BusinessDriverError, match="Unsupported source IDs"):
        load_business_driver_context("FY2026-Q4", tmp_path)


def test_rejects_mismatched_packet_period(tmp_path: Path) -> None:
    data = _packet_data()
    data["reporting_period"] = {"fiscal_year": 2025, "fiscal_period": "Q4"}
    _write_packet(tmp_path, data)
    with pytest.raises(BusinessDriverError, match="does not match"):
        load_business_driver_context("FY2026-Q4", tmp_path)


def test_reported_and_derived_classifications_are_not_interchangeable() -> None:
    with pytest.raises(ValidationError):
        DerivedBusinessMetric(
            metric="segment_change",
            value="1",
            unit=FigureUnit.USD,
            classification=FactClassification.REPORTED,
            source_ids=("msft_ir_fy2026_q4_press_release",),
        )


def test_management_explanation_requires_attribution() -> None:
    with pytest.raises(ValidationError):
        ManagementExplanation(
            explanation_id="test",
            statement="Microsoft said demand supported performance.",
            classification=FactClassification.MANAGEMENT_EXPLANATION,
            source_ids=("msft_ir_fy2026_q4_earnings_call",),
        )


def test_real_fy2026_q4_context_is_enriched_without_server_or_network() -> None:
    context = build_grounding_context(load_financial_datasets(), "FY2026-Q4")
    assert context.business_drivers is not None
    assert context.business_drivers.availability == "available"
    assert context.business_drivers.derived_ranking is not None
    assert context.business_drivers.derived_ranking.positive_contributors[0] == (
        "Intelligent Cloud"
    )
