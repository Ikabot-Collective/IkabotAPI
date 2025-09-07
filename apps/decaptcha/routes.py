import logging
import threading
import time
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

from apps.decaptcha import Captcha_detection, lock, logger, threadqueue
from apps.decaptcha.lobby_captcha.image import break_interactive_captcha

router = APIRouter()


@router.post("/v1/decaptcha/pirate")
def decaptcha_pirate(
    image: Annotated[UploadFile, File(description="Pirate captcha image to solve")],
):
    """
    Solve a pirate captcha for Pirate Fortress missions.
    NOTE: Synchronous to work with existing threading logic

    Args:
        image: The pirate captcha image file

    Returns:
        str: The captcha solution string

    Raises:
        HTTPException: 400 if no image provided
        HTTPException: 500 if captcha resolution fails
    """
    try:
        if not image:
            raise HTTPException(
                status_code=400, detail="Bad Request: No image provided"
            )

        start_time = time.time()

        threadqueue.append(threading.current_thread().ident)
        logger.info(f"Active threads: {threading.active_count()}")

        while True:
            with lock:
                if threading.current_thread().ident == threadqueue[-1]:
                    captcha_result = Captcha_detection(image.file)
                    threadqueue.remove(threading.current_thread().ident)
                    break
                else:
                    time.sleep(0.01)

        processing_time = time.time() - start_time

        # Return the result string
        if isinstance(captcha_result, str):
            return captcha_result
        else:
            # If it's a dict, extract the main result or return empty string
            return captcha_result.get("result", "")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in decaptcha_pirate route")
        raise HTTPException(
            status_code=500, detail="An error occurred during captcha resolution"
        )


@router.post("/v1/decaptcha/lobby")
async def decaptcha_lobby(
    text_image: Annotated[
        UploadFile, File(description="Text portion of the lobby captcha")
    ],
    icons_image: Annotated[
        UploadFile, File(description="Icons portion of the lobby captcha")
    ],
):
    """
    Solve a lobby interactive captcha by matching text to icons.

    Args:
        text_image: The text portion of the captcha
        icons_image: The icons portion of the captcha

    Returns:
        int: The solution as an integer (0, 1, 2, or 3)

    Raises:
        HTTPException: 400 if images are missing
        HTTPException: 500 if captcha resolution fails
    """
    try:
        if not text_image or not icons_image:
            raise HTTPException(
                status_code=400,
                detail="Bad Request: Both text_image and icons_image are required",
            )

        start_time = time.time()

        text_content = await text_image.read()
        icons_content = await icons_image.read()

        try:
            captcha_solution = break_interactive_captcha(text_content, icons_content)
            logger.info(
                f"Successfully solved interactive captcha, result: {captcha_solution}"
            )

            processing_time = time.time() - start_time

            # Return the solution integer
            return int(captcha_solution)

        except Exception as e:
            logger.exception("Failed to solve interactive captcha")
            raise HTTPException(
                status_code=500, detail="An error occurred during captcha resolution"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in decaptcha_lobby route")
        raise HTTPException(
            status_code=500, detail="An error occurred during captcha resolution"
        )
