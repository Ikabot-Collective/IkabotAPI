import logging
from contextlib import asynccontextmanager

import coloredlogs
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import settings
from apps.decaptcha.routes import router as decaptcha_router
from apps.home.routes import router as home_router
from apps.token.routes import router as token_router

logger = logging.getLogger(__name__)


def setup_logger():
    """
    Set up the root logger with a Discord handler and colored console output.
    This ensures all modules using logging.getLogger() will benefit from the configuration.
    """
    root_logger = logging.getLogger()
    coloredlogs.install(level=logging.INFO, logger=root_logger)

    if settings.LOGS_WEBHOOK_URL is not None and settings.LOGS_WEBHOOK_URL != "":
        from discord_logging.handler import DiscordHandler

        # Define format for logs
        discord_format = logging.Formatter("%(message)s")

        discord_handler = DiscordHandler("Ikabot API", settings.LOGS_WEBHOOK_URL)
        discord_handler.setFormatter(discord_format)

        root_logger.addHandler(discord_handler)

    root_logger.setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logger()
    logger.info("Ikabot API ready!")
    yield
    # Shutdown
    logger.info("Ikabot API shutting down")


app = FastAPI(
    title="Ikabot API",
    description="API for Ikabot captcha solving and token generation",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="apps/templates/static"), name="static")

# Include routers
app.include_router(home_router)
app.include_router(token_router)
app.include_router(decaptcha_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5005,
        reload=True,
        log_level="info"
    )
