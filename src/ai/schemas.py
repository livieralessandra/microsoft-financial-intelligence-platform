"""Strict provider-independent schemas for grounded executive briefings."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from enum import Enum
import re
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)


StrictText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


def _to_decimal(value: object) -> Decimal:
    if isinstance(value, bool):
        raise ValueError("Boolean values are not valid financial figures.")
    try:
        decimal_value = (
            value if isinstance(value, Decimal) else Decimal(str(value))
        )
    except (InvalidOperation, ValueError) as error:
        raise ValueError(
            "Financial figure must be a valid decimal number."
        ) from error
    if not decimal_value.is_finite():
        raise ValueError("Financial figure must be finite.")
    return decimal_value


class StrictModel(BaseModel):
    """Base model that rejects unknown fields and mutation."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class FigureUnit(str, Enum):
    """Supported financial figure units."""

    USD = "usd"
    PERCENT = "percent"
    COUNT = "count"


class FactClassification(str, Enum):
    """Provenance class for approved business-driver content."""

    REPORTED = "reported"
    DERIVED = "derived"
    MANAGEMENT_EXPLANATION = "management_explanation"


class MetricName(str, Enum):
    """Metrics available in the approved analytics exports."""

    REVENUE = "revenue"
    GROSS_PROFIT = "gross_profit"
    OPERATING_INCOME = "operating_income"
    NET_INCOME = "net_income"
    REVENUE_QOQ_GROWTH_PCT = "revenue_qoq_growth_pct"
    REVENUE_YOY_GROWTH_PCT = "revenue_yoy_growth_pct"
    GROSS_MARGIN_PCT = "gross_margin_pct"
    OPERATING_MARGIN_PCT = "operating_margin_pct"
    NET_MARGIN_PCT = "net_margin_pct"


class ReportingPeriod(StrictModel):
    """Canonical Microsoft fiscal-quarter identifier."""

    fiscal_year: int = Field(ge=1900, le=9999)
    fiscal_period: Literal["Q1", "Q2", "Q3", "Q4"]

    @property
    def identifier(self) -> str:
        return f"FY{self.fiscal_year}-{self.fiscal_period}"

    @property
    def quarter_number(self) -> int:
        return int(self.fiscal_period[1])

    @classmethod
    def parse(cls, value: str) -> ReportingPeriod:
        if not isinstance(value, str):
            raise ValueError("Reporting-period identifier must be a string.")
        match = re.fullmatch(r"FY(\d{4})-(Q[1-4])", value)
        if match is None:
            raise ValueError(
                "Reporting period must use the format FY2026-Q4."
            )
        return cls(
            fiscal_year=int(match.group(1)),
            fiscal_period=match.group(2),
        )

    def previous_quarter(self) -> ReportingPeriod:
        if self.fiscal_period == "Q1":
            return ReportingPeriod(
                fiscal_year=self.fiscal_year - 1,
                fiscal_period="Q4",
            )
        return ReportingPeriod(
            fiscal_year=self.fiscal_year,
            fiscal_period=f"Q{self.quarter_number - 1}",
        )

    def prior_year_quarter(self) -> ReportingPeriod:
        return ReportingPeriod(
            fiscal_year=self.fiscal_year - 1,
            fiscal_period=self.fiscal_period,
        )


class SourceReference(StrictModel):
    """Deterministic reference to one approved dataset row."""

    source_id: StrictText
    dataset: Literal["quarterly_analytics", "annual_financials"]
    period_id: StrictText

    @model_validator(mode="after")
    def validate_deterministic_id(self) -> SourceReference:
        expected = f"{self.dataset}:{self.period_id}"
        if self.source_id != expected:
            raise ValueError(
                f"Source ID must be deterministic; expected {expected}."
            )
        if self.dataset == "quarterly_analytics":
            ReportingPeriod.parse(self.period_id)
        elif re.fullmatch(r"FY\d{4}", self.period_id) is None:
            raise ValueError(
                "Annual source period must use the format FY2026."
            )
        return self


class OfficialSourceMetadata(StrictModel):
    """One approved Microsoft Investor Relations source."""

    source_id: StrictText
    reporting_period: ReportingPeriod
    source_type: Literal["press_release", "metrics", "earnings_call"]
    title: StrictText
    url: Annotated[str, StringConstraints(pattern=r"^https://www\.microsoft\.com/")]


class ReportedBusinessFact(StrictModel):
    """A numeric fact explicitly reported in an approved source."""

    metric: StrictText
    label: StrictText
    value: Decimal
    unit: FigureUnit
    classification: Literal[FactClassification.REPORTED]
    source_ids: tuple[StrictText, ...] = Field(min_length=1)
    qualifier: Literal["exact", "more_than"] = "exact"

    @field_validator("value", mode="before")
    @classmethod
    def normalize_decimal(cls, value: object) -> Decimal:
        return _to_decimal(value)

    @model_validator(mode="after")
    def validate_value(self) -> ReportedBusinessFact:
        if self.unit in {FigureUnit.USD, FigureUnit.COUNT}:
            if self.value != self.value.to_integral_value():
                raise ValueError("USD and count facts must be integers.")
        if len(self.source_ids) != len(set(self.source_ids)):
            raise ValueError("Reported fact contains duplicate source IDs.")
        return self


