"""Mocked tests for the Azure OpenAI v1 provider adapter."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.ai.azure_provider import (
    AzureConfigurationError,
    AzureOpenAIConfig,
    AzureOpenAIProvider,
    AzureProviderRefusalError,
    AzureProviderRequestError,
    AzureStructuredOutputError,
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
    normalize_azure_v1_endpoint,
)
from src.ai.prompting import BriefingPrompt
from src.ai.schemas import ExecutiveBriefing


ENVIRONMENT = {
    "AZURE_OPENAI_ENDPOINT": "https://finance-ai.openai.azure.com",
    "AZURE_OPENAI_API_KEY": "private-test-value",
    "AZURE_OPENAI_DEPLOYMENT": "executive-briefing-deployment",
}
PROMPT = BriefingPrompt(
    system_instructions="System instructions",
    approved_context_json='{"approved": true}',
    output_schema_json='{"type": "object"}',
)


@pytest.mark.parametrize(
    ("endpoint", "expected"),
    [
        (
            "https://finance-ai.openai.azure.com",
            "https://finance-ai.openai.azure.com/openai/v1/",
        ),
        (
            "https://finance-ai.openai.azure.com/",
            "https://finance-ai.openai.azure.com/openai/v1/",
        ),
        (
            "https://finance-ai.openai.azure.com/openai/v1/",
            "https://finance-ai.openai.azure.com/openai/v1/",
        ),
    ],
)
def test_endpoint_normalization(endpoint: str, expected: str) -> None:
    assert normalize_azure_v1_endpoint(endpoint) == expected


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://finance-ai.openai.azure.com",
        "https://user:password@finance-ai.openai.azure.com",
        "https://finance-ai.openai.azure.com?api-version=secret",
    ],
)
def test_endpoint_rejects_unsafe_values(endpoint: str) -> None:
    with pytest.raises(AzureConfigurationError):
        normalize_azure_v1_endpoint(endpoint)


def test_missing_configuration_lists_only_variable_names() -> None:
    with pytest.raises(AzureConfigurationError) as raised:
        AzureOpenAIConfig.from_environment(
            {"AZURE_OPENAI_API_KEY": "do-not-disclose"}
        )
    message = str(raised.value)
    assert "AZURE_OPENAI_ENDPOINT" in message
    assert "AZURE_OPENAI_DEPLOYMENT" in message
    assert "do-not-disclose" not in message


def test_client_uses_timeout_and_disables_retries() -> None:
    captured: dict = {}
    client = SimpleNamespace(responses=SimpleNamespace())

    def factory(**kwargs: object) -> object:
        captured.update(kwargs)
        return client

    AzureOpenAIProvider(
        AzureOpenAIConfig.from_environment(ENVIRONMENT),
        client_factory=factory,
    )
    assert captured == {
        "api_key": "private-test-value",
        "base_url": "https://finance-ai.openai.azure.com/openai/v1/",
        "timeout": DEFAULT_REQUEST_TIMEOUT_SECONDS,
        "max_retries": 0,
    }


def test_deployment_and_pydantic_schema_are_sent(
    complete_briefing: ExecutiveBriefing,
) -> None:
    captured: dict = {}

    class Responses:
        def parse(self, **kwargs: object) -> object:
            captured.update(kwargs)
            return SimpleNamespace(output_parsed=complete_briefing)

    provider = AzureOpenAIProvider(
        AzureOpenAIConfig.from_environment(ENVIRONMENT),
        client=SimpleNamespace(responses=Responses()),
    )
    assert ExecutiveBriefing.model_validate_json(provider.generate(PROMPT)) == (
        complete_briefing
    )
    assert captured["model"] == "executive-briefing-deployment"
    assert captured["text_format"] is ExecutiveBriefing
    assert captured["tools"] == []
    assert captured["store"] is False


def test_json_schema_fallback_is_strict(
    complete_briefing: ExecutiveBriefing,
) -> None:
    captured: dict = {}

    class Responses:
        def create(self, **kwargs: object) -> object:
            captured.update(kwargs)
            return SimpleNamespace(output_text=complete_briefing.model_dump_json())

    provider = AzureOpenAIProvider(
        AzureOpenAIConfig.from_environment(ENVIRONMENT),
        client=SimpleNamespace(responses=Responses()),
    )
    provider.generate(PROMPT)
    output_format = captured["text"]["format"]
    assert output_format["strict"] is True
    assert output_format["schema"] == ExecutiveBriefing.model_json_schema()


def test_provider_rejects_empty_or_refused_output() -> None:
    responses = SimpleNamespace(parse=lambda **kwargs: SimpleNamespace(output_parsed=None))
    provider = AzureOpenAIProvider(
        AzureOpenAIConfig.from_environment(ENVIRONMENT),
        client=SimpleNamespace(responses=responses),
    )
    with pytest.raises(AzureProviderRefusalError, match="no structured briefing"):
        provider.generate(PROMPT)


def test_provider_rejects_malformed_structured_output() -> None:
    responses = SimpleNamespace(
        parse=lambda **kwargs: SimpleNamespace(output_parsed={"unexpected": True})
    )
    provider = AzureOpenAIProvider(
        AzureOpenAIConfig.from_environment(ENVIRONMENT),
        client=SimpleNamespace(responses=responses),
    )
    with pytest.raises(AzureStructuredOutputError, match="malformed"):
        provider.generate(PROMPT)


def test_sdk_exception_is_wrapped_without_secret_text() -> None:
    def fail(**kwargs: object) -> object:
        raise RuntimeError("request failed with private-test-value")

    provider = AzureOpenAIProvider(
        AzureOpenAIConfig.from_environment(ENVIRONMENT),
        client=SimpleNamespace(responses=SimpleNamespace(parse=fail)),
    )
    with pytest.raises(AzureProviderRequestError) as raised:
        provider.generate(PROMPT)
    assert "private-test-value" not in str(raised.value)
