"""Pydantic schemas for /enrollments."""

from datetime import datetime

from pydantic import BaseModel

from app.schemas.classes import ClassOut


class EnrollmentCreate(BaseModel):
    # Body for POST /enrollments. The user is taken from the JWT, not the body
    # — never trust the client to tell you which user is enrolling.
    class_id: int


class EnrollmentOut(BaseModel):
    id: int
    class_id: int
    user_id: int
    enrolled_at: datetime

    class Config:
        from_attributes = True


class MyEnrollmentOut(BaseModel):
    """Returned by GET /enrollments/me — denormalizes the class details so
    the member dashboard can render the schedule in one round-trip."""
    id: int
    enrolled_at: datetime
    gym_class: ClassOut

    class Config:
        from_attributes = True
