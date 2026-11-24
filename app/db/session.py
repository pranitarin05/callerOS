from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base import Base

DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"

_database_url = settings.database_url
_connect_args = {}
if _database_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False, "timeout": 30}
    if "memory" in _database_url:
        _connect_args = {"check_same_thread": False}

engine = create_engine(
    _database_url,
    connect_args=_connect_args,
    pool_pre_ping=True,
    poolclass=StaticPool if "memory" in _database_url else None,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    from app import models  # noqa: F401
    from app.models import Profile

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.get(Profile, DEMO_USER_ID) is None:
            db.add(
                Profile(
                    id=DEMO_USER_ID,
                    email="demo@calleros.local",
                    full_name="Demo User",
                    is_active=True,
                    is_verified=True,
                )
            )
            db.commit()
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
