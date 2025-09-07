import os
from io import BytesIO

import pytest
from fastapi.testclient import TestClient


def test_decaptcha_without_data_should_return_422(client: TestClient):
    """Test that missing file upload returns 422 (FastAPI validation error)"""
    response = client.post("/v1/decaptcha/pirate")
    assert response.status_code == 422


def test_decaptcha_piracy_with_valid_image_should_return_the_right_string(
    client: TestClient,
):
    """Test pirate captcha solving with valid images returns correct strings"""
    current_directory = os.path.dirname(__file__)

    # Case 1
    file_path = os.path.join(current_directory, "img", "pirate1.png")
    with open(file_path, "rb") as f:
        files = {"image": ("pirate1.png", BytesIO(f.read()), "image/png")}
        response = client.post("/v1/decaptcha/pirate", files=files)

    assert response.status_code == 200
    result = response.json()
    assert result == "QKB24JC"

    # Case 2
    file_path = os.path.join(current_directory, "img", "pirate2.png")
    with open(file_path, "rb") as f:
        files = {"image": ("pirate2.png", BytesIO(f.read()), "image/png")}
        response = client.post("/v1/decaptcha/pirate", files=files)

    assert response.status_code == 200
    result = response.json()
    assert result == "DEVL5KA"


def test_decaptcha_piracy_with_invalid_size_should_return_status_code_500(client: TestClient):
    """Test pirate captcha with invalid image size"""
    current_directory = os.path.dirname(__file__)
    file_path = os.path.join(current_directory, "img", "pirate_invalid_size.png")

    with open(file_path, "rb") as f:
        files = {"image": ("pirate_invalid_size.png", BytesIO(f.read()), "image/png")}
        response = client.post("/v1/decaptcha/pirate", files=files)

    assert response.status_code == 500
    response_json = response.json()
    assert "detail" in response_json
