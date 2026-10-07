"""Sign in with GitHub or Google (OAuth), and who is signed in.

The signed-in user's id lives in a signed session cookie (Starlette's SessionMiddleware). Authlib
does the OAuth dance; each provider is switched on by putting its client id and secret in .env.
"""
import logging

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from . import config
from .db import Session, User, now

log = logging.getLogger("sparkle")
router = APIRouter(prefix="/auth")

oauth = OAuth()
for _name in config.enabled_providers():
    _p = config.PROVIDERS[_name]
    oauth.register(_name, client_id=_p["client_id"], client_secret=_p["client_secret"], **_p["oauth"])


def current_user(request: Request):
    """The signed-in User, or None."""
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    with Session() as db:
        return db.get(User, user_id)


def require_user(request: Request):
    user = current_user(request)
    if user is None:
        raise HTTPException(401, "Sign in to save scores")
    return user


def sign_in(request: Request, provider, provider_user_id, name, avatar_url):
    """Find or create the user for this provider account, and start their session."""
    with Session() as db:
        user = db.scalars(
            select(User).where(User.provider == provider, User.provider_user_id == str(provider_user_id))
        ).first()
        if user is None:
            user = User(provider=provider, provider_user_id=str(provider_user_id), total_stars=0)
            db.add(user)
        # Keep the name and picture in step with the provider profile.
        user.name = (name or "Player")[:100]
        user.avatar_url = (avatar_url or "")[:500]
        user.last_login_at = now()
        db.commit()
        user_id = user.id
    request.session.clear()  # a fresh session on every sign-in
    request.session["user_id"] = user_id


def _callback_url(request: Request, provider):
    if config.PUBLIC_URL:
        return f"{config.PUBLIC_URL}/auth/callback/{provider}"
    return str(request.url_for("auth_callback", provider=provider))


async def _profile(client, provider, token):
    """(id, display name, avatar url) from the provider."""
    if provider == "github":
        resp = await client.get("user", token=token)
        resp.raise_for_status()
        u = resp.json()
        return u["id"], u.get("name") or u["login"], u.get("avatar_url", "")
    if provider == "google":
        u = token.get("userinfo") or await client.userinfo(token=token)
        return u["sub"], u.get("name") or "Player", u.get("picture", "")
    raise ValueError(provider)


@router.get("/login/{provider}")
async def login(request: Request, provider: str):
    client = oauth.create_client(provider) if provider in config.enabled_providers() else None
    if client is None:
        raise HTTPException(404, "That sign-in option isn't set up")
    return await client.authorize_redirect(request, _callback_url(request, provider))


@router.get("/callback/{provider}", name="auth_callback")
async def callback(request: Request, provider: str):
    client = oauth.create_client(provider) if provider in config.enabled_providers() else None
    if client is None:
        raise HTTPException(404, "That sign-in option isn't set up")
    try:
        token = await client.authorize_access_token(request)
        uid, name, avatar = await _profile(client, provider, token)
    except Exception as e:  # they said no, the state expired, the provider hiccuped...
        log.warning("Sign-in with %s failed: %s", provider, e)
        return RedirectResponse("/?signin=failed", status_code=303)
    sign_in(request, provider, uid, name, avatar)
    return RedirectResponse("/", status_code=303)


@router.get("/dev-login")
def dev_login(request: Request, name: str = "Test Player"):
    """Only when DEV_LOGIN=true: sign in as a made-up player, no OAuth app needed."""
    if not config.DEV_LOGIN:
        raise HTTPException(404)
    sign_in(request, "dev", name.strip().lower() or "player", name.strip() or "Player", "")
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}
