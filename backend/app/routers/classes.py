"""Class CRUD + roster endpoint.

Reading classes is open to any logged-in user. Creating/editing/deleting and
viewing the roster are manager-only — enforced by the ``require_manager``
dependency, which returns 403 for anyone else.

Note: this file does N+1 COUNT queries on the list endpoint (one COUNT per
class). For the demo size that's fine; for a production system the right
fix is to use a single GROUP BY query or a SQL window function. Left as a
contribution opportunity (see CONTRIBUTING.md → "Database & Performance").
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user, require_manager
from app.models.enrollment import Enrollment
from app.models.gym_class import GymClass
from app.models.user import User
from app.schemas.classes import ClassCreate, ClassOut, ClassUpdate, RosterMember

router = APIRouter(prefix="/classes", tags=["classes"])


def _class_out(gym_class: GymClass, enrolled_count: int) -> ClassOut:
    """Helper that combines a model row with its enrollment count.

    Pulled out so we don't repeat this construction in every handler."""
    return ClassOut(
        id=gym_class.id,
        name=gym_class.name,
        description=gym_class.description,
        trainer_name=gym_class.trainer_name,
        day_of_week=gym_class.day_of_week,
        start_time=gym_class.start_time,
        duration_minutes=gym_class.duration_minutes,
        capacity=gym_class.capacity,
        enrolled_count=enrolled_count,
    )


@router.get("", response_model=list[ClassOut])
def list_classes(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),  # any logged-in user
):
    classes = db.query(GymClass).order_by(GymClass.day_of_week, GymClass.start_time).all()
    out = []
    for c in classes:
        # N+1 — one COUNT per class. See module docstring.
        count = db.query(Enrollment).filter(Enrollment.class_id == c.id).count()
        out.append(_class_out(c, count))
    return out


@router.post("", response_model=ClassOut, status_code=status.HTTP_201_CREATED)
def create_class(
    body: ClassCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_manager),
):
    # ``model_dump()`` turns the Pydantic schema into a dict; ``**`` unpacks
    # it as keyword args to the SQLAlchemy model.
    gym_class = GymClass(**body.model_dump())
    db.add(gym_class)
    db.commit()
    db.refresh(gym_class)
    return _class_out(gym_class, 0)


@router.patch("/{class_id}", response_model=ClassOut)
def update_class(
    class_id: int,
    body: ClassUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_manager),
):
    gym_class = db.query(GymClass).filter(GymClass.id == class_id).first()
    if not gym_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    # ``exclude_unset=True`` gives us only the fields the client actually sent
    # — that's the difference between a real PATCH and a sneaky PUT.
    updates = body.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(gym_class, key, value)
    db.commit()
    db.refresh(gym_class)
    count = db.query(Enrollment).filter(Enrollment.class_id == gym_class.id).count()
    return _class_out(gym_class, count)


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(
    class_id: int,
    # Query params show up as ?force=true in the URL. Pydantic-style defaults.
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
    _: User = Depends(require_manager),
):
    gym_class = db.query(GymClass).filter(GymClass.id == class_id).first()
    if not gym_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    enrollment_count = (
        db.query(Enrollment).filter(Enrollment.class_id == class_id).count()
    )
    # Safety net: refuse to delete a class with people in it unless the
    # caller explicitly confirms by passing ?force=true.
    if enrollment_count > 0 and not force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Class has {enrollment_count} active enrollment(s). "
                "Pass ?force=true to delete anyway."
            ),
        )

    db.delete(gym_class)
    db.commit()


@router.get("/{class_id}/roster", response_model=list[RosterMember])
def class_roster(
    class_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_manager),
):
    """Manager-only: who is enrolled in this class."""
    gym_class = db.query(GymClass).filter(GymClass.id == class_id).first()
    if not gym_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    # Join Enrollment + User in one query — much cheaper than fetching
    # enrollments and then looking up each user separately.
    rows = (
        db.query(Enrollment, User)
        .join(User, Enrollment.user_id == User.id)
        .filter(Enrollment.class_id == class_id)
        .order_by(Enrollment.enrolled_at.asc())
        .all()
    )
    return [
        RosterMember(
            user_id=user.id,
            name=user.name,
            email=user.email,
            enrolled_at=enrollment.enrolled_at.isoformat(),
        )
        for enrollment, user in rows
    ]
