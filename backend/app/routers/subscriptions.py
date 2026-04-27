"""Subscription endpoints (member-only).

Subscribing here is a no-op as far as money is concerned — we just create
a row with the right expiry date and call it active. Replacing this with a
real Stripe Checkout flow is one of the contribution ideas in
CONTRIBUTING.md → "Payments & Email".
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import require_member
from app.models.user import User
from app.schemas.subscriptions import SubscriptionCreate, SubscriptionOut
from app.services.subscriptions import (
    create_subscription,
    get_active_subscription,
    get_latest_subscription,
)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("", response_model=SubscriptionOut, status_code=status.HTTP_201_CREATED)
def subscribe(
    body: SubscriptionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_member),
):
    return create_subscription(db, user.id, body.plan)


@router.get("/me", response_model=SubscriptionOut | None)
def my_subscription(
    db: Session = Depends(get_db),
    user: User = Depends(require_member),
):
    """Returns the user's current subscription (preferred) or the most recent
    one (so the UI can show "expired since X" when nothing is active)."""
    return get_active_subscription(db, user.id) or get_latest_subscription(db, user.id)
