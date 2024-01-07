from flask import Blueprint

blueprint = Blueprint(
    'token_blueprint',
    __name__,
    url_prefix=''
)