class SegmentResult(StrictModel):
    """Approved reported revenue facts for one operating segment."""

    segment: StrictText
    current_revenue: Decimal
    prior_year_revenue: Decimal
    reported_growth_pct: Decimal
    classification: Literal[FactClassification.REPORTED]
    source_ids: tuple[StrictText, ...] = Field(min_length=1)

    @field_validator(
        "current_revenue", "prior_year_revenue", "reported_growth_pct",
        mode="before",
    )
    @classmethod
    def normalize_decimal(cls, value: object) -> Decimal:
        return _to_decimal(value)

    @model_validator(mode="after")
    def validate_result(self) -> SegmentResult:
        for value in (self.current_revenue, self.prior_year_revenue):
            if value != value.to_integral_value():
                raise ValueError("Segment revenue must use integer USD.")
        if len(self.source_ids) != len(set(self.source_ids)):
            raise ValueError("Segment result contains duplicate source IDs.")
        return self


class ManagementExplanation(StrictModel):
    """A qualitative explanation attributed to Microsoft management."""

    explanation_id: StrictText
    statement: StrictText
    attribution: Literal["Microsoft management"]
    classification: Literal[FactClassification.MANAGEMENT_EXPLANATION]
    source_ids: tuple[StrictText, ...] = Field(min_length=1)


class DerivedBusinessMetric(StrictModel):
    """A computed metric that must never be represented as reported."""

    metric: StrictText
    value: Decimal
    unit: FigureUnit
    classification: Literal[FactClassification.DERIVED]
    source_ids: tuple[StrictText, ...] = Field(min_length=1)

    @field_validator("value", mode="before")
    @classmethod
    def normalize_decimal(cls, value: object) -> Decimal:
        return _to_decimal(value)


class ApprovedBusinessDriverPacket(StrictModel):
    """Versioned, approved facts and explanations for one fiscal period."""

    schema_version: Literal["1.0"] = "1.0"
    entity: Literal["Microsoft Corporation"] = "Microsoft Corporation"
    reporting_period: ReportingPeriod
    sources: tuple[OfficialSourceMetadata, ...] = Field(min_length=1)
    reported_facts: tuple[ReportedBusinessFact, ...] = Field(min_length=1)
    segment_results: tuple[SegmentResult, ...] = Field(min_length=1)
    product_indicators: tuple[ReportedBusinessFact, ...] = Field(min_length=1)
    derived_metrics: tuple[DerivedBusinessMetric, ...] = ()
    management_explanations: tuple[ManagementExplanation, ...] = Field(
        min_length=1
    )


class DerivedSegmentContribution(StrictModel):
    """Computed contribution of a segment to company revenue change."""

    segment: StrictText
    absolute_revenue_change: Decimal
    contribution_pct: Decimal
    classification: Literal[FactClassification.DERIVED]
    source_ids: tuple[StrictText, ...] = Field(min_length=1)

    @field_validator(
        "absolute_revenue_change", "contribution_pct", mode="before"
    )
    @classmethod
    def normalize_decimal(cls, value: object) -> Decimal:
        return _to_decimal(value)


class DerivedDriverRanking(StrictModel):
    """Deterministic positive-contributor and headwind rankings."""

    reporting_period: ReportingPeriod
    total_revenue_change: Decimal
    contributions: tuple[DerivedSegmentContribution, ...] = Field(min_length=1)
    positive_contributors: tuple[StrictText, ...]
    negative_contributors: tuple[StrictText, ...]
    classification: Literal[FactClassification.DERIVED]

    @field_validator("total_revenue_change", mode="before")
    @classmethod
    def normalize_decimal(cls, value: object) -> Decimal:
        return _to_decimal(value)


class BusinessDriverContext(StrictModel):
    """Approved driver enrichment, or an explicit unavailable state."""

    reporting_period: ReportingPeriod
    availability: Literal["available", "unavailable"]
    packet: ApprovedBusinessDriverPacket | None = None
    derived_ranking: DerivedDriverRanking | None = None
    unavailable_reason: StrictText | None = None

    @model_validator(mode="after")
    def validate_availability(self) -> BusinessDriverContext:
        if self.availability == "available":
            if self.packet is None or self.derived_ranking is None:
                raise ValueError("Available driver context requires packet and ranking.")
            if self.unavailable_reason is not None:
                raise ValueError("Available driver context cannot have a reason.")
        elif self.packet is not None or self.derived_ranking is not None:
            raise ValueError("Unavailable driver context cannot contain approved data.")
        elif self.unavailable_reason is None:
            raise ValueError("Unavailable driver context requires a reason.")
        return self


