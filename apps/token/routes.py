import asyncio
import logging
import time
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from apps.models import TokenResponse
from apps.token import (
    logger,
    supported_user_agents,
    token_generator,
)

router = APIRouter()


@router.get("/v1/token", response_model=TokenResponse)
def v1_token_route(
    user_agent: Annotated[
        str, Query(description="User agent string for token generation")
    ],
):
    """
    Generate a token for the specified user agent.
    NOTE: Synchronous to avoid conflicts with sync Playwright code

    Args:
        user_agent: The user agent string to generate a token for

    Returns:
        TokenResponse: Contains the generated token and metadata

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
        token_data = token_generator.get_token(user_agent)
        processing_time = time.time() - start_time

        return TokenResponse(
            status="success",
            token=(
                token_data
                if isinstance(token_data, str)
                else token_data.get("token", "")
            ),
            user_agent=user_agent,
            timestamp=time.time(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in v1_token route")
        raise HTTPException(
            status_code=500, detail="An error occurred during token generation"
        )
