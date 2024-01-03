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
        yield client, token_generator

    token_generator.driver.quit()


def test_get_new_token_should_return_status_code_ok(client):
    flask_client, _ = client
    response = flask_client.get("/new_token")
    assert response.status_code == 200


def test_get_new_token_should_return_a_json(client):
    flask_client, _ = client
    response = flask_client.get("/new_token")
    try:
        json.loads(response.data)
    except ValueError as e:
        raise AssertionError(f"The response is not a valid JSON: {e}")


@pytest.mark.parametrize(
    "exception", [Exception("Test exception"), Exception("Another test exception")]
)
def test_get_new_token_with_exception_should_return_status_code_500(
    client, mocker, exception
):
    mocker.patch(
        "src.token.TokenGenerator.TokenGenerator.get_token", side_effect=exception
    )
    flask_client, _ = client
    response = flask_client.get("/new_token")
    assert response.status_code == 500
