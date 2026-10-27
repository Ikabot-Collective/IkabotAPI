import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient

from main import app
from tests.test_token_generator import block_first_token, wait_for_blocked_page
from tests.token_validator import verify_token_format


def test_each_lifespan_owns_and_closes_its_generator():
    previous = None
    for _ in range(2):
        with TestClient(app) as client:
            generator = app.state.token_generator
            assert generator is not previous
            # Importing the app and serving health do not launch Chromium.
            assert generator._session is None
            assert client.get("/health").status_code == 200
            verify_token_format(client.get("/v1/token").json())
            browser = generator._session.browser
        assert generator._closed
        assert not browser.is_connected()
        assert not hasattr(app.state, "token_generator")
        previous = generator


@pytest.mark.asyncio
async def test_health_responds_while_token_waits_on_playwright(monkeypatch):
    async with app.router.lifespan_context(app):
        generator = app.state.token_generator
        await generator.get_token()
        started, pages = await block_first_token(generator, monkeypatch)
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            token = asyncio.create_task(client.get("/v1/token"))
            await wait_for_blocked_page(started, pages)
            health = await asyncio.wait_for(client.get("/health"), 1)
            assert health.status_code == 200
            assert not token.done()
            await pages[0].evaluate("window.releaseToken()")
            assert (await token).json() == "released-token"


def test_generation_error_returns_generic_500(client, monkeypatch):
    async def fail(*args):
        raise RuntimeError("private driver details")

    monkeypatch.setattr(client.app.state.token_generator, "get_token", fail)
    response = client.get("/v1/token")
    assert response.status_code == 500
    assert response.json() == {"detail": "An error occurred during token generation"}
