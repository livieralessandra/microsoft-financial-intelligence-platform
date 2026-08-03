"""Tests for the explicit-submit Azure grounded-Q&A adapter."""

from types import SimpleNamespace

from src.ai.azure_provider import AzureOpenAIConfig
from src.ai.qa import build_qa_prompt
from src.ai.qa_azure import AzureQAProvider
from src.ai.grounding import build_grounding_context


def test_azure_qa_adapter_uses_bounded_tool_free_request(financial_datasets) -> None:
    context = build_grounding_context(financial_datasets, "FY2026-Q4")
    calls = []
    construction = {}

    class Responses:
        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(output_text='{"status":"insufficient_context"}')

    def client_factory(**kwargs):
        construction.update(kwargs)
        return SimpleNamespace(responses=Responses())

    provider = AzureQAProvider(
        AzureOpenAIConfig(
            endpoint="https://example.openai.azure.com/openai/v1/",
            api_key="not-a-real-secret",
            deployment="test-deployment",
            timeout_seconds=12.0,
        ),
        client_factory=client_factory,
    )
    output = provider.generate_answer(build_qa_prompt("Custom question", context))

    assert output == '{"status":"insufficient_context"}'
    assert construction["timeout"] == 12.0
    assert construction["max_retries"] == 0
    assert calls[0]["tools"] == []
    assert calls[0]["store"] is False
    assert calls[0]["max_output_tokens"] == 1800
    assert calls[0]["text"]["format"]["strict"] is True
