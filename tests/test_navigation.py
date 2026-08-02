"""Streamlit navigation behavior and safety tests."""

import socket

import pytest
from streamlit.testing.v1 import AppTest

from app import APP_CSS, PAGE_OPTIONS


def _rendered_markup(app: AppTest) -> str:
    return "\n".join(str(markdown.value) for markdown in app.markdown)


def _option_labels(navigation: object) -> tuple[str, ...]:
    """Normalize Streamlit AppTest options across supported releases."""
    return tuple(
        str(getattr(option, "content", option))
        for option in navigation.options
    )


def _select_page(navigation: object, page_name: str) -> None:
    """Set one segmented-control value across supported AppTest releases."""
    if all(isinstance(option, str) for option in navigation.options):
        navigation.set_value(page_name)
    else:
        # Streamlit 1.45 AppTest represents options as protobuf objects and its
        # button-group state serializer still expects a one-item collection.
        navigation.set_value([page_name])


def test_navigation_renders_complete_labels_and_identifiable_active_page() -> None:
    app = AppTest.from_file("app.py").run(timeout=20)

    assert not app.exception
    assert len(app.button_group) == 1
    navigation = app.button_group[0]
    assert _option_labels(navigation) == PAGE_OPTIONS
    assert navigation.value == "Executive Overview"
    assert '[aria-checked="true"]' in APP_CSS
    assert 'content: "Active"' in APP_CSS


@pytest.mark.parametrize(
    ("page_name", "expected_heading"),
    (
        ("Executive Overview", "Microsoft Financial Intelligence Platform"),
        ("Quarterly Performance", "Quarterly Performance"),
        ("Historical Trends", "Historical Trends"),
    ),
)
def test_selecting_navigation_label_loads_correct_page_without_network(
    page_name: str,
    expected_heading: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.ai import azure_provider

    def forbidden_call(*args: object, **kwargs: object) -> None:
        raise AssertionError("Streamlit navigation must not use the network")

    monkeypatch.setattr(
        azure_provider.AzureOpenAIProvider,
        "__init__",
        forbidden_call,
    )
    monkeypatch.setattr(socket.socket, "connect", forbidden_call)

    app = AppTest.from_file("app.py").run(timeout=20)
    _select_page(app.button_group[0], page_name)
    app.run(timeout=20)

    assert not app.exception
    assert app.button_group[0].value == page_name
    assert f"<h1>{expected_heading}</h1>" in _rendered_markup(app)
