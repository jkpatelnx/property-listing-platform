from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from config.settings import settings
from database.session import engine
from database.base import Base

# Import routers
from routers import auth, properties, pages, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: nothing to do — use Alembic for migrations
    yield
    # Shutdown: close DB engine
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="A property listing platform built with FastAPI + PostgreSQL",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# ── Mount static files ────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

# ── Include routers ───────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(properties.router)
app.include_router(pages.router)
app.include_router(admin.router)


# ── Global exception handlers ─────────────────────────────────────────────────
templates = Jinja2Templates(directory="templates")


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    return HTMLResponse("<h1>Server Error</h1><p>Something went wrong.</p>", status_code=500)
