"""The game's API: who's signed in, saving a finished maze, high scores and star totals."""
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from . import config
from .auth import current_user, require_user
from .db import LevelBest, Session, User, now

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import server  # noqa: E402  (the level loader lives next to the game)

router = APIRouter(prefix="/api")

SURPRISE_MAX_STARS = 500  # surprise mazes are random and trap doors carry stars along, so just a sanity cap
MAX_TIME_MS = 24 * 3600 * 1000


def level_limits():
    """Most stars you can finish each level with: its stars, plus up to 3 from each treasure chest."""
    limits = {"surprise-small": SURPRISE_MAX_STARS, "surprise-big": SURPRISE_MAX_STARS}
    for L in server.load_levels():
        cells = "".join(L["map"])
        limits[L["id"]] = cells.count("*") + 3 * cells.count("T")
    return limits


LEVEL_LIMITS = level_limits()


class Finish(BaseModel):
    level: str = Field(max_length=64)
    stars: int = Field(ge=0)
    time_ms: int = Field(gt=0, le=MAX_TIME_MS)


def user_json(u):
    return {"name": u.name, "avatar_url": u.avatar_url, "total_stars": u.total_stars}


def best_json(b):
    return {"level": b.level, "stars": b.stars, "time_ms": b.time_ms, "plays": b.plays}


def better(stars, time_ms, best):
    return best is None or stars > best.stars or (stars == best.stars and time_ms < best.time_ms)


@router.get("/me")
def me(request: Request):
    """Also how the game finds out there's a backend at all (on GitHub Pages this is a 404)."""
    u = current_user(request)
    providers = [{"id": p, "label": config.PROVIDERS[p]["label"]} for p in config.enabled_providers()]
    if config.DEV_LOGIN:
        providers.append({"id": "dev", "label": "Pretend (dev)"})
    return {"user": user_json(u) if u else None, "providers": providers}


@router.post("/finish")
def finish(run: Finish, user=Depends(require_user)):
    """Record a finished maze: add its stars to the player's total and keep it if it's a new high score."""
    limit = LEVEL_LIMITS.get(run.level)
    if limit is None:
        raise HTTPException(422, "Unknown level")
    if run.stars > limit:
        raise HTTPException(422, "More stars than that maze has")
    for attempt in range(2):
        try:
            with Session() as db, db.begin():
                best = db.scalars(
                    select(LevelBest).where(LevelBest.user_id == user.id, LevelBest.level == run.level).with_for_update()
                ).first()
                new_best = better(run.stars, run.time_ms, best)
                if best is None:
                    best = LevelBest(user_id=user.id, level=run.level, stars=run.stars, time_ms=run.time_ms, plays=0)
                    db.add(best)
                elif new_best:
                    best.stars, best.time_ms, best.achieved_at = run.stars, run.time_ms, now()
                best.plays += 1
                db.execute(update(User).where(User.id == user.id).values(total_stars=User.total_stars + run.stars))
                db.flush()
                total = db.scalar(select(User.total_stars).where(User.id == user.id))
                return {"new_best": new_best, "best": best_json(best), "total_stars": total}
        except IntegrityError:
            # Two finishes of a brand-new level raced to create its row; the retry finds it.
            if attempt:
                raise


@router.get("/scores")
def my_scores(user=Depends(require_user)):
    with Session() as db:
        bests = db.scalars(select(LevelBest).where(LevelBest.user_id == user.id)).all()
    return {"user": user_json(user), "levels": {b.level: best_json(b) for b in bests}}


@router.get("/leaderboard/stars")
def star_leaderboard(limit: int = 10):
    with Session() as db:
        users = db.scalars(
            select(User).where(User.total_stars > 0).order_by(User.total_stars.desc(), User.id).limit(min(limit, 50))
        ).all()
    return {"players": [{"name": u.name, "avatar_url": u.avatar_url, "total_stars": u.total_stars} for u in users]}


@router.get("/leaderboard/levels/{level}")
def level_leaderboard(level: str, limit: int = 10):
    if level not in LEVEL_LIMITS:
        raise HTTPException(404, "Unknown level")
    with Session() as db:
        rows = db.execute(
            select(LevelBest, User.name, User.avatar_url)
            .join(User, User.id == LevelBest.user_id)
            .where(LevelBest.level == level)
            .order_by(LevelBest.stars.desc(), LevelBest.time_ms, LevelBest.achieved_at)
            .limit(min(limit, 50))
        ).all()
    return {"level": level, "scores": [{"name": n, "avatar_url": a, **best_json(b)} for b, n, a in rows]}
