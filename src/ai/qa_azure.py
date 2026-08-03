"""Explicit-submit Azure adapter for structured grounded Q&A."""

from __future__ import annotations

from typing import Callable, Mapping

from openai import OpenAI

from src.ai.azure_provider import (
    AzureOpenAIConfig,
    AzureProviderRequestError,
    AzureProviderRefusalError,
)
from src.ai.qa import QAPrompt
from src.ai.schemas import GroundedAnswer


class AzureQAProvider:
    """Request one bounded answer with no tools, storage, or retries."""

    def __init__(
        self,
        config: AzureOpenAIConfig,
        *,
        client: object | None = None,
        client_factory: Callable[..., object] = OpenAI,
    ) -> None:
        self._config = config
        self._client = client or client_factory(
            api_key=config.api_key,
            base_url=config.endpoint,
            timeout=config.timeout_seconds,
            max_retries=0,
        )

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str] | None = None,
    ) -> AzureQAProvider:
        return cls(AzureOpenAIConfig.from_environment(environment))

    def generate_answer(self, prompt: QAPrompt) -> str:
        """Generate strict JSON only after an explicit caller invocation."""
        request = {
            "model": self._config.deployment,
            "input": [
                {"role": "system", "content": prompt.system_instructions},
                {
                    "role": "user",
                    "content": (
                        f"QUESTION\n{prompt.question}\n\n"
                        f"APPROVED CONTEXT\n{prompt.approved_context_json}\n\n"
                        f"PRIOR SESSION TURNS\n{prompt.history_json}\n\n"
                        f"OUTPUT SCHEMA\n{prompt.output_schema_json}"
                    ),
                },
            ],
            "store": False,
            "tools": [],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "grounded_financial_answer",
                    "schema": GroundedAnswer.model_json_schema(),
                    "strict": True,
                }
            },
            "max_output_tokens": 1800,
        }
        try:
            response = self._client.responses.create(**request)
            output = getattr(response, "output_text", None)
            if not isinstance(output, str) or not output.strip():
                raise AzureProviderRefusalError(
                    "Azure returned no structured answer."
                )
            return output
        except AzureProviderRefusalError:
            raise
        except Exception as error:
            raise AzureProviderRequestError(
                "Azure OpenAI Q&A request failed."
            ) from error
