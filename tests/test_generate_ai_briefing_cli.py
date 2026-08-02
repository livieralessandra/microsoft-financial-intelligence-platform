"""Tests for the explicit, offline Azure briefing generation command."""

from pathlib import Path

import pytest

import python.generate_ai_briefing as cli
from src.ai.prompting import BriefingPrompt
from src.ai.schemas import ExecutiveBriefing
from src.data_loader import FinancialDatasets


ENVIRONMENT = {
    "AZURE_OPENAI_ENDPOINT": "https://finance-ai.openai.azure.com",
    "AZURE_OPENAI_API_KEY": "private-test-value",
    "AZURE_OPENAI_DEPLOYMENT": "executive-briefing-deployment",
}


class FakeProvider:
    def __init__(self, briefing: ExecutiveBriefing) -> None:
        self.briefing = briefing
        self.calls = 0

    def generate(self, prompt: BriefingPrompt) -> str:
        self.calls += 1
        return self.briefing.model_dump_json()


def test_dry_run_does_not_construct_provider_or_write(
    tmp_path: Path,
    financial_datasets: FinancialDatasets,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def forbidden_factory(config: object) -> object:
        raise AssertionError("dry-run must not construct a network provider")

    result = cli.run(
        ["--period", "FY2026-Q4", "--dry-run", "--output-dir", str(tmp_path)],
        environment=ENVIRONMENT,
        datasets_loader=lambda: financial_datasets,
        provider_factory=forbidden_factory,
    )
    output = capsys.readouterr()
    assert result == 0
    assert "Requested reporting period: FY2026-Q4" in output.out
    assert "Validation success: dry run completed" in output.out
    assert "private-test-value" not in output.out + output.err
    assert not list(tmp_path.iterdir())


def test_refuses_existing_file_without_replace_before_provider_call(
    tmp_path: Path,
    financial_datasets: FinancialDatasets,
    complete_briefing: ExecutiveBriefing,
) -> None:
    destination = tmp_path / "FY2026-Q4.json"
    destination.write_text("existing")
    provider = FakeProvider(complete_briefing)
    result = cli.run(
        ["--period", "FY2026-Q4", "--output-dir", str(tmp_path)],
        environment=ENVIRONMENT,
        datasets_loader=lambda: financial_datasets,
        provider_factory=lambda config: provider,
    )
    assert result == cli.EXIT_EXISTS
    assert provider.calls == 0
    assert destination.read_text() == "existing"


def test_successful_mocked_generation_and_atomic_persistence(
    tmp_path: Path,
    financial_datasets: FinancialDatasets,
    complete_briefing: ExecutiveBriefing,
    capsys: pytest.CaptureFixture[str],
) -> None:
    provider = FakeProvider(complete_briefing)
    result = cli.run(
        ["--period", "FY2026-Q4", "--output-dir", str(tmp_path)],
        environment=ENVIRONMENT,
        datasets_loader=lambda: financial_datasets,
        provider_factory=lambda config: provider,
    )
    output = capsys.readouterr().out
    destination = tmp_path / "FY2026-Q4.json"
    assert result == 0
    assert provider.calls == 1
    assert ExecutiveBriefing.model_validate_json(destination.read_text()) == (
        complete_briefing
    )
    assert not list(tmp_path.glob("*.tmp"))
    assert "Validation success: briefing approved" in output
    assert "Insight count: 6" in output
    assert "private-test-value" not in output


def test_replace_validates_then_replaces_existing_file(
    tmp_path: Path,
    financial_datasets: FinancialDatasets,
    complete_briefing: ExecutiveBriefing,
) -> None:
    destination = tmp_path / "FY2026-Q4.json"
    destination.write_text("old briefing")
    result = cli.run(
        [
            "--period",
            "FY2026-Q4",
            "--replace",
            "--output-dir",
            str(tmp_path),
        ],
        environment=ENVIRONMENT,
        datasets_loader=lambda: financial_datasets,
        provider_factory=lambda config: FakeProvider(complete_briefing),
    )
    assert result == 0
    assert ExecutiveBriefing.model_validate_json(destination.read_text()) == (
        complete_briefing
    )


def test_configuration_failure_is_nonzero_and_secret_safe(
    financial_datasets: FinancialDatasets,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = cli.run(
        ["--period", "FY2026-Q4", "--dry-run"],
        environment={"AZURE_OPENAI_API_KEY": "do-not-disclose"},
        datasets_loader=lambda: financial_datasets,
    )
    output = capsys.readouterr()
    assert result == cli.EXIT_CONFIGURATION
    assert "do-not-disclose" not in output.out + output.err


def test_unavailable_driver_context_is_nonzero(
    tmp_path: Path,
    financial_datasets: FinancialDatasets,
) -> None:
    result = cli.run(
        ["--period", "FY2026-Q3", "--dry-run", "--output-dir", str(tmp_path)],
        environment=ENVIRONMENT,
        datasets_loader=lambda: financial_datasets,
    )
    assert result == cli.EXIT_GROUNDING


def test_provider_or_validation_failure_is_nonzero(
    tmp_path: Path,
    financial_datasets: FinancialDatasets,
) -> None:
    class InvalidProvider:
        def generate(self, prompt: BriefingPrompt) -> str:
            return "{malformed"

    result = cli.run(
        ["--period", "FY2026-Q4", "--output-dir", str(tmp_path)],
        environment=ENVIRONMENT,
        datasets_loader=lambda: financial_datasets,
        provider_factory=lambda config: InvalidProvider(),
    )
    assert result == cli.EXIT_GENERATION
    assert not list(tmp_path.iterdir())


def test_storage_failure_is_nonzero(
    tmp_path: Path,
    financial_datasets: FinancialDatasets,
    complete_briefing: ExecutiveBriefing,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_storage(*args: object, **kwargs: object) -> object:
        raise cli.BriefingStorageError("Storage unavailable.")

    monkeypatch.setattr(cli, "save_briefing", fail_storage)
    result = cli.run(
        ["--period", "FY2026-Q4", "--output-dir", str(tmp_path)],
        environment=ENVIRONMENT,
        datasets_loader=lambda: financial_datasets,
        provider_factory=lambda config: FakeProvider(complete_briefing),
    )
    assert result == cli.EXIT_STORAGE
    assert not list(tmp_path.iterdir())


def test_streamlit_rendering_never_constructs_azure_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from streamlit.testing.v1 import AppTest
    from src.ai import azure_provider

    def forbidden_init(*args: object, **kwargs: object) -> None:
        raise AssertionError("Streamlit must not construct Azure providers")

    monkeypatch.setattr(azure_provider.AzureOpenAIProvider, "__init__", forbidden_init)
    app = AppTest.from_file("app.py").run(timeout=20)
    assert not app.exception
