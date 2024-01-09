import pytest

from app.token.TokenGenerator import TokenGenerator


@pytest.fixture
def token_generator():
    token_generator = TokenGenerator()
    yield token_generator


def test_token_not_empty(token_generator):
    token = token_generator.get_token()
    assert token is not None, "Token should not be None"
    assert token != "", "Token should not be an empty string"


def test_tokens_are_unique(token_generator):
    tokens = [token_generator.get_token() for _ in range(5)]
    assert len(set(tokens)) == len(tokens), "Tokens should be unique"


def test_token_characteristics(token_generator):
    token = token_generator.get_token()
    assert isinstance(token, str), "Token should be a string"
    assert " " not in token, "Token should not contain any whitespace"
    assert any(c.isupper() for c in token), "The string must contain uppercase letters."
    assert any(c.islower() for c in token), "The string must contain lowercase letters."
    assert any(c.isdigit() for c in token), "The string must contain digits."
