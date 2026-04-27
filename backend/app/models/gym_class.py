"""GymClass model — the ``classes`` table.

A GymClass represents a recurring weekly slot (e.g. "Spin Intervals, Mondays
at 18:30, capacity 15"). Each one can have many enrollments up to ``capacity``.

Naming note: the class is called ``GymClass`` (not ``Class``) because
``class`` is a reserved keyword in Python. The DB table is still ``classes``.

Modeling limitation: this is a *template*, not an instance. There's no concept
of "the spin class on April 27th". Per-date attendance and cancellations
would require a separate ``ClassInstance`` model — see CONTRIBUTING.md →
"Bigger architecture moves".
"""

import enum
from datetime import time

from sqlalchemy import Enum, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class DayOfWeek(str, enum.Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class GymClass(Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    trainer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    day_of_week: Mapped[DayOfWeek] = mapped_column(
        Enum(DayOfWeek, name="day_of_week"), nullable=False
    )
    # ``Time`` (not ``DateTime``) — we only care about the wall-clock time.
    # When you want a real calendar slot you'd switch to DateTime + timezone.
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    # Hard cap on how many members can enroll. The business rule
    # "reject when full" lives in services/enrollments.py, not in the DB.
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=20)

    enrollments = relationship(
        "Enrollment", back_populates="gym_class", cascade="all, delete-orphan"
    )
