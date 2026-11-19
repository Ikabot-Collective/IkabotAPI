import logging
import threading
import time

import pytest
from pytest_mock import MockerFixture

import main
from main import BackgroundHandler, setup_logger


@pytest.fixture(autouse=True)
def no_discord_requests(mocker: MockerFixture):
    """Never reach the network, and stop the background thread after each test."""
    sent = []
    mocker.patch(
        "discord_logging.handler.DiscordHandler.emit",
        lambda self, record: sent.append(self.format(record)),
    )
    yield sent
    main.close_discord_logs()
    logging.getLogger().handlers.clear()


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
    return next(h.target for h in logger.handlers if isinstance(h, BackgroundHandler))


def _console_handler(logger):
    return next(h for h in logger.handlers if not isinstance(h, BackgroundHandler))


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


def _wait_for(condition, timeout=5):
    deadline = time.monotonic() + timeout
    while not condition():
        assert time.monotonic() < deadline, "timed out"
        time.sleep(0.01)


def test_slow_discord_never_blocks_the_logging_call(mocker: MockerFixture, no_discord_requests):
    """Discord sleeps when rate limited; that must not happen in the caller's thread."""
    sent = no_discord_requests
    mocker.patch("settings.LOGS_WEBHOOK_URL", "https://example.com/webhook")
    mocker.patch(
        "discord_logging.handler.DiscordHandler.emit",
        lambda self, record: (time.sleep(1), sent.append(self.format(record))),
    )
    setup_logger()

    start = time.perf_counter()
    for i in range(3):
        logging.getLogger("uvicorn.access").info("request %d from 203.0.113.7", i)
    assert time.perf_counter() - start < 0.2

    _wait_for(lambda: len(sent) >= 1)
    assert sent[0] == "uvicorn.access - request 0 from x.x.x.x"


def test_exceptions_reach_discord_with_their_traceback(mocker: MockerFixture, no_discord_requests):
    mocker.patch("settings.LOGS_WEBHOOK_URL", "https://example.com/webhook")
    setup_logger()
    try:
        raise ValueError("boom")
    except ValueError:
        logging.getLogger("apps.token").exception("Error in v1_token route")
    main.close_discord_logs()
    (message,) = no_discord_requests
    assert message.startswith("apps.token - Error in v1_token route")
    assert "ValueError: boom" in message


def test_discord_internal_logs_are_not_sent_to_discord(mocker: MockerFixture, no_discord_requests):
    """Sending "Webhook rate limited" to Discord would create more traffic, endlessly."""
    mocker.patch("settings.LOGS_WEBHOOK_URL", "https://example.com/webhook")
    setup_logger()
    logging.getLogger("discord_webhook.webhook").error("Webhook rate limited: sleeping")
    logging.getLogger("urllib3.connectionpool").warning("Retrying")
    logging.getLogger("requests").warning("timeout")
    logging.getLogger("requests_extra").warning("not an internal logger")
    main.close_discord_logs()
    assert no_discord_requests == ["requests_extra - not an internal logger"]


def test_full_queue_drops_records_instead_of_blocking():
    release = threading.Event()
    target = logging.Handler()
    target.emit = lambda record: release.wait()
    handler = BackgroundHandler(target, maxsize=2)
    try:
        record = logging.LogRecord("x", logging.INFO, __file__, 1, "msg", None, None)
        start = time.perf_counter()
        for _ in range(10):
            handler.handle(record)
        assert time.perf_counter() - start < 0.2
        # One record is being sent, two wait in the queue, the rest are dropped.
        assert handler.dropped >= 7
    finally:
        release.set()
        handler.close()
    assert not handler._thread.is_alive()


def test_close_does_not_wait_forever_for_a_stuck_discord():
    release = threading.Event()
    target = logging.Handler()
    target.emit = lambda record: release.wait()
    handler = BackgroundHandler(target)
    handler.handle(logging.LogRecord("x", logging.INFO, __file__, 1, "msg", None, None))
    start = time.perf_counter()
    handler.close(timeout=0.3)
    assert time.perf_counter() - start < 1
    release.set()


def test_setup_logger_twice_keeps_one_discord_thread(mocker: MockerFixture):
    mocker.patch("settings.LOGS_WEBHOOK_URL", "https://example.com/webhook")
    setup_logger()
    first = main._discord_logs
    setup_logger()
    _wait_for(lambda: not first._thread.is_alive())
    assert sum(isinstance(h, BackgroundHandler) for h in logging.getLogger().handlers) == 1


def test_close_drops_what_a_slow_discord_could_not_send():
    """At shutdown a flooded queue is dropped, so the thread stops soon after."""
    sent = []
    target = logging.Handler()
    target.emit = lambda record: (time.sleep(0.2), sent.append(record))
    handler = BackgroundHandler(target)
    for i in range(50):
        handler.handle(logging.LogRecord("x", logging.INFO, __file__, 1, str(i), None, None))
    handler.close(timeout=0.3)
    _wait_for(lambda: not handler._thread.is_alive(), timeout=1)
    assert 0 < len(sent) < 50
