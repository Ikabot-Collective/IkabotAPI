import pytest

from src.token.TokenGenerator import TokenGenerator


@pytest.fixture
def token_generator():
    generator = TokenGenerator()
    yield generator
    generator.driver.quit()


def test_token_not_empty(token_generator):
    token = token_generator.get_token()
    assert token is not None, "Token should not be None"
    assert token != "", "Token should not be an empty string"


def test_tokens_are_unique(token_generator):
    tokens = [token_generator.get_token() for _ in range(5)]

    for i, token1 in enumerate(tokens):
        for j, token2 in enumerate(tokens):
            if i != j:
                assert token1 != token2, "Tokens should be unique"


def test_token_characteristics(token_generator):
    token = token_generator.get_token()
    assert isinstance(token, str), "Token should be a string"
    assert " " not in token, "Token should not contain any whitespace"
    assert any(c.isupper() for c in token) and any(
        c.islower() for c in token
    ), "The string must contain both uppercase and lowercase letters."
    assert any(c.isdigit() for c in token), "The string must contain digits."
