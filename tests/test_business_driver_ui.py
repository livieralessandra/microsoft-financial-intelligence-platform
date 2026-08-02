"""Tests for deterministic approved business-driver presentation."""

import socket

from streamlit.testing.v1 import AppTest

from src.ai.business_drivers import load_business_driver_context
from src.business_driver_ui import build_business_driver_presentation


def test_fy2026_q4_driver_presentation_is_ranked_and_classified() -> None:
    context = load_business_driver_context("FY2026-Q4")
    presentation = build_business_driver_presentation(context)

    assert presentation is not None
    assert presentation.positive_contributors[0].segment == "Intelligent Cloud"
    assert presentation.positive_contributors[0].revenue_change == "+$9.428B"
    assert presentation.positive_contributors[0].contribution == "69.50%"
    assert presentation.positive_contributors[0].classification == "DERIVED"
    assert presentation.positive_contributors[1].segment == (
        "Productivity and Business Processes"
    )
    assert presentation.positive_contributors[1].revenue_change == "+$4.735B"
    assert presentation.headwinds[0].segment == "More Personal Computing"
    assert presentation.headwinds[0].revenue_change == "-$0.597B"
    assert presentation.headwinds[0].contribution == "-4.40%"


def test_reported_product_signals_and_management_attribution() -> None:
    context = load_business_driver_context("FY2026-Q4")
    presentation = build_business_driver_presentation(context)

    assert presentation is not None
    signals = {signal.label: signal for signal in presentation.signals}
    assert signals["Azure and other cloud services revenue growth"].value == "+43%"
    assert signals["Xbox content and services growth"].value == "-10%"
    assert signals["Windows OEM and Devices growth"].value == "-7%"
    assert signals["Microsoft 365 Copilot paid seats"].value == (
        "More than 30 million"
    )
    assert all(signal.classification == "REPORTED" for signal in signals.values())
    assert len(presentation.explanations) == 6
    assert all(
        explanation.attribution == "Microsoft management"
        for explanation in presentation.explanations
    )
    assert any(
        "Azure demand continued to exceed available capacity"
        in explanation.statement
        for explanation in presentation.explanations
    )


def test_missing_packet_produces_no_driver_presentation(tmp_path) -> None:
    context = load_business_driver_context("FY2025-Q3", tmp_path)
    assert build_business_driver_presentation(context) is None


def test_executive_overview_renders_approved_drivers_without_azure(
    monkeypatch,
) -> None:
    from src.ai import azure_provider

    def forbidden_init(*args: object, **kwargs: object) -> None:
        raise AssertionError("Streamlit must not construct an Azure provider")

    monkeypatch.setattr(
        azure_provider.AzureOpenAIProvider,
        "__init__",
        forbidden_init,
    )
    app = AppTest.from_file("app.py").run(timeout=20)
    assert not app.exception
    rendered = "\n".join(str(markdown.value) for markdown in app.markdown)
    assert "Performance Drivers and Headwinds" in rendered
    assert "Approved Microsoft-reported indicators and derived segment contributions." in rendered
    assert "Intelligent Cloud" in rendered
    assert "More Personal Computing" in rendered
    assert "+43%" in rendered
    assert "Azure and other cloud services revenue growth" in rendered
    assert "-10%" in rendered
    assert "Xbox content and services growth" in rendered
    assert "Windows OEM and Devices growth" in rendered
    assert "DERIVED" in rendered
    assert "REPORTED" in rendered
    assert "Microsoft management explanation" in rendered
    assert "Microsoft FY2026 Q4 Earnings Release" in rendered
    assert "Microsoft FY2026 Q4 Earnings Metrics" in rendered
    assert "Microsoft FY2026 Q4 Earnings Conference Call" in rendered


def test_executive_overview_renders_approved_source_section_without_calls(
    monkeypatch,
) -> None:
    """Regress undefined briefing references in driver-source rendering."""
    from src.ai import azure_provider

    def forbidden_call(*args: object, **kwargs: object) -> None:
        raise AssertionError("Streamlit rendering must not make external calls")

    monkeypatch.setattr(
        azure_provider.AzureOpenAIProvider,
        "__init__",
        forbidden_call,
    )
    monkeypatch.setattr(socket.socket, "connect", forbidden_call)

    app = AppTest.from_file("app.py").run(timeout=20)

    assert not app.exception
    rendered = "\n".join(str(markdown.value) for markdown in app.markdown)
    assert "Official sources" in rendered
    assert "Microsoft FY2026 Q4 Earnings Release" in rendered
    assert "msft_ir_fy2026_q4_press_release" in rendered
    assert (
        "https://www.microsoft.com/en-us/investor/earnings/"
        "fy-2026-q4/press-release-webcast"
    ) in rendered
    assert "Microsoft FY2026 Q4 Earnings Metrics" in rendered
    assert "msft_ir_fy2026_q4_metrics" in rendered
    assert "Microsoft FY2026 Q4 Earnings Conference Call" in rendered
    assert "msft_ir_fy2026_q4_earnings_call" in rendered
