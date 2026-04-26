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
    return get_active_subscription(db, user.id) or get_latest_subscription(db, user.id)
