import logging
from importlib import import_module

import coloredlogs
from flask import Flask

logger = logging.getLogger()


def setup_logger():
    coloredlogs.install(level=logging.INFO, logger=logger)
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
