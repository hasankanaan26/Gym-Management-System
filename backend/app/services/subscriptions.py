from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.subscription import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
)

PLAN_DURATIONS = {
    SubscriptionPlan.MONTHLY: timedelta(days=30),
    SubscriptionPlan.QUARTERLY: timedelta(days=90),
    SubscriptionPlan.YEARLY: timedelta(days=365),
}


def get_active_subscription(db: Session, user_id: int) -> Optional[Subscription]:
    """Return the user's active, non-expired subscription, if any."""
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
    return (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id)
        .order_by(Subscription.started_at.desc())
        .first()
    )


def create_subscription(db: Session, user_id: int, plan: SubscriptionPlan) -> Subscription:
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
