import json

import pytest

from apps import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True})

    with app.test_client() as client:
        yield client


def test_get_new_token_should_return_status_code_ok(client):
    response = client.get("/new_token")
    assert response.status_code == 200


def test_get_new_token_should_return_a_json(client):
    response = client.get("/new_token")
    try:
        json.loads(response.data)
    except ValueError as e:
        raise AssertionError(f"The response is not a valid JSON: {e}")


def test_token_not_empty(client):
    data = client.get("/new_token").data
    token = json.loads(data)
    assert token is not None, "Token should not be None"
    assert token != "", "Token should not be an empty string"


def test_tokens_are_unique(client):
    tokens = [client.get("/new_token").data for _ in range(5)]
    assert len(set(tokens)) == len(tokens), "Tokens should be unique"


def test_token_characteristics(client):
    data = client.get("/new_token").data
    token = json.loads(data)
    assert " " not in token, "Token should not contain any whitespace"
    assert any(c.isupper() for c in token), "The string must contain uppercase letters."
    assert any(c.islower() for c in token), "The string must contain lowercase letters."
    assert any(c.isdigit() for c in token), "The string must contain digits."
