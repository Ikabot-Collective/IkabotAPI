import json
import os

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
    token_generator = TokenGenerator(supported_user_agents=supported_user_agents)
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
