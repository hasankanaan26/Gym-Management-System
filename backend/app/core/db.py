"""Database engine, session factory, and SQLAlchemy declarative base.

This is the foundation every model and route depends on. Three pieces:

  1. ``engine`` — the connection pool to Postgres. One per process.
  2. ``SessionLocal`` — a factory that produces short-lived Session objects.
     A Session is what you actually use to query and persist data.
  3. ``Base`` — the parent class for every ORM model. SQLAlchemy collects
     subclasses' table metadata via this base.

The ``get_db`` function is a FastAPI dependency. Routes that need DB access
declare ``db: Session = Depends(get_db)`` and FastAPI handles open/close
automatically — even if the route raises an exception.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


# ``pool_pre_ping=True`` checks each connection is still alive before handing
# it out. Useful when your DB might restart (e.g. cloud Postgres maintenance).
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# autocommit=False / autoflush=False give us explicit control over when
# changes are persisted. We commit manually after a successful operation.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """The declarative base. Every ORM model inherits from this."""
    pass


def get_db():
    """Yields a Session and closes it when the request finishes.

    The ``yield`` (not ``return``) is what makes this a *dependency*: FastAPI
    runs the code before the yield, hands the value to your route, then runs
    the code after the yield (in the ``finally``) when the request ends.

    This is the dependency-injection pattern — your routes never see the
    engine or pool directly, only the Session for the duration of one request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
