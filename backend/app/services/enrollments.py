from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enrollment import Enrollment
from app.models.gym_class import GymClass
from app.models.user import User
from app.services.subscriptions import get_active_subscription


def enroll_member(db: Session, user: User, class_id: int) -> Enrollment:
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
