import logging
import threading
import time

from flask import jsonify, request

from apps.decaptcha import Captcha_detection, blueprint, lock, logger, threadqueue
from apps.decaptcha.lobby_captcha.image import break_interactive_captcha


# TODO: Remove this route in the future
@blueprint.route("/ikagod/ikabot", methods=["POST"])
def deprecated_decaptcha():
    try:
        if "upload_file" in request.files:
            threadqueue.append(threading.current_thread().ident)
            logger.info(threading.active_count())
            while True:
                with lock:
                    if threading.current_thread().ident == threadqueue[-1]:
                        captcha = Captcha_detection(request.files["upload_file"])
                        threadqueue.remove(threading.current_thread().ident)
                        break
                    else:
                        time.sleep(0.01)

        elif "text_image" in request.files and "drag_icons" in request.files:
            text_image = request.files["text_image"].read()
            drag_icons = request.files["drag_icons"].read()
            try:
                captcha = break_interactive_captcha(text_image, drag_icons)
                logger.info(
                    f"Successfully solved interactive captcha, result: {captcha}"
                )
            except Exception as e:
                logger.exception("Failed to solve interactive captcha")
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": f"An error occurred during captcha resolution: {e}",
                        }
                    ),
                    500,
                )

        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Bad Request: Invalid input",
                    }
                ),
                400,
            )

        return jsonify(captcha), 200

    except Exception as e:
        logger.exception("Error in decaptcha route")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"An error occurred in the decaptcha route: {e}",
                }
            ),
            500,
        )


@blueprint.route("/decaptcha/pirate", methods=["POST"])
def decaptcha_pirate():
    try:
        if "image" in request.files:
            threadqueue.append(threading.current_thread().ident)
            logger.info(threading.active_count())
            while True:
                with lock:
                    if threading.current_thread().ident == threadqueue[-1]:
                        captcha = Captcha_detection(request.files["image"])
                        threadqueue.remove(threading.current_thread().ident)
                        break
                    else:
                        time.sleep(0.01)
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Bad Request: Invalid input",
                    }
                ),
                400,
            )

        return jsonify(captcha), 200

    except Exception as e:
        logger.exception("Error in decaptcha_pirate route")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"An error occurred in the decaptcha_pirate route: {e}",
                }
            ),
            500,
        )


@blueprint.route("/decaptcha/lobby", methods=["POST"])
def decaptcha_lobby():
    try:
        if "text_image" in request.files and "icons_image" in request.files:
            text_image = request.files["text_image"].read()
            icons_image = request.files["icons_image"].read()
            try:
                captcha = break_interactive_captcha(text_image, icons_image)
                logger.info(
                    f"Successfully solved interactive captcha, result: {captcha}"
                )
            except Exception as e:
                logger.exception("Failed to solve interactive captcha")
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": f"An error occurred during captcha resolution: {e}",
                        }
                    ),
                    500,
                )

        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Bad Request: Invalid input",
                    }
                ),
                400,
            )

        return jsonify(captcha), 200

    except Exception as e:
        logger.exception("Error in decaptcha_lobby route")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"An error occurred in the decaptcha_lobby route: {e}",
                }
            ),
            500,
        )
