"""Streamlit rendering tests for comprehension and Q&A surfaces."""

import socket
from decimal import Decimal

from streamlit.testing.v1 import AppTest

from app import APP_CSS
from src.ai.grounding import build_grounding_context
from src.ai.schemas import (
    FigureUnit,
    GroundedAnswer,
    GroundedAnswerClaim,
    QAClassification,
)
from src.data_loader import load_financial_datasets


def test_initial_overview_renders_plain_english_and_qa_without_external_calls(
    monkeypatch,
) -> None:
    from src.ai import azure_provider, qa_azure

    def forbidden_call(*args: object, **kwargs: object) -> None:
        raise AssertionError("Initial rendering must not construct providers or use network")

    monkeypatch.delenv("ENABLE_AZURE_QA", raising=False)
    monkeypatch.setattr(azure_provider.AzureOpenAIProvider, "__init__", forbidden_call)
    monkeypatch.setattr(qa_azure.AzureQAProvider, "__init__", forbidden_call)
    monkeypatch.setattr(socket.socket, "connect", forbidden_call)

    app = AppTest.from_file("app.py").run(timeout=20)

    assert not app.exception
    rendered = "\n".join(str(markdown.value) for markdown in app.markdown)
    captions = "\n".join(str(caption.value) for caption in app.caption)
    assert "In Plain English" in rendered
    assert "Microsoft had a strong quarter" in rendered
    assert "Ask the Platform" in rendered
    assert "What does revenue mean?" in captions
    assert "Live grounded Q&amp;A is not enabled" in captions or "Live grounded Q&A is not enabled" in captions
    assert len(app.text_area) == 1
    assert app.text_area[0].max_chars == 500
    assert "@media (max-width: 600px)" in APP_CSS
    assert "overflow-x" not in APP_CSS or "overflow-x: hidden" in APP_CSS


def test_compact_summary_follows_kpis_and_preserves_full_detail() -> None:
    app = AppTest.from_file("app.py").run(timeout=20)
    assert not app.exception
    markup = [str(markdown.value) for markdown in app.markdown]
    net_margin_index = next(
        index
        for index, value in enumerate(markup)
        if '<div class="kpi-label">Net Margin' in value
    )
    summary_index = next(
        index
        for index, value in enumerate(markup)
        if '<div class="plain-english-shell">' in value
    )
    trajectory_index = next(
        index
        for index, value in enumerate(markup)
        if "Revenue trajectory and executive briefing" in value
    )
    compact_card = markup[summary_index]

    assert summary_index == net_margin_index + 1
    assert summary_index < trajectory_index
    assert "Microsoft had a strong quarter" in compact_card
    assert compact_card.count('class="plain-takeaway"') <= 4
    assert compact_card.count('class="plain-takeaway"') == 4
    assert "Productivity and Business Processes" not in compact_card
    assert "Azure was a major positive product signal" not in compact_card

    expander_labels = [expander.label for expander in app.expander]
    assert "View full plain-language summary" in expander_labels
    full_summary = "\n".join(
        value
        for value in markup
        if "second positive contributor" in value
        or "major positive product signal" in value
        or "negative product signals" in value
        or "management attributed" in value
    )
    assert "Productivity and Business Processes" in full_summary
    assert "Azure was a major positive product signal" in full_summary
    assert "Windows OEM and Devices and Xbox content and services" in full_summary
    assert "Microsoft management attributed" in full_summary


def test_metric_guide_renders_every_definition() -> None:
    app = AppTest.from_file("app.py").run(timeout=20)
    assert not app.exception
    rendered = "\n".join(str(markdown.value) for markdown in app.markdown)
    for label in (
        "Revenue", "Gross profit", "Operating income", "Net income",
        "QoQ growth", "YoY growth", "Gross margin", "Operating margin",
        "Net margin", "Segment contribution", "Headwind",
    ):
        assert label in rendered


def test_enabled_azure_provider_runs_only_after_explicit_submission(
    monkeypatch,
) -> None:
    from src.ai import qa_azure

    context = build_grounding_context(
        load_financial_datasets(),
        "FY2026-Q4",
    )
    revenue = next(
        figure
        for figure in context.current_period.figures
        if figure.metric.value == "revenue"
    )
    response = GroundedAnswer(
        reporting_period=context.requested_period,
        status="supported",
        answer="The approved quarterly revenue figure is shown in the current context.",
        claims=(
            GroundedAnswerClaim(
                metric="revenue",
                classification=QAClassification.REPORTED_FACT,
                value=Decimal(revenue.value),
                unit=FigureUnit.USD,
                source_ids=(revenue.source_id,),
            ),
        ),
        metric_names=("revenue",),
        source_ids=(revenue.source_id,),
        suggested_investigation_areas=(),
    )

    class Provider:
        calls = 0

        def generate_answer(self, prompt) -> str:
            self.calls += 1
            return response.model_dump_json()

    provider = Provider()
    monkeypatch.setenv("ENABLE_AZURE_QA", "true")
    monkeypatch.setattr(
        qa_azure.AzureQAProvider,
        "from_environment",
        lambda: provider,
    )

    app = AppTest.from_file("app.py").run(timeout=20)
    assert not app.exception
    assert provider.calls == 0

    app.text_area[0].set_value("Summarize the approved revenue figure.")
    navigation = app.button_group[0]
    navigation.set_value(
        "Executive Overview"
        if all(isinstance(option, str) for option in navigation.options)
        else ["Executive Overview"]
    )
    submit = next(button for button in app.button if button.label == "Ask the Platform")
    submit.click().run(timeout=20)

    assert not app.exception
    assert provider.calls == 1
    rendered = "\n".join(str(markdown.value) for markdown in app.markdown)
    assert "Grounded AI answer" in rendered
    assert revenue.source_id in rendered
