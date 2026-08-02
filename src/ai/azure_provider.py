"""Azure OpenAI v1 adapter for provider-independent briefing generation."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Callable, Mapping, Protocol
from urllib.parse import urlsplit, urlunsplit

from openai import OpenAI
from pydantic import ValidationError

from src.ai.prompting import BriefingPrompt
from src.ai.schemas import ExecutiveBriefing


AZURE_ENVIRONMENT_VARIABLES = (
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_DEPLOYMENT",
)
DEFAULT_REQUEST_TIMEOUT_SECONDS = 60.0


class AzureConfigurationError(RuntimeError):
    """Raised when required Azure configuration is missing or invalid."""


class AzureProviderRequestError(RuntimeError):
    """Raised when Azure cannot complete a provider request."""


class AzureProviderRefusalError(RuntimeError):
    """Raised when Azure refuses or returns no structured output."""


class AzureStructuredOutputError(RuntimeError):
    """Raised when Azure output does not match the briefing schema."""


class _ResponsesAPI(Protocol):
    def create(self, **kwargs: object) -> object: ...


class _OpenAIClient(Protocol):
    responses: _ResponsesAPI


def normalize_azure_v1_endpoint(endpoint: str) -> str:
    """Normalize an Azure resource endpoint to its OpenAI v1 base URL."""
    candidate = endpoint.strip()
    parsed = urlsplit(candidate)
    if (
        parsed.scheme.lower() != "https"
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise AzureConfigurationError(
            "AZURE_OPENAI_ENDPOINT must be a valid HTTPS endpoint without "
            "credentials, query parameters, or fragments."
        )
    path = parsed.path.rstrip("/")
    if path.lower().endswith("/openai/v1"):
        path = path[: -len("/openai/v1")]
    normalized_path = f"{path}/openai/v1/"
    return urlunsplit(("https", parsed.netloc, normalized_path, "", ""))


@dataclass(frozen=True)
class AzureOpenAIConfig:
    """Secret-safe Azure OpenAI configuration."""

    endpoint: str
    api_key: str
    deployment: str
    timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT_SECONDS

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str] | None = None,
    ) -> AzureOpenAIConfig:
        values = os.environ if environment is None else environment
        missing = [
            name
            for name in AZURE_ENVIRONMENT_VARIABLES
            if not values.get(name, "").strip()
        ]
        if missing:
            raise AzureConfigurationError(
                "Missing required environment variables: " + ", ".join(missing) + "."
            )
        return cls(
            endpoint=normalize_azure_v1_endpoint(values["AZURE_OPENAI_ENDPOINT"]),
            api_key=values["AZURE_OPENAI_API_KEY"],
            deployment=values["AZURE_OPENAI_DEPLOYMENT"].strip(),
        )


def _prompt_input(prompt: BriefingPrompt) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": prompt.system_instructions},
        {
            "role": "user",
            "content": (
                "APPROVED CONTEXT\n"
                f"{prompt.approved_context_json}\n\n"
                "REQUIRED OUTPUT SCHEMA\n"
                f"{prompt.output_schema_json}"
            ),
        },
    ]


class AzureOpenAIProvider:
    """Generate structured briefings through Azure's OpenAI v1 endpoint."""

    def __init__(
        self,
        config: AzureOpenAIConfig,
        *,
        client: _OpenAIClient | None = None,
        client_factory: Callable[..., _OpenAIClient] = OpenAI,
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
    ) -> AzureOpenAIProvider:
        return cls(AzureOpenAIConfig.from_environment(environment))

    def generate(self, prompt: BriefingPrompt) -> str:
        """Request one structured response without tools, storage, or retries."""
        request = {
            "model": self._config.deployment,
            "input": _prompt_input(prompt),
            "store": False,
            "tools": [],
        }
        parse = getattr(self._client.responses, "parse", None)
        try:
            if callable(parse):
                response = parse(
                    **request,
                    text_format=ExecutiveBriefing,
                )
                parsed = getattr(response, "output_parsed", None)
                if parsed is None:
                    raise AzureProviderRefusalError(
                        "Azure returned no structured briefing."
                    )
                if isinstance(parsed, ExecutiveBriefing):
                    return parsed.model_dump_json()
                try:
                    return ExecutiveBriefing.model_validate(parsed).model_dump_json()
                except ValidationError as error:
                    raise AzureStructuredOutputError(
                        "Azure returned malformed structured output."
                    ) from error

            response = self._client.responses.create(
                **request,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "executive_briefing",
                        "schema": ExecutiveBriefing.model_json_schema(),
                        "strict": True,
                    }
                },
            )
            output_text = getattr(response, "output_text", None)
            if not isinstance(output_text, str) or not output_text.strip():
                raise AzureProviderRefusalError(
                    "Azure returned no structured briefing."
                )
            try:
                return ExecutiveBriefing.model_validate_json(output_text).model_dump_json()
            except (ValidationError, ValueError) as error:
                raise AzureStructuredOutputError(
                    "Azure returned malformed structured output."
                ) from error
        except (
            AzureProviderRefusalError,
            AzureStructuredOutputError,
        ):
            raise
        except Exception as error:
            raise AzureProviderRequestError(
                "Azure OpenAI request failed."
            ) from error
