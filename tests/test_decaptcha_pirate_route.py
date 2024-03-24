import json
import os
from io import BytesIO

import pytest

from apps import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True})

    with app.test_client() as client:
        yield client


def test_decaptcha_without_data_should_return_status_code_400(client):
    response = client.post("v1/decaptcha/pirate")
    assert response.status_code == 400


def test_decaptcha_piracy_with_valid_image_should_return_the_right_string(client):
    current_directory = os.path.dirname(__file__)

    # Case 1
    file_path = os.path.join(current_directory, "img", "pirate1.png")
    with open(file_path, "rb") as f:
        response = client.post(
            "v1/decaptcha/pirate",
            data={"image": (BytesIO(f.read()), "pirate1.png")},
        )
    assert response.status_code == 200
    assert json.loads(response.data) == "QKB24JC"

    # Case 2
    file_path = os.path.join(current_directory, "img", "pirate2.png")
    with open(file_path, "rb") as f:
        response = client.post(
            "v1/decaptcha/pirate",
            data={"image": (BytesIO(f.read()), "pirate2.png")},
        )
    assert response.status_code == 200
    assert json.loads(response.data) == "DEVL5KA"


def test_decaptcha_piracy_with_invalid_size_should_return_status_code_500(client):
    current_directory = os.path.dirname(__file__)
    file_path = os.path.join(current_directory, "img", "pirate_invalid_size.png")
    with open(file_path, "rb") as f:
        response = client.post(
            "v1/decaptcha/pirate",
            data={"image": (BytesIO(f.read()), "pirate_invalid_size.png")},
        )
    assert response.status_code == 500
