"""Pydantic schemas for the /classes endpoints.

The pattern of three schemas per resource is intentional and worth knowing:

  - ``ClassBase``    — fields common to create + read.
  - ``ClassCreate``  — what the client sends when creating.
  - ``ClassUpdate``  — same fields but all optional, for PATCH.
  - ``ClassOut``     — what the API returns. Adds derived fields (``id``,
                       ``enrolled_count``) the client doesn't supply.

Why split? Because ``id`` is set by the DB (not the client), and PATCH
should accept a partial document. Squashing them into one schema would
either leak required fields into PATCH or weaken validation on POST.
"""

from datetime import time
from typing import Optional

from pydantic import BaseModel, Field

from app.models.gym_class import DayOfWeek


class ClassBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    trainer_name: str = Field(min_length=1, max_length=120)
    day_of_week: DayOfWeek
    start_time: time
    # ge/le = "greater or equal" / "less or equal" — Pydantic enforces these
    # at validation time, before the route function runs.
    duration_minutes: int = Field(ge=15, le=240, default=60)
    capacity: int = Field(ge=1, le=200, default=20)


class ClassCreate(ClassBase):
    """Body of POST /classes. All ClassBase fields are required."""
    pass


class ClassUpdate(BaseModel):
    """Body of PATCH /classes/{id}.

    All fields are Optional so the client can update just one or two without
    having to resend the whole resource. The router uses
    ``model_dump(exclude_unset=True)`` to get only the fields the client
    actually supplied.
    """
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=1000)
    trainer_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    day_of_week: Optional[DayOfWeek] = None
    start_time: Optional[time] = None
    duration_minutes: Optional[int] = Field(default=None, ge=15, le=240)
    capacity: Optional[int] = Field(default=None, ge=1, le=200)


class ClassOut(ClassBase):
    id: int
    # Derived field — calculated by the router from a separate COUNT query.
    # Not stored on the GymClass model. (See the N+1 query optimization
    # opportunity in CONTRIBUTING.md.)
    enrolled_count: int = 0

    class Config:
        from_attributes = True


class RosterMember(BaseModel):
    """Tiny DTO for the /classes/{id}/roster endpoint."""
    user_id: int
    name: str
    email: str
    enrolled_at: str
