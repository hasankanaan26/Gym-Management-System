from datetime import datetime

from pydantic import BaseModel

from app.models.subscription import SubscriptionPlan, SubscriptionStatus


class SubscriptionCreate(BaseModel):
    plan: SubscriptionPlan


class SubscriptionOut(BaseModel):
    id: int
    plan: SubscriptionPlan
    status: SubscriptionStatus
    started_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True
