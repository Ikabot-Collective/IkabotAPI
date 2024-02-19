import logging
import os
import time

from flask import jsonify, request

from apps.token import blueprint, logger, token_generator


@blueprint.route("/token", methods=["GET"])
def token_route():
    try:
        user_id = request.args.get('user_id')
        start_time = time.time()
        token = token_generator.get_token(user_id)
        logger.info("Token generated in %s seconds" % (time.time() - start_time))
        return jsonify(token), 200
    except Exception:
        logger.exception("An error occurred during the token generation")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "An error occurred during the token generation",
                }
            ),
            500,
        )
