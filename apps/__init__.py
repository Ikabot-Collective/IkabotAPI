import logging
from importlib import import_module

import coloredlogs
from flask import Flask

logger = logging.getLogger()


def setup_logger():
    coloredlogs.install(level=logging.INFO, logger=logger)
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
