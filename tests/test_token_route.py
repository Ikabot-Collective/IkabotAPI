import pytest
from fastapi.testclient import TestClient

from tests.token_validator import verify_token_format


def test_v1_token_route_without_user_agent_should_return_422(client: TestClient):
    """Test that missing user_agent parameter returns 422 (FastAPI validation error)"""
    response = client.get("/v1/token")
    assert response.status_code == 422
    response_json = response.json()
    assert "detail" in response_json


def test_v1_token_route_with_empty_user_agent_should_return_400(client: TestClient):
    """Test that empty user_agent returns 400"""
    response = client.get("/v1/token?user_agent=")
    assert response.status_code == 400
    response_json = response.json()
    assert "detail" in response_json
    assert "Empty user_agent" in response_json["detail"]


def test_v1_token_route_with_unsupported_user_agent_should_return_400(
    client: TestClient,
):
    """Test that unsupported user_agent returns 400"""
    user_agent = "Unsupported User Agent"
    response = client.get(f"/v1/token?user_agent={user_agent}")
    assert response.status_code == 400
    response_json = response.json()
    assert "detail" in response_json
    assert "Unsupported user_agent" in response_json["detail"]


def test_v1_token_route_with_supported_user_agent_should_return_200(client: TestClient):
    """Test that supported user_agent returns 200 with valid token response"""
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.3"
    response = client.get(f"/v1/token?user_agent={user_agent}")
    assert response.status_code == 200

    token_response = response.json()
    assert token_response["status"] == "success"
    assert "token" in token_response
    assert token_response["user_agent"] == user_agent
    assert "timestamp" in token_response

    # Verify token format using existing validator
    verify_token_format(token_response["token"])
