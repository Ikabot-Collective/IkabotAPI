import json
import os
import time

import pytest
from pytest_mock import MockerFixture

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
        supported_user_agents=supported_user_agents, cache_ttl=60
    )
    yield token_generator


@pytest.fixture
def token_generator_no_cache():
    json_file_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "apps", "token", "SupportedUserAgents.json"
        )
    )
    supported_user_agents = json.load(open(json_file_path))
    token_generator = TokenGenerator(
        supported_user_agents=supported_user_agents, cache_ttl=0
    )
    yield token_generator


def test_get_token_returns_unique_tokens(token_generator):
    tokens = [token_generator.get_token() for _ in range(5)]
    assert len(set(tokens)) == len(tokens), "Tokens should be unique"


def test_get_token_returns_unique_tokens_with_specific_user_agent(token_generator_no_cache):
    tokens = [
        token_generator_no_cache.get_token(
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


def test_cache_returns_same_token_for_same_user_agent(token_generator):
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.3"
    token1 = token_generator.get_token(user_agent=ua)
    token2 = token_generator.get_token(user_agent=ua)
    assert token1 == token2, "Cached token should be returned for the same user_agent"


def test_cache_returns_different_tokens_for_different_user_agents(token_generator):
    ua1 = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.3"
    ua2 = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.3"
    token1 = token_generator.get_token(user_agent=ua1)
    token2 = token_generator.get_token(user_agent=ua2)
    assert token1 != token2, "Different user agents should produce different tokens"


def test_cache_does_not_apply_without_user_agent(token_generator):
    token1 = token_generator.get_token()
    token2 = token_generator.get_token()
    assert token1 != token2, "Tokens without user_agent should not be cached"


def test_cache_expires_after_ttl():
    json_file_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "apps", "token", "SupportedUserAgents.json"
        )
    )
    supported_user_agents = json.load(open(json_file_path))
    tg = TokenGenerator(supported_user_agents=supported_user_agents, cache_ttl=1)
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.3"
    token1 = tg.get_token(user_agent=ua)
    time.sleep(1.1)
    token2 = tg.get_token(user_agent=ua)
    assert token1 != token2, "Token should be regenerated after cache TTL expires"
