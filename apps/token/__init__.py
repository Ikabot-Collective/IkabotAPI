import logging
import threading
import time

from flask import Blueprint

from apps.token.TokenGenerator import TokenGenerator

logger = logging.getLogger()

blueprint = Blueprint("token_blueprint", __name__, url_prefix="")

token_generator = TokenGenerator()

tokenList = []
refreshCounter = 0


def populateTokenList():
    global refreshCounter
    while True:
        try:
            if len(tokenList) <= 20:
                curr = time.time()
                tokenList.append(token_generator.get_token())
                logger.info(
                    "Token generated in " + str(time.time() - curr) + " seconds"
                )
            else:
                time.sleep(0.5)
            refreshCounter += 1
            if refreshCounter % 100 == 0 and len(tokenList) > 0:
                tokenList.pop(0)
        except Exception:
            logger.exception("Ran into error while generating token. Retrying...")
            time.sleep(5)
            pass


tokenGenThread = threading.Thread(target=populateTokenList, daemon=True)
tokenGenThread.start()


def getTokenFromList():
    while True:
        if len(tokenList) > 0:
            return tokenList.pop(0)
        else:
            logger.info("No token available. Waiting for token to be generated...")
            time.sleep(0.5)


threadqueue = []
lock = threading.Lock()
