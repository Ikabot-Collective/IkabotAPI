import logging
import os
import threading
import time

from flask import jsonify, request

from apps.token import (
    blueprint,
    getTokenFromList,
    lock,
    logger,
    supported_user_agents,
    threadqueue,
    token_generator,
)


@blueprint.route("/token", methods=["GET"])
def token_route():
    try:
        threadqueue.append(threading.current_thread().ident)
        logger.debug(threading.active_count())
        while True:
            with lock:
                if threading.current_thread().ident == threadqueue[-1]:
                    curr = time.time()
                    token = getTokenFromList()
                    logger.info("Token sent in " + str(time.time() - curr) + " seconds")
                    threadqueue.remove(threading.current_thread().ident)
                    break
                else:
                    time.sleep(0.01)
        return token
    except Exception:
        logger.exception("Error in token route")
        return "Error"


@blueprint.route("/v1/token", methods=["GET"])
def v1_token_route():
    try:
        if "user_agent" not in request.args:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Bad Request: Missing user_agent query parameter",
                    }
                ),
                400,
            )

        user_agent = request.args.get("user_agent")

        if user_agent == "":
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Bad Request: Empty user_agent query parameter",
                    }
                ),
                400,
            )

        if user_agent not in supported_user_agents:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Bad Request: Unsupported user_agent query parameter",
                    }
                ),
                400,
            )

        token = token_generator.get_token(user_agent)
        return jsonify(token), 200
    except Exception:
        logger.exception("Error in v1_token route")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "An error occurred during token generation",
                }
            ),
            500,
        )
