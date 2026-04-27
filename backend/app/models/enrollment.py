"""Enrollment model — the ``enrollments`` table.

A join table between users and classes: each row says "this user is signed
up for that class". The ``UniqueConstraint`` enforces the rule "a member
can't enroll in the same class twice" *at the database level* — even if the
application code forgot to check, Postgres would refuse the insert.

Defense-in-depth: we *also* check this in ``services/enrollments.py`` so we
can return a friendly 409 error instead of a raw integrity error.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        # Composite unique constraint — (user_id, class_id) pairs must be
        # unique across the whole table.
        UniqueConstraint("user_id", "class_id", name="uq_enrollment_user_class"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="enrollments")
    gym_class = relationship("GymClass", back_populates="enrollments")
