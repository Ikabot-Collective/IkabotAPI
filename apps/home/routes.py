import time
from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from apps import __version__
from apps.models import HealthResponse

router = APIRouter()
templates = Jinja2Templates(directory="apps/templates")

start_time = time.time()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "home/index.html", {"request": request, "version": __version__}
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={503: {"model": HealthResponse, "description": "Token generation is unavailable"}},
)
async def health(request: Request, response: Response):
    # A token generator that could not stop its browser stays closed until the
    # API restarts, so report it instead of looking healthy.
    generator = getattr(request.app.state, "token_generator", None)
    if generator is None or generator.closed:
        response.status_code = 503
        return HealthResponse(status="unhealthy", uptime=time.time() - start_time)
    return HealthResponse(uptime=time.time() - start_time)
