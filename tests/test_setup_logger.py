import logging

import pytest
from pytest_mock import MockerFixture

from main import setup_logger


def test_setup_logger_with_webhook_url_defined(mocker: MockerFixture):
    mocker.patch("settings.LOGS_WEBHOOK_URL", "https://example.com/webhook")

    # Get the root logger (used by setup_logger)
    logger = logging.getLogger()
    logger.handlers.clear()

    setup_logger()

    assert len(logger.handlers) == 2  # One for console and one for Discord


def test_setup_logger_with_webhook_url_not_defined(mocker: MockerFixture):
    mocker.patch("settings.LOGS_WEBHOOK_URL", None)

    # Get the root logger (used by setup_logger)
    logger = logging.getLogger()
    logger.handlers.clear()

    setup_logger()

    assert len(logger.handlers) == 1  # Only one for console


def test_setup_logger_with_empty_webhook_url(mocker: MockerFixture):
    mocker.patch("settings.LOGS_WEBHOOK_URL", "")

    # Get the root logger (used by setup_logger)
    logger = logging.getLogger()
    logger.handlers.clear()

    setup_logger()

    assert len(logger.handlers) == 1  # Only one for console


def _discord_handler(logger):
    return next(h for h in logger.handlers if type(h).__name__ == "DiscordHandler")


def _console_handler(logger):
    return next(h for h in logger.handlers if type(h).__name__ != "DiscordHandler")


def _access_record():
    return logging.LogRecord(
        "uvicorn.access", logging.INFO, __file__, 1,
        '%s - "GET /v1/token HTTP/1.1" 200 from %s',
        ("203.0.113.7:51234", "2001:db8:85a3::8a2e:370:7334"), None,
    )


@pytest.mark.parametrize("hide_ips", [True, False])
def test_discord_logs_hide_ips_only_when_enabled(mocker: MockerFixture, hide_ips):
    mocker.patch("settings.LOGS_WEBHOOK_URL", "https://example.com/webhook")
    mocker.patch("settings.LOGS_WEBHOOK_HIDE_IPS", hide_ips)
    logger = logging.getLogger()
    logger.handlers.clear()

    setup_logger()
    sent = _discord_handler(logger).format(_access_record())

    if hide_ips:
        assert "203.0.113.7" not in sent and "2001:db8" not in sent
        assert 'x.x.x.x:51234 - "GET /v1/token HTTP/1.1" 200 from x.x.x.x' in sent
    else:
        assert "203.0.113.7:51234" in sent and "2001:db8:85a3::8a2e:370:7334" in sent


def test_console_logs_keep_ips_when_discord_hides_them(mocker: MockerFixture):
    mocker.patch("settings.LOGS_WEBHOOK_URL", "https://example.com/webhook")
    mocker.patch("settings.LOGS_WEBHOOK_HIDE_IPS", True)
    logger = logging.getLogger()
    logger.handlers.clear()

    setup_logger()
    record = _access_record()
    _discord_handler(logger).format(record)

    console = _console_handler(logger)
    console.filter(record)  # coloredlogs adds hostname/programname in its filters
    assert "203.0.113.7:51234" in console.format(record)
    assert "203.0.113.7:51234" in record.getMessage()  # the record itself is untouched


@pytest.mark.parametrize(
    "value, expected",
    [(None, True), ("true", True), ("TRUE", True), ("no", True), ("", True), ("false", False), (" False ", False)],
)
def test_hide_ips_setting_only_shows_ips_when_explicitly_false(monkeypatch, value, expected):
    import importlib

    import settings

    if value is None:
        monkeypatch.delenv("LOGS_WEBHOOK_HIDE_IPS", raising=False)
    else:
        monkeypatch.setenv("LOGS_WEBHOOK_HIDE_IPS", value)
    try:
        assert importlib.reload(settings).LOGS_WEBHOOK_HIDE_IPS is expected
    finally:
        monkeypatch.delenv("LOGS_WEBHOOK_HIDE_IPS", raising=False)
        importlib.reload(settings)
