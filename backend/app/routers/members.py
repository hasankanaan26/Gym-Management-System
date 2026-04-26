from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import hash_password, require_manager
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User, UserRole
from app.schemas.auth import (
    MemberOut,
    MemberStats,
    PaginatedMembers,
    RegisterRequest,
    UserOut,
)
from app.services.subscriptions import (
    get_active_subscription,
    get_latest_subscription,
)

router = APIRouter(prefix="/members", tags=["members"])


def _member_out(db: Session, user: User) -> MemberOut:
    active = get_active_subscription(db, user.id)
    latest = active or get_latest_subscription(db, user.id)
    return MemberOut(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        created_at=user.created_at,
        subscription_status=(active.status.value if active else ("expired" if latest else None)),
        subscription_plan=(latest.plan.value if latest else None),
        subscription_expires_at=(latest.expires_at if latest else None),
    )


@router.get("", response_model=PaginatedMembers)
def list_members(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    q: Optional[str] = Query(default=None, description="Search by name or email"),
    db: Session = Depends(get_db),
    _: User = Depends(require_manager),
):
    query = db.query(User).filter(User.role == UserRole.MEMBER)

    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(User.name.ilike(like), User.email.ilike(like)))

    total = query.count()
    users = (
        query.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedMembers(
        items=[_member_out(db, u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=MemberStats)
def member_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_manager),
):
    total = db.query(User).filter(User.role == UserRole.MEMBER).count()
    now = datetime.now(timezone.utc)
    active = (
        db.query(User.id)
        .join(Subscription, Subscription.user_id == User.id)
        .filter(
            User.role == UserRole.MEMBER,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.expires_at > now,
        )
        .distinct()
        .count()
    )
    return MemberStats(total=total, active=active, inactive=total - active)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def add_member(
    body: RegisterRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_manager),
):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )
    user = User(
        email=body.email,
        name=body.name,
        password_hash=hash_password(body.password),
        role=UserRole.MEMBER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_manager),
):
    user = db.query(User).filter(User.id == user_id, User.role == UserRole.MEMBER).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    db.delete(user)
    db.commit()
