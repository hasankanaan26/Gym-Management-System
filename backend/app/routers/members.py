"""Member management endpoints (manager-only).

Endpoints:
  GET    /members            paginated list, optional ?q= search
  GET    /members/stats      total / active / inactive counts
  POST   /members            create a member (admin add)
  DELETE /members/{id}       remove a member

The list endpoint demonstrates **server-side pagination**: instead of
shipping every member to the client and paginating in JavaScript, we accept
``page`` and ``page_size`` query params and use SQL ``OFFSET``/``LIMIT``.
This scales: a thousand members costs the same as ten in network bytes.

The stats endpoint exists separately so the dashboard can show counts
without loading any member rows. Computing aggregates server-side is
almost always faster than computing them client-side.
"""

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
    """Compose a MemberOut from a User row + their subscription summary."""
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
    # Query() lets us declare validation: page>=1, page_size between 1 and 100.
    # If the client violates these, FastAPI returns a 422 before we run.
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    q: Optional[str] = Query(default=None, description="Search by name or email"),
    db: Session = Depends(get_db),
    _: User = Depends(require_manager),
):
    query = db.query(User).filter(User.role == UserRole.MEMBER)

    if q:
        # ``ilike`` = case-insensitive LIKE (Postgres extension).
        # Wrapping in % means "contains" search.
        like = f"%{q.strip()}%"
        query = query.filter(or_(User.name.ilike(like), User.email.ilike(like)))

    # Two queries: one COUNT for the total, then SELECT with offset+limit
    # for the actual page. The count is cheap because Postgres can use the
    # primary key. For very large tables you'd cache it or estimate with
    # pg_stat_user_tables.
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
    """Aggregate counts for the dashboard.

    A member is "active" if they have *any* subscription with status=ACTIVE
    and ``expires_at`` in the future. ``distinct().count()`` collapses
    multiple subscriptions per user.
    """
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
    """Manager creates a member directly. The member can log in with the
    temp password and (in a real app) would be prompted to change it."""
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
    # We restrict to role=MEMBER so a manager can't accidentally delete
    # another manager (or themselves) through this endpoint.
    user = db.query(User).filter(User.id == user_id, User.role == UserRole.MEMBER).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    db.delete(user)
    db.commit()
