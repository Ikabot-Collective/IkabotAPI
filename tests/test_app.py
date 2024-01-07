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
