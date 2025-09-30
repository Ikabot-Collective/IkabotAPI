import os
from io import BytesIO

import pytest
from fastapi.testclient import TestClient


def test_decaptcha_without_data_should_return_422(client: TestClient):
    """Test that missing files return 422 (FastAPI validation error)"""
    response = client.post("/v1/decaptcha/lobby")
    assert response.status_code == 422


def test_decaptcha_login_captcha_with_valid_image_should_return_solution(
    client: TestClient,
):
    """Test lobby captcha solving with valid images"""
    current_directory = os.path.dirname(__file__)

    # Case 1
    file_path1 = os.path.join(current_directory, "img", "login_text1.png")
    file_path2 = os.path.join(current_directory, "img", "login_icons1.png")

    with open(file_path1, "rb") as text_image, open(file_path2, "rb") as drag_icons:
        files = {
            "text_image": ("login_text1.png", BytesIO(text_image.read()), "image/png"),
            "icons_image": (
                "login_icons1.png",
                BytesIO(drag_icons.read()),
                "image/png",
            ),
        }
        response = client.post("/v1/decaptcha/lobby", files=files)

    assert response.status_code == 200
    # Returns the solution integer
    solution = response.json()
    assert isinstance(solution, int)
    assert solution == 3

    # Case 2
    file_path1 = os.path.join(current_directory, "img", "login_text2.png")
    file_path2 = os.path.join(current_directory, "img", "login_icons2.png")

    with open(file_path1, "rb") as text_image, open(file_path2, "rb") as drag_icons:
        files = {
            "text_image": ("login_text2.png", BytesIO(text_image.read()), "image/png"),
            "icons_image": (
                "login_icons2.png",
                BytesIO(drag_icons.read()),
                "image/png",
            ),
        }
        response = client.post("/v1/decaptcha/lobby", files=files)

    assert response.status_code == 200
    # Returns the solution integer
    solution = response.json()
    assert isinstance(solution, int)
    assert solution == 0


def test_decaptcha_login_captcha_with_invalid_image_should_return_500(
    client: TestClient,
):
    """Test lobby captcha with invalid images"""
    current_directory = os.path.dirname(__file__)

    file_path1 = os.path.join(current_directory, "img", "login_text_invalid.png")
    file_path2 = os.path.join(current_directory, "img", "login_icons_invalid.png")

    with open(file_path1, "rb") as text_image, open(file_path2, "rb") as drag_icons:
        files = {
            "text_image": (
                "login_text_invalid.png",
                BytesIO(text_image.read()),
                "image/png",
            ),
            "icons_image": (
                "login_icons_invalid.png",
                BytesIO(drag_icons.read()),
                "image/png",
            ),
        }
        response = client.post("/v1/decaptcha/lobby", files=files)

    assert response.status_code == 500
    response_json = response.json()
    assert "detail" in response_json
