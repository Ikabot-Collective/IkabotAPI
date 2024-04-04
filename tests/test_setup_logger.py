import logging

import pytest
from pytest_mock import MockerFixture

from apps import setup_logger


def test_setup_logger_with_webhook_url_defined(mocker: MockerFixture):
    mocker.patch("settings.LOGS_WEBHOOK_URL", "https://example.com/webhook")

    logger = logging.getLogger()
    logger.handlers.clear()

    setup_logger()

    assert len(logger.handlers) == 2  # One for console and one for Discord


def test_setup_logger_with_webhook_url_not_defined(mocker: MockerFixture):
    mocker.patch("settings.LOGS_WEBHOOK_URL", None)

    logger = logging.getLogger()
    logger.handlers.clear()

    setup_logger()

    assert len(logger.handlers) == 1  # Only one for console


def test_setup_logger_with_empty_webhook_url(mocker: MockerFixture):
    mocker.patch("settings.LOGS_WEBHOOK_URL", "")

    logger = logging.getLogger()
    logger.handlers.clear()

    setup_logger()

    assert len(logger.handlers) == 1  # Only one for console
