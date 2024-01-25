import logging

from flask import Blueprint

from apps.token.TokenGenerator import TokenGenerator

logger = logging.getLogger()

token_generator = TokenGenerator()

blueprint = Blueprint("token_blueprint", __name__, url_prefix="")
