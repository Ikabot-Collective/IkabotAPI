import logging
from importlib import import_module

import coloredlogs
from flask import Flask

import settings

logger = logging.getLogger()


def setup_logger():
    """
    Set up the logger with a Discord handler and colored console output.
    """
    coloredlogs.install(level=logging.INFO, logger=logger)

    if settings.LOGS_WEBHOOK_URL is not None and settings.LOGS_WEBHOOK_URL != "":
        from discord_logging.handler import DiscordHandler

        # Define format for logs
        discord_format = logging.Formatter("%(message)s")

        discord_handler = DiscordHandler("Ikabot API", settings.LOGS_WEBHOOK_URL)
        discord_handler.setFormatter(discord_format)

        logger.addHandler(discord_handler)

    logger.setLevel(logging.INFO)


def register_blueprints(app):
    for module_name in ("home", "token", "decaptcha"):
        module = import_module("apps.{}.routes".format(module_name))
        app.register_blueprint(module.blueprint)


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    register_blueprints(app)
    setup_logger()

    logger.info("Ikabot API ready!")
    return app
