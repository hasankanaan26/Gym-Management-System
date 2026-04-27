"""Centralized application configuration.

Every value the app reads from the environment lives here. Two reasons:

  1. **Single source of truth.** When you wonder "where does this setting
     come from?", you only have one file to look at.
  2. **Easy to evolve.** Today this is a plain class with ``os.getenv``.
     Tomorrow you might switch to ``pydantic-settings`` for typed validation,
     or fetch secrets from HashiCorp Vault — and the rest of the app
     wouldn't change because it only imports ``settings``.

For a production-ready upgrade, see CONTRIBUTING.md → "Secrets & Config".
"""

import os


class Settings:
    PROJECT_NAME: str = "Gym Management API"
    API_V1_PREFIX: str = ""

    # The DATABASE_URL format is dialect+driver://user:password@host:port/dbname
    # In Docker Compose, ``db`` is the service name and resolves to the
    # Postgres container's IP via Docker's internal DNS.
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://gym:gym@db:5432/gym",
    )

    # JWT secret — used to sign and verify tokens. If an attacker learns this
    # value they can mint valid tokens for any user, so in real deployments
    # this MUST come from a secret manager (Vault, AWS Secrets Manager, etc.)
    # and be rotated periodically.
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    # CORS_ORIGINS is a comma-separated list. We split it once here so the rest
    # of the app gets a real Python list.
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173",
    ).split(",")


# Importing ``settings`` (the instance) gives the rest of the app a single,
# already-loaded object — no need to re-read env vars or re-parse anything.
settings = Settings()
