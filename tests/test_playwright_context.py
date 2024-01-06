import pytest

from src.token.PlaywrightContext import PlaywrightContext


@pytest.fixture(scope="function")
def playwright_context():
    with PlaywrightContext() as context:
        yield context


def test_playwright_context_initialization(playwright_context: PlaywrightContext):
    assert playwright_context.loop is not None
    assert playwright_context.playwright is not None
    assert playwright_context.browser is not None
    playwright_context.close_and_stop()


def test_enter_and_exit_context():
    with PlaywrightContext() as context:
        assert isinstance(context, PlaywrightContext)
    context.close_and_stop()


def test_close_and_stop(playwright_context: PlaywrightContext):
    playwright_context.close_and_stop()
    assert playwright_context.playwright is None
    assert playwright_context.browser is None
    assert playwright_context.loop.is_closed()


def test_context_reusability(playwright_context: PlaywrightContext):
    # Ensure the context can be reused
    with playwright_context:
        assert playwright_context.loop is not None
        assert playwright_context.playwright is not None
        assert playwright_context.browser is not None

    playwright_context.close_and_stop()
