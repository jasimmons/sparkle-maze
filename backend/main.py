"""The game server with accounts: serves the game, and the API it saves scores to.

    uvicorn backend.main:app --port 8000      (docker compose up does this for you)
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from . import api, auth, config
from .api import server
from .db import init_db

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(title="Pip's Sparkle Maze", lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(
    SessionMiddleware,
    secret_key=config.SESSION_SECRET,
    session_cookie="sparkle_session",
    max_age=30 * 24 * 3600,
    same_site="lax",
    https_only=config.COOKIE_SECURE,
)
app.include_router(auth.router)
app.include_router(api.router)


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(server.full_page(), headers={"Cache-Control": "no-store"})


@app.get("/healthz")
def healthz():
    return {"ok": True}


app.mount("/levels", StaticFiles(directory=server.LEVELS), name="levels")
