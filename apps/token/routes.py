import logging
import re
import time
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from apps.token import (
    logger,
    supported_user_agents,
    token_generator,
)

router = APIRouter()

LOCALE_PATTERN = re.compile(r"^[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*$")
TIMEZONE_PATTERN = re.compile(r"^(UTC|[A-Za-z_]+(/[A-Za-z0-9_+\-]+)+)$")


def _normalize_context_param(
    value: str | None,
    default: str,
    pattern: re.Pattern,
    param_name: str,
) -> str:
    if value is None or value == "":
        return default

    if not pattern.fullmatch(value):
        raise HTTPException(
            status_code=400,
            detail=f"Bad Request: Unsupported {param_name} query parameter",
        )

    return value


@router.get("/v1/token")
def v1_token_route(
    user_agent: Annotated[
        str | None, Query(description="User agent string for token generation")
    ] = None,
    locale: Annotated[
        str | None, Query(description="Browser locale for token generation")
    ] = None,
    timezone_id: Annotated[
        str | None, Query(description="Browser timezone ID for token generation")
    ] = None,
):
    """
    Generate a Blackbox token for the specified user agent.
    NOTE: Synchronous to avoid conflicts with sync Playwright code

    Args:
        user_agent: The user agent string to generate a token for (optional)
        locale: The browser locale to generate a token with (optional)
        timezone_id: The browser timezone ID to generate a token with (optional)

    Returns:
        str: The generated Blackbox token string

    Raises:
        HTTPException: 400 if user_agent is invalid or unsupported
        HTTPException: 500 if token generation fails
    """
    try:
        # If user_agent is None or empty, use default (random) user agent
        if user_agent and user_agent != "" and user_agent not in supported_user_agents:
            raise HTTPException(
                status_code=400,
                detail="Bad Request: Unsupported user_agent query parameter",
            )

        effective_locale = _normalize_context_param(
            locale,
            token_generator.default_locale,
            LOCALE_PATTERN,
            "locale",
        )
        effective_timezone_id = _normalize_context_param(
            timezone_id,
            token_generator.default_timezone_id,
            TIMEZONE_PATTERN,
            "timezone_id",
        )

        start_time = time.time()
        token_string = token_generator.get_token(
            user_agent,
            effective_locale,
            effective_timezone_id,
        )
        processing_time = time.time() - start_time

        return token_string
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in v1_token route")
        raise HTTPException(
            status_code=500, detail="An error occurred during token generation"
        )
