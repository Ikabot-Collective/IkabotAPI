import logging
import threading
import time
from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

from apps.decaptcha import Captcha_detection, lock, logger
from apps.decaptcha.lobby_captcha.image import break_interactive_captcha

router = APIRouter()

# Pirate captchas are small images. Anything else (e.g. the full HTML page that
# old clients used to send) is rejected before it can take a place in the queue.
PIRATE_MAX_BYTES = 50_000
IMAGE_MAGIC_BYTES = (
    b"\x89PNG\r\n\x1a\n",  # PNG
    b"\xff\xd8\xff",  # JPEG
    b"GIF87a",
    b"GIF89a",
)


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
        HTTPException: 413 if the upload is larger than 50 KB
        HTTPException: 415 if the upload is not a PNG/JPEG/GIF image
        HTTPException: 500 if captcha resolution fails
    """
    try:
        if not image:
            raise HTTPException(
                status_code=400, detail="Bad Request: No image provided"
            )

        # Validate before queueing so invalid uploads fail fast and never wait
        # for (or hold) the lock. Reads at most one byte over the limit.
        data = image.file.read(PIRATE_MAX_BYTES + 1)
        if len(data) > PIRATE_MAX_BYTES:
            raise HTTPException(status_code=413, detail="Image too large (max 50 KB)")
        if not data.startswith(IMAGE_MAGIC_BYTES):
            raise HTTPException(
                status_code=415,
                detail="Unsupported file type: send only the captcha image",
            )

        start_time = time.time()

        logger.info(f"Active threads: {threading.active_count()}")

        with lock:
            captcha_result = Captcha_detection(BytesIO(data))

        processing_time = time.time() - start_time

        # Return the result string
        return captcha_result

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
