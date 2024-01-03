import json

import pytest

from app import create_app
from src.token.clean_up_driver_processes import clean_up_driver_processes
from src.token.TokenGenerator import TokenGenerator


@pytest.fixture
def client():
    clean_up_driver_processes()
    token_generator = TokenGenerator()
    app = create_app({"TESTING": True}, token_generator)
    with app.test_client() as client:
        yield client


def test_root_should_status_code_ok(client):
    response = client.get("/")
    assert response.status_code == 200


def test_new_token_should_status_code_ok(client):
    response = client.get("/new_token")
    assert response.status_code == 200


def test_new_token_should_return_a_json(client):
    response = client.get("/new_token")
    try:
        json.loads(response.data)
    except ValueError as e:
        raise AssertionError(f"The response is not a valid JSON: {e}")
