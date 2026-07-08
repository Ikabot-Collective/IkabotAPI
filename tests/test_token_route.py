import pytest
from fastapi.testclient import TestClient

import apps.token.routes as token_routes
from tests.token_validator import verify_token_format


def test_v1_token_route_without_user_agent_should_return_200(client: TestClient):
    """Test that missing user_agent parameter returns 200 with random user agent"""
    response = client.get("/v1/token")
    assert response.status_code == 200
    
    # Returns the token string
    token_string = response.json()
    assert isinstance(token_string, str)
    assert len(token_string) > 0

    # Verify token format using existing validator
    verify_token_format(token_string)


def test_v1_token_route_with_empty_user_agent_should_return_200(client: TestClient):
    """Test that empty user_agent returns 200 with random user agent"""
    response = client.get("/v1/token?user_agent=")
    assert response.status_code == 200
    
    # Returns the token string
    token_string = response.json()
    assert isinstance(token_string, str)
    assert len(token_string) > 0

    # Verify token format using existing validator
    verify_token_format(token_string)


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

    # Returns the token string
    token_string = response.json()
    assert isinstance(token_string, str)
    assert len(token_string) > 0

    # Verify token format using existing validator
    verify_token_format(token_string)


def test_v1_token_route_passes_locale_and_timezone_to_token_generator(
    client: TestClient,
    monkeypatch,
):
    """Test that supported browser context params are passed to the generator"""
    captured = {}

    class FakeTokenGenerator:
        default_locale = "en-GB"
        default_timezone_id = "Europe/London"

        def get_token(self, user_agent=None, locale=None, timezone_id=None):
            captured["user_agent"] = user_agent
            captured["locale"] = locale
            captured["timezone_id"] = timezone_id
            return "ValidToken123"

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.3"
    monkeypatch.setattr(token_routes, "token_generator", FakeTokenGenerator())

    response = client.get(
        "/v1/token",
        params={
            "user_agent": user_agent,
            "locale": "es-ES",
            "timezone_id": "Europe/Madrid",
        },
    )

    assert response.status_code == 200
    assert response.json() == "ValidToken123"
    assert captured == {
        "user_agent": user_agent,
        "locale": "es-ES",
        "timezone_id": "Europe/Madrid",
    }


def test_v1_token_route_rejects_invalid_locale(client: TestClient, monkeypatch):
    """Test that clearly invalid locale values return 400"""

    class FakeTokenGenerator:
        default_locale = "en-GB"
        default_timezone_id = "Europe/London"

        def get_token(self, user_agent=None, locale=None, timezone_id=None):
            raise AssertionError("token generator should not be called")

    monkeypatch.setattr(token_routes, "token_generator", FakeTokenGenerator())

    response = client.get("/v1/token?locale=not a locale")

    assert response.status_code == 400
    assert "Unsupported locale" in response.json()["detail"]


def test_v1_token_route_rejects_invalid_timezone(client: TestClient, monkeypatch):
    """Test that clearly invalid timezone values return 400"""

    class FakeTokenGenerator:
        default_locale = "en-GB"
        default_timezone_id = "Europe/London"

        def get_token(self, user_agent=None, locale=None, timezone_id=None):
            raise AssertionError("token generator should not be called")

    monkeypatch.setattr(token_routes, "token_generator", FakeTokenGenerator())

    response = client.get("/v1/token?timezone_id=not a timezone")

    assert response.status_code == 400
    assert "Unsupported timezone_id" in response.json()["detail"]
