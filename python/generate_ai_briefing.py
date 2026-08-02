"""Explicit offline command for validated Azure-generated briefings."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys
from typing import Callable, Mapping, Sequence

from streamlit.logger import get_logger


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

get_logger("streamlit.runtime.caching.cache_data_api").setLevel(
    logging.ERROR
)

from src.ai.azure_provider import (  # noqa: E402
    AzureConfigurationError,
    AzureOpenAIConfig,
    AzureOpenAIProvider,
)
from src.ai.business_drivers import BusinessDriverError  # noqa: E402
from src.ai.grounding import GroundingError, build_grounding_context  # noqa: E402
from src.ai.prompting import build_briefing_prompt  # noqa: E402
from src.ai.schemas import GroundingContext, ReportingPeriod  # noqa: E402
from src.ai.service import BriefingGenerationError, generate_executive_briefing  # noqa: E402
from src.ai.storage import (  # noqa: E402
    DEFAULT_BRIEFING_DIRECTORY,
    BriefingStorageError,
    briefing_path,
    save_briefing,
)
from src.data_loader import (  # noqa: E402
    DataValidationError,
    FinancialDatasets,
    load_financial_datasets,
)


EXIT_CONFIGURATION = 3
EXIT_GROUNDING = 4
EXIT_EXISTS = 5
EXIT_GENERATION = 6
EXIT_STORAGE = 7


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate one validated Azure executive briefing."
    )
    parser.add_argument("--period", required=True, help="Fiscal period, e.g. FY2026-Q4")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_BRIEFING_DIRECTORY,
    )
    return parser


def _source_count(context: GroundingContext) -> int:
    financial_sources = len(context.sources)
    drivers = context.business_drivers
    driver_sources = len(drivers.packet.sources) if drivers.packet is not None else 0
    return financial_sources + driver_sources


def run(
    argv: Sequence[str] | None = None,
    *,
    environment: Mapping[str, str] | None = None,
    datasets_loader: Callable[[], FinancialDatasets] = load_financial_datasets,
    provider_factory: Callable[
        [AzureOpenAIConfig], AzureOpenAIProvider
    ] = AzureOpenAIProvider,
) -> int:
    args = _parser().parse_args(argv)
    try:
        period = ReportingPeriod.parse(args.period)
        config = AzureOpenAIConfig.from_environment(environment)
    except (ValueError, AzureConfigurationError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_CONFIGURATION

    try:
        context = build_grounding_context(datasets_loader(), period)
        drivers = context.business_drivers
        if drivers is None or drivers.availability != "available":
            raise GroundingError(
                f"Approved business-driver context is unavailable for {period.identifier}."
            )
        build_briefing_prompt(context)
        destination = briefing_path(period, args.output_dir)
    except (DataValidationError, GroundingError, BusinessDriverError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_GROUNDING

    if args.dry_run:
        print(f"Requested reporting period: {period.identifier}")
        print("Validation success: dry run completed")
        print(f"Output path: {destination}")
        print(f"Source count: {_source_count(context)}")
        print("Insight count: 0")
        return 0

    if destination.exists() and not args.replace:
        print(
            "Error: A briefing already exists; pass --replace to replace it.",
            file=sys.stderr,
        )
        return EXIT_EXISTS

    try:
        provider = provider_factory(config)
        briefing = generate_executive_briefing(period, context, provider)
    except (AzureConfigurationError, BriefingGenerationError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_GENERATION
    except Exception:
        print("Error: Azure provider initialization failed.", file=sys.stderr)
        return EXIT_GENERATION

    try:
        output_path = save_briefing(briefing, context, args.output_dir)
    except BriefingStorageError as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_STORAGE

    print(f"Requested reporting period: {period.identifier}")
    print("Validation success: briefing approved")
    print(f"Output path: {output_path}")
    print(f"Source count: {len(briefing.source_ids)}")
    print(f"Insight count: {len(briefing.insights)}")
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
