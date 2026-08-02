"""Provider-neutral contract for future structured-output model adapters."""

from typing import Protocol, runtime_checkable

from src.ai.prompting import BriefingPrompt


@runtime_checkable
class BriefingProvider(Protocol):
    """A model provider that returns one structured JSON briefing."""

    def generate(self, prompt: BriefingPrompt) -> str:
        """Return an ExecutiveBriefing JSON document for the prompt."""
        ...
