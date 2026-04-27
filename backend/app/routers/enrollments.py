"""Enrollment endpoints (member-only).

The actual rules — "must have an active subscription, can't double-enroll,
can't enroll in a full class, can't cancel someone else's row" — live in
``services/enrollments.py``. This router is just plumbing: validate input
via Pydantic, delegate to the service, return the result.

That separation matters: it means the rules can be unit-tested without
booting an HTTP server, and reused if we add another way to enroll.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import require_member
from app.models.enrollment import Enrollment
from app.models.user import User
from app.schemas.classes import ClassOut
from app.schemas.enrollments import (
    EnrollmentCreate,
    EnrollmentOut,
    MyEnrollmentOut,
)
from app.services.enrollments import cancel_enrollment, enroll_member

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


@router.post("", response_model=EnrollmentOut, status_code=status.HTTP_201_CREATED)
def create_enrollment(
    body: EnrollmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_member),
):
    """The user is taken from the JWT (require_member), never the body —
    that's why ``EnrollmentCreate`` only contains ``class_id``."""
    return enroll_member(db, user, body.class_id)


@router.delete("/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_member),
):
    """Ownership check happens inside ``cancel_enrollment``."""
    cancel_enrollment(db, user, enrollment_id)


@router.get("/me", response_model=list[MyEnrollmentOut])
def my_enrollments(
    db: Session = Depends(get_db),
    user: User = Depends(require_member),
):
    """The member's own upcoming classes, with the class details inlined.

    We denormalize the class info into the response so the dashboard can
    render the schedule from a single API call.
    """
    enrollments = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user.id)
        .order_by(Enrollment.enrolled_at.desc())
        .all()
    )
    out = []
    for e in enrollments:
        # Same N+1 pattern as classes.py — fine for the demo, would be
        # worth optimizing in production.
        count = (
            db.query(Enrollment).filter(Enrollment.class_id == e.class_id).count()
        )
        out.append(
            MyEnrollmentOut(
                id=e.id,
                enrolled_at=e.enrolled_at,
                gym_class=ClassOut(
                    id=e.gym_class.id,
                    name=e.gym_class.name,
                    description=e.gym_class.description,
                    trainer_name=e.gym_class.trainer_name,
                    day_of_week=e.gym_class.day_of_week,
                    start_time=e.gym_class.start_time,
                    duration_minutes=e.gym_class.duration_minutes,
                    capacity=e.gym_class.capacity,
                    enrolled_count=count,
                ),
            )
        )
    return out
