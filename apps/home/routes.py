import time
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from apps.models import HealthResponse

router = APIRouter()
templates = Jinja2Templates(directory="apps/templates")

start_time = time.time()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home/index.html", {"request": request})


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy", version="2.0.0", uptime=time.time() - start_time
    )
