from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True


class MemberOut(UserOut):
    subscription_status: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_expires_at: Optional[datetime] = None


class PaginatedMembers(BaseModel):
    items: list[MemberOut]
    total: int
    page: int
    page_size: int


class MemberStats(BaseModel):
    total: int
    active: int
    inactive: int


TokenResponse.model_rebuild()
