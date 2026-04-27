"""Subscription helpers — used by the subscriptions router and elsewhere
that needs to know "is this member subscribed right now?".

We compute "is active" from two columns at query time rather than relying
on the ``status`` column alone — that way a subscription whose ``expires_at``
has passed automatically counts as inactive without any background job
having to flip the status flag.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.subscription import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
)

# How long each plan lasts. Centralized here so the API contract and the
# logic stay in sync — pricing/duration tweaks only touch this dict.
PLAN_DURATIONS = {
    SubscriptionPlan.MONTHLY: timedelta(days=30),
    SubscriptionPlan.QUARTERLY: timedelta(days=90),
    SubscriptionPlan.YEARLY: timedelta(days=365),
}


def get_active_subscription(db: Session, user_id: int) -> Optional[Subscription]:
    """Return the user's currently-valid subscription, if any.

    "Valid" = status is ACTIVE *and* the expiry date is still in the future.
    Returning the latest one (by expiry) is intentional: if the user
    re-subscribed before the previous one expired, we want the longer one.
    """
    now = datetime.now(timezone.utc)
    sub = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.expires_at > now,
        )
        .order_by(Subscription.expires_at.desc())
        .first()
    )
    return sub


def get_latest_subscription(db: Session, user_id: int) -> Optional[Subscription]:
    """Return the user's most recent subscription regardless of status.

    Used by the manager UI to show "expired since X" for inactive members.
    """
    return (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id)
        .order_by(Subscription.started_at.desc())
        .first()
    )


def create_subscription(db: Session, user_id: int, plan: SubscriptionPlan) -> Subscription:
    """Create a new active subscription with the right expiry date for the plan."""
    now = datetime.now(timezone.utc)
    sub = Subscription(
        user_id=user_id,
        plan=plan,
        status=SubscriptionStatus.ACTIVE,
        started_at=now,
        expires_at=now + PLAN_DURATIONS[plan],
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub
