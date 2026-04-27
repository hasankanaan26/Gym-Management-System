"""FastAPI application entry point.

This module wires the whole backend together:

  - Creates the FastAPI app (the "application factory" pattern).
  - Configures CORS so the React dev server (a different origin) can call the API.
  - Ensures database tables exist on startup.
  - Mounts every router so the routes are reachable.

Run locally with:

    uvicorn app.main:app --reload

In production you would *not* call ``Base.metadata.create_all`` at startup —
you'd run Alembic migrations instead. We use ``create_all`` here because it
makes the demo "just work" with no extra steps. See ``alembic/README.md``
for the proper approach.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import Base, engine

# Importing ``app.models`` has a side effect: every model class gets registered
# with ``Base.metadata``. Without this import, ``create_all`` would not know
# which tables to create.
from app.models import *  # noqa: F401,F403  (register models with metadata)
from app.routers import auth, classes, enrollments, members, subscriptions


def create_app() -> FastAPI:
    """Application factory.

    Wrapping app construction in a function (instead of building the app at
    module import time) makes it easier to:
      - create separate instances for tests with different settings,
      - delay expensive setup until the app is actually used.
    """
    app = FastAPI(title=settings.PROJECT_NAME)

    # CORS = Cross-Origin Resource Sharing. The browser blocks requests from
    # one origin (e.g. http://localhost:3000) to another (http://localhost:8000)
    # unless the server explicitly allows it via these headers.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Dev shortcut: create any missing tables. In production, replace this
    # with `alembic upgrade head` run as part of deployment.
    Base.metadata.create_all(bind=engine)

    # Each router groups related endpoints. Keeping them in separate modules
    # keeps this file short and lets us evolve features independently.
    app.include_router(auth.router)
    app.include_router(classes.router)
    app.include_router(enrollments.router)
    app.include_router(members.router)
    app.include_router(subscriptions.router)

    @app.get("/health", tags=["meta"])
    def health():
        """Liveness probe — used by Docker, Kubernetes, load balancers, etc."""
        return {"status": "ok"}

    return app


# Uvicorn imports this module and looks for an ``app`` attribute by default.
app = create_app()
