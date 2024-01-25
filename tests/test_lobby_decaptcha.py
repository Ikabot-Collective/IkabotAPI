import base64
import io

import pytest

from apps.decaptcha.lobby_captcha.image import break_interactive_captcha

text_image = "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"
drag_icons = "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"


def from_base64(base64string):
    return io.BytesIO(base64.b64decode(base64string))


def test_lobby_captcha():
    text = from_base64(text_image).read()
    icons = from_base64(drag_icons).read()
    result = break_interactive_captcha(text, icons)
    assert result == 2, f"Expected 2, got {result}"
