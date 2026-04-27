"""User model — the ``users`` table.

A "model" is a Python class that mirrors a database table. SQLAlchemy turns
attribute access (``user.email``) into SQL queries and table creation. This
mapping is called an ORM (Object-Relational Mapper).

Key concepts shown here:

  - **Mapped[T]** — type hints that tell SQLAlchemy 2.0 the column type.
  - **Enums** — store role as a constrained string ('manager' or 'member')
    rather than a free-text column. Postgres enforces it at the DB level.
  - **server_default=func.now()** — the default value comes from Postgres
    (``NOW()``), not Python. Useful when DB and app clocks differ.
  - **relationship()** — virtual attribute that loads related rows. Combined
    with ``cascade="all, delete-orphan"``, deleting a user automatically
    cleans up their subscriptions and enrollments.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class UserRole(str, enum.Enum):
    """Role enum.

    Inheriting from ``str`` makes JSON serialization "just work" — a
    ``UserRole.MANAGER`` becomes the string ``"manager"`` in the API response.
    """
    MANAGER = "manager"
    MEMBER = "member"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # ``unique=True`` creates a unique index. ``index=True`` speeds up lookups
    # by email (every login does one). The unique constraint also doubles as
    # protection against duplicate signups.
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), nullable=False, default=UserRole.MEMBER
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Reverse relationships. ``back_populates`` keeps both sides in sync.
    # ``cascade="all, delete-orphan"`` means deleting a User also deletes
    # their subscriptions and enrollments — we don't want orphan rows.
    subscriptions = relationship(
        "Subscription", back_populates="user", cascade="all, delete-orphan"
    )
    enrollments = relationship(
        "Enrollment", back_populates="user", cascade="all, delete-orphan"
    )
