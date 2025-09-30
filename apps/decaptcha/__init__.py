import logging
import threading
import time

from apps.decaptcha.pirates_captcha.ikapiratesdecaptcha import get_captcha_string

threadqueue = []
lock = threading.Lock()

logger = logging.getLogger()


def Captcha_detection(image):
    curr = time.time()
    result = get_captcha_string(image)
    logger.info(
        "detect_image done, elapsed: " + str(time.time() - curr) + " result: " + result
    )
    return result
