"""Enrollment business rules.

This module exists because the rules around enrolling in a class are
non-trivial and we don't want them tangled into HTTP routing code:

  1. The class must exist.
  2. The member must have an active, non-expired subscription.
  3. The member can't already be enrolled in this class.
  4. The class can't be at capacity.
  5. Members can only cancel their *own* enrollments.

Keeping these in a service module means:
  - The route is short and reads like a story (delegate, return).
  - The rules can be unit-tested without booting an HTTP server.
  - If we add another way to enroll (admin override, batch import, CLI),
    they all go through the same enforcement point.

This is the "service layer" pattern — common in larger applications.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enrollment import Enrollment
from app.models.gym_class import GymClass
from app.models.user import User
from app.services.subscriptions import get_active_subscription


def enroll_member(db: Session, user: User, class_id: int) -> Enrollment:
    """Enroll ``user`` in the class identified by ``class_id``.

    Raises HTTPException with the appropriate status code if any rule fails.
    Each ``raise`` uses a status code that maps cleanly to the HTTP semantic:
      - 404 — the class doesn't exist
      - 402 — payment required (no active subscription)
      - 409 — conflict (duplicate enrollment, or class is full)
    """
    gym_class = db.query(GymClass).filter(GymClass.id == class_id).first()
    if not gym_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    if get_active_subscription(db, user.id) is None:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="An active subscription is required to enroll",
        )

    existing = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user.id, Enrollment.class_id == class_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already enrolled in this class",
        )

    # NOTE: there's a race condition between this COUNT and the INSERT below.
    # Two concurrent enrollments at exactly the right moment could both pass
    # this check and overshoot the capacity by one. Fixing it properly needs
    # a transaction with row-level locking (``SELECT ... FOR UPDATE``) or a
    # serializable transaction isolation level. Good contribution for someone
    # learning about concurrency in databases.
    current_count = (
        db.query(Enrollment).filter(Enrollment.class_id == class_id).count()
    )
    if current_count >= gym_class.capacity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Class is full",
        )

    enrollment = Enrollment(user_id=user.id, class_id=class_id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def cancel_enrollment(db: Session, user: User, enrollment_id: int) -> None:
    """Cancel one of the calling user's enrollments.

    Returns 403 if a member tries to cancel someone else's row — never trust
    "I am user X" from the URL alone; we get the real user from the JWT.
    """
    enrollment = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found"
        )
    if enrollment.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own enrollments",
        )
    db.delete(enrollment)
    db.commit()
