"""Database tables and connection. MySQL in docker-compose; SQLite works too (the tests use it)."""
import logging
import time
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from . import config

log = logging.getLogger("sparkle")


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class User(Base):
    """One player. They sign in with an OAuth provider, so (provider, provider_user_id) is who they are."""
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("provider", "provider_user_id", name="uq_users_provider_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(32))
    provider_user_id: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(100))
    avatar_url: Mapped[str] = mapped_column(String(500), default="")
    # Every star from every finished maze, replays included. Only ever goes up.
    total_stars: Mapped[int] = mapped_column(Integer, default=0, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    last_login_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class LevelBest(Base):
    """A player's high score on one level: their best finish (most stars, then fastest time)."""
    __tablename__ = "level_bests"
    __table_args__ = (Index("ix_level_bests_rank", "level", "stars", "time_ms"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    level: Mapped[str] = mapped_column(String(64), primary_key=True)
    stars: Mapped[int] = mapped_column(Integer)
    time_ms: Mapped[int] = mapped_column(BigInteger)
    plays: Mapped[int] = mapped_column(Integer, default=0)
    achieved_at: Mapped[datetime] = mapped_column(DateTime, default=now)


engine = create_engine(config.DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
Session = sessionmaker(engine, expire_on_commit=False)


def init_db(attempts=30):
    """Create any missing tables, waiting for the database to come up first."""
    for i in range(attempts):
        try:
            Base.metadata.create_all(engine)
            return
        except OperationalError as e:
            if i == attempts - 1:
                raise
            log.info("Waiting for the database (%s)", e.orig)
            time.sleep(2)
