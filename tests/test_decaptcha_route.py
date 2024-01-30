import json
import os
from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from apps import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True})

    with app.test_client() as client:
        yield client


def test_decaptcha_without_data_should_return_status_code_400(client):
    response = client.post("/ikagod/ikabot")
    assert response.status_code == 400


def test_decaptcha_piracy_with_valid_image_should_return_the_right_string(client):
    current_directory = os.path.dirname(__file__)

    # Case 1
    file_path = os.path.join(current_directory, "img", "pirate1.png")
    with open(file_path, "rb") as f:
        response = client.post(
            "/ikagod/ikabot",
            data={"upload_file": (BytesIO(f.read()), "pirate1.png")},
        )
    assert response.status_code == 200
    assert json.loads(response.data) == "QKB24JC"

    # Case 2
    file_path = os.path.join(current_directory, "img", "pirate2.png")
    with open(file_path, "rb") as f:
        response = client.post(
            "/ikagod/ikabot",
            data={"upload_file": (BytesIO(f.read()), "pirate2.png")},
        )
    assert response.status_code == 200
    assert json.loads(response.data) == "DEVL5KA"


def test_decaptcha_piracy_with_invalid_size_should_return_status_code_500(client):
    current_directory = os.path.dirname(__file__)
    file_path = os.path.join(current_directory, "img", "pirate_invalid_size.png")
    with open(file_path, "rb") as f:
        response = client.post(
            "/ikagod/ikabot",
            data={"upload_file": (BytesIO(f.read()), "pirate_invalid_size.png")},
        )
    assert response.status_code == 500


def test_decaptcha_login_captcha_with_valid_image_should_return_the_right_int(client):
    current_directory = os.path.dirname(__file__)

    # Case 1
    file_path1 = os.path.join(current_directory, "img", "login_text1.png")
    file_path2 = os.path.join(current_directory, "img", "login_icons1.png")

    with open(file_path1, "rb") as text_image, open(file_path2, "rb") as drag_icons:
        data = {
            "text_image": (BytesIO(text_image.read()), "login_text1.png"),
            "drag_icons": (BytesIO(drag_icons.read()), "login_icons1.png"),
        }
        response = client.post("/ikagod/ikabot", data=data)
    assert response.status_code == 200
    assert json.loads(response.data) == 3

    # Case 2
    file_path1 = os.path.join(current_directory, "img", "login_text2.png")
    file_path2 = os.path.join(current_directory, "img", "login_icons2.png")
    with open(file_path1, "rb") as text_image, open(file_path2, "rb") as drag_icons:
        data = {
            "text_image": (BytesIO(text_image.read()), "login_text2.png"),
            "drag_icons": (BytesIO(drag_icons.read()), "login_icons2.png"),
        }
        response = client.post("/ikagod/ikabot", data=data)
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
            "drag_icons": (BytesIO(drag_icons.read()), "login_icons_invalid.png"),
        }
        response = client.post("/ikagod/ikabot", data=data)
    assert response.status_code == 500
