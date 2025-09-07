import asyncio
import logging
import time
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from apps.token import (
    logger,
    supported_user_agents,
    token_generator,
)

router = APIRouter()


@router.get("/v1/token")
def v1_token_route(
    user_agent: Annotated[
        str, Query(description="User agent string for token generation")
    ],
):
    """
    Generate a Blackbox token for the specified user agent.
    NOTE: Synchronous to avoid conflicts with sync Playwright code

    Args:
        user_agent: The user agent string to generate a token for

    Returns:
        str: The generated Blackbox token string

    Raises:
        HTTPException: 400 if user_agent is invalid or unsupported
        HTTPException: 500 if token generation fails
    """
    try:
        if not user_agent or user_agent == "":
            raise HTTPException(
                status_code=400, detail="Bad Request: Empty user_agent query parameter"
            )

        if user_agent not in supported_user_agents:
            raise HTTPException(
                status_code=400,
                detail="Bad Request: Unsupported user_agent query parameter",
            )

        start_time = time.time()
        token_string = token_generator.get_token(user_agent)
        processing_time = time.time() - start_time

        return token_string
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in v1_token route")
        raise HTTPException(
            status_code=500, detail="An error occurred during token generation"
        )
