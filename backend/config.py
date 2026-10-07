"""Settings, read from environment variables (docker-compose loads them from .env)."""
import logging
import os
import secrets

log = logging.getLogger("sparkle")


def _flag(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./sparkle.db")

SESSION_SECRET = os.environ.get("SESSION_SECRET", "")
if not SESSION_SECRET:
    log.warning("SESSION_SECRET is not set; using a random one, so everyone is signed out when the server restarts.")
    SESSION_SECRET = secrets.token_urlsafe(32)

# Set to true once the site is served over https, so the login cookie is never sent over plain http.
COOKIE_SECURE = _flag("COOKIE_SECURE")

# The address people open the game at, e.g. https://sparkle.example.com. Used to build the OAuth
# callback URL. Leave empty to use whatever address the request came in on (fine for localhost).
PUBLIC_URL = os.environ.get("PUBLIC_URL", "").rstrip("/")

# A "pretend login" for trying things locally without registering an OAuth app. Never turn this on
# for a server other people can reach: anyone could sign in as anyone.
DEV_LOGIN = _flag("DEV_LOGIN")

PROVIDERS = {
    "github": {
        "label": "GitHub",
        "client_id": os.environ.get("GITHUB_CLIENT_ID", ""),
        "client_secret": os.environ.get("GITHUB_CLIENT_SECRET", ""),
        "oauth": dict(
            access_token_url="https://github.com/login/oauth/access_token",
            authorize_url="https://github.com/login/oauth/authorize",
            api_base_url="https://api.github.com/",
            # No scopes: the public profile (id, login, name, avatar) is all the game needs.
        ),
    },
    "google": {
        "label": "Google",
        "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
        "oauth": dict(
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid profile"},
        ),
    },
}


def enabled_providers():
    """Providers with both a client id and a secret set, in a stable order."""
    return [name for name, p in PROVIDERS.items() if p["client_id"] and p["client_secret"]]
