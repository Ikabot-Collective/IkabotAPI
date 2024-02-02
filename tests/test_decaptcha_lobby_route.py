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
    response = client.post("/decaptcha/lobby")
    assert response.status_code == 400


def test_decaptcha_login_captcha_with_valid_image_should_return_the_right_int(client):
    current_directory = os.path.dirname(__file__)

    # Case 1
    file_path1 = os.path.join(current_directory, "img", "login_text1.png")
    file_path2 = os.path.join(current_directory, "img", "login_icons1.png")

    with open(file_path1, "rb") as text_image, open(file_path2, "rb") as drag_icons:
        data = {
            "text_image": (BytesIO(text_image.read()), "login_text1.png"),
            "icons_image": (BytesIO(drag_icons.read()), "login_icons1.png"),
        }
        response = client.post("/decaptcha/lobby", data=data)
    assert response.status_code == 200
    assert json.loads(response.data) == 3

    # Case 2
    file_path1 = os.path.join(current_directory, "img", "login_text2.png")
    file_path2 = os.path.join(current_directory, "img", "login_icons2.png")
    with open(file_path1, "rb") as text_image, open(file_path2, "rb") as drag_icons:
        data = {
            "text_image": (BytesIO(text_image.read()), "login_text2.png"),
            "icons_image": (BytesIO(drag_icons.read()), "login_icons2.png"),
        }
        response = client.post("/decaptcha/lobby", data=data)
    assert response.status_code == 200
    assert json.loads(response.data) == 0


def test_decaptcha_login_captcha_with_invalid_image_should_return_status_code_500(
    client,
):
    current_directory = os.path.dirname(__file__)

    file_path1 = os.path.join(current_directory, "img", "login_text_invalid.png")
    file_path2 = os.path.join(current_directory, "img", "login_icons_invalid.png")

    with open(file_path1, "rb") as text_image, open(file_path2, "rb") as drag_icons:
        data = {
            "text_image": (BytesIO(text_image.read()), "login_text_invalid.png"),
            "icons_image": (BytesIO(drag_icons.read()), "login_icons_invalid.png"),
        }
        response = client.post("/decaptcha/lobby", data=data)
    assert response.status_code == 500
