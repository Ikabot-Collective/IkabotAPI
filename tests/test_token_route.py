import json
import token

import pytest
from pytest_mock import MockerFixture

from apps import create_app
from tests.token_validator import verify_token_format


@pytest.fixture
def client():
    app = create_app({"TESTING": True})

    with app.test_client() as client:
        yield client


def test_token_should_return_status_code_200_even_on_error(client):
    """
    Test that the /token route returns status code 200.
    Note: This test reflects the behavior where the route may return status code 200 even if there is an error.
    """
    response = client.get("/token")
    assert response.status_code == 200


def test_v1_token_route_without_user_agent_should_return_400(client):
    response = client.get("/v1/token")
    assert response.status_code == 400
    response_json = json.loads(response.data)
    assert response_json["status"] == "error"
    assert response_json["message"] == "Bad Request: Missing user_agent query parameter"


def test_v1_token_route_with_empty_user_agent_should_return_400(client):
    user_agent = ""
    response = client.get(f"/v1/token?user_agent={user_agent}")
    assert response.status_code == 400
    response_json = json.loads(response.data)
    assert response_json["status"] == "error"
    assert response_json["message"] == "Bad Request: Empty user_agent query parameter"


def test_v1_token_route_with_unsupported_user_agent_should_return_400(client):
    user_agent = "Unsupported User Agent"
    response = client.get(f"/v1/token?user_agent={user_agent}")
    assert response.status_code == 400
    response_json = json.loads(response.data)
    assert response_json["status"] == "error"
    assert (
        response_json["message"]
        == "Bad Request: Unsupported user_agent query parameter"
    )


def test_v1_token_route_with_supported_user_agent_should_return_200(client):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.3"
    response = client.get(f"/v1/token?user_agent={user_agent}")
    assert response.status_code == 200
    token = json.loads(response.data)
    verify_token_format(token)


def test_v1_token_route_error(client, mocker: MockerFixture):
    mocker.patch(
        "apps.token.TokenGenerator.get_token",
        side_effect=Exception("Test Exception"),
    )

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.3"
    response = client.get(f"/v1/token?user_agent={user_agent}")
    assert response.status_code == 500
