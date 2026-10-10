import json
import os

import pytest

import settings
from apps.token.TokenGenerator import TokenGenerator
from tests.token_validator import verify_token_format


@pytest.fixture
def token_generator():
    json_file_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "apps", "token", "SupportedUserAgents.json"
        )
    )
    supported_user_agents = json.load(open(json_file_path))
    token_generator = TokenGenerator(
        supported_user_agents=supported_user_agents,
    )
    yield token_generator


def test_get_token_returns_unique_tokens(token_generator):
    tokens = [token_generator.get_token() for _ in range(5)]
    assert len(set(tokens)) == len(tokens), "Tokens should be unique"


def test_get_token_returns_unique_tokens_with_specific_user_agent(token_generator):
    tokens = [
        token_generator.get_token(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        )
        for _ in range(5)
    ]
    assert len(set(tokens)) == len(tokens), "Tokens should be unique"


def test_get_token_returns_valid_token(token_generator):
    token = token_generator.get_token()
    verify_token_format(token)


def test_get_token_returns_valid_token_with_specific_user_agent(token_generator):
    token = token_generator.get_token(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    )
    verify_token_format(token)


def test_get_token_returns_valid_token_with_empty_user_agent(token_generator):
    token = token_generator.get_token(user_agent="")
    verify_token_format(token)


def test_get_token_passes_locale_and_timezone_to_generator(token_generator):
    captured = {}

    def fake_generate_token(user_agent, locale, timezone_id):
        captured["user_agent"] = user_agent
        captured["locale"] = locale
        captured["timezone_id"] = timezone_id
        return "ValidToken123"

    token_generator._generate_token = fake_generate_token

    token = token_generator.get_token(
        user_agent="Test User Agent",
        locale="es-ES",
        timezone_id="Europe/Madrid",
    )

    assert token == "ValidToken123"
    assert captured == {
        "user_agent": "Test User Agent",
        "locale": "es-ES",
        "timezone_id": "Europe/Madrid",
    }


def test_get_token_uses_default_locale_and_timezone(token_generator):
    captured = {}

    def fake_generate_token(user_agent, locale, timezone_id):
        captured["locale"] = locale
        captured["timezone_id"] = timezone_id
        return "ValidToken123"

    token_generator._generate_token = fake_generate_token

    token = token_generator.get_token(user_agent="Test User Agent")

    assert token == "ValidToken123"
    assert captured == {
        "locale": "en-GB",
        "timezone_id": "Europe/London",
    }


def test_get_token_reuses_browser_with_a_fresh_context_per_token(token_generator):
    token_generator.get_token()
    browser = token_generator._browser
    assert browser is not None

    contexts = []
    original_new_context = browser.new_context

    def spy_new_context(**kwargs):
        contexts.append(kwargs)
        return original_new_context(**kwargs)

    browser.new_context = spy_new_context

    first_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    second_ua = token_generator.supported_user_agents[0]
    first = token_generator.get_token(
        user_agent=first_ua, locale="es-AR", timezone_id="America/Argentina/Buenos_Aires"
    )
    second = token_generator.get_token(
        user_agent=second_ua, locale="en-GB", timezone_id="Europe/London"
    )

    assert token_generator._browser is browser, "Browser should be reused"
    assert first != second
    assert contexts == [
        {"user_agent": first_ua, "locale": "es-AR", "timezone_id": "America/Argentina/Buenos_Aires"},
        {"user_agent": second_ua, "locale": "en-GB", "timezone_id": "Europe/London"},
    ]


def test_get_token_relaunches_browser_after_recycle_limit(token_generator):
    token_generator.get_token()
    browser = token_generator._browser
    token_generator._served = settings.BROWSER_RECYCLE_AFTER

    verify_token_format(token_generator.get_token())

    assert token_generator._browser is not browser, "Browser should be relaunched"


def test_get_token_recovers_after_a_failed_token(token_generator):
    token_generator.get_token()
    browser = token_generator._browser

    def broken_new_context(**kwargs):
        raise RuntimeError("boom")

    browser.new_context = broken_new_context
    with pytest.raises(RuntimeError):
        token_generator.get_token()

    verify_token_format(token_generator.get_token())
    assert token_generator._browser is not browser
