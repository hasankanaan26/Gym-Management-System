"""Subscription model — the ``subscriptions`` table.

Each subscription belongs to one user and has a plan (monthly/quarterly/yearly),
a status (active/expired/cancelled), and an expiry date.

Modeling note: in this beginner app a "subscription" is just a row with dates
and a status flag — there's no real payment processing. In production you'd
back this with Stripe/Paddle and let webhook events drive ``status``.
See CONTRIBUTING.md → "Payments & Email".
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class SubscriptionPlan(str, enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # ``ondelete="CASCADE"`` is the database-level cascade. Combined with the
    # ORM-level ``cascade="all, delete-orphan"`` on User.subscriptions, this
    # guarantees no orphan rows even if rows are deleted via raw SQL.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan: Mapped[SubscriptionPlan] = mapped_column(
        Enum(SubscriptionPlan, name="subscription_plan"), nullable=False
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status"),
        nullable=False,
        default=SubscriptionStatus.ACTIVE,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # Note: there's no auto-expiry job. A subscription with status=ACTIVE but
    # ``expires_at`` in the past is treated as expired by the queries in
    # ``services/subscriptions.py``. A nightly job to flip the status flag
    # would be a nice contribution (Celery beat or a simple cron).
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="subscriptions")
