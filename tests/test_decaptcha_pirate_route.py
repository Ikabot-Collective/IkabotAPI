import os
from concurrent.futures import ThreadPoolExecutor
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


def test_decaptcha_piracy_with_invalid_size_should_return_status_code_413(client: TestClient):
    """Oversized uploads are rejected before reaching the queue"""
    current_directory = os.path.dirname(__file__)
    file_path = os.path.join(current_directory, "img", "pirate_invalid_size.png")

    with open(file_path, "rb") as f:
        files = {"image": ("pirate_invalid_size.png", BytesIO(f.read()), "image/png")}
        response = client.post("/v1/decaptcha/pirate", files=files)

    assert response.status_code == 413
    assert "detail" in response.json()


def test_decaptcha_piracy_with_html_should_return_status_code_415(client: TestClient):
    """A small non-image upload (e.g. HTML) is rejected before reaching the queue"""
    html = b"<html><body>not a captcha</body></html>"
    files = {"image": ("page.html", BytesIO(html), "text/html")}
    response = client.post("/v1/decaptcha/pirate", files=files)

    assert response.status_code == 415
    assert "detail" in response.json()


def test_decaptcha_piracy_with_large_html_should_return_status_code_413(client: TestClient):
    """A large HTML upload (old client behaviour) fails fast with 413"""
    html = b"<html>" + b"x" * 60_000 + b"</html>"
    files = {"image": ("page.html", BytesIO(html), "text/html")}
    response = client.post("/v1/decaptcha/pirate", files=files)

    assert response.status_code == 413


def test_decaptcha_piracy_concurrent_requests_all_succeed(client: TestClient):
    """Concurrent requests are all served (no request is left waiting forever)"""
    current_directory = os.path.dirname(__file__)
    with open(os.path.join(current_directory, "img", "pirate1.png"), "rb") as f:
        data = f.read()

    def solve(_):
        files = {"image": ("pirate1.png", BytesIO(data), "image/png")}
        return client.post("/v1/decaptcha/pirate", files=files)

    with ThreadPoolExecutor(max_workers=16) as pool:
        responses = list(pool.map(solve, range(48)))

    assert all(r.status_code == 200 for r in responses)
    assert all(r.json() == "QKB24JC" for r in responses)
