import json

import pytest
from pytest_mock import MockerFixture

from apps import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True})

    with app.test_client() as client:
        yield client


def test_get_token_should_return_status_code_ok(client):
    response = client.get("/token")
    assert response.status_code == 200
