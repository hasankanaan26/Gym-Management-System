from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import Base, engine
from app.models import *  # noqa: F401,F403  (register models with metadata)
from app.routers import auth, classes, enrollments, members, subscriptions


def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create tables on startup for dev/demo. In production, rely on Alembic.
    Base.metadata.create_all(bind=engine)

    app.include_router(auth.router)
    app.include_router(classes.router)
    app.include_router(enrollments.router)
    app.include_router(members.router)
    app.include_router(subscriptions.router)

    @app.get("/health", tags=["meta"])
    def health():
        return {"status": "ok"}

    return app


app = create_app()