class GroundedFigure(StrictModel):
    """One numeric fact tied to a metric, unit, and approved source."""

    metric: MetricName
    value: Decimal
    unit: FigureUnit
    source_id: StrictText

    @field_validator("value", mode="before")
    @classmethod
    def normalize_decimal(cls, value: object) -> Decimal:
        return _to_decimal(value)

    @model_validator(mode="after")
    def validate_unit_and_value(self) -> GroundedFigure:
        percentage_metrics = {
            MetricName.REVENUE_QOQ_GROWTH_PCT,
            MetricName.REVENUE_YOY_GROWTH_PCT,
            MetricName.GROSS_MARGIN_PCT,
            MetricName.OPERATING_MARGIN_PCT,
            MetricName.NET_MARGIN_PCT,
        }
        expected_unit = (
            FigureUnit.PERCENT
            if self.metric in percentage_metrics
            else FigureUnit.USD
        )
        if self.unit != expected_unit:
            raise ValueError(
                f"{self.metric.value} must use unit {expected_unit.value}."
            )
        if (
            self.unit == FigureUnit.USD
            and self.value != self.value.to_integral_value()
        ):
            raise ValueError("USD figures must be integer dollar values.")
        return self


class PeriodFacts(StrictModel):
    """Grounded figures for one fiscal quarter."""

    period: ReportingPeriod
    source_id: StrictText
    figures: tuple[GroundedFigure, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_figures(self) -> PeriodFacts:
        metrics = [figure.metric for figure in self.figures]
        if len(metrics) != len(set(metrics)):
            raise ValueError("Period facts contain duplicate metrics.")
        if any(
            figure.source_id != self.source_id for figure in self.figures
        ):
            raise ValueError(
                "Every period figure must use the period source ID."
            )
        return self


class AnnualFacts(StrictModel):
    """Grounded figures for one completed fiscal year."""

    fiscal_year: int = Field(ge=1900, le=9999)
    source_id: StrictText
    figures: tuple[GroundedFigure, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_figures(self) -> AnnualFacts:
        metrics = [figure.metric for figure in self.figures]
        if len(metrics) != len(set(metrics)):
            raise ValueError("Annual facts contain duplicate metrics.")
        if any(
            figure.source_id != self.source_id for figure in self.figures
        ):
            raise ValueError(
                "Every annual figure must use the annual source ID."
            )
        return self


class GroundingContext(StrictModel):
    """Approved facts available as of one requested reporting period."""

    schema_version: Literal["1.0"] = "1.0"
    entity: Literal["Microsoft Corporation"] = "Microsoft Corporation"
    requested_period: ReportingPeriod
    current_period: PeriodFacts
    previous_quarter: PeriodFacts | None = None
    prior_year_quarter: PeriodFacts | None = None
    annual_context: AnnualFacts | None = None
    business_drivers: BusinessDriverContext | None = None
    sources: tuple[SourceReference, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_context_links(self) -> GroundingContext:
        if self.current_period.period != self.requested_period:
            raise ValueError(
                "Current period must match the requested reporting period."
            )
        source_ids = [source.source_id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("Grounding context contains duplicate sources.")
        expected_ids = {self.current_period.source_id}
        for facts in (
            self.previous_quarter,
            self.prior_year_quarter,
            self.annual_context,
        ):
            if facts is not None:
                expected_ids.add(facts.source_id)
        if set(source_ids) != expected_ids:
            raise ValueError(
                "Grounding sources must exactly match referenced fact sources."
            )
        return self


class BriefingFigureClaim(StrictModel):
    """A structured numeric claim made by an executive briefing."""

    metric: MetricName
    value: Decimal
    unit: FigureUnit
    source_id: StrictText

    @field_validator("value", mode="before")
    @classmethod
    def normalize_decimal(cls, value: object) -> Decimal:
        return _to_decimal(value)


class BriefingInsight(StrictModel):
    """One structured executive insight and its numeric claims."""

    category: Literal[
        "current_performance",
        "change",
        "profitability",
        "attention",
    ]
    title: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=80),
    ]
    narrative: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
    ]
    figure_claims: tuple[BriefingFigureClaim, ...] = ()


class ExecutiveBriefing(StrictModel):
    """Strict provider-independent output contract for a briefing."""

    schema_version: Literal["1.0"] = "1.0"
    entity: Literal["Microsoft Corporation"] = "Microsoft Corporation"
    reporting_period: ReportingPeriod
    headline: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=140),
    ]
    executive_summary: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=800),
    ]
    insights: tuple[BriefingInsight, ...] = Field(min_length=1, max_length=6)
    source_ids: tuple[StrictText, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_references(self) -> ExecutiveBriefing:
        if len(self.source_ids) != len(set(self.source_ids)):
            raise ValueError("Executive briefing has duplicate source IDs.")
        return self
