"""API tests on a throwaway SQLite database, signing in with the dev login.

    pip install -r backend/requirements.txt pytest
    python3 -m pytest backend/tests
"""
import os
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["DEV_LOGIN"] = "true"
os.environ["SESSION_SECRET"] = "test-secret"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def signed_in(name):
    c = TestClient(app)
    c.__enter__()
    r = c.get("/auth/dev-login", params={"name": name}, follow_redirects=False)
    assert r.status_code == 303
    return c


def test_game_page_and_levels(client):
    r = client.get("/")
    assert r.status_code == 200 and "Sparkle" in r.text and "<!doctype html>" in r.text
    assert client.get("/levels/index.json").status_code == 200


def test_signed_out(client):
    me = client.get("/api/me").json()
    assert me["user"] is None
    assert {"id": "dev", "label": "Pretend (dev)"} in me["providers"]
    assert client.post("/api/finish", json={"level": "01-hello-friend", "stars": 1, "time_ms": 5000}).status_code == 401


def test_high_score_and_star_total():
    c = signed_in("Ada")
    post = lambda **kw: c.post("/api/finish", json=kw).json()

    r = post(level="01-hello-friend", stars=2, time_ms=40000)
    assert r["new_best"] and r["best"]["stars"] == 2 and r["total_stars"] == 2
    # Fewer stars but faster: not a better run, but its stars still count toward the total.
    r = post(level="01-hello-friend", stars=1, time_ms=10000)
    assert not r["new_best"] and r["best"]["stars"] == 2 and r["total_stars"] == 3
    # Same stars, faster: new high score.
    r = post(level="01-hello-friend", stars=2, time_ms=30000)
    assert r["new_best"] and r["best"]["time_ms"] == 30000 and r["best"]["plays"] == 3 and r["total_stars"] == 5
    r = post(level="surprise-big", stars=7, time_ms=90000)
    assert r["total_stars"] == 12

    mine = c.get("/api/scores").json()
    assert mine["user"]["total_stars"] == 12
    assert mine["levels"]["01-hello-friend"] == {"level": "01-hello-friend", "stars": 2, "time_ms": 30000, "plays": 3}
    assert c.get("/api/me").json()["user"]["name"] == "Ada"


def test_leaderboards():
    a, b = signed_in("Bea"), signed_in("Cy")
    a.post("/api/finish", json={"level": "03-heart-box", "stars": 2, "time_ms": 50000})
    b.post("/api/finish", json={"level": "03-heart-box", "stars": 2, "time_ms": 20000})
    scores = a.get("/api/leaderboard/levels/03-heart-box").json()["scores"]
    assert [s["name"] for s in scores[:2]] == ["Cy", "Bea"]
    players = a.get("/api/leaderboard/stars").json()["players"]
    assert players == sorted(players, key=lambda p: -p["total_stars"])
    assert a.get("/api/leaderboard/levels/nope").status_code == 404


def test_rejects_bad_finishes():
    c = signed_in("Dee")
    assert c.post("/api/finish", json={"level": "nope", "stars": 1, "time_ms": 1}).status_code == 422
    assert c.post("/api/finish", json={"level": "01-hello-friend", "stars": 99, "time_ms": 1}).status_code == 422
    assert c.post("/api/finish", json={"level": "01-hello-friend", "stars": -1, "time_ms": 1}).status_code == 422
    assert c.post("/api/finish", json={"level": "01-hello-friend", "stars": 1, "time_ms": 0}).status_code == 422


def test_logout():
    c = signed_in("Eve")
    assert c.get("/api/me").json()["user"]["name"] == "Eve"
    c.post("/auth/logout")
    assert c.get("/api/me").json()["user"] is None


def test_oauth_provider_not_configured(client):
    assert client.get("/auth/login/github", follow_redirects=False).status_code == 404
