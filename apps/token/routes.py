import logging
import os
import threading
import time

from apps.token import blueprint, getTokenFromList, lock, logger, threadqueue


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
        logger.exception("Ran into error while generating token. Retrying...")
        return "Error"
