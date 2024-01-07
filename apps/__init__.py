import logging
from importlib import import_module

import coloredlogs
from flask import Flask

logger = logging.getLogger()


def setup_logger():
    """
    Set up the logger with a Discord handler and colored console output.
    """
    coloredlogs.install(level=logging.INFO, logger=logger)
    gunicorn_logger = logging.getLogger("gunicorn.error")
    logger.addHandler(gunicorn_logger)
    logger.setLevel(logging.INFO)


def register_blueprints(app):
    module = import_module("apps.token.routes")
    app.register_blueprint(module.blueprint)


def create_app(config):
    setup_logger()
    app = Flask(__name__)
    app.config.from_object(config)
    register_blueprints(app)

    return app
