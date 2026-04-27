"""Pydantic schemas for auth and member endpoints.

**Why have schemas separate from models?**

  - **Models** (SQLAlchemy) describe the *database* shape.
  - **Schemas** (Pydantic) describe the *API* shape — what clients send
    in and what we send back.

Keeping them separate means:
  - We never accidentally leak fields like ``password_hash`` to the client.
  - Internal columns can change without breaking the public API contract.
  - Each endpoint can pick exactly the fields it needs (e.g. ``MemberOut``
    adds subscription info on top of ``UserOut``).

Pydantic v2 also gives us automatic JSON validation, OpenAPI/Swagger doc
generation, and clear 422 errors when input is malformed — all from these
class definitions.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class RegisterRequest(BaseModel):
    # ``EmailStr`` validates RFC-compliant email syntax. Note: it rejects
    # reserved TLDs like .local — that's why the seed uses .com domains.
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    # Forward reference (string) because UserOut is defined below. Pydantic
    # resolves this when ``model_rebuild()`` is called at the bottom.
    user: "UserOut"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: UserRole
    created_at: datetime

    class Config:
        # Lets Pydantic build this schema from a SQLAlchemy ORM object
        # (rather than only from a dict). Pulls attributes via getattr().
        from_attributes = True


class MemberOut(UserOut):
    """A member as seen by a manager — includes subscription summary."""
    subscription_status: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_expires_at: Optional[datetime] = None


class PaginatedMembers(BaseModel):
    """Generic paginated wrapper for the members list.

    Returning ``total`` lets the client render "showing 1–10 of 60" and
    compute the number of pages without a second request.
    """
    items: list[MemberOut]
    total: int
    page: int
    page_size: int


class MemberStats(BaseModel):
    """Aggregate counts for the manager dashboard.

    Computed via SQL ``COUNT(...)`` on the server so we don't have to ship
    every member row to the client just to count them.
    """
    total: int
    active: int
    inactive: int


# Resolves the "UserOut" forward reference inside TokenResponse.
TokenResponse.model_rebuild()
