"""Pydantic schemas for /subscriptions."""

from datetime import datetime

from pydantic import BaseModel

from app.models.subscription import SubscriptionPlan, SubscriptionStatus


class SubscriptionCreate(BaseModel):
    # The only thing the client picks. Status is always 'active' on creation,
    # and the expiry date is computed server-side based on the plan.
    plan: SubscriptionPlan


class SubscriptionOut(BaseModel):
    id: int
    plan: SubscriptionPlan
    status: SubscriptionStatus
    started_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True
